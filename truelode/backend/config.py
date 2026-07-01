"""Runtime configuration loaded from environment."""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _f(key: str, default: float) -> float:
    return float(os.getenv(key, default))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt")
    # Default access token life is 15 min; there is no refresh token, so use a
    # longer working session to avoid silent 401s mid-use.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_HOURS", "12")))
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///truelode.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WEIGHT_TOLERANCE_PCT = _f("WEIGHT_TOLERANCE_PCT", 2.0)
    GRADE_TOLERANCE_PCT = _f("GRADE_TOLERANCE_PCT", 5.0)
    CORRIDOR_BUFFER_M = _f("CORRIDOR_BUFFER_M", 500)
    STOP_DWELL_MIN = _f("STOP_DWELL_MIN", 15)

    PASSPORT_KEY_PATH = os.getenv("PASSPORT_KEY_PATH", "passport_key.pem")
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:3000")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

    # Frontend base used to build Payonify return URLs (where the checkout lands back).
    WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://localhost:3001")

    # --- Billing -------------------------------------------------------------
    BILLING_CURRENCY = os.getenv("BILLING_CURRENCY", "USD")
    PER_BATCH_FEE_USD = _f("PER_BATCH_FEE_USD", 5.0)     # ORG pay-as-you-go per batch
    SEAT_FEE_USD = _f("SEAT_FEE_USD", 10.0)              # ORG per active staff / cycle
    INDIVIDUAL_FLAT_USD = _f("INDIVIDUAL_FLAT_USD", 15.0)  # INDIVIDUAL flat / cycle

    # --- Payonify (https://api.payonify.com) ---------------------------------
    PAYONIFY_BASE_URL = os.getenv("PAYONIFY_BASE_URL", "https://api.payonify.com")
    PAYONIFY_SECRET_KEY = os.getenv("PAYONIFY_SECRET_KEY", "sk_test_demo")
    PAYONIFY_WEBHOOK_SECRET = os.getenv("PAYONIFY_WEBHOOK_SECRET", "whsec_demo")
