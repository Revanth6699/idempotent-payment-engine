from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AnomalyModelName = Literal[
    "isolation_forest",
    "local_outlier_factor",
    "kmeans_distance",
    "robust_zscore",
]


class AnomalyPrediction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: AnomalyModelName
    is_anomaly: bool
    score: float
    prediction: int = Field(
        description="1 for normal, -1 for anomaly."
    )


class AnomalyDetectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: AnomalyModelName
    predictions: list[AnomalyPrediction]
    anomaly_count: int
    anomaly_rate: float


class AnomalyModelEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: AnomalyModelName
    sample_count: int
    anomaly_count: int
    anomaly_rate: float
    mean_score: float
    score_std: float