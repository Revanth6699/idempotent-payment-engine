from __future__ import annotations

from math import exp
from uuid import UUID

from backend.app.schemas.anomaly_schemas import AnomalyPrediction
from backend.app.schemas.risk_schemas import (
    RiskAssessment,
    RiskLevel,
)


class RiskAssessmentService:
    """Converts anomaly-detection output into a normalized risk assessment.

    The anomaly detector remains responsible for identifying anomalous
    transactions. This service only translates that result into a
    normalized risk score and risk level for downstream APIs, persistence,
    and the frontend dashboard.
    """

    @staticmethod
    def _normalize_anomaly_score(
        prediction: AnomalyPrediction,
    ) -> float:
        """Convert a model-specific anomaly score to a 0-100 risk score."""

        score = float(prediction.score)

        if prediction.model_name == "isolation_forest":
            normalized = 1.0 / (1.0 + exp(-12.0 * score))

        elif prediction.model_name == "local_outlier_factor":
            normalized = 1.0 / (
                1.0 + exp(-5.0 * (score - 1.0))
            )

        elif prediction.model_name == "kmeans_distance":
            normalized = 1.0 / (
                1.0 + exp(-2.0 * (score - 1.0))
            )

        elif prediction.model_name == "robust_zscore":
            normalized = 1.0 / (
                1.0 + exp(-1.2 * (score - 3.5))
            )

        else:
            raise ValueError(
                f"Unsupported anomaly model: {prediction.model_name}"
            )

        risk_score = normalized * 100.0

        if not prediction.is_anomaly:
            risk_score = min(risk_score, 49.99)

        return round(
            max(0.0, min(100.0, risk_score)),
            2,
        )

    @staticmethod
    def _determine_risk_level(
        risk_score: float,
        is_anomaly: bool,
    ) -> RiskLevel:
        """Map the normalized risk score to a risk level."""

        if not is_anomaly:
            return "LOW"

        if risk_score < 70.0:
            return "MEDIUM"

        if risk_score < 85.0:
            return "HIGH"

        return "CRITICAL"

    @classmethod
    def assess(
        cls,
        transaction_id: UUID,
        transaction_reference: str,
        prediction: AnomalyPrediction,
    ) -> RiskAssessment:
        """Create a risk assessment for one transaction."""

        risk_score = cls._normalize_anomaly_score(
            prediction
        )

        risk_level = cls._determine_risk_level(
            risk_score=risk_score,
            is_anomaly=prediction.is_anomaly,
        )

        return RiskAssessment(
            transaction_id=transaction_id,
            transaction_reference=transaction_reference,
            model_name=prediction.model_name,
            anomaly_score=prediction.score,
            is_anomaly=prediction.is_anomaly,
            risk_score=risk_score,
            risk_level=risk_level,
        )