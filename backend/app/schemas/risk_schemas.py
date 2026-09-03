from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


RiskLevel = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]


class RiskAssessment(BaseModel):
    """Risk assessment produced from anomaly-detection results."""

    model_config = ConfigDict(extra="forbid")

    transaction_id: UUID
    transaction_reference: str

    model_name: str

    anomaly_score: float
    is_anomaly: bool

    risk_score: float = Field(
        ge=0.0,
        le=100.0,
    )

    risk_level: RiskLevel


class RiskAssessmentResponse(RiskAssessment):
    """API response representation of a risk assessment."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )