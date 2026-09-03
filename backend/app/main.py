from fastapi import FastAPI

from backend.app.api.payment_api import router as payment_router
from backend.app.api.transaction_api import router as transaction_router
from backend.app.api.reconciliation_api import router as reconciliation_router



app = FastAPI(
    title="Idempotent Payment Processing & Transaction Reconciliation Engine",
    version="0.1.0",
    description=(
        "A distributed payment processing system designed to "
        "prevent duplicate financial execution and reconcile "
        "ambiguous transaction states."
    ),
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "payment-engine",
        "version": "0.1.0",
    }


app.include_router(payment_router)
app.include_router(transaction_router)
app.include_router(reconciliation_router)