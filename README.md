# RecoverAI — Autonomous Revenue Recovery Agent

**Track 03 — AI Revenue Recovery.** A bounded, four-agent system that closes the
loop dashboards leave open: not just *"₹6.7L is at risk"* but *what we did about
it, why, whether it worked, and a full audit trail* — the judging loop
**Detect → Diagnose → Decide → Safely Execute → Measure → Audit.**

Runs **fully offline and deterministic**: no API keys, no live Razorpay, no LLM.
Payment links are simulated and outcomes are computed from each case's recovery
probability with a fixed seed, so **every run produces the identical numbers** —
your rehearsal and your live demo match exactly.

Verified end-to-end: **40 at-risk cases · ₹6,70,700 at risk · ₹4,51,500
recovered · 67.3% recovery rate**, with 34 approved, 1 escalated (over the
₹50k authority limit), 5 blocked (fraud / opt-out).

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for the frontend)

## Run it (two terminals in VS Code)

### Terminal 1 — backend (FastAPI, port 8000)

```bash
cd recoverai/backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python data/generate_data.py      # writes data/transactions.csv (100 rows)
uvicorn main:app --reload
```

Backend is now at http://localhost:8000 (interactive API docs at
http://localhost:8000/docs).

### Terminal 2 — frontend (React + Vite, port 5173)

```bash
cd recoverai/frontend
npm install
npm run dev
```

Open **http://localhost:5173**. On the **Command Center**, click **Run
Recovery** — it seeds, runs the 4 agents over every at-risk transaction,
executes the approved ones, and fills the dashboard. That's the whole demo in
one click.

> The frontend talks to the backend through Vite's proxy (`/api` → :8000), so
> both must be running. No CORS setup needed.

### Don't want the UI? Drive it from the API

```bash
curl -X POST http://localhost:8000/api/recovery/run   # one-click: seed+diagnose+execute
curl http://localhost:8000/api/dashboard/metrics
curl http://localhost:8000/api/dashboard/audit-trail
```

---

## How the pieces connect

```
                    ┌─────────────── FRONTEND (React/Vite :5173) ───────────────┐
                    │  Command Center · Cases · Decision View · Safety · Audit   │
                    └───────────────────────────┬───────────────────────────────┘
                                    fetch /api/* │  (Vite proxy)
                    ┌───────────────────────────▼───────────────────────────────┐
                    │                 BACKEND (FastAPI :8000)                    │
                    │  routes/  transactions · recovery · dashboard · webhook    │
                    └───────────────────────────┬───────────────────────────────┘
                                                │ services/recovery_service.py (orchestrator)
        ┌───────────────┬───────────────┬───────┴────────┬────────────────┐
        ▼               ▼               ▼                ▼                ▼
  risk_detector   root_cause_agent  recovery_        safety_          razorpay_
  (Agent 1)       (Agent 2)         strategist       guardian         service
                                    (Agent 3)        (Agent 4)        (demo/live)
        └───────────────┴───────────────┴────────────────┴──── every step →  audit_service
                                        │
                                        ▼
                             SQLite (recoverai.db):
                             transactions · recovery_cases · audit_logs
```

**The pipeline per case** (in `services/recovery_service.py::process_batch`):
Risk Detector promotes a non-successful transaction to a `RecoveryCase` →
Root Cause Analyst diagnoses *why* (cause + confidence + customer intent) →
Recovery Strategist ranks the four interventions by *expected recovery =
amount × probability* and picks the best → Safety Guardian applies the bounded
policy and returns **APPROVED / ESCALATED / REJECTED** → approved cases are
executed and the outcome is measured. Every step writes an `audit_logs` row.

---

## Project structure

