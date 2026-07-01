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
    proc = Account(name="Proc", primary_role=OrgType.PROCESSOR)
    lab = Account(name="Lab", primary_role=OrgType.LAB)
    db.session.add_all([mine, proc, lab])
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
    for acct, role in [(mine, OrgType.MINE), (proc, OrgType.PROCESSOR),
                       (lab, OrgType.LAB)]:
        u = User(email=f"{role}@t.test".lower(), name=role, role=role,
                 account_id=acct.id, is_account_owner=True)
        u.set_password("pw")
        db.session.add(u)
    db.session.commit()
    return {"mine_site": msite.id, "plant_site": psite.id, "route": route.id}


def _token(client, role):
    r = client.post("/api/auth/login", json={"email": f"{role}@t.test",
                                             "password": "pw"})
    return {"Authorization": "Bearer " + r.get_json()["token"]}


def test_full_chain(client, world):
    mine_h = _token(client, OrgType.MINE)
    proc_h = _token(client, OrgType.PROCESSOR)

    # 1. Birth a batch (30 t raw ore).
    r = client.post("/api/loadtickets", headers=mine_h, json={
        "mine_site_id": world["mine_site"], "net_weight_kg": 30000,
        "grade_pct": 1.5, "route_id": world["route"], "lat": -20.08, "lng": 31.80})
    assert r.status_code == 201
    body = r.get_json()
    batch_id, trip_id = body["batch"]["id"], body["trip"]["id"]

    # 2. Off-route GPS ping -> flag.
    r = client.post("/api/gps/bulk", headers=mine_h, json={
        "trip_id": trip_id, "pings": [{"lat": -18.90, "lng": 32.6, "speed": 40}]})
    assert any(f["type"] == "OFF_ROUTE" for f in r.get_json()["flags"])

    # 3. Weight mismatch on arrival (34 t -> top-up) -> reconcile fails.
    r = client.post("/api/weighevents", headers=proc_h, json={
        "batch_id": batch_id, "kind": WeighKind.PLANT_IN, "net_kg": 34000})
    assert r.get_json()["reconcile"]["ok"] is False

    # 4. Processing: 8 t concentrate basis -> 1 t product (use clean child).
    r = client.post("/api/processing-steps", headers=proc_h, json={
        "parent_ids": [batch_id], "out_stage": "PRODUCT", "out_kg": 4000,
        "out_grade": 11.0, "unit_count": 20, "unit_label": "drums", "tol_pct": 50})
    child_id = r.get_json()["child"]["id"]

    # 5. Issue passport + public verify.
    r = client.post(f"/api/passport/{child_id}", headers=proc_h)
    token = r.get_json()["qr_token"]
    r = client.get(f"/api/verify/{token}")
    data = r.get_json()
    assert data["signature_valid"] is True
    assert data["ledger_intact"] is True
    assert data["passport"]["snapshot"]["final_batch"]["unit_count"] == 20

    # 6. Handover by QR scan: resolve the scanned token back to the batch.
    r = client.get(f"/api/batches/resolve/{token}", headers=proc_h)
    assert r.status_code == 200
    assert r.get_json()["id"] == child_id
    assert client.get("/api/batches/resolve/bogus", headers=proc_h).status_code == 404
