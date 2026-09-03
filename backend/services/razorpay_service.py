"""Razorpay integration — Payment Link creation + webhook parsing.

Offline by default: if no API keys are set, `create_payment_link` returns a
deterministic *demo* link and the recovery outcome is simulated locally (see
recovery_service). Drop real `rzp_test_...` keys into .env to switch to live
Test Mode + real webhooks with no code changes.
"""
import os
import hmac
import hashlib
from typing import Dict, Any

try:
    import httpx
except Exception:  # httpx only needed for live mode
    httpx = None


class RazorpayService:
    def __init__(self):
        self.key_id = os.getenv("RAZORPAY_KEY_ID", "").strip()
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
        self.base_url = "https://api.razorpay.com/v1"
        # Live only when BOTH keys look real (not the placeholder).
        self.live = bool(
            self.key_id
            and self.key_secret
            and self.key_id.startswith("rzp_")
            and "YOUR_KEY" not in self.key_id
        )
        self.auth = (self.key_id, self.key_secret) if self.live else None

    async def create_payment_link(self, amount: float, description: str,
                                  reference_id: str = "",
                                  customer_name: str = "Customer",
                                  customer_email: str = "customer@example.com",
                                  customer_contact: str = "9999999999") -> Dict[str, Any]:
        if not self.live:
            # Deterministic demo link (reproducible per case).
            token = hashlib.md5(f"{reference_id}:{amount}".encode()).hexdigest()[:10]
            return {
                "id": f"plink_demo_{token}",
                "short_url": f"https://rzp.io/demo/{token}",
                "status": "created",
                "amount": int(amount * 100),
                "currency": "INR",
                "description": description,
                "reference_id": reference_id,
                "demo": True,
            }

        payload = {
            "amount": int(amount * 100),
            "currency": "INR",
            "accept_partial": False,
            "description": description,
            "reference_id": reference_id,
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_contact,
            },
            "notify": {"sms": True, "email": True},
            "reminder_enable": True,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{self.base_url}/payment_links", json=payload, auth=self.auth
            )
            resp.raise_for_status()
            data = resp.json()
            data["demo"] = False
            return data

    def verify_webhook_signature(self, body: bytes, signature: str, secret: str) -> bool:
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature or "")

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = payload.get("event", "")
        entity = (
            payload.get("payload", {})
            .get("payment_link", {})
            .get("entity", {})
        )
        return {
            "event": event,
            "link_id": entity.get("id"),
            "status": entity.get("status"),
            "amount": entity.get("amount", 0) / 100,
            "reference_id": entity.get("reference_id"),
        }
