from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.payment_schemas import (
    PaymentIntentCreate,
    PaymentIntentResponse,
)
from backend.app.services.idempotency_service import IdempotencyService


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "/intents",
    response_model=PaymentIntentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_intent(
    payment_data: PaymentIntentCreate,
    db: Session = Depends(get_db),
) -> PaymentIntentResponse:
    """
    Create or retrieve a PaymentIntent using the idempotency key.
    """

    payment_intent = IdempotencyService.get_or_create_payment_intent(
        db=db,
        payment_data=payment_data,
    )

    return payment_intent