from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentIntentCreate(BaseModel):
    merchant_reference: str = Field(
        min_length=1,
        max_length=100,
    )

    idempotency_key: str = Field(
        min_length=1,
        max_length=255,
    )

    amount: Decimal = Field(
        gt=Decimal("1.00"),
        max_digits=18,
        decimal_places=2,
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
    )


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payment_intent_id: UUID
    transaction_reference: str
    provider: str
    provider_transaction_id: str | None
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime


class PaymentIntentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_reference: str
    idempotency_key: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    transactions: list[TransactionResponse] = []