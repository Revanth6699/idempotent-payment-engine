from uuid import UUID

from pydantic import BaseModel, Field


class MLFeatureRecord(BaseModel):
    transaction_id: UUID
    payment_intent_id: UUID

    amount: float = Field(gt=0)

    is_success: int = Field(ge=0, le=1)
    is_failed: int = Field(ge=0, le=1)
    is_unknown: int = Field(ge=0, le=1)
    is_processing: int = Field(ge=0, le=1)

    provider: str
    currency: str = Field(min_length=3, max_length=3)