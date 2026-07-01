"""Staff management for ENTERPRISE account owners."""
from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app.extensions import db
from app.models.enums import OrgType
from app.models.invite import Invite
from app.models.ledger import LedgerEntry
from app.models.user import User

from app.services import entitlements

from .utils import current_account, current_user, err, feature_required, owner_required

bp = Blueprint("staff", __name__, url_prefix="/api/staff")


def _my_account_id() -> str | None:
    user = current_user()
    return user.account_id if user else None


def _activity_index(user_ids: list[str]) -> dict[str, dict]:
    """One grouped query: per-user event count + latest event (no N+1)."""
    if not user_ids:
        return {}
    rows = (db.session.query(LedgerEntry.actor_id,
                             func.count(LedgerEntry.seq),
                             func.max(LedgerEntry.seq))
            .filter(LedgerEntry.actor_id.in_(user_ids))
            .group_by(LedgerEntry.actor_id).all())
    out: dict[str, dict] = {}
    for actor_id, count, last_seq in rows:
        last = db.session.get(LedgerEntry, last_seq)
        out[actor_id] = {
            "event_count": count,
            "last_event": {"event_type": last.event_type,
                           "ts": last.ts.isoformat() if last and last.ts else None}
            if last else None,
        }
    return out


@bp.get("")
@owner_required
def list_staff():
    acct_id = _my_account_id()
    staff = User.query.filter_by(account_id=acct_id).order_by(User.created_at).all()
    activity = _activity_index([u.id for u in staff])
    rows = []
    for u in staff:
        row = u.to_dict()
        row.update(activity.get(u.id, {"event_count": 0, "last_event": None}))
        rows.append(row)
    return jsonify(rows)


@bp.get("/<user_id>/activity")
@owner_required
def staff_activity(user_id):
    user = db.session.get(User, user_id)
    if not user or user.account_id != _my_account_id():
        return err("not found", 404)
    limit = min(int(request.args.get("limit", 50)), 200)
    rows = (LedgerEntry.query.filter_by(actor_id=user_id)
            .order_by(LedgerEntry.seq.desc()).limit(limit).all())
    return jsonify([{"seq": r.seq, "event_type": r.event_type,
                     "ts": r.ts.isoformat() if r.ts else None,
                     "payload": r.payload} for r in rows])


@bp.post("/<user_id>/reset-password")
@owner_required
def reset_password(user_id):
    d = request.get_json() or {}
    password = d.get("password", "")
    user = db.session.get(User, user_id)
    if not user or user.account_id != _my_account_id():
        return err("not found", 404)
    if len(password) < 6:
        return err("password must be at least 6 characters", 400)
    user.set_password(password)
    db.session.commit()
    return jsonify({"ok": True, "id": user.id})


@bp.post("")
@owner_required
@feature_required(entitlements.TEAM)
def add_staff():
    d = request.get_json() or {}
    email = (d.get("email") or "").strip().lower()
    role = (d.get("role") or "").upper()
    password = d.get("password", "")
    if not email or not role or not password:
        return err("email, role and password are required", 400)
    if role not in OrgType.ALL:
        return err("invalid role", 400)
    if len(password) < 6:
        return err("password must be at least 6 characters", 400)
    if User.query.filter_by(email=email).first():
        return err("email already registered", 409)

    user = User(email=email, name=(d.get("name") or "").strip(), role=role,
                account_id=_my_account_id(), is_account_owner=False, active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@bp.patch("/<user_id>")
@owner_required
def update_staff(user_id):
    d = request.get_json() or {}
    user = db.session.get(User, user_id)
    if not user or user.account_id != _my_account_id():
        return err("not found", 404)
    if "role" in d and d["role"].upper() in OrgType.ALL:
        user.role = d["role"].upper()
    if "active" in d:
        user.active = bool(d["active"])
    if "name" in d:
        user.name = d["name"]
    db.session.commit()
    return jsonify(user.to_dict())


@bp.delete("/<user_id>")
@owner_required
def deactivate_staff(user_id):
    user = db.session.get(User, user_id)
    if not user or user.account_id != _my_account_id():
        return err("not found", 404)
    if user.is_account_owner:
        return err("cannot deactivate the account owner", 400)
    user.active = False  # stops seat billing; keeps history intact
    db.session.commit()
    return jsonify(user.to_dict())


# ----- invite codes -------------------------------------------------------------

@bp.get("/invites")
@owner_required
def list_invites():
    rows = (Invite.query.filter_by(account_id=_my_account_id())
            .order_by(Invite.created_at.desc()).all())
    return jsonify([i.to_dict() for i in rows])


@bp.post("/invites")
@owner_required
@feature_required(entitlements.TEAM)
def create_invite():
    d = request.get_json() or {}
    role = (d.get("role") or "").upper()
    if role not in OrgType.ALL:
        return err("invalid role", 400)
    invite = Invite(account_id=_my_account_id(), role=role)
    db.session.add(invite)
    db.session.commit()
    return jsonify(invite.to_dict()), 201


@bp.post("/invites/<invite_id>/revoke")
@owner_required
def revoke_invite(invite_id):
    invite = db.session.get(Invite, invite_id)
    if not invite or invite.account_id != _my_account_id():
        return err("not found", 404)
    invite.active = False
    db.session.commit()
    return jsonify(invite.to_dict())
