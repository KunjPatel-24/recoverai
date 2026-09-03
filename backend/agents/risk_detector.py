"""Agent 1: Revenue Risk Detector.

Scans transactions and promotes anything that isn't SUCCESS into a
RecoveryCase.

Changes vs. the original scaffold:
  * Deterministic case IDs (RCV_<txn id>) instead of random UUIDs, so the
    whole demo is reproducible AND re-running detection is idempotent.
  * Skips transactions that already have a case (no duplicate cases when
    /process is called more than once).
"""
from typing import List, Dict, Any, Optional

from models import Transaction, RecoveryCase, RecoveryStatus, RiskCategory, Priority
from services.audit_service import AuditService


class RiskDetector:
    def __init__(self, db):
        self.db = db
        self.audit = AuditService(db)

    def detect_risks(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        cases = []
        for tx in transactions:
            if str(tx.status).upper() == "SUCCESS":
                continue
            case = self._analyze_transaction(tx)
            if case:
                cases.append(case)
        return cases

    def _analyze_transaction(self, tx: Transaction) -> Optional[Dict[str, Any]]:
        status = str(tx.status).upper()
        risk_detected = False
        category = None
        priority = Priority.LOW

        if status == "FAILED":
            risk_detected = True
            category = RiskCategory.PAYMENT_FAILURE
            if tx.failure_reason in ["BANK_TIMEOUT", "NETWORK_ERROR"]:
                priority = Priority.HIGH
            elif tx.failure_reason == "INSUFFICIENT_FUNDS":
                priority = Priority.MEDIUM
            else:
                priority = Priority.HIGH
        elif status == "ABANDONED":
            risk_detected = True
            category = RiskCategory.CHECKOUT_ABANDONMENT
            priority = Priority.MEDIUM
        elif status == "PENDING":
            risk_detected = True
            category = RiskCategory.SUBSCRIPTION_FAILED
            priority = Priority.HIGH if tx.previous_attempts > 1 else Priority.MEDIUM
        elif status == "OVERDUE":
            risk_detected = True
            category = RiskCategory.INVOICE_OVERDUE
            priority = Priority.HIGH if tx.amount > 20000 else Priority.MEDIUM

        if not risk_detected:
            return None

        # Deterministic, idempotent case id.
        case_id = f"RCV_{tx.id}"
        existing = self.db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if existing:
            return {
                "case_id": existing.id,
                "transaction_id": tx.id,
                "risk_detected": True,
                "amount_at_risk": existing.amount_at_risk,
                "category": existing.category,
                "priority": existing.priority,
                "failure_reason": tx.failure_reason,
                "payment_method": tx.payment_method,
                "previous_attempts": tx.previous_attempts,
                "reused": True,
            }

        case = RecoveryCase(
            id=case_id,
            transaction_id=tx.id,
            amount_at_risk=tx.amount,
            category=category.value,
            priority=priority.value,
            status=RecoveryStatus.DETECTED.value,
            max_interventions=2,
        )
        tx.is_at_risk = True
        self.db.add(case)
        self.db.commit()

        self.audit.log(
            case_id=case_id,
            agent="RISK_DETECTOR",
            action="RISK_DETECTED",
            details=f"Transaction {tx.id}: {tx.status} | {tx.failure_reason} | Amount: ₹{tx.amount:.0f}",
            status="SUCCESS",
            amount=tx.amount,
        )

        return {
            "case_id": case_id,
            "transaction_id": tx.id,
            "risk_detected": True,
            "amount_at_risk": tx.amount,
            "category": category.value,
            "priority": priority.value,
            "failure_reason": tx.failure_reason,
            "payment_method": tx.payment_method,
            "previous_attempts": tx.previous_attempts,
        }
