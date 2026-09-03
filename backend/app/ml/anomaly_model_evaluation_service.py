from __future__ import annotations

import numpy as np
import pandas as pd

from backend.app.ml.anomaly_detection_service import (
    AnomalyDetectionService,
)
from backend.app.schemas.anomaly_schemas import (
    AnomalyModelEvaluation,
)


class AnomalyModelEvaluationService:
    """Evaluates and compares the unsupervised anomaly candidates.

    Because the anomaly-detection pipeline has no ground-truth labels,
    this service reports descriptive model behavior rather than
    fabricated supervised metrics such as accuracy or recall.
    """

    @staticmethod
    def evaluate(
        features: pd.DataFrame,
    ) -> list[AnomalyModelEvaluation]:
        """Run all candidate models and produce comparable evaluations."""

        results = AnomalyDetectionService.detect_all(features)

        evaluations: list[AnomalyModelEvaluation] = []

        for model_name, result in results.items():
            scores = np.asarray(
                [
                    prediction.score
                    for prediction in result.predictions
                ],
                dtype=float,
            )

            evaluations.append(
                AnomalyModelEvaluation(
                    model_name=model_name,
                    sample_count=len(result.predictions),
                    anomaly_count=result.anomaly_count,
                    anomaly_rate=result.anomaly_rate,
                    mean_score=float(scores.mean()),
                    score_std=float(scores.std()),
                )
            )

        return evaluations

    @staticmethod
    def as_dataframe(
        evaluations: list[AnomalyModelEvaluation],
    ) -> pd.DataFrame:
        """Convert model evaluations into a Pandas DataFrame."""

        return pd.DataFrame(
            [
                evaluation.model_dump()
                for evaluation in evaluations
            ]
        )