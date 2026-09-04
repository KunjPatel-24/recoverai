"""
Generate the synthetic transactions dataset for RecoverAI.

    python data/generate_data.py                    # run from backend/
    python generate_data.py                         # or from backend/data/
    python data/generate_data.py --profile stress   # a differently-shaped batch

Deterministic (fixed seed) so every run — and every machine — produces the
identical CSV. Statuses and failure reasons are paired so they line up with the
Risk Detector and Root Cause agents.

The default `demo` profile is the dataset every quoted number comes from, and
it plants four judge-facing edge cases at fixed positions. The other profiles
are un-planted and differently shaped, so the safety policy can be shown
holding on data that wasn't hand-arranged (see validation_outputs/).

Profiles:
    demo    100 rows, 40 at risk, planted edge cases  (the demo dataset)
    stress  fraud/opt-out heavy, amounts well over the ₹50,000 authority limit
    clean   all-low fraud, no opt-outs, every amount within authority
"""
import argparse
import csv
import os
import random

OUT = os.path.join(os.path.dirname(__file__), "transactions.csv")

FIELDS = [
    "id", "amount", "status", "failure_reason", "payment_method",
    "customer_id", "previous_attempts", "fraud_signal", "customer_opted_out",
    "description",
]

# Each profile is one dataset shape. `demo` reproduces the committed CSV
# exactly — don't change its values or the quoted demo numbers move.
PROFILES = {
    "demo": {
        "seed": 2026,
        "distribution": [("SUCCESS", 60), ("FAILED", 20), ("ABANDONED", 10),
                         ("PENDING", 5), ("OVERDUE", 5)],
        "amount": (500, 28000),
        "fraud_weights": [88, 9, 3],
        "optout_rate": 0.05,
        "plant": True,
    },
    "stress": {
        "seed": 7,
        "distribution": [("SUCCESS", 20), ("FAILED", 45), ("ABANDONED", 20),
                         ("PENDING", 8), ("OVERDUE", 7)],
        "amount": (500, 90000),
        "fraud_weights": [70, 15, 15],
        "optout_rate": 0.15,
        "plant": False,
    },
    "clean": {
        "seed": 11,
        "distribution": [("SUCCESS", 55), ("FAILED", 25), ("ABANDONED", 10),
                         ("PENDING", 5), ("OVERDUE", 5)],
        "amount": (500, 40000),
        "fraud_weights": [100, 0, 0],
        "optout_rate": 0.0,
        "plant": False,
    },
}

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


def _amount(rng, low, high):
    return int(round(rng.randint(low, high) / 100.0) * 100)


def generate(profile):
    rng = random.Random(profile["seed"])

    statuses = []
    for status, count in profile["distribution"]:
        statuses.extend([status] * count)
    rng.shuffle(statuses)

    low, high = profile["amount"]
    rows = []
    for i, status in enumerate(statuses, start=1):
        at_risk = status != "SUCCESS"
        rows.append({
            "id": f"TX{i:03d}",
            "amount": _amount(rng, low, high),
            "status": status,
            "failure_reason": rng.choice(FAILURE_BY_STATUS[status]),
            "payment_method": rng.choice(PAYMENT_METHODS),
            "customer_id": f"CUST_{rng.randint(1, 70):03d}",
            "previous_attempts": rng.randint(0, 3) if at_risk else rng.randint(0, 1),
            "fraud_signal": rng.choices(["low", "medium", "high"],
                                        weights=profile["fraud_weights"], k=1)[0],
            "customer_opted_out": 1 if rng.random() < profile["optout_rate"] else 0,
            "description": rng.choice(DESCRIPTIONS),
        })

    if profile["plant"]:
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
    ap = argparse.ArgumentParser(
        description="Generate the RecoverAI transactions dataset.")
    ap.add_argument("--profile", choices=sorted(PROFILES), default="demo",
                    help="dataset shape (default: demo, the dataset every "
                         "quoted number comes from)")
    ap.add_argument("--seed", type=int,
                    help="override the profile's seed to get another batch "
                         "of the same shape")
    ap.add_argument("--out", default=OUT,
                    help="output CSV path (default: data/transactions.csv)")
    args = ap.parse_args()

    profile = dict(PROFILES[args.profile])
    if args.seed is not None:
        profile["seed"] = args.seed

    rows = generate(profile)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    at_risk = sum(1 for r in rows if r["status"] != "SUCCESS")
    print(f"Wrote {len(rows)} transactions -> {args.out}")
    print(f"  profile={args.profile}  seed={profile['seed']}")
    print(f"  {at_risk} at-risk / {len(rows) - at_risk} successful")


if __name__ == "__main__":
    main()
