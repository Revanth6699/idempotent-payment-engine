from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import f1_score, precision_score, recall_score

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
    """Orchestrates anomaly-model experiments and model selection."""

    EXPERIMENT_NAME = "payment-anomaly-detection"
    MODEL_SELECTION_RUN_NAME = "model-selection"
    GROUND_TRUTH_COLUMN = "ground_truth_anomaly"

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

    @classmethod
    def evaluate_model_predictions(
        cls,
        features: pd.DataFrame,
        model_name: AnomalyModelName,
    ) -> dict[str, float]:
        """Evaluate one candidate against synthetic ground truth.

        Ground-truth labels are used only for offline evaluation.
        They are never supplied to the anomaly-detection model.
        """

        if not isinstance(features, pd.DataFrame):
            raise TypeError("features must be a pandas DataFrame")

        if features.empty:
            raise ValueError("features must not be empty")

        if cls.GROUND_TRUTH_COLUMN not in features.columns:
            raise ValueError(
                f"features must contain '{cls.GROUND_TRUTH_COLUMN}'"
            )

        ground_truth = features[cls.GROUND_TRUTH_COLUMN]

        if ground_truth.isna().any():
            raise ValueError(
                "ground truth must not contain missing values"
            )

        if not ground_truth.isin([False, True, 0, 1]).all():
            raise ValueError(
                "ground truth must contain only boolean or binary values"
            )

        result = AnomalyDetectionService.detect(
            features=features,
            model_name=model_name,
        )

        predicted_anomalies = np.asarray(
            [
                prediction.is_anomaly
                for prediction in result.predictions
            ],
            dtype=int,
        )

        actual_anomalies = ground_truth.astype(int).to_numpy()

        if len(predicted_anomalies) != len(actual_anomalies):
            raise ValueError(
                "prediction count does not match ground-truth count"
            )

        return {
            "precision": float(
                precision_score(
                    actual_anomalies,
                    predicted_anomalies,
                    zero_division=0,
                )
            ),
            "recall": float(
                recall_score(
                    actual_anomalies,
                    predicted_anomalies,
                    zero_division=0,
                )
            ),
            "f1_score": float(
                f1_score(
                    actual_anomalies,
                    predicted_anomalies,
                    zero_division=0,
                )
            ),
        }

    @classmethod
    def evaluate_all_models(
        cls,
        features: pd.DataFrame,
    ) -> pd.DataFrame:
        """Evaluate every candidate against synthetic ground truth."""

        rows: list[dict[str, float | str]] = []

        for model_name in AnomalyDetectionService.SUPPORTED_MODELS:
            metrics = cls.evaluate_model_predictions(
                features=features,
                model_name=model_name,
            )

            rows.append(
                {
                    "model_name": model_name,
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1_score": metrics["f1_score"],
                }
            )

        return pd.DataFrame(rows)

    @classmethod
    def select_best_model(
        cls,
        features: pd.DataFrame,
    ) -> AnomalyModelName:
        """Select the best anomaly model using F1 score.

        Recall and precision are deterministic tie-breakers.
        """

        evaluation = cls.evaluate_all_models(features)

        best_row = evaluation.sort_values(
            by=["f1_score", "recall", "precision"],
            ascending=[False, False, False],
            kind="mergesort",
        ).iloc[0]

        return best_row["model_name"]

    @staticmethod
    def _create_selected_model_artifact(
        selected_model: AnomalyModelName,
        best_row: pd.Series,
    ) -> Path:
        """Create a reproducible configuration artifact for the selected model."""

        configuration = {
            "model_name": selected_model,
            "model_type": "statistical_anomaly_detection",
            "selection_metric": "f1_score",
            "precision": float(best_row["precision"]),
            "recall": float(best_row["recall"]),
            "f1_score": float(best_row["f1_score"]),
            "robust_zscore_threshold": 3.5,
        }

        temporary_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            prefix="selected_anomaly_model_",
            delete=False,
            encoding="utf-8",
        )

        artifact_path = Path(temporary_file.name)

        try:
            json.dump(
                configuration,
                temporary_file,
                indent=2,
            )
        finally:
            temporary_file.close()

        return artifact_path



    @classmethod
    def run_model_selection(
        cls,
        features: pd.DataFrame,
    ) -> tuple[AnomalyModelName, pd.DataFrame]:
        """Evaluate candidates, select the winner, and track selection."""

        evaluation = cls.evaluate_all_models(features)

        best_row = evaluation.sort_values(
            by=["f1_score", "recall", "precision"],
            ascending=[False, False, False],
            kind="mergesort",
        ).iloc[0]

        selected_model = best_row["model_name"]

        MLflowTrackingService.start_run(
            run_name=cls.MODEL_SELECTION_RUN_NAME,
            experiment_name=cls.EXPERIMENT_NAME,
        )

        try:
            MLflowTrackingService.log_parameters(
                {
                    "selection_metric": "f1_score",
                    "candidate_count": len(evaluation),
                    "sample_count": len(features),
                }
            )

            MLflowTrackingService.log_metrics(
                {
                    "selected_precision": float(
                        best_row["precision"]
                    ),
                    "selected_recall": float(
                        best_row["recall"]
                    ),
                    "selected_f1_score": float(
                        best_row["f1_score"]
                    ),
                }
            )

            MLflowTrackingService.log_tags(
                {
                    "experiment_type": "unsupervised_anomaly_detection",
                    "selected_model": selected_model,
                    "selection_method": "f1_score",
                }
            )

            artifact_path = cls._create_selected_model_artifact(
                selected_model=selected_model,
                best_row=best_row,
            )

            try:
                MLflowTrackingService.log_artifact(
                    artifact_path
                )
            finally:
                artifact_path.unlink(missing_ok=True)

        finally:
            MLflowTrackingService.end_run()
            
        return selected_model, evaluation

    @staticmethod
    def evaluations_to_dataframe(
        evaluations: list[AnomalyModelEvaluation],
    ) -> pd.DataFrame:
        """Convert experiment results into a Pandas DataFrame."""

        return AnomalyModelEvaluationService.as_dataframe(
            evaluations
        )