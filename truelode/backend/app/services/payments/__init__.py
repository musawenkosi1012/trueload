"""Payment provider package. Use get_provider() to obtain the active gateway."""
from .base import PaymentProvider
from .payonify import PayonifyProvider

_provider: PaymentProvider | None = None


def get_provider() -> PaymentProvider:
    global _provider
    if _provider is None:
        _provider = PayonifyProvider()
    return _provider
