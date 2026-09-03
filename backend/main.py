from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import init_db
from routes import transactions, recovery, dashboard, webhook

app = FastAPI(
    title="RecoverAI",
    description="Autonomous, bounded revenue-recovery agent for merchants.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(transactions.router)
app.include_router(recovery.router)
app.include_router(dashboard.router)
app.include_router(webhook.router)


@app.get("/")
def root():
    return {
        "service": "RecoverAI",
        "status": "operational",
        "version": "1.0.0",
        "endpoints": [
            "POST /api/transactions/seed",
            "GET  /api/transactions",
            "POST /api/recovery/run     (one-click: seed+diagnose+execute)",
            "POST /api/recovery/process",
            "GET  /api/recovery/cases",
            "GET  /api/recovery/cases/{id}",
            "POST /api/recovery/cases/{id}/execute",
            "GET  /api/dashboard/metrics",
            "GET  /api/dashboard/audit-trail",
            "POST /webhook/razorpay",
        ],
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
