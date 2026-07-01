"""Shared API helpers: auth context, role guards and billing gates."""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, jwt_required, verify_jwt_in_request

from app.extensions import db
from app.models.account import Account
from app.models.user import User


def current_user() -> User | None:
    claims = get_jwt()
    return db.session.get(User, claims.get("sub")) if claims else None


def current_account() -> Account | None:
    claims = get_jwt()
    account_id = claims.get("account_id") if claims else None
    return db.session.get(Account, account_id) if account_id else None


def role_required(*roles: str):
    """Allow only listed roles (ADMIN always allowed)."""
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def inner(*args, **kwargs):
            verify_jwt_in_request()
            role = get_jwt().get("role")
            if role != "ADMIN" and roles and role not in roles:
                return jsonify({"error": "forbidden", "role": role}), 403
            return fn(*args, **kwargs)
        return inner
    return wrapper


def owner_required(fn):
    """Allow only an ENTERPRISE account owner (or ADMIN)."""
    @wraps(fn)
    @jwt_required()
    def inner(*args, **kwargs):
        verify_jwt_in_request()
        if get_jwt().get("role") == "ADMIN":
            return fn(*args, **kwargs)
        user = current_user()
        if not user or not user.is_account_owner:
            return jsonify({"error": "account owner only"}), 403
        return fn(*args, **kwargs)
    return inner


def feature_required(feature: str):
    """Gate an endpoint on a tier entitlement (see services/entitlements.py)."""
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def inner(*args, **kwargs):
            verify_jwt_in_request()
            from app.services import entitlements
            if not entitlements.has(current_account(), feature):
                return jsonify({"error": "feature not in your plan",
                                "feature": feature, "upgrade": "ENTERPRISE"}), 403
            return fn(*args, **kwargs)
        return inner
    return wrapper


def err(message: str, code: int = 400):
    return jsonify({"error": message}), code
