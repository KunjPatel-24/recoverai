"""Agent 2: Root Cause Analyst.

Deterministic diagnosis: maps the raw failure reason to a plain-language root
cause, a confidence score, and an inferred customer-intent signal. No LLM —
so it's reproducible and instant. (An LLM can be dropped in behind this same
interface later without touching the pipeline.)
"""
from typing import Dict, Any

from models import RecoveryCase, RecoveryStatus
from services.audit_service import AuditService


CAUSE_MAP = {
    "BANK_TIMEOUT": {
        "cause": "Temporary bank-side degradation",
        "confidence": 0.91,
        "customer_intent": "HIGH",
        "recoverable": True,
        "explanation": "Bank response timeout indicates a temporary infrastructure issue, not customer intent.",
    },
    "NETWORK_ERROR": {
        "cause": "Transient network connectivity issue",
        "confidence": 0.88,
        "customer_intent": "HIGH",
        "recoverable": True,
        "explanation": "Network interruption during payment flow. Customer likely unaware of failure.",
    },
    "INSUFFICIENT_FUNDS": {
        "cause": "Customer liquidity constraint",
        "confidence": 0.85,
        "customer_intent": "MEDIUM",
        "recoverable": True,
        "explanation": "Account balance issue. Retry after 24-48 hours or offer a payment link.",
    },
    "CARD_EXPIRED": {
        "cause": "Expired payment instrument",
        "confidence": 0.95,
        "customer_intent": "HIGH",
        "recoverable": True,
        "explanation": "Customer likely unaware of expiry. Payment link with a new instrument recommended.",
    },
    "DECLINED_BY_BANK": {
        "cause": "Bank risk policy decline",
        "confidence": 0.72,
        "customer_intent": "MEDIUM",
        "recoverable": False,
        "explanation": "Bank declined for risk reasons. Alternative payment method may work.",
    },
    "CHECKOUT_INCOMPLETE": {
        "cause": "Customer abandoned checkout session",
        "confidence": 0.78,
        "customer_intent": "MEDIUM",
        "recoverable": True,
        "explanation": "Session abandoned. Reminder or simplified payment link may recover.",
    },
    "SUBSCRIPTION_PAYMENT_PENDING": {
        "cause": "Subscription renewal pending",
        "confidence": 0.82,
        "customer_intent": "HIGH",
        "recoverable": True,
        "explanation": "Recurring payment not processed. Customer likely intends to continue.",
    },
    "INVOICE_OVERDUE": {
        "cause": "Invoice payment overdue",
        "confidence": 0.80,
        "customer_intent": "LOW",
        "recoverable": True,
        "explanation": "Payment deadline exceeded. Escalation may be needed for high values.",
    },
    "UPI_FAILURE": {
        "cause": "UPI system degradation",
        "confidence": 0.86,
        "customer_intent": "HIGH",
        "recoverable": True,
        "explanation": "UPI-specific failure. Card or netbanking alternative recommended.",
    },
    "INVALID_DETAILS": {
        "cause": "Incorrect payment credentials",
        "confidence": 0.90,
        "customer_intent": "HIGH",
        "recoverable": True,
        "explanation": "Data entry error. A fresh payment link usually resolves it.",
    },
}

_FALLBACK = {
    "cause": "Unclassified failure",
    "confidence": 0.50,
    "customer_intent": "UNKNOWN",
    "recoverable": False,
    "explanation": "Insufficient data for a confident diagnosis.",
}


class RootCauseAgent:
    def __init__(self, db):
        self.db = db
        self.audit = AuditService(db)

    def analyze(self, case: RecoveryCase, transaction) -> Dict[str, Any]:
        failure_reason = transaction.failure_reason or "UNKNOWN"
        previous_attempts = transaction.previous_attempts

        result = dict(CAUSE_MAP.get(failure_reason, _FALLBACK))  # copy

        # Repeated failed attempts lower our confidence and the intent signal.
        if previous_attempts > 2:
            result["confidence"] = max(0.30, result["confidence"] - 0.15)
            result["customer_intent"] = "LOW" if previous_attempts > 3 else "MEDIUM"

        case.status = RecoveryStatus.ANALYZING.value
        case.root_cause = result["cause"]
        case.root_cause_confidence = result["confidence"]
        case.customer_intent = result["customer_intent"]
        # Deterministic default explanation. If an LLM key is configured, this
        # gets replaced with a live-generated one when the case is opened
        # (see recovery_service.get_case_details).
        case.root_cause_explanation = result["explanation"]
        case.explanation_source = "rules"
        self.db.commit()

        self.audit.log(
            case_id=case.id,
            agent="ROOT_CAUSE_ANALYST",
            action="ROOT_CAUSE_IDENTIFIED",
            details=f"{result['cause']} | Confidence: {result['confidence']*100:.0f}% | Intent: {result['customer_intent']}",
            status="SUCCESS",
            amount=case.amount_at_risk,
        )

        return {
            "case_id": case.id,
            "root_cause": result["cause"],
            "confidence": result["confidence"],
            "customer_intent": result["customer_intent"],
            "recoverable": result["recoverable"],
            "explanation": result["explanation"],
        }
