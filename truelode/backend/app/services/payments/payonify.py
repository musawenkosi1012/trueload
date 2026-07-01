"""Payonify gateway (https://api.payonify.com).

Stripe-style REST API: Bearer secret key (sk_test_/sk_live_), JSON, /v1/ prefix,
resources Charges/Checkout/Refunds/Payouts/Webhooks, HMAC-signed webhooks.

NOTE: only the Introduction doc page was available locally, so the exact Checkout
request/response field names and the webhook signature header are best-effort and
isolated here. Confirm them against the Checkout + Webhooks doc pages before going live.
When a real `sk_live_`/`sk_test_` key is configured the provider calls the API; with the
demo placeholder key it returns a simulated hosted-checkout URL so the flow is testable.
"""
import hashlib
import hmac
import json
import urllib.error
import urllib.request

from flask import current_app

SIGNATURE_HEADER = "X-Payonify-Signature"


class PayonifyProvider:
    # ---- config -----------------------------------------------------------
    @property
    def _base(self) -> str:
        return current_app.config["PAYONIFY_BASE_URL"].rstrip("/")

    @property
    def _key(self) -> str:
        return current_app.config["PAYONIFY_SECRET_KEY"]

    @property
    def _webhook_secret(self) -> str:
        return current_app.config["PAYONIFY_WEBHOOK_SECRET"]

    @property
    def _is_demo(self) -> bool:
        # Placeholder key => no live credentials; simulate instead of calling out.
        return self._key.endswith("_demo") or not self._key.startswith("sk_")

    # ---- checkout ---------------------------------------------------------
    def create_checkout(self, *, amount_usd, reference, return_url,
                        customer_email=None, description=None):
        if self._is_demo:
            # Simulated hosted checkout — a local page can confirm via the webhook.
            web = current_app.config["WEB_BASE_URL"].rstrip("/")
            url = (f"{web}/billing/mock-checkout?reference={reference}"
                   f"&amount={amount_usd}&return_url={return_url}")
            return {"checkout_url": url, "session_id": f"cs_demo_{reference}",
                    "reference": reference}

        payload = {
            "amount": round(amount_usd * 100),  # minor units (cents)
            "currency": current_app.config.get("BILLING_CURRENCY", "USD"),
            "reference": reference,
            "return_url": return_url,
            "customer_email": customer_email,
            "description": description or "Truelode wallet top-up",
        }
        data = self._post("/v1/checkout", payload)
        return {
            "checkout_url": data.get("checkout_url") or data.get("url"),
            "session_id": data.get("id") or data.get("session_id", ""),
            "reference": reference,
        }

    # ---- webhook ----------------------------------------------------------
    def verify_webhook(self, *, headers, raw_body):
        sig = headers.get(SIGNATURE_HEADER) or headers.get(SIGNATURE_HEADER.lower())
        if not sig:
            return False
        expected = hmac.new(self._webhook_secret.encode(), raw_body,
                            hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, sig)

    def parse_event(self, raw_body):
        body = json.loads(raw_body.decode() or "{}")
        data = body.get("data", body)
        raw_status = (data.get("status") or body.get("type") or "").upper()
        status = ("PAID" if raw_status in ("PAID", "SUCCESS", "SUCCEEDED",
                                           "CHARGE.SUCCEEDED", "COMPLETED")
                  else "FAILED" if raw_status in ("FAILED", "CHARGE.FAILED",
                                                  "DECLINED")
                  else "PENDING")
        amount = data.get("amount", 0)
        amount_usd = amount / 100 if amount and amount > 1000 else float(amount or 0)
        return {
            "reference": data.get("reference") or data.get("metadata", {}).get("reference"),
            "status": status,
            "amount_usd": amount_usd,
            "method": data.get("method") or data.get("payment_method"),
            "raw": body,
        }

    # ---- transport --------------------------------------------------------
    def _post(self, path: str, payload: dict) -> dict:
        req = urllib.request.Request(
            self._base + path,
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {self._key}",
                     "Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="ignore")
            raise RuntimeError(f"Payonify error {e.code}: {detail}") from e

    def sign_for_test(self, raw_body: bytes) -> str:
        """Helper to forge a valid signature when simulating a webhook locally."""
        return hmac.new(self._webhook_secret.encode(), raw_body,
                        hashlib.sha256).hexdigest()