```
recoverai/
├── README.md
├── LICENSE
├── project.md                   hard constraints + agent pipeline context
├── validation_outputs/          independent decision verification
│   ├── verify_decisions.py      checks agent decisions against a policy "answer key"
│   └── validation_report.md     latest verification run + dashboard metrics
├── backend/                     FastAPI + SQLAlchemy + 4 agents
│   ├── main.py                  app + routers
│   ├── requirements.txt
│   ├── .env                     offline by default; add rzp_test_ keys to go live
│   ├── models/__init__.py       SQLAlchemy models + DB session + enums
│   ├── agents/
│   │   ├── risk_detector.py         Agent 1 — find revenue at risk
│   │   ├── root_cause_agent.py      Agent 2 — why it's at risk (+confidence)
│   │   ├── recovery_strategist.py   Agent 3 — pick highest expected recovery
│   │   └── safety_guardian.py       Agent 4 — approve / escalate / reject
│   ├── services/
│   │   ├── recovery_service.py      orchestrator + execution + metrics
│   │   ├── audit_service.py         immutable audit trail
│   │   └── razorpay_service.py      demo link (offline) or live Test Mode
│   ├── routes/                  transactions · recovery · dashboard · webhook
│   └── data/generate_data.py    deterministic 100-transaction generator
└── frontend/                    React + Vite + Tailwind + Recharts
    ├── vite.config.js           /api + /webhook proxy to :8000
    ├── tailwind.config.js       brand/danger/warning palette
    └── src/
        ├── App.jsx              sidebar + routes
        ├── api.js               fetch helpers
        ├── components/          MetricsCards · RecoveryTable · AgentTimeline · StrategyComparison
        └── pages/               Dashboard · RecoveryCases · DecisionView · Safety · AuditTrail
```

---

## What I fixed / added versus the original drafts

The pasted code was a solid scaffold but couldn't run as-is. Changes:

1. **Missing dataset generator written** (`data/generate_data.py`) — the
   original referenced it but never provided it. Statuses and failure reasons
   are paired to match the agents' expectations.
2. **`webhook.py` crash fixed** — it called `datetime.utcnow()` without
   importing `datetime`.
3. **Deterministic, idempotent case IDs** (`RCV_<txn id>` instead of random
   UUIDs) — so re-running detection doesn't create duplicate cases, and the
   whole demo is reproducible.
4. **Real safety checks** — fraud and opt-out now read genuine transaction
   fields (`fraud_signal`, `customer_opted_out`) instead of a fake
   `priority != CRITICAL` proxy; over-authority / low-confidence cases
   **escalate** rather than silently reject.
5. **Offline outcome measurement** — approved cases resolve deterministically
   from their recovery probability, so the dashboard shows a real recovery
   rate without needing a live webhook.
6. **API returns clean JSON** — routes serialize to dicts (SQLAlchemy models
   don't serialize directly through FastAPI).
7. **The entire frontend scaffold** — package.json, Vite config with proxy,
   Tailwind/PostCSS config, `index.css` (the `card`/`btn-primary`/`badge`
   classes + palette the pages assume), `App.jsx` router + nav, `api.js`, all
   four components, and the two pages (Dashboard, RecoveryCases) that were
   referenced but never provided. The three pasted pages drop in unchanged.
8. **One-click `/api/recovery/run`** — resets, seeds, diagnoses, and executes in
   a single call so the demo is trivial to drive and always reproduces.

---

## Going live with Razorpay Test Mode (optional, later)

Everything above is offline. To use real Razorpay Payment Links + webhooks:

1. Put your test keys in `backend/.env`
   (`RAZORPAY_KEY_ID=rzp_test_...`, `RAZORPAY_KEY_SECRET=...`).
2. Expose the backend so Razorpay can reach the webhook
   (e.g. `ngrok http 8000`) and register
   `https://<tunnel>/webhook/razorpay` in the Razorpay dashboard.

No code changes — `razorpay_service.py` switches to live mode automatically
when real keys are present, and the webhook route resolves paid links. (Note:
UPI payment links aren't supported in Razorpay Test Mode, so live demos should
use standard payment links.)
