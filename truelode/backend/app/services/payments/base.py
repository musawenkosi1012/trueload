"""Provider-agnostic payment interface.

A concrete provider (Payonify) implements these three operations. Keeping the surface
small lets us swap gateways or stub the provider in tests without touching the API layer.
"""
from typing import Protocol, TypedDict


class CheckoutSession(TypedDict):
    checkout_url: str
    session_id: str
    reference: str


class WebhookEvent(TypedDict):
    reference: str
    status: str   # PAID | FAILED | PENDING
    amount_usd: float
    method: str | None
    raw: dict


class PaymentProvider(Protocol):
    def create_checkout(self, *, amount_usd: float, reference: str,
                        return_url: str, customer_email: str | None = None,
                        description: str | None = None) -> CheckoutSession:
        """Create a hosted checkout session and return its redirect URL."""
        ...

    def verify_webhook(self, *, headers: dict, raw_body: bytes) -> bool:
        """Verify the webhook signature against the shared secret."""
        ...

    def parse_event(self, raw_body: bytes) -> WebhookEvent:
        """Parse a verified webhook body into a normalised event."""
        ...
