import csv
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import Transaction, RecoveryCase, AuditLog, get_db, init_db

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "transactions.csv")


def _tx_dict(t: Transaction) -> dict:
    return {
        "id": t.id, "amount": t.amount, "status": t.status,
        "failure_reason": t.failure_reason, "payment_method": t.payment_method,
        "customer_id": t.customer_id, "previous_attempts": t.previous_attempts,
        "fraud_signal": t.fraud_signal, "customer_opted_out": t.customer_opted_out,
        "description": t.description, "is_at_risk": t.is_at_risk,
    }


@router.post("/seed")
def seed_transactions(db: Session = Depends(get_db)):
    """(Re)load transactions from the CSV and reset all cases + audit logs."""
    init_db()
    if not os.path.exists(CSV_PATH):
        raise HTTPException(
            status_code=400,
            detail="data/transactions.csv missing. Run `python data/generate_data.py` first.",
        )

    # Full reset so a run is reproducible from a clean slate.
    db.query(AuditLog).delete()
    db.query(RecoveryCase).delete()
    db.query(Transaction).delete()
    db.commit()

    count = 0
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            db.add(Transaction(
                id=row["id"],
                amount=float(row["amount"]),
                status=row["status"].strip().upper(),
                failure_reason=(row.get("failure_reason") or "").strip(),
                payment_method=row["payment_method"],
                customer_id=row["customer_id"],
                previous_attempts=int(row.get("previous_attempts", 0) or 0),
                fraud_signal=(row.get("fraud_signal") or "low").strip().lower(),
                customer_opted_out=int(row.get("customer_opted_out", 0) or 0),
                description=row.get("description", ""),
            ))
            count += 1
    db.commit()
    return {"message": f"Seeded {count} transactions", "count": count}


@router.get("/")
def list_transactions(db: Session = Depends(get_db)):
    return [_tx_dict(t) for t in db.query(Transaction).all()]


@router.get("/{tx_id}")
def get_transaction(tx_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _tx_dict(tx)
