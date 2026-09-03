from __future__ import annotations

from pathlib import Path
from typing import Any

import mlflow
import mlflow.sklearn


class MLflowTrackingService:
    """Handles MLflow experiment tracking for anomaly-detection models.

    This service is responsible only for experiment tracking.
    Model training, anomaly detection, evaluation, and model selection
    remain in their respective ML modules.
    """

    DEFAULT_EXPERIMENT_NAME = "payment-anomaly-detection"

    @classmethod
    def configure(
        cls,
        tracking_uri: str | None = None,
        experiment_name: str = DEFAULT_EXPERIMENT_NAME,
    ) -> str:
        """Configure MLflow tracking and return the experiment ID."""

        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)

        experiment = mlflow.get_experiment_by_name(experiment_name)

        if experiment is None:
            experiment_id = mlflow.create_experiment(
                name=experiment_name
            )
        else:
            experiment_id = experiment.experiment_id

        mlflow.set_experiment(experiment_name)

        return experiment_id

    @classmethod
    def start_run(
        cls,
        run_name: str,
        experiment_name: str = DEFAULT_EXPERIMENT_NAME,
        tracking_uri: str | None = None,
    ) -> mlflow.ActiveRun:
        """Start an MLflow run for an anomaly-model experiment."""

        cls.configure(
            tracking_uri=tracking_uri,
            experiment_name=experiment_name,
        )

        return mlflow.start_run(run_name=run_name)

    @staticmethod
    def log_parameters(
        parameters: dict[str, Any],
    ) -> None:
        """Log model or experiment parameters."""

        if not parameters:
            return

        normalized_parameters = {
            str(key): str(value)
            for key, value in parameters.items()
        }

        mlflow.log_params(normalized_parameters)

    @staticmethod
    def log_metrics(
        metrics: dict[str, float],
    ) -> None:
        """Log numerical evaluation metrics."""

        if not metrics:
            return

        normalized_metrics = {
            str(key): float(value)
            for key, value in metrics.items()
        }

        mlflow.log_metrics(normalized_metrics)

    @staticmethod
    def log_tags(
        tags: dict[str, str],
    ) -> None:
        """Log descriptive experiment metadata."""

        if not tags:
            return

        normalized_tags = {
            str(key): str(value)
            for key, value in tags.items()
        }

        mlflow.set_tags(normalized_tags)

    @staticmethod
    def log_artifact(
        artifact_path: str | Path,
    ) -> None:
        """Log a local file as an MLflow artifact."""

        path = Path(artifact_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Artifact does not exist: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Artifact path must be a file: {path}"
            )

        mlflow.log_artifact(str(path))

    @staticmethod
    def log_model(
        model: Any,
        artifact_path: str,
    ) -> None:
        """Persist a scikit-learn model through MLflow."""

        mlflow.sklearn.log_model(
            sk_model=model,
            name=artifact_path,
        )

    @staticmethod
    def end_run(
        status: str = "FINISHED",
    ) -> None:
        """End the currently active MLflow run."""

        if mlflow.active_run() is not None:
            mlflow.end_run(status=status)

    @staticmethod
    def get_active_run_id() -> str | None:
        """Return the active MLflow run ID, if one exists."""

        active_run = mlflow.active_run()

        if active_run is None:
            return None

        return active_run.info.run_id