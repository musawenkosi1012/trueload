"""Entitlements API: the tier/feature matrix and the caller's own feature set."""
from flask import Blueprint, jsonify

from app.services import entitlements

from .utils import current_account, role_required

bp = Blueprint("entitlements", __name__, url_prefix="/api/entitlements")


@bp.get("/matrix")
def matrix():
    """Public tier/feature comparison for pricing + upgrade screens."""
    return jsonify(entitlements.matrix())


@bp.get("/me")
@role_required()
def my_features():
    acct = current_account()
    return jsonify({
        "account_type": acct.account_type if acct else None,
        "features": entitlements.features_for(acct),
        "site_limit": entitlements.site_limit(acct),
    })
