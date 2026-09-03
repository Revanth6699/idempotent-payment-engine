from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.app.ml.anomaly_detection_service import (
    AnomalyDetectionService,
)
from backend.app.ml.anomaly_model_evaluation_service import (
    AnomalyModelEvaluationService,
)


def build_test_features() -> pd.DataFrame:
    """Build a deterministic synthetic feature dataset."""

    rng = np.random.default_rng(42)

    normal_features = rng.normal(
        loc=0.0,
        scale=1.0,
        size=(60, 4),
    )

    anomalous_features = np.array(
        [
            [8.0, 8.0, 8.0, 8.0],
            [-8.0, -8.0, -8.0, -8.0],
            [10.0, -10.0, 9.0, -9.0],
        ]
    )

    feature_matrix = np.vstack(
        [
            normal_features,
            anomalous_features,
        ]
    )

    return pd.DataFrame(
        feature_matrix,
        columns=[
            "amount_feature",
            "retry_feature",
            "failure_feature",
            "processing_time_feature",
        ],
    )


def test_detect_all_runs_all_candidate_models() -> None:
    features = build_test_features()

    results = AnomalyDetectionService.detect_all(features)

    expected_models = {
        "isolation_forest",
        "local_outlier_factor",
        "kmeans_distance",
        "robust_zscore",
    }

    assert set(results.keys()) == expected_models

    for model_name, result in results.items():
        assert result.model_name == model_name
        assert len(result.predictions) == len(features)
        assert result.anomaly_count >= 0
        assert 0.0 <= result.anomaly_rate <= 1.0


def test_isolation_forest_detects_anomalous_observations() -> None:
    features = build_test_features()

    result = AnomalyDetectionService.detect(
        features,
        "isolation_forest",
    )

    assert result.model_name == "isolation_forest"
    assert result.anomaly_count > 0

    anomaly_predictions = [
        prediction
        for prediction in result.predictions
        if prediction.is_anomaly
    ]

    assert len(anomaly_predictions) == result.anomaly_count


def test_local_outlier_factor_detects_anomalies() -> None:
    features = build_test_features()

    result = AnomalyDetectionService.detect(
        features,
        "local_outlier_factor",
    )

    assert result.model_name == "local_outlier_factor"
    assert result.anomaly_count > 0


def test_kmeans_distance_returns_valid_predictions() -> None:
    features = build_test_features()

    result = AnomalyDetectionService.detect(
        features,
        "kmeans_distance",
    )

    assert result.model_name == "kmeans_distance"
    assert len(result.predictions) == len(features)
    assert result.anomaly_count >= 0


def test_robust_zscore_detects_extreme_observations() -> None:
    features = build_test_features()

    result = AnomalyDetectionService.detect(
        features,
        "robust_zscore",
    )

    assert result.model_name == "robust_zscore"
    assert result.anomaly_count > 0


def test_model_evaluation_produces_all_candidates() -> None:
    features = build_test_features()

    evaluations = AnomalyModelEvaluationService.evaluate(
        features
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
        assert np.isfinite(evaluation.mean_score)
        assert np.isfinite(evaluation.score_std)


def test_model_evaluation_can_be_converted_to_dataframe() -> None:
    features = build_test_features()

    evaluations = AnomalyModelEvaluationService.evaluate(
        features
    )

    dataframe = AnomalyModelEvaluationService.as_dataframe(
        evaluations
    )

    assert isinstance(dataframe, pd.DataFrame)
    assert len(dataframe) == 4

    expected_columns = {
        "model_name",
        "sample_count",
        "anomaly_count",
        "anomaly_rate",
        "mean_score",
        "score_std",
    }

    assert set(dataframe.columns) == expected_columns


def test_empty_features_are_rejected() -> None:
    features = pd.DataFrame()

    with pytest.raises(ValueError, match="must not be empty"):
        AnomalyDetectionService.detect(
            features,
            "isolation_forest",
        )


def test_non_numeric_features_are_rejected() -> None:
    features = pd.DataFrame(
        {
            "status": ["SUCCESS", "FAILED"],
            "provider": ["SIMULATOR", "SIMULATOR"],
        }
    )

    with pytest.raises(
        ValueError,
        match="must contain numeric columns",
    ):
        AnomalyDetectionService.detect(
            features,
            "isolation_forest",
        )


def test_non_finite_features_are_rejected() -> None:
    features = pd.DataFrame(
        {
            "feature_a": [1.0, np.nan, 3.0],
            "feature_b": [2.0, 4.0, 5.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="must contain only finite numeric values",
    ):
        AnomalyDetectionService.detect(
            features,
            "isolation_forest",
        )


def test_local_outlier_factor_rejects_too_few_samples() -> None:
    features = pd.DataFrame(
        {
            "feature_a": [1.0, 2.0],
            "feature_b": [2.0, 3.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="at least 3 samples",
    ):
        AnomalyDetectionService.detect(
            features,
            "local_outlier_factor",
        )


def test_kmeans_rejects_single_sample() -> None:
    features = pd.DataFrame(
        {
            "feature_a": [1.0],
            "feature_b": [2.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="at least 2 samples",
    ):
        AnomalyDetectionService.detect(
            features,
            "kmeans_distance",
        )