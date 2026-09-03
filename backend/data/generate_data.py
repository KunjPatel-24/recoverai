"""
Generate the synthetic transactions dataset for RecoverAI.

    python data/generate_data.py          # run from backend/
    python generate_data.py               # or from backend/data/

Deterministic (fixed seed) so every run — and every machine — produces the
identical 100-row CSV. Statuses and failure reasons are paired so they line up
with the Risk Detector and Root Cause agents.

Distribution:
    SUCCESS    60      FAILED   20      ABANDONED 10
    PENDING     5      OVERDUE   5   (PENDING = subscription, OVERDUE = invoice)
"""
import csv
import os
import random

SEED = 2026
OUT = os.path.join(os.path.dirname(__file__), "transactions.csv")

FIELDS = [
    "id", "amount", "status", "failure_reason", "payment_method",
    "customer_id", "previous_attempts", "fraud_signal", "customer_opted_out",
    "description",
]

DISTRIBUTION = [
    ("SUCCESS", 60),
    ("FAILED", 20),
    ("ABANDONED", 10),
    ("PENDING", 5),
    ("OVERDUE", 5),
]

# Failure reasons valid for each status (must match root_cause_agent CAUSE_MAP).
FAILURE_BY_STATUS = {
    "SUCCESS": [""],
    "FAILED": [
        "BANK_TIMEOUT", "NETWORK_ERROR", "INSUFFICIENT_FUNDS",
        "CARD_EXPIRED", "DECLINED_BY_BANK", "UPI_FAILURE", "INVALID_DETAILS",
    ],
    "ABANDONED": ["CHECKOUT_INCOMPLETE"],
    "PENDING": ["SUBSCRIPTION_PAYMENT_PENDING"],
    "OVERDUE": ["INVOICE_OVERDUE"],
}

PAYMENT_METHODS = ["upi", "card", "netbanking", "wallet"]

DESCRIPTIONS = [
    "Order checkout", "Subscription renewal", "Invoice settlement",
    "Cart purchase", "Service payment", "Membership fee",
]


def _amount(rng):
    return int(round(rng.randint(500, 28000) / 100.0) * 100)


def generate():
    rng = random.Random(SEED)

    statuses = []
    for status, count in DISTRIBUTION:
        statuses.extend([status] * count)
    rng.shuffle(statuses)

    rows = []
    for i, status in enumerate(statuses, start=1):
        at_risk = status != "SUCCESS"
        rows.append({
            "id": f"TX{i:03d}",
            "amount": _amount(rng),
            "status": status,
            "failure_reason": rng.choice(FAILURE_BY_STATUS[status]),
            "payment_method": rng.choice(PAYMENT_METHODS),
            "customer_id": f"CUST_{rng.randint(1, 70):03d}",
            "previous_attempts": rng.randint(0, 3) if at_risk else rng.randint(0, 1),
            "fraud_signal": rng.choices(["low", "medium", "high"],
                                        weights=[88, 9, 3], k=1)[0],
            "customer_opted_out": 1 if rng.random() < 0.05 else 0,
            "description": rng.choice(DESCRIPTIONS),
        })

    _plant_demo_scenarios(rows)
    return rows


def _plant_demo_scenarios(rows):
    """Guarantee the four judge-facing edge cases always exist."""
    at_risk = [r for r in rows if r["status"] != "SUCCESS"]

    # 1) High value ABOVE the ₹50,000 authority limit -> Safety ESCALATES.
    at_risk[0].update(status="FAILED", failure_reason="BANK_TIMEOUT",
                      amount=62000, fraud_signal="low", customer_opted_out=0)

    # 2) High fraud signal -> Safety BLOCKS (rejected).
    at_risk[1].update(fraud_signal="high", customer_opted_out=0)

    # 3) Customer opted out -> Safety BLOCKS (no contact).
    at_risk[2].update(fraud_signal="low", customer_opted_out=1)

    # 4) Clean, high-confidence bank timeout -> the happy-path recovery.
    at_risk[3].update(status="FAILED", failure_reason="BANK_TIMEOUT",
                      amount=5000, fraud_signal="low", customer_opted_out=0,
                      previous_attempts=1)


def main():
    rows = generate()
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    at_risk = sum(1 for r in rows if r["status"] != "SUCCESS")
    print(f"Wrote {len(rows)} transactions -> {OUT}")
    print(f"  {at_risk} at-risk / {len(rows) - at_risk} successful")


if __name__ == "__main__":
    main()
