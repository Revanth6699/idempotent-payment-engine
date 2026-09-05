from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.payment_schemas import TransactionResponse
from backend.app.services.transaction_orchestrator_service import (
    TransactionOrchestratorService,
)
from backend.app.core.security import get_current_user


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


@router.post(
    "/{payment_intent_id}/start",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_transaction(
    payment_intent_id: UUID,
    provider: str = "SIMULATOR",
    outcome: str = "SUCCESS",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> TransactionResponse:

    """
    Start transaction processing for an existing PaymentIntent.

    The normal client flow uses the default simulator provider and does not
    expose processor outcome selection. The outcome parameter remains available
    for authorized failure/unknown simulation.
    """

    transaction = TransactionOrchestratorService.start_transaction(
        db=db,
        payment_intent_id=payment_intent_id,
        provider=provider,
        outcome=outcome,
    )

    return transaction