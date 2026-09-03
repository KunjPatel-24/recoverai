"""Agent 3: Recovery Strategist.

Generates the four interventions, scores each one's success probability from
the case context, and selects the highest *expected recovery* where
    expected_recovery = amount_at_risk x success_probability.
Deterministic — same inputs always pick the same strategy.
"""
from typing import Dict, Any

from models import RecoveryCase, RecoveryStatus, InterventionType
from services.audit_service import AuditService


class RecoveryStrategist:
    def __init__(self, db):
        self.db = db
        self.audit = AuditService(db)

    def generate_strategies(self, case: RecoveryCase, transaction) -> Dict[str, Any]:
        amount = case.amount_at_risk
        payment_method = transaction.payment_method

        strategies = []

        retry_prob = self._retry_probability(case, transaction)
        strategies.append({
            "type": InterventionType.SMART_RETRY.value,
            "success_probability": retry_prob,
            "expected_recovery": round(amount * retry_prob, 2),
            "cost": 0,
            "time_to_recover": "Immediate",
            "rationale": f"Retry after a temporary failure ({transaction.failure_reason}).",
        })

        link_prob = self._link_probability(case, transaction)
        strategies.append({
            "type": InterventionType.PAYMENT_LINK.value,
            "success_probability": link_prob,
            "expected_recovery": round(amount * link_prob, 2),
            "cost": 0,
            "time_to_recover": "5-30 minutes",
            "rationale": f"Fresh payment link via a {payment_method} alternative.",
        })

        reminder_prob = self._reminder_probability(case, transaction)
        strategies.append({
            "type": InterventionType.REMINDER.value,
            "success_probability": reminder_prob,
            "expected_recovery": round(amount * reminder_prob, 2),
            "cost": 0,
            "time_to_recover": "1-24 hours",
            "rationale": "Contextual nudge for abandoned or pending payments.",
        })

        escalation_prob = self._escalation_probability(case, transaction)
        strategies.append({
            "type": InterventionType.HUMAN_ESCALATION.value,
            "success_probability": escalation_prob,
            "expected_recovery": round(amount * escalation_prob, 2),
            "cost": 500,
            "time_to_recover": "24-72 hours",
            "rationale": "Manual intervention for complex or high-value cases.",
        })

        strategies.sort(key=lambda x: x["expected_recovery"], reverse=True)
        selected = strategies[0]

        case.status = RecoveryStatus.STRATEGY_SELECTED.value
        case.selected_strategy = selected["type"]
        case.expected_recovery = selected["expected_recovery"]
        case.recovery_probability = selected["success_probability"]
        self.db.commit()

        self.audit.log(
            case_id=case.id,
            agent="RECOVERY_STRATEGIST",
            action="STRATEGY_SELECTED",
            details=(
                f"Selected: {selected['type']} | "
                f"Expected: ₹{selected['expected_recovery']:.0f} | "
                f"Prob: {selected['success_probability']*100:.0f}%"
            ),
            status="SUCCESS",
            amount=case.amount_at_risk,
        )

        return {
            "case_id": case.id,
            "strategies": strategies,
            "selected_strategy": selected["type"],
            "expected_recovery": selected["expected_recovery"],
            "recovery_probability": selected["success_probability"],
        }

    # ---- probability models (deterministic heuristics) -------------------- #
    # The four probabilities are shaped so the *best* action genuinely depends
    # on the failure type: temporary failures favour a retry, instrument
    # problems favour a fresh payment link, and abandonment/overdue favour a
    # reminder. That's what makes the Strategist's choice vary across cases.
    def _retry_probability(self, case, tx) -> float:
        fr = tx.failure_reason
        base = 0.30
        if fr == "BANK_TIMEOUT":
            base = 0.86           # temporary glitch → just retry
        elif fr == "NETWORK_ERROR":
            base = 0.82
        elif fr == "UPI_FAILURE":
            base = 0.55
        elif fr == "INSUFFICIENT_FUNDS":
            base = 0.48
        elif fr in ("CARD_EXPIRED", "INVALID_DETAILS"):
            base = 0.18           # retrying the same broken instrument won't help
        elif fr == "DECLINED_BY_BANK":
            base = 0.22
        if tx.previous_attempts > 2:
            base -= 0.20
        if case.customer_intent == "LOW":
            base -= 0.15
        return round(max(0.10, min(0.95, base)), 2)

    def _link_probability(self, case, tx) -> float:
        fr = tx.failure_reason
        base = 0.55
        if fr == "CARD_EXPIRED":
            base = 0.90           # need a new instrument → fresh link
        elif fr == "INVALID_DETAILS":
            base = 0.87
        elif fr == "SUBSCRIPTION_PAYMENT_PENDING":
            base = 0.82           # re-collect the renewal via a link
        elif fr == "UPI_FAILURE":
            base = 0.80
        elif fr == "DECLINED_BY_BANK":
            base = 0.74           # try an alternative method
        elif fr == "INSUFFICIENT_FUNDS":
            base = 0.60
        elif fr in ("BANK_TIMEOUT", "NETWORK_ERROR"):
            base = 0.58           # below retry, so retry wins for these
        if case.category == "CHECKOUT_ABANDONMENT":
            base = 0.55
        elif case.category == "INVOICE_OVERDUE":
            base = 0.45
        if tx.previous_attempts > 2:
            base -= 0.10
        if case.customer_intent == "LOW":
            base -= 0.12
        return round(max(0.10, min(0.95, base)), 2)

    def _reminder_probability(self, case, tx) -> float:
        base = 0.40
        if case.category == "CHECKOUT_ABANDONMENT":
            base = 0.78           # a nudge brings them back to finish
        elif case.category == "INVOICE_OVERDUE":
            base = 0.62           # payment reminder for an overdue invoice
        elif tx.failure_reason == "INSUFFICIENT_FUNDS":
            base = 0.55
        if case.customer_intent == "LOW":
            base -= 0.18
        return round(max(0.10, min(0.85, base)), 2)

    def _escalation_probability(self, case, tx) -> float:
        # Kept modest: real escalation is the Safety Guardian's job (authority /
        # confidence), not usually the Strategist's first choice.
        base = 0.35
        if case.amount_at_risk > 40000:
            base = 0.55
        if case.customer_intent == "LOW":
            base += 0.08
        return round(max(0.15, min(0.70, base)), 2)
