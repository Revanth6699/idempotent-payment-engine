from fastapi import FastAPI

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