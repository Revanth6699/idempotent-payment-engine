from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PaymentEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "PAYMENT"
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    payment_intent_id: UUID
    transaction_id: UUID
    transaction_reference: str

    amount: Decimal
    currency: str

    status: str
    provider: str


class RetryEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "RETRY"
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    payment_intent_id: UUID
    transaction_id: UUID
    transaction_reference: str

    retry_number: int = Field(gt=0)
    reason: str


class CallbackEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "CALLBACK"
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    payment_intent_id: UUID
    transaction_id: UUID
    transaction_reference: str

    provider: str
    provider_transaction_id: str | None = None

    status: str


class ReconciliationEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "RECONCILIATION"
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    transaction_id: UUID
    transaction_reference: str

    previous_status: str
    reconciled_status: str

    provider: str
    provider_transaction_id: str | None = None


class MLFeatureEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "ML_FEATURE"
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    payment_intent_id: UUID
    transaction_id: UUID
    transaction_reference: str

    amount: Decimal
    currency: str
    status: str

    provider: str