"""End-to-end vertical slice through the HTTP API + Socket layer."""
import pytest

from app.extensions import db
from app.models.account import Account
from app.models.billing import Wallet
from app.models.enums import OrgType, SiteType, WeighKind
from app.models.route import Route
from app.models.site import Site
from app.models.user import User

CORRIDOR = [[-20.08, 31.80], [-18.90, 31.05], [-17.88, 30.70]]


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def world(app):
    mine = Account(name="Mine", primary_role=OrgType.MINE)
    trans = Account(name="Trans", primary_role=OrgType.TRANSPORTER)
    proc = Account(name="Proc", primary_role=OrgType.PROCESSOR)
    lab = Account(name="Lab", primary_role=OrgType.LAB)
    buyer = Account(name="Buyer", primary_role=OrgType.BUYER)
    reg = Account(name="Reg", primary_role=OrgType.REGULATOR)
    db.session.add_all([mine, trans, proc, lab, buyer, reg])
    db.session.flush()
    # Fund wallets so the per-batch PAYG gate passes during the test.
    for acct in (mine, proc, lab):
        db.session.add(Wallet(account_id=acct.id, balance_usd=100.0))
    msite = Site(name="Pit", type=SiteType.MINE, account_id=mine.id, lat=-20.08, lng=31.80)
    psite = Site(name="Plant", type=SiteType.PLANT, account_id=proc.id, lat=-17.88, lng=30.70)
    db.session.add_all([msite, psite])
    db.session.flush()
    route = Route(name="R", origin_site_id=msite.id, dest_site_id=psite.id,
                  path=CORRIDOR, buffer_m=2000)
    db.session.add(route)
    for acct, role in [(mine, OrgType.MINE), (trans, OrgType.TRANSPORTER),
                       (proc, OrgType.PROCESSOR), (lab, OrgType.LAB),
                       (buyer, OrgType.BUYER), (reg, OrgType.REGULATOR)]:
        u = User(email=f"{role}@t.test".lower(), name=role, role=role,
                 account_id=acct.id, is_account_owner=True)
        u.set_password("pw")
        db.session.add(u)
    db.session.commit()
    return {"mine_site": msite.id, "plant_site": psite.id, "route": route.id,
            "proc_org": proc.id, "buyer_org": buyer.id}


def _token(client, role):
    r = client.post("/api/auth/login", json={"email": f"{role}@t.test",
                                             "password": "pw"})
    return {"Authorization": "Bearer " + r.get_json()["token"]}


def test_full_chain(client, world):
    mine_h = _token(client, OrgType.MINE)
    trans_h = _token(client, OrgType.TRANSPORTER)
    proc_h = _token(client, OrgType.PROCESSOR)
    buyer_h = _token(client, OrgType.BUYER)
    reg_h = _token(client, OrgType.REGULATOR)

    # 1. Birth a batch (30 t raw ore).
    r = client.post("/api/loadtickets", headers=mine_h, json={
        "mine_site_id": world["mine_site"], "net_weight_kg": 30000,
        "grade_pct": 1.5, "route_id": world["route"], "lat": -20.08, "lng": 31.80})
    assert r.status_code == 201
    body = r.get_json()
    batch_id, trip_id = body["batch"]["id"], body["trip"]["id"]
    # Batch lookups accept the human TL- code as well as the internal id.
    assert client.get(f"/api/batches/{body['batch']['code']}",
                      headers=mine_h).status_code == 200

    # 2. Off-route GPS ping -> flag. Pings are org-bound: the custodian (mine)
    #    may post, a bystander haulier may not.
    ping = {"trip_id": trip_id, "pings": [{"lat": -18.90, "lng": 32.6, "speed": 40}]}
    r = client.post("/api/gps/bulk", headers=trans_h, json=ping)
    assert r.status_code == 403
    r = client.post("/api/gps/bulk", headers=mine_h, json=ping)
    assert any(f["type"] == "OFF_ROUTE" for f in r.get_json()["flags"])

    # 3. Mine offers custody to the plant; processor scans the batch QR to accept.
    r = client.post(f"/api/batches/{batch_id}/transfer", headers=mine_h,
                    json={"to_org_id": world["proc_org"]})
    assert r.status_code == 201
    handover_id = r.get_json()["id"]
    r = client.post(f"/api/handovers/{handover_id}/accept", headers=proc_h,
                    json={"qr_token": body["batch"]["qr_token"]})
    assert r.status_code == 200

    # 4. Weight mismatch on arrival (34 t -> top-up) -> reconcile fails.
    r = client.post("/api/weighevents", headers=proc_h, json={
        "batch_id": body["batch"]["code"], "kind": WeighKind.PLANT_IN,
        "net_kg": 34000})
    assert r.get_json()["reconcile"]["ok"] is False

    # 4b. The flagged party cannot clear its own anomaly; only the regulator
    #     can, and only with a written justification (kept on the ledger).
    flags = client.get("/api/flags", headers=reg_h).get_json()
    mismatch = next(f for f in flags
                    if f["type"] == "WEIGHT_MISMATCH" and f["status"] == "OPEN")
    r = client.post(f"/api/flags/{mismatch['id']}/clear", headers=proc_h,
                    json={"note": "trust me"})
    assert r.status_code == 403
    r = client.post(f"/api/flags/{mismatch['id']}/clear", headers=reg_h, json={})
    assert r.status_code == 400
    r = client.post(f"/api/flags/{mismatch['id']}/clear", headers=reg_h,
                    json={"note": "re-weigh confirmed 30 t"})
    assert r.status_code == 200

    # 5. Processing: 8 t concentrate basis -> 1 t product (use clean child).
    r = client.post("/api/processing-steps", headers=proc_h, json={
        "parent_ids": [batch_id], "out_stage": "PRODUCT", "out_kg": 4000,
        "out_grade": 11.0, "unit_count": 20, "unit_label": "drums", "tol_pct": 50})
    child_id = r.get_json()["child"]["id"]

    # 6. Issue passport + public verify.
    r = client.post(f"/api/passport/{child_id}", headers=proc_h)
    token = r.get_json()["qr_token"]
    r = client.get(f"/api/verify/{token}")
    data = r.get_json()
    assert data["signature_valid"] is True
    assert data["ledger_intact"] is True
    assert data["passport"]["snapshot"]["final_batch"]["unit_count"] == 20

    # 7. Handover by QR scan: resolve the scanned token back to the batch.
    r = client.get(f"/api/batches/resolve/{token}", headers=proc_h)
    assert r.status_code == 200
    assert r.get_json()["id"] == child_id
    assert client.get("/api/batches/resolve/bogus", headers=proc_h).status_code == 404

    # 8. Buyer takes custody only by presenting the passport QR token.
    r = client.post(f"/api/batches/{child_id}/claim", headers=buyer_h, json={})
    assert r.status_code == 400
    r = client.post(f"/api/batches/{child_id}/claim", headers=buyer_h,
                    json={"qr_token": "forged"})
    assert r.status_code == 400
    r = client.post(f"/api/batches/{child_id}/claim", headers=buyer_h,
                    json={"qr_token": token})
    assert r.status_code == 200
    assert r.get_json()["custodian"] == world["buyer_org"]
