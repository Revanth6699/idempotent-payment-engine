from __future__ import annotations

import numpy as np
import pandas as pd

from backend.app.ml.anomaly_detection_service import (
    AnomalyDetectionService,
)
from backend.app.ml.anomaly_model_evaluation_service import (
    AnomalyModelEvaluationService,
)
from backend.app.ml.mlflow_tracking_service import (
    MLflowTrackingService,
)
from backend.app.schemas.anomaly_schemas import (
    AnomalyModelEvaluation,
    AnomalyModelName,
)


class AnomalyExperimentService:
    """Orchestrates anomaly-model experiments.

    This service connects candidate anomaly detection, evaluation,
    and MLflow tracking without deciding the final production model.
    """

    EXPERIMENT_NAME = "payment-anomaly-detection"

    @classmethod
    def run_candidate_experiment(
        cls,
        features: pd.DataFrame,
        model_name: AnomalyModelName,
    ) -> AnomalyModelEvaluation:
        """Run and track one anomaly-detection candidate."""

        result = AnomalyDetectionService.detect(
            features=features,
            model_name=model_name,
        )

        scores = np.asarray(
            [
                prediction.score
                for prediction in result.predictions
            ],
            dtype=float,
        )

        evaluation = AnomalyModelEvaluation(
            model_name=model_name,
            sample_count=len(result.predictions),
            anomaly_count=result.anomaly_count,
            anomaly_rate=result.anomaly_rate,
            mean_score=float(scores.mean()),
            score_std=float(scores.std()),
        )

        MLflowTrackingService.start_run(
            run_name=f"{model_name}-experiment",
            experiment_name=cls.EXPERIMENT_NAME,
        )

        try:
            MLflowTrackingService.log_parameters(
                {
                    "model_name": model_name,
                    "sample_count": evaluation.sample_count,
                }
            )

            MLflowTrackingService.log_metrics(
                {
                    "anomaly_count": evaluation.anomaly_count,
                    "anomaly_rate": evaluation.anomaly_rate,
                    "mean_score": evaluation.mean_score,
                    "score_std": evaluation.score_std,
                }
            )

            MLflowTrackingService.log_tags(
                {
                    "experiment_type": "unsupervised_anomaly_detection",
                    "model_name": model_name,
                }
            )

        finally:
            MLflowTrackingService.end_run()

        return evaluation

    @classmethod
    def run_all_experiments(
        cls,
        features: pd.DataFrame,
    ) -> list[AnomalyModelEvaluation]:
        """Run and track every supported anomaly candidate."""

        evaluations: list[AnomalyModelEvaluation] = []

        for model_name in AnomalyDetectionService.SUPPORTED_MODELS:
            evaluation = cls.run_candidate_experiment(
                features=features,
                model_name=model_name,
            )

            evaluations.append(evaluation)

        return evaluations

    @staticmethod
    def evaluations_to_dataframe(
        evaluations: list[AnomalyModelEvaluation],
    ) -> pd.DataFrame:
        """Convert experiment results into a Pandas DataFrame."""

        return AnomalyModelEvaluationService.as_dataframe(
            evaluations
        )