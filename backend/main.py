import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import init_db
from routes import transactions, recovery, dashboard, webhook

app = FastAPI(
    title="RecoverAI",
    description="Autonomous, bounded revenue-recovery agent for merchants.",
    version="1.0.0",
)

# Which browser origins may call this API.
#
# Local dev needs nothing: the Vite proxy makes requests same-origin. Once the
# frontend is deployed it calls this API cross-origin, so set ALLOWED_ORIGINS to
# a comma-separated list of frontend origins, e.g.
#   ALLOWED_ORIGINS=https://recoverai.vercel.app,http://localhost:5173
# Leaving it unset -- or set but blank, which is what Render does for a
# `sync: false` var you skip at blueprint creation -- falls back to "*", which
# is open but works everywhere.
_origins = [o.strip().rstrip("/") for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
_wildcard = not _origins or "*" in _origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _wildcard else _origins,
    # Browsers reject a wildcard origin when credentials are allowed, so only
    # turn credentials on once the origins are pinned to an explicit list.
    allow_credentials=not _wildcard,
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
