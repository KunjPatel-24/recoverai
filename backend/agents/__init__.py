"""
RecoverAI data models + DB session (SQLAlchemy).

Runs on SQLite for the hackathon; point DATABASE_URL at Postgres and the same
models work unchanged.

Changes vs. the original scaffold (all to make the demo real + reproducible):
  * Transaction gains `fraud_signal` and `customer_opted_out` so the Safety
    Guardian can enforce genuine stopping rules (not a fake proxy).
  * That's it for schema — everything else is the original design.
"""
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, DateTime, Boolean, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import enum
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional; env vars still work without it.
    pass

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recoverai.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={} if "postgresql" in DATABASE_URL else {"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --------------------------------------------------------------------------- #
# Enums (string-valued so they serialize cleanly to JSON / SQLite)
# --------------------------------------------------------------------------- #
class TransactionStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"
    PENDING = "PENDING"     # subscription renewal pending
    OVERDUE = "OVERDUE"     # invoice overdue


class RiskCategory(str, enum.Enum):
    PAYMENT_FAILURE = "PAYMENT_FAILURE"
    CHECKOUT_ABANDONMENT = "CHECKOUT_ABANDONMENT"
    SUBSCRIPTION_FAILED = "SUBSCRIPTION_FAILED"
    INVOICE_OVERDUE = "INVOICE_OVERDUE"
    PAYMENT_DEGRADATION = "PAYMENT_DEGRADATION"


class Priority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecoveryStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    ANALYZING = "ANALYZING"
    STRATEGY_SELECTED = "STRATEGY_SELECTED"
    SAFETY_CHECK = "SAFETY_CHECK"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"
    REJECTED = "REJECTED"


class InterventionType(str, enum.Enum):
    SMART_RETRY = "SMART_RETRY"
    PAYMENT_LINK = "PAYMENT_LINK"
    REMINDER = "REMINDER"
    HUMAN_ESCALATION = "HUMAN_ESCALATION"


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    failure_reason = Column(String, nullable=True)
    payment_method = Column(String, nullable=False)
    customer_id = Column(String, nullable=False)
    previous_attempts = Column(Integer, default=0)
    # NEW — drive genuine safety decisions
    fraud_signal = Column(String, default="low")        # low | medium | high
    customer_opted_out = Column(Integer, default=0)     # 0 | 1
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    merchant_id = Column(String, default="MERCHANT_001")
    description = Column(String, nullable=True)
    is_at_risk = Column(Boolean, default=False)


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(String, primary_key=True)
    transaction_id = Column(String, nullable=False)
    amount_at_risk = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    status = Column(String, default=RecoveryStatus.DETECTED.value)
    root_cause = Column(Text, nullable=True)
    root_cause_confidence = Column(Float, nullable=True)
    root_cause_explanation = Column(Text, default="")   # human-readable "why"
    explanation_source = Column(String, default="")      # "rules" or "llm:<model>"
    selected_strategy = Column(String, nullable=True)
    expected_recovery = Column(Float, nullable=True)
    actual_recovered = Column(Float, default=0.0)
    recovery_probability = Column(Float, nullable=True)
    interventions_tried = Column(Integer, default=0)
    max_interventions = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    razorpay_link_id = Column(String, nullable=True)
    razorpay_link_url = Column(String, nullable=True)
    customer_intent = Column(String, nullable=True)
    escalation_reason = Column(Text, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    agent = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    amount = Column(Float, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
