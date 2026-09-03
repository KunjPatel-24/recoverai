from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models import get_db
from services.recovery_service import RecoveryService
from services.audit_service import AuditService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    return RecoveryService(db).get_dashboard_metrics()


@router.get("/audit-trail")
def get_audit_trail(limit: int = 100, db: Session = Depends(get_db)):
    logs = AuditService(db).get_all_logs(limit)
    return [
        {
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "case_id": log.case_id,
            "agent": log.agent,
            "action": log.action,
            "details": log.details,
            "status": log.status,
            "amount": log.amount,
        }
        for log in logs
    ]
