import json

from kafka import KafkaConsumer

from backend.app.events.payment_events import MLFeatureEvent


class MLFeatureEventConsumer:
    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        topic: str = "ml-feature-events",
        group_id: str = "ml-feature-event-consumer",
    ):
        self.topic = topic

        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda value: json.loads(
                value.decode("utf-8")
            ),
        )

    def consume_once(self) -> MLFeatureEvent | None:
        message = next(self.consumer, None)

        if message is None:
            return None

        return MLFeatureEvent.model_validate(message.value)

    def close(self) -> None:
        self.consumer.close()