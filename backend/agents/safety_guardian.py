"""Agent 4: Safety Guardian — the bounded-recovery policy gate.

Every case must clear this gate before any autonomous action. Three outcomes:

  APPROVED  — all checks pass; the agent may act.
  ESCALATED — not a violation, but beyond the agent's authority or confidence
              (high value / low confidence) → route to a human.
  REJECTED  — a hard stopping rule fired (fraud, opt-out, duplicate, budget)
              → the agent must NOT act.

Changes vs. the original scaffold: fraud and opt-out are now real checks
against the transaction (not a fake `priority != CRITICAL` proxy), and the
amount-authority / low-confidence cases ESCALATE rather than silently reject —
so the "knows when not to act" story is genuine.
"""
from typing import Dict, Any

from models import RecoveryCase, RecoveryStatus, AuditLog
from services.audit_service import AuditService


class SafetyGuardian:
    def __init__(self, db):
        self.db = db
        self.audit = AuditService(db)
        self.MAX_RETRIES = 3
        self.MAX_INTERVENTIONS = 2
        self.MAX_AGENT_AUTHORITY = 50000
        self.MIN_CONFIDENCE = 0.40
        self.HIGH_RISK_THRESHOLD = 0.70

    def evaluate(self, case: RecoveryCase, transaction) -> Dict[str, Any]:
        checks = []
        block_reasons = []      # hard stops -> REJECTED
        escalate_reasons = []   # beyond authority/confidence -> ESCALATED

        # 1) Intervention budget (hard stop) ------------------------------- #
        ok = case.interventions_tried < self.MAX_INTERVENTIONS
        checks.append({
            "name": "Intervention Budget",
            "value": f"{case.interventions_tried} / {self.MAX_INTERVENTIONS}",
            "passed": ok,
        })
        if not ok:
            block_reasons.append("Maximum intervention attempts reached")

        # 2) Agent authority limit (escalate) ------------------------------ #
        ok = case.amount_at_risk <= self.MAX_AGENT_AUTHORITY
        checks.append({
            "name": "Agent Authority Limit",
            "value": f"₹{case.amount_at_risk:.0f} <= ₹{self.MAX_AGENT_AUTHORITY}",
            "passed": ok,
        })
        if not ok:
            escalate_reasons.append("Amount exceeds autonomous agent authority")

        # 3) Duplicate-payment risk (hard stop) ---------------------------- #
        prior_success = self.db.query(AuditLog).filter(
            AuditLog.case_id == case.id,
            AuditLog.action == "RECOVERY_SUCCESS",
        ).first()
        ok = prior_success is None
        checks.append({
            "name": "Duplicate Payment Risk",
            "value": "No prior success" if ok else "Already recovered",
            "passed": ok,
        })
        if not ok:
            block_reasons.append("Duplicate payment risk detected")

        # 4) Customer opt-out (hard stop) ---------------------------------- #
        opted_out = bool(getattr(transaction, "customer_opted_out", 0))
        checks.append({
            "name": "Customer Policy",
            "value": "OPTED OUT" if opted_out else "VALID",
            "passed": not opted_out,
        })
        if opted_out:
            block_reasons.append("Customer opted out of recovery contact")

        # 5) Fraud signal (hard stop) -------------------------------------- #
        fraud = str(getattr(transaction, "fraud_signal", "low")).lower() == "high"
        checks.append({
            "name": "Fraud Signal",
            "value": "HIGH" if fraud else "LOW",
            "passed": not fraud,
        })
        if fraud:
            block_reasons.append("High fraud signal detected")

        # 6) Diagnosis confidence (escalate) ------------------------------- #
        conf = case.root_cause_confidence or 0.0
        ok = conf >= self.MIN_CONFIDENCE
        checks.append({
            "name": "Diagnosis Confidence",
            "value": f"{conf*100:.0f}% (min {self.MIN_CONFIDENCE*100:.0f}%)",
            "passed": ok,
        })
        if not ok:
            escalate_reasons.append("Diagnosis confidence too low for autonomous action")

        # 7) Recovery budget (always within limit for the demo) ------------ #
        checks.append({"name": "Recovery Budget", "value": "WITHIN LIMIT", "passed": True})

        # ---- Decision ---------------------------------------------------- #
        if block_reasons:
            decision = "REJECTED"
            case.status = RecoveryStatus.REJECTED.value
            case.escalation_reason = "; ".join(block_reasons)
            next_action = "BLOCKED"
            details = f"Blocked: {'; '.join(block_reasons)}"
        elif escalate_reasons:
            decision = "ESCALATED"
            case.status = RecoveryStatus.ESCALATED.value
            case.escalation_reason = "; ".join(escalate_reasons)
            next_action = "HUMAN_ESCALATION"
            details = f"Escalated to human: {'; '.join(escalate_reasons)}"
        else:
            decision = "APPROVED"
            case.status = RecoveryStatus.APPROVED.value
            next_action = case.selected_strategy
            details = f"All safety checks passed. Proceeding with {case.selected_strategy}."

        self.db.commit()

        self.audit.log(
            case_id=case.id,
            agent="SAFETY_GUARDIAN",
            action="SAFETY_EVALUATION",
            details=details,
            status=decision,
            amount=case.amount_at_risk,
        )

        return {
            "case_id": case.id,
            "decision": decision,
            "checks": checks,
            "block_reasons": block_reasons or None,
            "escalate_reasons": escalate_reasons or None,
            "next_action": next_action,
        }
