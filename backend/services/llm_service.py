"""
Optional live LLM for the Root Cause Analyst's explanation.

Design: the root-cause *label*, *confidence* and *customer intent* stay
deterministic (computed in root_cause_agent) so the demo numbers never move.
This module only generates the human-readable *explanation* shown on a case —
and only when an API key is configured. With no key, the app is fully offline
and uses the built-in explanation instead.

Works with any OpenAI-compatible Chat Completions endpoint:
    LLM_API_KEY   = sk-...            (required to enable)
    LLM_BASE_URL  = https://api.openai.com/v1     (default)
    LLM_MODEL     = gpt-4o-mini                    (default)
Examples: OpenAI (default), Groq (base https://api.groq.com/openai/v1,
model llama-3.1-8b-instant), Together, etc.
"""
import os

try:
    import httpx
except Exception:
    httpx = None

SYSTEM = (
    "You are a payments revenue-recovery analyst. Given one failed or at-risk "
    "transaction, explain in TWO short, specific sentences why it is (or isn't) "
    "recoverable and what the chosen recovery action implies. Be concrete, avoid "
    "generic filler, and do not restate the numbers back verbatim. No preamble."
)


def _cfg():
    return {
        "key": os.getenv("LLM_API_KEY", "").strip(),
        "base": os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/"),
        "model": os.getenv("LLM_MODEL", "gpt-4o-mini").strip(),
    }


def llm_enabled() -> bool:
    c = _cfg()
    return bool(c["key"]) and "YOUR_KEY" not in c["key"] and httpx is not None


def model_name() -> str:
    return _cfg()["model"]


def generate_root_cause_explanation(*, transaction_id, amount, failure_reason,
                                    category, previous_attempts,
                                    cause, confidence, customer_intent,
                                    selected_strategy) -> str | None:
    """Return a live-generated explanation, or None on any failure/disabled."""
    c = _cfg()
    if not llm_enabled():
        return None

    user = (
        f"Transaction {transaction_id}\n"
        f"Amount at risk: INR {int(amount)}\n"
        f"Category: {category}\n"
        f"Failure reason: {failure_reason or 'unknown'}\n"
        f"Previous attempts: {previous_attempts}\n"
        f"Diagnosed cause: {cause} (confidence {int((confidence or 0)*100)}%)\n"
        f"Customer intent: {customer_intent}\n"
        f"Chosen recovery action: {selected_strategy}\n\n"
        "Write the two-sentence explanation for the merchant."
    )
    try:
        with httpx.Client(timeout=20) as client:
            r = client.post(
                f"{c['base']}/chat/completions",
                headers={"Authorization": f"Bearer {c['key']}",
                         "Content-Type": "application/json"},
                json={
                    "model": c["model"],
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 140,
                },
            )
            r.raise_for_status()
            data = r.json()
            text = (data["choices"][0]["message"]["content"] or "").strip()
            return text or None
    except Exception:
        # Any problem (no network, bad key, timeout) -> silent fallback.
        return None
