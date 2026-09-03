from __future__ import annotations

import pandas as pd

from backend.app.ml.anomaly_experiment_service import (
    AnomalyExperimentService,
)
from backend.app.schemas.anomaly_schemas import (
    AnomalyModelEvaluation,
)


def build_test_features() -> pd.DataFrame:
    """Build deterministic synthetic features for experiments."""

    return pd.DataFrame(
        {
            "amount": [
                100.0,
                120.0,
                95.0,
                110.0,
                105.0,
                130.0,
                115.0,
                125.0,
                1000.0,
                1500.0,
            ],
            "retry_count": [
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                5.0,
                7.0,
            ],
            "failure_indicator": [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                1.0,
            ],
            "processing_time": [
                0.20,
                0.25,
                0.30,
                0.22,
                0.27,
                0.24,
                0.29,
                0.21,
                2.50,
                3.00,
            ],
        }
    )


def test_run_candidate_experiment_returns_evaluation(
    monkeypatch,
) -> None:
    features = build_test_features()

    def fake_start_run(
        run_name: str,
        experiment_name: str,
        tracking_uri: str | None = None,
    ):
        return None

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.start_run",
        fake_start_run,
    )

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.log_parameters",
        lambda parameters: None,
    )

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.log_metrics",
        lambda metrics: None,
    )

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.log_tags",
        lambda tags: None,
    )

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.end_run",
        lambda: None,
    )

    evaluation = (
        AnomalyExperimentService.run_candidate_experiment(
            features=features,
            model_name="isolation_forest",
        )
    )

    assert isinstance(
        evaluation,
        AnomalyModelEvaluation,
    )

    assert evaluation.model_name == "isolation_forest"
    assert evaluation.sample_count == len(features)
    assert evaluation.anomaly_count >= 0
    assert 0.0 <= evaluation.anomaly_rate <= 1.0


def test_run_all_experiments_runs_all_candidates(
    monkeypatch,
) -> None:
    features = build_test_features()

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.start_run",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.log_parameters",
        lambda parameters: None,
    )

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.log_metrics",
        lambda metrics: None,
    )

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.log_tags",
        lambda tags: None,
    )

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.end_run",
        lambda: None,
    )

    evaluations = (
        AnomalyExperimentService.run_all_experiments(
            features
        )
    )

    assert len(evaluations) == 4

    model_names = {
        evaluation.model_name
        for evaluation in evaluations
    }

    assert model_names == {
        "isolation_forest",
        "local_outlier_factor",
        "kmeans_distance",
        "robust_zscore",
    }

    for evaluation in evaluations:
        assert evaluation.sample_count == len(features)
        assert evaluation.anomaly_count >= 0
        assert 0.0 <= evaluation.anomaly_rate <= 1.0


def test_evaluations_to_dataframe() -> None:
    evaluations = [
        AnomalyModelEvaluation(
            model_name="isolation_forest",
            sample_count=10,
            anomaly_count=2,
            anomaly_rate=0.2,
            mean_score=0.15,
            score_std=0.05,
        ),
        AnomalyModelEvaluation(
            model_name="robust_zscore",
            sample_count=10,
            anomaly_count=2,
            anomaly_rate=0.2,
            mean_score=1.8,
            score_std=0.7,
        ),
    ]

    dataframe = (
        AnomalyExperimentService.evaluations_to_dataframe(
            evaluations
        )
    )

    assert isinstance(dataframe, pd.DataFrame)
    assert len(dataframe) == 2

    assert set(dataframe["model_name"]) == {
        "isolation_forest",
        "robust_zscore",
    }

    assert list(dataframe["sample_count"]) == [
        10,
        10,
    ]


def test_candidate_experiment_closes_mlflow_run_on_failure(
    monkeypatch,
) -> None:
    features = build_test_features()

    calls = {
        "start": 0,
        "end": 0,
    }

    def fake_start_run(**kwargs):
        calls["start"] += 1
        return None

    def fake_end_run():
        calls["end"] += 1

    def failing_log_metrics(metrics):
        raise RuntimeError("MLflow metric failure")

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.start_run",
        fake_start_run,
    )

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.log_parameters",
        lambda parameters: None,
    )

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.log_metrics",
        failing_log_metrics,
    )

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.log_tags",
        lambda tags: None,
    )

    monkeypatch.setattr(
        "backend.app.ml.anomaly_experiment_service."
        "MLflowTrackingService.end_run",
        fake_end_run,
    )

    try:
        AnomalyExperimentService.run_candidate_experiment(
            features=features,
            model_name="isolation_forest",
        )
    except RuntimeError as exc:
        assert str(exc) == "MLflow metric failure"
    else:
        raise AssertionError(
            "Expected RuntimeError"
        )

    assert calls["start"] == 1
    assert calls["end"] == 1