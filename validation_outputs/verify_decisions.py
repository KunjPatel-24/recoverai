"""
RecoverAI — decision verification ("answer key").

Independently checks every recovery decision the agent made against the policy
we designed — WITHOUT reusing the agent's own code. Two kinds of checks:

  SAFETY GUARANTEES (must always hold — these are the real correctness claims)
    * a fraud or opted-out case is NEVER acted on (must be BLOCKED)
    * a case above the ₹50,000 authority limit is NEVER auto-executed (ESCALATED)
    * anything BLOCKED or ESCALATED never recovered money

  STRATEGY INTENT (does it pick the action a human would expect per failure type)
    bank timeout / network error   -> Smart Retry
    card expired / invalid / upi / declined / subscription -> Payment Link
    checkout abandoned / invoice overdue / insufficient funds -> Reminder/Link

Usage (with the backend running on http://localhost:8000):
    python verify_decisions.py
Exit code is 0 if every decision is consistent with policy, 1 otherwise.
"""
import json
import sys
import urllib.request

# Windows consoles default stdout to cp1252, which can't encode the ₹ sign
# this report prints — force UTF-8 so the script runs without env-var setup.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://localhost:8000"
AUTHORITY_LIMIT = 50000
MIN_CONFIDENCE = 0.40

# The answer key: which strategy SHOULD win, by failure reason.
EXPECTED_STRATEGY = {
    "BANK_TIMEOUT": "SMART_RETRY",
    "NETWORK_ERROR": "SMART_RETRY",
    "CARD_EXPIRED": "PAYMENT_LINK",
    "INVALID_DETAILS": "PAYMENT_LINK",
    "UPI_FAILURE": "PAYMENT_LINK",
    "DECLINED_BY_BANK": "PAYMENT_LINK",
    "SUBSCRIPTION_PAYMENT_PENDING": "PAYMENT_LINK",
    "INSUFFICIENT_FUNDS": "PAYMENT_LINK",
    "CHECKOUT_INCOMPLETE": "REMINDER",
    "INVOICE_OVERDUE": "REMINDER",
}


def _get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.loads(r.read().decode())


def _post(path):
    req = urllib.request.Request(BASE + path, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def expected_outcome(tx, confidence):
    """What SHOULD happen to this case, from ground-truth transaction data."""
    if int(tx.get("customer_opted_out", 0)) == 1:
        return "BLOCK", "customer opted out"
    if str(tx.get("fraud_signal", "low")).lower() == "high":
        return "BLOCK", "high fraud signal"
    if tx["amount"] > AUTHORITY_LIMIT:
        return "ESCALATE", "over ₹50,000 authority"
    if (confidence or 0) < MIN_CONFIDENCE:
        return "ESCALATE", "low diagnosis confidence"
    return "ACT", "within bounds"


def actual_outcome(status):
    if status == "REJECTED":
        return "BLOCK"
    if status == "ESCALATED":
        return "ESCALATE"
    if status in ("SUCCESS", "FAILED"):
        return "ACT"
    return status  # DETECTED/APPROVED/EXECUTING shouldn't survive a full run


def main():
    try:
        _post("/api/recovery/run")           # fresh, deterministic state
        txns = {t["id"]: t for t in _get("/api/transactions")}
        cases = _get("/api/recovery/cases")
    except Exception as e:
        print(f"Could not reach the backend at {BASE} — is it running?\n  {e}")
        sys.exit(2)

    failures = []
    strat_ok = strat_total = 0
    # headline safety counters
    fraud_optout_acted = 0
    over_limit_executed = 0
    blocked_recovered = 0

    for c in cases:
        tx = txns.get(c["transaction_id"], {})
        exp, why = expected_outcome(tx, c.get("root_cause_confidence"))
        act = actual_outcome(c["status"])

        # --- safety outcome check ---
        if exp != act:
            failures.append(f"{c['id']}: expected {exp} ({why}) but agent did {act} [{c['status']}]")

        # --- headline safety invariants ---
        acted = c["status"] in ("SUCCESS", "FAILED")
        is_fraud = str(tx.get("fraud_signal", "low")).lower() == "high"
        is_optout = int(tx.get("customer_opted_out", 0)) == 1
        recovered = (c.get("actual_recovered") or 0) > 0

        if (is_fraud or is_optout) and acted:
            fraud_optout_acted += 1
            failures.append(f"{c['id']}: acted on a fraud/opt-out case (SAFETY VIOLATION)")
        if tx.get("amount", 0) > AUTHORITY_LIMIT and acted:
            over_limit_executed += 1
            failures.append(f"{c['id']}: auto-executed ₹{int(tx['amount'])} > authority (SAFETY VIOLATION)")
        if c["status"] in ("REJECTED", "ESCALATED") and recovered:
            blocked_recovered += 1
            failures.append(f"{c['id']}: {c['status']} case still recovered money (SAFETY VIOLATION)")

        # --- strategy intent check ---
        want = EXPECTED_STRATEGY.get(tx.get("failure_reason", ""))
        if want:
            strat_total += 1
            if c.get("selected_strategy") == want:
                strat_ok += 1
            else:
                failures.append(
                    f"{c['id']}: strategy {c.get('selected_strategy')} "
                    f"but expected {want} for {tx.get('failure_reason')}"
                )

    # ---------------- report ----------------
    line = "=" * 60
    print(line)
    print("  RECOVERAI — DECISION VERIFICATION REPORT")
    print(line)
    print(f"  Cases checked                       : {len(cases)}")
    print()
    print("  SAFETY GUARANTEES")
    print(f"   Fraud / opt-out cases acted on     : {fraud_optout_acted}   "
          f"{'OK' if fraud_optout_acted == 0 else 'FAIL'}")
    print(f"   Over-₹50k cases auto-executed      : {over_limit_executed}   "
          f"{'OK' if over_limit_executed == 0 else 'FAIL'}")
    print(f"   Blocked/escalated that got money   : {blocked_recovered}   "
          f"{'OK' if blocked_recovered == 0 else 'FAIL'}")
    print()
    print(f"  STRATEGY matches expected policy    : {strat_ok}/{strat_total}   "
          f"{'OK' if strat_ok == strat_total else 'FAIL'}")
    print(line)

    if not failures:
        print("  RESULT: PASS — every decision is consistent with policy.")
        print(line)
        sys.exit(0)
    else:
        print(f"  RESULT: {len(failures)} issue(s) found:")
        for f in failures:
            print(f"   - {f}")
        print(line)
        sys.exit(1)


if __name__ == "__main__":
    main()
