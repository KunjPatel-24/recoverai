"""Razorpay webhook — resolves a case when a real payment link is paid.

Only used in LIVE mode (real rzp_test_ keys). In offline/demo mode the outcome
is simulated by recovery_service, so this endpoint is not needed for the demo
— but it's here and correct for when you wire real Test Mode.
"""
import os
from datetime import datetime

from fastapi import APIRouter, Request, Depends, Header
from sqlalchemy.orm import Session

from models import get_db, RecoveryCase, RecoveryStatus
from services.razorpay_service import RazorpayService
from services.audit_service import AuditService

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str = Header(None),
):
    body = await request.body()
    payload = await request.json()

    razorpay = RazorpayService()
    audit = AuditService(db)

    # Verify signature when a webhook secret is configured.
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "").strip()
    if secret and not razorpay.verify_webhook_signature(body, x_razorpay_signature, secret):
        return {"status": "invalid_signature"}

    parsed = razorpay.parse_webhook(payload)
    case = db.query(RecoveryCase).filter(
        RecoveryCase.razorpay_link_id == parsed["link_id"]
    ).first()
    if not case:
        return {"status": "ignored", "reason": "Case not found"}

    if "paid" in (parsed["event"] or "") or parsed["status"] == "paid":
        case.status = RecoveryStatus.SUCCESS.value
        case.actual_recovered = parsed["amount"]
        case.resolved_at = datetime.utcnow()
        db.commit()
        audit.log(
            case_id=case.id,
            agent="WEBHOOK_HANDLER",
            action="RECOVERY_SUCCESS",
            details=f"Payment received via webhook. Amount: ₹{parsed['amount']:.0f}",
            status="SUCCESS",
            amount=parsed["amount"],
        )
        return {"status": "success", "case_id": case.id,
                "amount_recovered": parsed["amount"]}

    return {"status": "received", "event": parsed["event"]}
