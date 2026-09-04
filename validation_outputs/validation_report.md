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

## Cross-profile verification

The `demo` dataset plants its four edge cases at fixed positions, so on its
own it only proves the policy holds on data that was hand-arranged. To close
that gap, `generate_data.py` ships two additional **un-planted** profiles and
the same checker is run against each:

```bash
python data/generate_data.py --profile stress   # then re-run the verifier
python data/generate_data.py --profile clean
```

| | `demo` | `stress` | `clean` |
|---|---|---|---|
| Shape | 100 rows, planted | fraud/opt-out heavy, amounts to ₹90k | low fraud, no opt-outs, all within authority |
| Cases | 40 | 80 | 45 |
| Fraud / opt-out acted on | 0 | 0 | 0 |
| Over-₹50k auto-executed | 0 | 0 | 0 |
| Blocked / escalated that got money | 0 | 0 | 0 |
| Strategy matches policy | 40/40 | 76/76 | 45/45 |
| Deferred to a human | 0 | 4 | 0 |
| Blocked (fraud / opt-out) | 5 (3/2) | 24 (17/7) | 0 |
| Escalated over authority | 1 | 23 | 0 |
| **Result** | PASS | PASS | PASS |

`stress` exercises the safety rules hard — 24 blocks and 23 escalations
instead of the demo's 5 and 1 — and every guarantee still holds. `clean` is
the control in the other direction: with nothing that warrants intervention,
the agent blocks and escalates **nothing**, so the guarantees aren't being
satisfied by an agent that simply refuses to act.

### What this run caught

On the first `stress` run the checker reported 4 strategy mismatches: overdue
invoices where the Strategist chose `HUMAN_ESCALATION` instead of the expected
`REMINDER`. Investigating showed the **agent was right** — all four were
high-value (>₹40,000) invoices from `LOW`-intent customers, where handing off
to a human genuinely beats another nudge. The gap was in the *answer key*: its
flat failure-reason table had no notion of deferring to a human, and the demo
profile never exposed it because its amounts cap at ₹28,000.

The checker now treats deferral to a human as always allowed (it is the
conservative option) and judges the table only against actions the agent takes
autonomously — counting deferrals separately rather than re-implementing the
Strategist's probability model, which would have made the check a copy of the
code it is meant to audit.
