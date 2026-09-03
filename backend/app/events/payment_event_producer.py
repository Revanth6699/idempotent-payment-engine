import json

from kafka import KafkaProducer

from backend.app.events.payment_events import (
    CallbackEvent,
    MLFeatureEvent,
    PaymentEvent,
    ReconciliationEvent,
    RetryEvent,
)


class PaymentEventProducer:
    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
    ):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )

    def publish_payment_event(
        self,
        event: PaymentEvent,
    ) -> None:
        self.producer.send(
            "payment-events",
            value=event.model_dump(mode="json"),
        )
        self.producer.flush()

    def publish_retry_event(
        self,
        event: RetryEvent,
    ) -> None:
        self.producer.send(
            "retry-events",
            value=event.model_dump(mode="json"),
        )
        self.producer.flush()

    def publish_callback_event(
        self,
        event: CallbackEvent,
    ) -> None:
        self.producer.send(
            "callback-events",
            value=event.model_dump(mode="json"),
        )
        self.producer.flush()

    def publish_reconciliation_event(
        self,
        event: ReconciliationEvent,
    ) -> None:
        self.producer.send(
            "reconciliation-events",
            value=event.model_dump(mode="json"),
        )
        self.producer.flush()

    def publish_ml_feature_event(
        self,
        event: MLFeatureEvent,
    ) -> None:
        self.producer.send(
            "ml-feature-events",
            value=event.model_dump(mode="json"),
        )
        self.producer.flush()

    def close(self) -> None:
        self.producer.close()