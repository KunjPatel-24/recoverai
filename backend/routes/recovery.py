from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db
from routes.transactions import seed_transactions
from services.recovery_service import RecoveryService

router = APIRouter(prefix="/api/recovery", tags=["recovery"])


@router.post("/process")
def process_batch(db: Session = Depends(get_db)):
    """Run the 4-agent pipeline over all at-risk transactions (no execution)."""
    return RecoveryService(db).process_batch()


@router.post("/diagnose")
def diagnose_only(db: Session = Depends(get_db)):
    """Step 1 of the two-step demo: reset -> seed -> diagnose only.

    Unlike /run, this stops before execution, so APPROVED cases stay open and
    show up under "Active Cases" on the dashboard until you execute them.
    """
    seed_transactions(db)  # full reset + reload from CSV
    service = RecoveryService(db)
    processed = service.process_batch()
    return {
        "processed": processed["processed"],
        "decisions": processed["decisions"],
        "metrics": service.get_dashboard_metrics(),
    }


@router.post("/execute-approved")
async def execute_approved(db: Session = Depends(get_db)):
    """Step 2 of the two-step demo: execute every currently APPROVED case."""
    service = RecoveryService(db)
    executed = await service.execute_all_approved()
    return {
        **executed,
        "metrics": service.get_dashboard_metrics(),
    }


@router.post("/run")
async def run_all(db: Session = Depends(get_db)):
    """One-click demo: reset -> seed -> diagnose -> execute every approved case.

    Always resets first, so every click reproduces the identical run.
    """
    seed_transactions(db)  # full reset + reload from CSV
    service = RecoveryService(db)
    processed = service.process_batch()
    executed = await service.execute_all_approved()
    return {
        "processed": processed["processed"],
        "decisions": processed["decisions"],
        **executed,
        "metrics": service.get_dashboard_metrics(),
    }


@router.get("/cases")
def list_cases(db: Session = Depends(get_db)):
    return RecoveryService(db).list_cases()


@router.get("/cases/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    details = RecoveryService(db).get_case_details(case_id)
    if not details:
        raise HTTPException(status_code=404, detail="Case not found")
    return details


@router.post("/cases/{case_id}/execute")
async def execute_recovery(case_id: str, db: Session = Depends(get_db)):
    result = await RecoveryService(db).execute_case(case_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
