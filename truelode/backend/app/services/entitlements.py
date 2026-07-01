"""Tier entitlements: which capabilities each account tier unlocks.

A single source of truth mapping account_type -> feature flags, mirroring a modern SaaS
Individual / Enterprise model. The API gates real capabilities through `has()`, and the
frontend reads `features_for()` to show the plan matrix and hide locked actions.

Only enforced, real features live here — no vapourware flags.
"""
from app.models.account import Account
from app.models.enums import AccountType

# Feature keys (stable identifiers used by API gates + the frontend).
TEAM = "team"                 # invite & manage staff users
MULTI_SITE = "multi_site"     # operate more than one site
PAY_AS_YOU_GO = "pay_as_you_go"   # per-batch metered billing (vs flat)
PASSPORT = "passport"         # issue provenance passports
PRIORITY_SUPPORT = "priority_support"

# Human labels for the plan matrix UI.
FEATURE_LABELS = {
    TEAM: "Team management (multiple staff)",
    MULTI_SITE: "Multiple sites",
    PAY_AS_YOU_GO: "Pay-as-you-go metered billing",
    PASSPORT: "Issue provenance passports",
    PRIORITY_SUPPORT: "Priority support",
}

# Per-tier feature set. Exempt accounts (REGULATOR/ADMIN) get everything.
_INDIVIDUAL = {
    TEAM: False,
    MULTI_SITE: False,
    PAY_AS_YOU_GO: False,   # flat plan
    PASSPORT: True,
    PRIORITY_SUPPORT: False,
}
_ENTERPRISE = {
    TEAM: True,
    MULTI_SITE: True,
    PAY_AS_YOU_GO: True,
    PASSPORT: True,
    PRIORITY_SUPPORT: True,
}
_ALL_ON = {k: True for k in FEATURE_LABELS}

TIER_FEATURES = {
    AccountType.INDIVIDUAL: _INDIVIDUAL,
    AccountType.ENTERPRISE: _ENTERPRISE,
}

# Limits per tier (None = unlimited).
SITE_LIMIT = {AccountType.INDIVIDUAL: 1, AccountType.ENTERPRISE: None}


def features_for(account: Account | None) -> dict[str, bool]:
    if not account:
        return {k: False for k in FEATURE_LABELS}
    if account.exempt:
        return dict(_ALL_ON)
    return dict(TIER_FEATURES.get(account.account_type, _INDIVIDUAL))


def has(account: Account | None, feature: str) -> bool:
    return features_for(account).get(feature, False)


def site_limit(account: Account | None) -> int | None:
    """Max sites the account may own (None = unlimited)."""
    if not account or account.exempt:
        return None
    return SITE_LIMIT.get(account.account_type, 1)


def matrix() -> dict:
    """Full tier/feature matrix for the pricing + upgrade UI."""
    return {
        "features": [{"key": k, "label": FEATURE_LABELS[k]} for k in FEATURE_LABELS],
        "tiers": {
            AccountType.INDIVIDUAL: _INDIVIDUAL,
            AccountType.ENTERPRISE: _ENTERPRISE,
        },
    }
