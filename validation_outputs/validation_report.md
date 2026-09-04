# RecoverAI — Decision Verification Report

Independent, offline check of every recovery decision the agents made against
the policy the system is supposed to enforce — computed **without reusing the
agents' own code** (see [`verify_decisions.py`](./verify_decisions.py)).

Run with:

```bash
cd backend
uvicorn main:app --reload      # terminal 1
python ../validation_outputs/verify_decisions.py   # terminal 2
```

## What is checked

**Safety guarantees** (must always hold):

- a fraud or opted-out case is never acted on — must be `BLOCKED`
- a case above the ₹50,000 authority limit is never auto-executed — must be `ESCALATED`
- anything `BLOCKED` or `ESCALATED` never recovered money

**Strategy intent** (does the agent pick the action a human would expect for
the failure type — bank timeout → Smart Retry, card expired → Payment Link,
checkout abandoned → Reminder, etc).

## Latest run

```
============================================================
  RECOVERAI — DECISION VERIFICATION REPORT
============================================================
  Cases checked                       : 40

  SAFETY GUARANTEES
   Fraud / opt-out cases acted on     : 0   OK
   Over-₹50k cases auto-executed      : 0   OK
   Blocked/escalated that got money   : 0   OK

  STRATEGY matches expected policy    : 40/40   OK
============================================================
  RESULT: PASS — every decision is consistent with policy.
============================================================
```

Exit code: `0`

## Corresponding dashboard metrics

Pulled from `GET /api/dashboard/metrics` on the same deterministic run:

| Metric | Value |
|---|---|
| Total at risk | ₹6,70,700 |
| Total recovered | ₹4,51,500 |
| Recovery rate | 67.3% |
| Total cases | 40 |
| Approved & executed | 34 (29 succeeded, 5 failed to recover) |
| Escalated (over ₹50k authority) | 1 |
| Blocked — fraud | 3 |
| Blocked — customer opted out | 2 |

Because the pipeline is deterministic (fixed seed, no live LLM/payment
calls), these numbers are reproducible on every run and match the figures
quoted in the top-level [README](../README.md).
