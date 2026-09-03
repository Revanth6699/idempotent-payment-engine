from __future__ import annotations

from pathlib import Path

import mlflow
import numpy as np
from sklearn.ensemble import IsolationForest

from backend.app.ml.mlflow_tracking_service import (
    MLflowTrackingService,
)
from mlflow.tracking import MlflowClient


def build_tracking_uri(tmp_path: Path) -> str:
    """Create an isolated SQLite MLflow tracking database."""

    database_path = tmp_path / "mlflow_test.db"

    return f"sqlite:///{database_path.as_posix()}"


def test_configure_creates_experiment(tmp_path: Path) -> None:
    tracking_uri = build_tracking_uri(tmp_path)

    experiment_name = "test-payment-anomaly-experiment"

    experiment_id = MLflowTrackingService.configure(
        tracking_uri=tracking_uri,
        experiment_name=experiment_name,
    )

    assert experiment_id is not None
    assert experiment_id != ""

    experiment = mlflow.get_experiment_by_name(
        experiment_name
    )

    assert experiment is not None
    assert experiment.experiment_id == experiment_id


def test_start_run_and_log_run_metadata(
    tmp_path: Path,
) -> None:
    tracking_uri = build_tracking_uri(tmp_path)

    experiment_name = "test-anomaly-run"

    MLflowTrackingService.start_run(
        run_name="isolation-forest-test",
        experiment_name=experiment_name,
        tracking_uri=tracking_uri,
    )

    try:
        MLflowTrackingService.log_parameters(
            {
                "n_estimators": 100,
                "random_state": 42,
            }
        )

        MLflowTrackingService.log_metrics(
            {
                "anomaly_rate": 0.05,
                "mean_score": 0.21,
            }
        )

        MLflowTrackingService.log_tags(
            {
                "model_type": "isolation_forest",
                "dataset": "synthetic",
            }
        )

        run_id = MLflowTrackingService.get_active_run_id()

        assert run_id is not None

        client = MlflowClient(
            tracking_uri=tracking_uri
        )

        persisted_run = client.get_run(run_id)

        assert persisted_run.data.params["n_estimators"] == "100"
        assert persisted_run.data.params["random_state"] == "42"

        assert persisted_run.data.metrics["anomaly_rate"] == 0.05
        assert persisted_run.data.metrics["mean_score"] == 0.21

        assert persisted_run.data.tags["model_type"] == (
            "isolation_forest"
        )

        assert persisted_run.data.tags["dataset"] == (
            "synthetic"
        )

    finally:
        MLflowTrackingService.end_run()

def test_end_run_closes_active_run(
    tmp_path: Path,
) -> None:
    tracking_uri = build_tracking_uri(tmp_path)

    MLflowTrackingService.start_run(
        run_name="run-close-test",
        experiment_name="test-run-close",
        tracking_uri=tracking_uri,
    )

    assert (
        MLflowTrackingService.get_active_run_id()
        is not None
    )

    MLflowTrackingService.end_run()

    assert (
        MLflowTrackingService.get_active_run_id()
        is None
    )

    assert mlflow.active_run() is None


def test_end_run_is_safe_without_active_run() -> None:
    mlflow.end_run()

    MLflowTrackingService.end_run()

    assert (
        MLflowTrackingService.get_active_run_id()
        is None
    )


def test_log_artifact(tmp_path: Path) -> None:
    tracking_uri = build_tracking_uri(tmp_path)

    artifact_file = tmp_path / "evaluation.txt"

    artifact_file.write_text(
        "anomaly_rate=0.05\n",
        encoding="utf-8",
    )

    MLflowTrackingService.start_run(
        run_name="artifact-test",
        experiment_name="test-artifact-run",
        tracking_uri=tracking_uri,
    )

    try:
        MLflowTrackingService.log_artifact(
            artifact_file
        )

        run_id = MLflowTrackingService.get_active_run_id()

        assert run_id is not None

    finally:
        MLflowTrackingService.end_run()


def test_log_artifact_rejects_missing_file(
    tmp_path: Path,
) -> None:
    missing_file = tmp_path / "missing.txt"

    try:
        MLflowTrackingService.log_artifact(
            missing_file
        )
    except FileNotFoundError as exc:
        assert "Artifact does not exist" in str(exc)
    else:
        raise AssertionError(
            "Expected FileNotFoundError"
        )


def test_log_artifact_rejects_directory(
    tmp_path: Path,
) -> None:
    artifact_directory = tmp_path / "artifacts"
    artifact_directory.mkdir()

    try:
        MLflowTrackingService.log_artifact(
            artifact_directory
        )
    except ValueError as exc:
        assert "Artifact path must be a file" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_log_sklearn_model(tmp_path: Path) -> None:
    tracking_uri = build_tracking_uri(tmp_path)

    features = np.array(
        [
            [1.0, 1.0],
            [1.1, 1.0],
            [0.9, 1.2],
            [1.2, 0.8],
            [8.0, 8.0],
        ]
    )

    model = IsolationForest(
        n_estimators=20,
        random_state=42,
    )

    model.fit(features)

    MLflowTrackingService.start_run(
        run_name="model-artifact-test",
        experiment_name="test-model-artifact",
        tracking_uri=tracking_uri,
    )

    try:
        MLflowTrackingService.log_model(
            model=model,
            artifact_path="isolation_forest_model",
        )

        run_id = MLflowTrackingService.get_active_run_id()

        assert run_id is not None

    finally:
        MLflowTrackingService.end_run()


def test_empty_parameters_and_metrics_are_safe(
    tmp_path: Path,
) -> None:
    tracking_uri = build_tracking_uri(tmp_path)

    MLflowTrackingService.start_run(
        run_name="empty-metadata-test",
        experiment_name="test-empty-metadata",
        tracking_uri=tracking_uri,
    )

    try:
        MLflowTrackingService.log_parameters({})
        MLflowTrackingService.log_metrics({})
        MLflowTrackingService.log_tags({})

        assert (
            MLflowTrackingService.get_active_run_id()
            is not None
        )

    finally:
        MLflowTrackingService.end_run()