"""Authentication: login, who-am-i, admin user creation, tiered self-registration."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.account import Account
from app.models.enums import AccountType, OrgType
from app.models.invite import Invite
from app.models.user import User
from app.services import billing, entitlements

from .utils import current_account, current_user, err, role_required

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Government / platform roles never pay.
EXEMPT_ROLES = ("REGULATOR", "ADMIN")
# Privileged roles are provisioned by the platform, never via open self-registration:
# ADMIN is a superuser and REGULATOR gets a billing-exempt oversight account.
SELF_SIGNUP_ROLES = ("MINE", "TRANSPORTER", "PROCESSOR", "BUYER", "LAB")


def _issue_token(user: User) -> str:
    return create_access_token(identity=user.id,
                               additional_claims={
                                   "role": user.role,
                                   "account_id": user.account_id,
                                   "account_type": _account_type(user)})


def _account_type(user: User) -> str | None:
    acct = db.session.get(Account, user.account_id) if user.account_id else None
    return acct.account_type if acct else None


def _me_payload(user: User) -> dict:
    out = user.to_dict()
    acct = db.session.get(Account, user.account_id) if user.account_id else None
    if acct:
        out["account"] = acct.to_dict()
        wallet = billing.get_wallet(acct.id)
        out["balance_usd"] = round(wallet.balance_usd, 2) if wallet else 0.0
        out["account_type"] = acct.account_type
        out["account_status"] = acct.status
        out["features"] = entitlements.features_for(acct)
    return out


@bp.post("/login")
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=(data.get("email") or "").lower()).first()
    if not user or not user.check_password(data.get("password", "")):
        return err("invalid credentials", 401)
    from app.models.base import utcnow
    user.last_login_at = utcnow()
    db.session.commit()
    return jsonify({"token": _issue_token(user), "user": _me_payload(user)})


@bp.get("/me")
@role_required()
def me():
    user = current_user()
    return jsonify(_me_payload(user) if user else {})


@bp.post("/users")
@role_required("ADMIN")
def create_user():
    data = request.get_json() or {}
    user = User(email=data["email"].lower(), name=data.get("name", ""),
                role=data["role"], account_id=data.get("account_id"))
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@bp.get("/accounts")
def list_accounts():
    accts = Account.query.order_by(Account.name).all()
    return jsonify([a.to_dict() for a in accts])


@bp.post("/register")
def register():
    """Tiered self-registration.

    INDIVIDUAL -> one Account(INDIVIDUAL) + one owner User. Flat fee, solo.
    ENTERPRISE -> one Account(ENTERPRISE) + owner User (manages staff). Per-seat + PAYG.
    REGULATOR/ADMIN roles -> exempt account (never billed).
    """
    data = request.get_json() or {}

    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    password = data.get("password", "")
    role = (data.get("role") or "").upper()
    account_type = (data.get("account_type") or AccountType.INDIVIDUAL).upper()

    if not email or not name or not password or not role:
        return err("email, name, password and role are required", 400)
    if len(password) < 6:
        return err("password must be at least 6 characters", 400)
    if role not in OrgType.ALL:
        return err("invalid role", 400)
    # Block self-registration of privileged roles (ADMIN superuser, exempt REGULATOR).
    if role not in SELF_SIGNUP_ROLES:
        return err("this role is provisioned by the platform, not self-registration", 403)
    if account_type not in AccountType.ALL:
        return err("invalid account_type", 400)
    if User.query.filter_by(email=email).first():
        return err("email already registered", 409)

    exempt = role in EXEMPT_ROLES
    # Account name: company name for enterprise, the person's name for individuals.
    acct_name = (data.get("account_name") or data.get("org_name") or "").strip()
    if account_type == AccountType.ENTERPRISE and not acct_name and not exempt:
        return err("account_name is required for an enterprise account", 400)

    account = Account(name=acct_name or name, account_type=account_type,
                      primary_role=role, exempt=exempt,
                      country=data.get("country", "Zimbabwe"))
    db.session.add(account)
    db.session.flush()

    user = User(email=email, name=name, role=role, account_id=account.id,
                is_account_owner=True)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    # Wallet + subscription. Give a small starting credit so the demo can act.
    billing.provision_account(account, starting_balance=0.0)
    db.session.commit()

    return jsonify({"token": _issue_token(user), "user": _me_payload(user)}), 201


@bp.get("/invite/<code>")
def invite_preview(code):
    """Public: show which org + role a join code grants, before registering."""
    invite = Invite.query.filter_by(code=code.upper(), active=True).first()
    if not invite:
        return err("invalid or revoked code", 404)
    acct = db.session.get(Account, invite.account_id)
    return jsonify({"valid": True, "code": invite.code, "role": invite.role,
                    "organisation": acct.name if acct else None})


@bp.post("/join")
def join():
    """Public: join an existing ENTERPRISE org with an invite code -> staff user."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    password = data.get("password", "")
    code = (data.get("code") or "").strip().upper()

    if not email or not name or not password or not code:
        return err("name, email, password and code are required", 400)
    if len(password) < 6:
        return err("password must be at least 6 characters", 400)

    invite = Invite.query.filter_by(code=code, active=True).first()
    if not invite:
        return err("invalid or revoked code", 404)
    if User.query.filter_by(email=email).first():
        return err("email already registered", 409)

    account = db.session.get(Account, invite.account_id)
    if not account:
        return err("organisation not found", 404)

    # Join as staff: role fixed by the code, not the owner of the account.
    user = User(email=email, name=name, role=invite.role, account_id=account.id,
                is_account_owner=False, active=True)
    user.set_password(password)
    db.session.add(user)
    invite.uses += 1
    db.session.commit()

    return jsonify({"token": _issue_token(user), "user": _me_payload(user)}), 201
