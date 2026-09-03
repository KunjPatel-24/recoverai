"""Recovery service — orchestrates the full agent pipeline and executes
approved recoveries.

Pipeline per case:
    Risk Detector -> Root Cause -> Strategist -> Safety Guardian
Only APPROVED cases are executed. In offline/demo mode the payment outcome is
*simulated deterministically* from the case's recovery probability, so the
dashboard shows a real, reproducible recovery rate without a live webhook.
"""
import random
from datetime import datetime
from typing import Dict, Any, Optional

from models import Transaction, RecoveryCase, RecoveryStatus
from agents.risk_detector import RiskDetector
from agents.root_cause_agent import RootCauseAgent
from agents.recovery_strategist import RecoveryStrategist
from agents.safety_guardian import SafetyGuardian
from services.audit_service import AuditService
from services.razorpay_service import RazorpayService
from services import llm_service


class RecoveryService:
    def __init__(self, db):
        self.db = db
        self.risk_detector = RiskDetector(db)
        self.root_cause = RootCauseAgent(db)
        self.strategist = RecoveryStrategist(db)
        self.safety = SafetyGuardian(db)
        self.audit = AuditService(db)
        self.razorpay = RazorpayService()

    # ------------------------------------------------------------------ #
    # Pipeline
    # ------------------------------------------------------------------ #
    def process_batch(self) -> Dict[str, Any]:
        transactions = self.db.query(Transaction).all()
        detected = self.risk_detector.detect_risks(transactions)

        results = []
        decisions = {"APPROVED": 0, "ESCALATED": 0, "REJECTED": 0}
        for case_data in detected:
            tx = self.db.query(Transaction).filter(
                Transaction.id == case_data["transaction_id"]
            ).first()
            case = self.db.query(RecoveryCase).filter(
                RecoveryCase.id == case_data["case_id"]
            ).first()
            if not case or not tx:
                continue

            # Don't re-diagnose a case that's already been executed/closed.
            if case.status in (RecoveryStatus.SUCCESS.value, RecoveryStatus.FAILED.value):
                continue

            root_cause = self.root_cause.analyze(case, tx)
            strategy = self.strategist.generate_strategies(case, tx)
            safety = self.safety.evaluate(case, tx)
            decisions[safety["decision"]] = decisions.get(safety["decision"], 0) + 1

            results.append({
                "case_id": case.id,
                "amount": case.amount_at_risk,
                "root_cause": root_cause,
                "strategy": strategy,
                "safety": safety,
            })

        return {
            "processed": len(results),
            "decisions": decisions,
            "total_at_risk": sum(r["amount"] for r in results),
            "cases": results,
        }

    # ------------------------------------------------------------------ #
    # Execution
    # ------------------------------------------------------------------ #
    async def execute_case(self, case_id: str) -> Dict[str, Any]:
        case = self.db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            return {"error": "Case not found"}
        if case.status != RecoveryStatus.APPROVED.value:
            return {"skipped": True, "case_id": case_id,
                    "reason": f"Not approved (status={case.status})"}

        tx = self.db.query(Transaction).filter(
            Transaction.id == case.transaction_id
        ).first()

        # Payment Link strategy -> create a link (demo or live).
        link_info = None
        if case.selected_strategy == "PAYMENT_LINK":
            link = await self.razorpay.create_payment_link(
                amount=case.amount_at_risk,
                description=f"Recovery for {case.transaction_id}",
                reference_id=case.id,
            )
            case.razorpay_link_id = link.get("id")
            case.razorpay_link_url = link.get("short_url")
            link_info = {"link_id": link.get("id"), "link_url": link.get("short_url"),
                         "demo": link.get("demo", False)}

        case.interventions_tried += 1
        case.status = RecoveryStatus.EXECUTING.value
        self.db.commit()

        self.audit.log(
            case_id=case.id,
            agent="EXECUTOR",
            action="ACTION_EXECUTED",
            details=f"Executed {case.selected_strategy}" +
                    (f" | link {case.razorpay_link_url}" if link_info else ""),
            status="SUCCESS",
            amount=case.amount_at_risk,
        )

        # LIVE mode: a real webhook will resolve the case, so stop here.
        if self.razorpay.live:
            return {"case_id": case.id, "action": case.selected_strategy,
                    "status": "EXECUTING", "link": link_info, "awaiting_webhook": True}

        # OFFLINE/DEMO mode: resolve deterministically from the probability.
        return self._simulate_outcome(case, tx, link_info)

    async def execute_all_approved(self) -> Dict[str, Any]:
        approved = self.db.query(RecoveryCase).filter(
            RecoveryCase.status == RecoveryStatus.APPROVED.value
        ).all()
        executed, recovered = 0, 0.0
        for case in approved:
            res = await self.execute_case(case.id)
            if res.get("outcome") == "SUCCESS":
                recovered += res.get("amount_recovered", 0)
            executed += 1
        return {"executed": executed, "recovered": recovered}

    def _simulate_outcome(self, case: RecoveryCase, tx, link_info) -> Dict[str, Any]:
        """Deterministic pass/fail from recovery_probability (offline demo)."""
        seed = self._seed_for(case.id)
        rng = random.Random(seed)
        success = rng.random() < (case.recovery_probability or 0.0)

        if success:
            case.status = RecoveryStatus.SUCCESS.value
            case.actual_recovered = case.amount_at_risk
            case.resolved_at = datetime.utcnow()
            self.db.commit()
            self.audit.log(
                case_id=case.id, agent="OUTCOME_MONITOR", action="RECOVERY_SUCCESS",
                details=f"Payment recovered via {case.selected_strategy}. "
                        f"Amount: ₹{case.amount_at_risk:.0f}",
                status="SUCCESS", amount=case.amount_at_risk,
            )
            outcome = "SUCCESS"
        else:
            case.status = RecoveryStatus.FAILED.value
            case.resolved_at = datetime.utcnow()
            self.db.commit()
            self.audit.log(
                case_id=case.id, agent="OUTCOME_MONITOR", action="RECOVERY_FAILED",
                details=f"{case.selected_strategy} did not recover the payment.",
                status="FAILED", amount=case.amount_at_risk,
            )
            outcome = "FAILED"

        return {
            "case_id": case.id,
            "action": case.selected_strategy,
            "outcome": outcome,
            "amount_recovered": case.actual_recovered,
            "link": link_info,
            "demo": True,
        }

    @staticmethod
    def _seed_for(case_id: str) -> int:
        digits = "".join(ch for ch in case_id if ch.isdigit())
        return int(digits) if digits else abs(hash(case_id)) % (2 ** 31)

    # ------------------------------------------------------------------ #
    # Read models (serialized dicts for the API)
    # ------------------------------------------------------------------ #
    def list_cases(self):
        cases = (
            self.db.query(RecoveryCase)
            .order_by(RecoveryCase.amount_at_risk.desc())
            .all()
        )
        return [self._case_dict(c) for c in cases]

    def get_case_details(self, case_id: str) -> Optional[Dict[str, Any]]:
        case = self.db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            return None
        tx = self.db.query(Transaction).filter(
            Transaction.id == case.transaction_id
        ).first()

        # Live LLM explanation (only if a key is configured, and only once per
        # case). Falls back silently to the deterministic explanation.
        self._maybe_generate_llm_explanation(case, tx)

        trail = self.audit.get_trail(case_id)
        return {
            "case": self._case_dict(case),
            "transaction": self._tx_dict(tx) if tx else None,
            "audit_trail": [self._audit_dict(a) for a in trail],
        }

    def _maybe_generate_llm_explanation(self, case: RecoveryCase, tx) -> None:
        model_tag = f"llm:{llm_service.model_name()}"
        if not llm_service.llm_enabled():
            return
        if (case.explanation_source or "") == model_tag:
            return  # already generated for this model — cache hit
        text = llm_service.generate_root_cause_explanation(
            transaction_id=case.transaction_id,
            amount=case.amount_at_risk,
            failure_reason=(tx.failure_reason if tx else ""),
            category=case.category,
            previous_attempts=(tx.previous_attempts if tx else 0),
            cause=case.root_cause,
            confidence=case.root_cause_confidence,
            customer_intent=case.customer_intent,
            selected_strategy=case.selected_strategy,
        )
        if text:
            case.root_cause_explanation = text
            case.explanation_source = model_tag
            self.db.commit()
            self.audit.log(
                case_id=case.id,
                agent="ROOT_CAUSE_ANALYST",
                action="LLM_EXPLANATION",
                details=f"Root-cause explanation generated live by {llm_service.model_name()}.",
                status="SUCCESS",
                amount=case.amount_at_risk,
            )

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        cases = self.db.query(RecoveryCase).all()
        total_at_risk = sum(c.amount_at_risk for c in cases)
        total_recovered = sum(c.actual_recovered or 0 for c in cases)
        expected = sum(c.expected_recovery or 0 for c in cases)
        recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk else 0

        status_counts, category_counts = {}, {}
        # Real policy-enforcement counts (what the Safety Guardian actually did).
        enforcement = {"blocked_total": 0, "escalations": 0, "fraud_blocks": 0,
                       "optout_blocks": 0, "duplicate_blocks": 0}
        for c in cases:
            status_counts[c.status] = status_counts.get(c.status, 0) + 1
            cat = category_counts.setdefault(c.category, {"count": 0, "amount": 0})
            cat["count"] += 1
            cat["amount"] += c.amount_at_risk

            reason = (c.escalation_reason or "").lower()
            if c.status == RecoveryStatus.ESCALATED.value:
                enforcement["escalations"] += 1
            elif c.status == RecoveryStatus.REJECTED.value:
                enforcement["blocked_total"] += 1
                if "fraud" in reason:
                    enforcement["fraud_blocks"] += 1
                if "opted out" in reason:
                    enforcement["optout_blocks"] += 1
                if "duplicate" in reason:
                    enforcement["duplicate_blocks"] += 1

        closed = {RecoveryStatus.SUCCESS.value, RecoveryStatus.FAILED.value,
                  RecoveryStatus.REJECTED.value, RecoveryStatus.ESCALATED.value}
        return {
            "total_at_risk": round(total_at_risk, 2),
            "total_recovered": round(total_recovered, 2),
            "expected_recovery": round(expected, 2),
            "recovery_rate": round(recovery_rate, 1),
            "active_cases": len([c for c in cases if c.status not in closed]),
            "total_cases": len(cases),
            "enforcement": enforcement,
            "status_breakdown": status_counts,
            "category_breakdown": category_counts,
        }

    # ---- serializers -------------------------------------------------- #
    @staticmethod
    def _case_dict(c: RecoveryCase) -> Dict[str, Any]:
        return {
            "id": c.id,
            "transaction_id": c.transaction_id,
            "amount_at_risk": c.amount_at_risk,
            "category": c.category,
            "priority": c.priority,
            "status": c.status,
            "root_cause": c.root_cause,
            "root_cause_confidence": c.root_cause_confidence,
            "root_cause_explanation": c.root_cause_explanation,
            "explanation_source": c.explanation_source,
            "selected_strategy": c.selected_strategy,
            "expected_recovery": c.expected_recovery,
            "actual_recovered": c.actual_recovered,
            "recovery_probability": c.recovery_probability,
            "interventions_tried": c.interventions_tried,
            "customer_intent": c.customer_intent,
            "escalation_reason": c.escalation_reason,
            "razorpay_link_url": c.razorpay_link_url,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
        }

    @staticmethod
    def _tx_dict(t: Transaction) -> Dict[str, Any]:
        return {
            "id": t.id,
            "amount": t.amount,
            "status": t.status,
            "failure_reason": t.failure_reason,
            "payment_method": t.payment_method,
            "previous_attempts": t.previous_attempts,
            "fraud_signal": t.fraud_signal,
            "customer_opted_out": t.customer_opted_out,
            "customer_id": t.customer_id,
        }
 
    @staticmethod
    def _audit_dict(a) -> Dict[str, Any]:
        return {
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            "case_id": a.case_id,
            "agent": a.agent,
            "action": a.action,
            "details": a.details,
            "status": a.status,
            "amount": a.amount,
       }
