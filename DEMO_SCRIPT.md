# RecoverAI — 3-Minute Demo Script

A tight, judge-facing walkthrough. Every number below is **deterministic** — it
comes out identical every run, so you can rehearse to it exactly.

---

## Before you present (2-minute setup checklist)

- [ ] **Backend running:** `cd recoverai/backend && uvicorn main:app --reload` (port 8000)
- [ ] **Frontend running:** `cd recoverai/frontend && npm run dev` (port 5173)
- [ ] Browser open at **http://localhost:5173**, on the **Command Center** page
- [ ] Browser zoom ~110%, window maximized, other tabs closed
- [ ] Do a silent dry-run: click **Run Recovery** once, confirm the numbers below, then it's warm
- [ ] (Optional) Have the **Audit Trail** page open in a second tab for a fast switch

**The numbers you should see** (memorize these — they never change):

| Metric | Value |
| --- | --- |
| Cases | 40 |
| At risk | ₹6,70,700 |
| Recovered | ₹4,51,500 |
| Recovery rate | **67.3%** |
| Approved / Escalated / Blocked | 34 / 1 / 5 |
| Strategy mix | Payment Link 16 · Reminder 15 · Smart Retry 9 |

---

## The script (target: 3:00)

### 0:00 – 0:20 · The hook *(on Command Center)*

> "Merchants lose revenue every day — failed payments, abandoned checkouts,
> failed subscriptions, overdue invoices. Every dashboard tells them *how much*
> is at risk. **None of them tell you what to do about it right now.**
> RecoverAI is an autonomous agent that closes that loop."

### 0:20 – 0:50 · One click, the whole loop *(click "Run Recovery")*

Click **Run Recovery**. As the tiles fill and the Live Agent Activity feed
scrolls:

> "In one click, RecoverAI scanned 100 transactions, found **40 at risk worth
> ₹6.7 lakh**, and ran four agents on each one — detect, diagnose, decide,
> execute, measure. It just recovered **₹4.52 lakh — a 67% recovery rate** —
> and every step you see scrolling is being written to an immutable audit log."

Point at the **Recovery Rate** tile and the **Live Agent Activity** feed.

### 0:50 – 1:30 · The happy path — full reasoning *(Recovery Cases → open RCV_TX010)*

Go to **Recovery Cases**, click **RCV_TX010** (₹5,000).

> "Here's one case end to end. A ₹5,000 payment failed on a **bank timeout**.
> The Root Cause agent diagnosed it as *temporary bank-side degradation* with
> **91% confidence** — the customer still wants to pay. The Strategist compared
> four interventions and picked **Smart Retry** — a bank timeout is temporary,
> so simply retrying is the highest *expected recovery = amount × probability*.
> Safety approved it, we executed, and the money came back. That's the full loop
> on one case."

Point at: Root Cause (91%), Strategy Comparison (Smart Retry selected),
Safety Evaluation (all green), Audit Trail at the bottom.

> Tip: open a **Reminder** case too (any CHECKOUT ABANDONMENT row) and a
> **Payment Link** case (any SUBSCRIPTION FAILED row) to show the Strategist
> picks *different* actions for different failures — that proves it's reasoning,
> not defaulting.

### 1:30 – 2:15 · The differentiator — it knows when NOT to act

> "But the real story is restraint. An autonomous agent touching money is only
> safe if it's bounded."

Back to **Recovery Cases**, open **RCV_TX003** (₹62,000):

> "This one is ₹62,000 — **over the agent's ₹50,000 authority limit**. It did
> **not** act. It escalated to a human."

Open **RCV_TX004** (₹23,100):

> "This one has a **high fraud signal** — the agent **blocked** it outright.
> Same for customers who've **opted out**, like RCV_TX007. Out of 40 cases, the
> agent refused to act on **6** — and it logged exactly why for every one."

*(This is the winning beat — say it slowly.)*

### 2:15 – 2:45 · Auditability *(Audit Trail page)*

Switch to **Audit Trail**.

> "Every decision every agent made is here — immutable, timestamped,
> filterable. If a judge or a compliance officer asks *why did the agent do
> this?*, the answer is one click away. This is what makes it a real fintech
> agent, not a chatbot guessing with money."

### 2:45 – 3:00 · Close

> "So: RecoverAI **detects** revenue at risk, **diagnoses** the cause,
> **decides** the highest-value action, executes it **within hard safety
> bounds**, **measures** what actually came back, and **audits** every step.
> It's deterministic, it's bounded, and it's already wired for real Razorpay
> Test Mode. Thank you."

---

## If something breaks (stay calm)

- **Numbers look off / page empty?** Click **Run Recovery** again — it resets and
  reproduces the identical run. Nothing is random.
- **Frontend won't load?** The backend still works: hit
  `http://localhost:8000/docs` and run `POST /api/recovery/run` live — the JSON
  tells the same story (decisions + metrics).
- **Total fallback:** take screenshots of all five pages beforehand and keep
  them in a folder; the deck's demo slide can stand in.

---

## Judge Q&A — quick answers

**"Is the recovery real or are the numbers faked?"**
> Outcomes are simulated deterministically from each case's recovery
> probability — we don't invent a rate. The pipeline, decisions, and audit are
> fully real; only the *payment settlement* is stubbed for an offline demo, and
> it's one env var to switch to live Razorpay Test Mode.

**"Why not use an LLM for everything?"**
> Policy, retry limits, money math, and the audit trail are deterministic code
> on purpose — that's what makes a money-moving agent safe and reproducible. An
> LLM plugs in behind the Root Cause / Strategist interfaces for richer
> reasoning without changing the pipeline.

**"What exactly is 'bounded'?"**
> Hard limits: max 2 interventions, max 3 retries, ₹50,000 authority, plus stop
> rules for fraud, opt-out, duplicate payments, and low confidence. Over-limit
> or low-confidence cases escalate to a human; fraud/opt-out are blocked. 6 of
> 40 cases were stopped in this run.

**"How do you measure success honestly?"**
> Recovery rate = actual money recovered ÷ money at risk. We also show
> *expected vs actual* recovery, so you can see the agent's forecasts against
> outcomes.

**"Is it production-ready?"**
> The architecture is: FastAPI + SQLAlchemy (swap SQLite → Postgres unchanged),
> a clean agent pipeline, and real Razorpay Payment Links + webhooks already
> coded. What's stubbed for the demo is only the live payment settlement.

---

## Exact demo case IDs (cheat sheet)

| Case | Amount | What it shows |
| --- | --- | --- |
| **RCV_TX010** | ₹5,000 | Happy path — bank timeout, 91% confidence, Smart Retry, recovered |
| **RCV_TX003** | ₹62,000 | Escalated — over ₹50,000 authority limit |
| **RCV_TX004** | ₹23,100 | Blocked — high fraud signal |
| **RCV_TX007** | ₹20,500 | Blocked — customer opted out |
