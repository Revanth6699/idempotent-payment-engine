from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from backend.app.schemas.anomaly_schemas import (
    AnomalyDetectionResult,
    AnomalyModelName,
    AnomalyPrediction,
)


class AnomalyDetectionService:
    """Runs the locked unsupervised anomaly-detection candidates.

    This service executes candidate models independently.
    Model selection and comparative evaluation are handled separately.
    """

    SUPPORTED_MODELS: tuple[AnomalyModelName, ...] = (
        "isolation_forest",
        "local_outlier_factor",
        "kmeans_distance",
        "robust_zscore",
    )

    RANDOM_STATE = 42

    @staticmethod
    def _prepare_features(features: pd.DataFrame) -> np.ndarray:
        """Validate and convert the feature DataFrame into a numeric matrix."""

        if not isinstance(features, pd.DataFrame):
            raise TypeError("features must be a pandas DataFrame")

        if features.empty:
            raise ValueError("features must not be empty")

        numeric_features = features.select_dtypes(
            include=[np.number]
        ).copy()

        if numeric_features.empty:
            raise ValueError(
                "features must contain numeric columns"
            )

        feature_matrix = numeric_features.to_numpy(dtype=float)

        if not np.isfinite(feature_matrix).all():
            raise ValueError(
                "features must contain only finite numeric values"
            )

        return feature_matrix

    @staticmethod
    def _build_predictions(
        model_name: AnomalyModelName,
        prediction: np.ndarray,
        scores: np.ndarray,
    ) -> AnomalyDetectionResult:
        """Convert model outputs into the common anomaly result schema."""

        prediction = prediction.astype(int)
        scores = scores.astype(float)

        anomalies = prediction == -1

        records = [
            AnomalyPrediction(
                model_name=model_name,
                is_anomaly=bool(is_anomaly),
                score=float(score),
                prediction=int(label),
            )
            for is_anomaly, score, label in zip(
                anomalies,
                scores,
                prediction,
            )
        ]

        return AnomalyDetectionResult(
            model_name=model_name,
            predictions=records,
            anomaly_count=int(anomalies.sum()),
            anomaly_rate=float(anomalies.mean()),
        )

    @classmethod
    def detect(
        cls,
        features: pd.DataFrame,
        model_name: AnomalyModelName,
    ) -> AnomalyDetectionResult:
        """Run one supported anomaly-detection candidate."""

        feature_matrix = cls._prepare_features(features)

        if model_name not in cls.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported anomaly model: {model_name}"
            )

        if model_name == "isolation_forest":
            return cls._isolation_forest(feature_matrix)

        if model_name == "local_outlier_factor":
            return cls._local_outlier_factor(feature_matrix)

        if model_name == "kmeans_distance":
            return cls._kmeans_distance(feature_matrix)

        return cls._robust_zscore(feature_matrix)

    @classmethod
    def detect_all(
        cls,
        features: pd.DataFrame,
    ) -> dict[AnomalyModelName, AnomalyDetectionResult]:
        """Run every candidate model for experimental comparison."""

        return {
            model_name: cls.detect(features, model_name)
            for model_name in cls.SUPPORTED_MODELS
        }

    @classmethod
    def _isolation_forest(
        cls,
        feature_matrix: np.ndarray,
    ) -> AnomalyDetectionResult:
        """Run Isolation Forest."""

        model = IsolationForest(
            n_estimators=200,
            random_state=cls.RANDOM_STATE,
            contamination="auto",
        )

        prediction = model.fit_predict(feature_matrix)

        # Isolation Forest decision_function:
        # larger values indicate more normal observations.
        #
        # Negating the value gives us a score where:
        # larger score = more anomalous.
        scores = -model.decision_function(feature_matrix)

        return cls._build_predictions(
            model_name="isolation_forest",
            prediction=prediction,
            scores=scores,
        )

    @classmethod
    def _local_outlier_factor(
        cls,
        feature_matrix: np.ndarray,
    ) -> AnomalyDetectionResult:
        """Run Local Outlier Factor."""

        sample_count = len(feature_matrix)

        if sample_count < 3:
            raise ValueError(
                "Local Outlier Factor requires at least 3 samples"
            )

        n_neighbors = min(20, sample_count - 1)

        model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination="auto",
            novelty=False,
        )

        prediction = model.fit_predict(feature_matrix)

        # negative_outlier_factor_:
        # lower values indicate stronger outlier behavior.
        #
        # Negating it gives a consistent interpretation:
        # larger score = more anomalous.
        scores = -model.negative_outlier_factor_

        return cls._build_predictions(
            model_name="local_outlier_factor",
            prediction=prediction,
            scores=scores,
        )

    @classmethod
    def _kmeans_distance(
        cls,
        feature_matrix: np.ndarray,
    ) -> AnomalyDetectionResult:
        """Run clustering-distance anomaly detection."""

        sample_count = len(feature_matrix)

        if sample_count < 2:
            raise ValueError(
                "KMeans anomaly detection requires at least 2 samples"
            )

        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(feature_matrix)

        n_clusters = min(
            max(2, int(np.sqrt(sample_count))),
            sample_count - 1,
        )

        model = KMeans(
            n_clusters=n_clusters,
            random_state=cls.RANDOM_STATE,
            n_init=10,
        )

        model.fit(scaled_features)

        cluster_centers = model.cluster_centers_[
            model.labels_
        ]

        distances = np.linalg.norm(
            scaled_features - cluster_centers,
            axis=1,
        )

        # Experimental candidate threshold.
        #
        # Observations above the 95th percentile of their
        # cluster-distance distribution are marked anomalous.
        threshold = float(
            np.quantile(distances, 0.95)
        )

        prediction = np.where(
            distances > threshold,
            -1,
            1,
        )

        return cls._build_predictions(
            model_name="kmeans_distance",
            prediction=prediction,
            scores=distances,
        )

    @classmethod
    def _robust_zscore(
        cls,
        feature_matrix: np.ndarray,
    ) -> AnomalyDetectionResult:
        """Run robust statistical anomaly detection using median and MAD."""

        median = np.median(
            feature_matrix,
            axis=0,
        )

        mad = np.median(
            np.abs(feature_matrix - median),
            axis=0,
        )

        # Prevent division by zero for constant features.
        safe_mad = np.where(
            mad == 0,
            1.0,
            mad,
        )

        robust_z_scores = (
            0.6745
            * np.abs(feature_matrix - median)
            / safe_mad
        )

        # Use the strongest deviation across all features
        # as the observation-level anomaly score.
        scores = np.max(
            robust_z_scores,
            axis=1,
        )

        prediction = np.where(
            scores > 3.5,
            -1,
            1,
        )

        return cls._build_predictions(
            model_name="robust_zscore",
            prediction=prediction,
            scores=scores,
        )