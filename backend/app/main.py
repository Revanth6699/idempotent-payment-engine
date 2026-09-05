from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.payment_api import router as payment_router
from backend.app.api.transaction_api import router as transaction_router
from backend.app.api.reconciliation_api import router as reconciliation_router
from backend.app.api.risk_api import router as risk_router
from backend.app.api.auth_api import router as auth_router
from backend.app.api.monitoring_api import router as monitoring_router




app = FastAPI(
    title="Idempotent Payment Processing & Transaction Reconciliation Engine",
    version="0.1.0",
    description=(
        "A distributed payment processing system designed to "
        "prevent duplicate financial execution and reconcile "
        "ambiguous transaction states."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "payment-engine",
        "version": "0.1.0",
    }



app.include_router(auth_router)
app.include_router(payment_router)
app.include_router(transaction_router)
app.include_router(reconciliation_router)
app.include_router(risk_router)
app.include_router(monitoring_router)
