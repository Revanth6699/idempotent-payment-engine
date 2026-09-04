from __future__ import annotations

import json
from collections import deque

import pandas as pd
from kafka import KafkaConsumer
from sqlalchemy.orm import Session

from backend.app.events.payment_events import MLFeatureEvent
from backend.app.ml.anomaly_detection_service import AnomalyDetectionService
from backend.app.schemas.anomaly_schemas import AnomalyModelName
from backend.app.ml.feature_engineering_service import (
    FeatureEngineeringService,
)
from backend.app.services.risk_assessment_service import (
    RiskAssessmentService,
)
from backend.app.services.risk_persistence_service import (
    RiskPersistenceService,
)


class MLFeatureEventConsumer:
    """
    Consumes ML feature events and executes the ML risk pipeline.

    Flow:

        MLFeatureEvent
            -> feature engineering
            -> anomaly detection
            -> risk assessment
            -> risk persistence
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        topic: str = "ml-feature-events",
        group_id: str = "ml-feature-event-consumer",
        model_name: AnomalyModelName = "isolation_forest",
        feature_window_size: int = 100,
    ) -> None:
        if feature_window_size < 1:
            raise ValueError(
                "feature_window_size must be greater than zero"
            )

        if model_name not in AnomalyDetectionService.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported anomaly model: {model_name}"
            )

        self.topic = topic
        self.model_name = model_name

        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda value: json.loads(
                value.decode("utf-8")
            ),
        )

        self._feature_window: deque[pd.DataFrame] = deque(
            maxlen=feature_window_size
        )

    def consume_once(self) -> MLFeatureEvent | None:
        """
        Consume and validate one ML feature event.

        This method reads one event but does not commit its Kafka offset.
        """
        message = next(self.consumer, None)

        if message is None:
            return None

        return MLFeatureEvent.model_validate(message.value)

    def process_event(
        self,
        db: Session,
        event: MLFeatureEvent,
    ):
        """
        Execute the complete ML -> risk pipeline.
        """
        features = FeatureEngineeringService.build_features(event)

        self._feature_window.append(features)

        feature_batch = pd.concat(
            list(self._feature_window),
            ignore_index=True,
        )

        anomaly_result = AnomalyDetectionService.detect(
            features=feature_batch,
            model_name=self.model_name,
        )

        prediction = self._get_current_prediction(
            event=event,
            feature_batch=feature_batch,
            anomaly_result=anomaly_result,
        )

        risk_assessment = RiskAssessmentService.assess(
            transaction_id=event.transaction_id,
            transaction_reference=event.transaction_reference,
            prediction=prediction,
        )

        return RiskPersistenceService.save(
            db=db,
            assessment=risk_assessment,
        )

        
    @staticmethod
    def _get_current_prediction(
        event: MLFeatureEvent,
        feature_batch: pd.DataFrame,
        anomaly_result,
    ):
        """
        Locate the anomaly prediction belonging to the current event.
        """
        current_indexes = feature_batch.index[
            feature_batch["transaction_id"]
            == str(event.transaction_id)
        ].tolist()

        if not current_indexes:
            raise ValueError(
                "Current transaction was not found in the feature batch"
            )

        current_index = current_indexes[-1]

        if current_index >= len(anomaly_result.predictions):
            raise ValueError(
                "Anomaly prediction count does not match feature batch"
            )

        return anomaly_result.predictions[current_index]

    def consume_and_process_once(
        self,
        db: Session,
    ):
        """
        Consume one event, execute the ML/risk pipeline, and commit
        the Kafka offset only after successful persistence.
        """
        message = next(self.consumer, None)

        if message is None:
            return None

        event = MLFeatureEvent.model_validate(message.value)

        risk_assessment = self.process_event(
            db=db,
            event=event,
        )

        self.consumer.commit()

        return risk_assessment

    def close(self) -> None:
        """Close the Kafka consumer."""
        self.consumer.close()