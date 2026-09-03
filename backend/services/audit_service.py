"""Audit service — appends an immutable row for every agent action."""
from models import AuditLog


class AuditService:
    def __init__(self, db):
        self.db = db

    def log(self, case_id: str, agent: str, action: str, details: str,
            status: str, amount: float = None) -> AuditLog:
        entry = AuditLog(
            case_id=case_id,
            agent=agent,
            action=action,
            details=details,
            status=status,
            amount=amount,
        )
        self.db.add(entry)
        self.db.commit()
        return entry

    def get_trail(self, case_id: str):
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.case_id == case_id)
            .order_by(AuditLog.id)
            .all()
        )

    def get_all_logs(self, limit: int = 100):
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.id.desc())
            .limit(limit)
            .all()
        )
