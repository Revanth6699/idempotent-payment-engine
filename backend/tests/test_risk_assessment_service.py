from __future__ import annotations

from uuid import uuid4

import pytest

from backend.app.schemas.anomaly_schemas import AnomalyPrediction
from backend.app.services.risk_assessment_service import (
    RiskAssessmentService,
)


TRANSACTION_ID = uuid4()
TRANSACTION_REFERENCE = "TXN-RISK-TEST-001"


def build_prediction(
    model_name: str,
    score: float,
    is_anomaly: bool,
    prediction: int,
) -> AnomalyPrediction:
    return AnomalyPrediction(
        model_name=model_name,
        is_anomaly=is_anomaly,
        score=score,
        prediction=prediction,
    )


@pytest.mark.parametrize(
    "model_name,score",
    [
        ("isolation_forest", 0.0),
        ("local_outlier_factor", 1.0),
        ("kmeans_distance", 1.0),
        ("robust_zscore", 3.5),
    ],
)
def test_normal_prediction_produces_low_risk(
    model_name: str,
    score: float,
) -> None:
    prediction = build_prediction(
        model_name=model_name,
        score=score,
        is_anomaly=False,
        prediction=1,
    )

    result = RiskAssessmentService.assess(
        transaction_id=TRANSACTION_ID,
        transaction_reference=TRANSACTION_REFERENCE,
        prediction=prediction,
    )

    assert result.transaction_id == TRANSACTION_ID
    assert result.transaction_reference == TRANSACTION_REFERENCE
    assert result.model_name == model_name
    assert result.anomaly_score == score
    assert result.is_anomaly is False
    assert 0.0 <= result.risk_score < 50.0
    assert result.risk_level == "LOW"


def test_isolation_forest_anomaly_produces_elevated_risk() -> None:
    prediction = build_prediction(
        model_name="isolation_forest",
        score=0.2,
        is_anomaly=True,
        prediction=-1,
    )

    result = RiskAssessmentService.assess(
        transaction_id=TRANSACTION_ID,
        transaction_reference=TRANSACTION_REFERENCE,
        prediction=prediction,
    )

    assert result.is_anomaly is True
    assert result.risk_score >= 50.0
    assert result.risk_level in {
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }


def test_robust_zscore_extreme_anomaly_produces_critical_risk() -> None:
    prediction = build_prediction(
        model_name="robust_zscore",
        score=10.0,
        is_anomaly=True,
        prediction=-1,
    )

    result = RiskAssessmentService.assess(
        transaction_id=TRANSACTION_ID,
        transaction_reference=TRANSACTION_REFERENCE,
        prediction=prediction,
    )

    assert result.is_anomaly is True
    assert result.risk_score >= 85.0
    assert result.risk_level == "CRITICAL"


@pytest.mark.parametrize(
    "model_name,score",
    [
        ("isolation_forest", 1.0),
        ("local_outlier_factor", 2.0),
        ("kmeans_distance", 3.0),
        ("robust_zscore", 5.0),
    ],
)
def test_anomaly_scores_are_normalized_to_valid_range(
    model_name: str,
    score: float,
) -> None:
    prediction = build_prediction(
        model_name=model_name,
        score=score,
        is_anomaly=True,
        prediction=-1,
    )

    result = RiskAssessmentService.assess(
        transaction_id=TRANSACTION_ID,
        transaction_reference=TRANSACTION_REFERENCE,
        prediction=prediction,
    )

    assert 0.0 <= result.risk_score <= 100.0


def test_anomalous_prediction_cannot_be_classified_as_low_risk() -> None:
    prediction = build_prediction(
        model_name="robust_zscore",
        score=4.0,
        is_anomaly=True,
        prediction=-1,
    )

    result = RiskAssessmentService.assess(
        transaction_id=TRANSACTION_ID,
        transaction_reference=TRANSACTION_REFERENCE,
        prediction=prediction,
    )

    assert result.risk_level != "LOW"


def test_invalid_anomaly_model_is_rejected() -> None:
    prediction = build_prediction(
        model_name="isolation_forest",
        score=0.1,
        is_anomaly=True,
        prediction=-1,
    )

    prediction.model_name = "invalid_model"  # type: ignore[assignment]

    with pytest.raises(ValueError, match="Unsupported anomaly model"):
        RiskAssessmentService.assess(
            transaction_id=TRANSACTION_ID,
            transaction_reference=TRANSACTION_REFERENCE,
            prediction=prediction,
        )