# project.md — RecoverAI Project Context

## Project

**RecoverAI — Autonomous Revenue Recovery Agent.** Track 03 — AI Revenue
Recovery.

Dashboards tell merchants *how much* revenue is at risk (failed payments,
abandoned checkouts, failed subscriptions, overdue invoices) but not what to
do about it. RecoverAI is a bounded, four-agent system that closes that loop:
not just "₹6.7L is at risk" but *what we did about it, why, whether it
worked, and a full audit trail* — the judging loop **Detect → Diagnose →
Decide → Safely Execute → Measure → Audit**.

## Hard constraints

- **Fully offline and deterministic by default.** No API keys, no live
  Razorpay, no LLM calls required to run. Payment links are simulated and
  outcomes are computed from each case's recovery probability with a fixed
  seed, so every run produces identical numbers — rehearsal and live demo
  match exactly.
- **Bounded agent authority.** Agents never act outside policy: a case above
  the ₹50,000 authority limit is escalated, never auto-executed; fraud or
  opted-out customers are always blocked, never contacted.
- **Full auditability.** Every agent decision writes an immutable row to
  `audit_logs` — no step happens without a recorded reason.
- **Independent verification.** Decisions are checked by
  [`validation_outputs/verify_decisions.py`](./validation_outputs/verify_decisions.py)
  against a hand-written policy "answer key" that does **not** reuse the
  agents' own code, so a bug shared between the agent and its own checker
  can't hide. The same check runs against two un-planted dataset profiles
  (`--profile stress` / `clean`) so the guarantees are shown holding on data
  that wasn't hand-arranged for the demo.

## The four-agent pipeline

Per case, in `backend/services/recovery_service.py::process_batch`:

1. **Risk Detector** (`agents/risk_detector.py`) — promotes a non-successful
   transaction to a `RecoveryCase`.
2. **Root Cause Agent** (`agents/root_cause_agent.py`) — diagnoses *why*
   (cause + confidence + customer intent).
3. **Recovery Strategist** (`agents/recovery_strategist.py`) — ranks the four
   interventions (Smart Retry, Payment Link, Reminder, Escalate-to-human) by
   *expected recovery = amount × probability* and picks the best.
4. **Safety Guardian** (`agents/safety_guardian.py`) — applies the bounded
   policy and returns `APPROVED` / `ESCALATED` / `REJECTED`.

Approved cases are executed and the outcome is measured; every step writes an
`audit_logs` row.

## Verified baseline (deterministic, seed-fixed)

40 at-risk cases · ₹6,70,700 at risk · ₹4,51,500 recovered · 67.3% recovery
rate — 34 approved, 1 escalated (over the ₹50k authority limit), 5 blocked
(fraud / opt-out). Reproduced and independently checked in
[`validation_outputs/validation_report.md`](./validation_outputs/validation_report.md).

## Going live (optional)

Everything above runs offline. Real Razorpay Test Mode payment links +
webhooks are opt-in via `backend/.env` (`RAZORPAY_KEY_ID` /
`RAZORPAY_KEY_SECRET`) — see the README's "Going live with Razorpay Test
Mode" section. No code changes are needed; `razorpay_service.py` switches to
live mode automatically when real keys are present.
