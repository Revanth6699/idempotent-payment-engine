from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.payment import PaymentIntent, Transaction
from backend.app.schemas.payment_schemas import TransactionResponse
from backend.app.services.reconciliation_service import ReconciliationService


router = APIRouter(
    prefix="/reconciliation",
    tags=["Reconciliation"],
)


@router.post(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
)
def reconcile_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
) -> Transaction:
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    payment_intent = (
        db.query(PaymentIntent)
        .filter(PaymentIntent.id == transaction.payment_intent_id)
        .first()
    )

    if payment_intent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found",
        )

    try:
        return ReconciliationService.reconcile_transaction(
            db=db,
            payment_intent=payment_intent,
            transaction=transaction,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc