"""Registry CRUD: accounts and sites."""
from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.account import Account
from app.models.site import Site
from app.services import entitlements

from .utils import current_account, err, role_required

bp = Blueprint("registry", __name__, url_prefix="/api")


@bp.get("/accounts")
@role_required()
def list_accounts():
    return jsonify([a.to_dict() for a in Account.query.all()])


@bp.post("/accounts")
@role_required("ADMIN")
def create_account():
    d = request.get_json() or {}
    acct = Account(name=d["name"], account_type=d.get("account_type", "ENTERPRISE"),
                   primary_role=d.get("primary_role", d.get("type", "MINE")),
                   country=d.get("country", "Zimbabwe"), kyc_ref=d.get("kyc_ref"),
                   exempt=d.get("exempt", False))
    db.session.add(acct)
    db.session.commit()
    return jsonify(acct.to_dict()), 201


@bp.patch("/accounts/<account_id>")
@role_required("ADMIN")
def update_account(account_id):
    d = request.get_json() or {}
    acct = db.session.get(Account, account_id)
    if not acct:
        return err("account not found", 404)
    if "status" in d:
        acct.status = d["status"]
    if "exempt" in d:
        acct.exempt = bool(d["exempt"])
    db.session.commit()
    return jsonify(acct.to_dict())


@bp.get("/sites")
@role_required()
def list_sites():
    q = Site.query
    if account_id := (request.args.get("account_id") or request.args.get("org_id")):
        q = q.filter_by(account_id=account_id)
    return jsonify([s.to_dict() for s in q.all()])


@bp.post("/sites")
@role_required("ADMIN", "MINE", "PROCESSOR")
def create_site():
    d = request.get_json() or {}
    account_id = d.get("account_id") or d.get("org_id")

    # Enforce the tier's site limit (INDIVIDUAL = 1, ENTERPRISE = unlimited).
    acct = current_account()
    limit = entitlements.site_limit(acct)
    if acct and not acct.exempt and limit is not None:
        owned = Site.query.filter_by(account_id=acct.id).count()
        if account_id == acct.id and owned >= limit:
            return err(f"your plan allows {limit} site(s) — upgrade to Enterprise "
                       "for multiple sites", 403)

    site = Site(name=d["name"], type=d["type"], account_id=account_id,
                lat=d["lat"], lng=d["lng"], address=d.get("address"))
    db.session.add(site)
    db.session.commit()
    return jsonify(site.to_dict()), 201
