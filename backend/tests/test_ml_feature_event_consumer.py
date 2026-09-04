from collections import deque
from decimal import Decimal
from uuid import uuid4

import pandas as pd

from backend.app.core.database import SessionLocal
from backend.app.events.ml_feature_event_consumer import (
    MLFeatureEventConsumer,
)
from backend.app.events.payment_events import MLFeatureEvent
from backend.app.models.payment import PaymentIntent, Transaction
from backend.app.models.risk_score_model import RiskScore


def create_transaction(db):
    payment_intent = PaymentIntent(
        merchant_reference=f"ML-CONSUMER-{uuid4().hex}",
        idempotency_key=f"ML-CONSUMER-IDEMP-{uuid4().hex}",
        amount=Decimal("500.00"),
        currency="INR",
        status="SUCCESS",
    )

    db.add(payment_intent)
    db.flush()

    transaction = Transaction(
        payment_intent_id=payment_intent.id,
        transaction_reference=f"TXN-ML-CONSUMER-{uuid4().hex.upper()}",
        provider="SIMULATED_PROVIDER",
        amount=payment_intent.amount,
        currency=payment_intent.currency,
        status="SUCCESS",
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return payment_intent, transaction


def create_event(payment_intent, transaction):
    return MLFeatureEvent(
        payment_intent_id=payment_intent.id,
        transaction_id=transaction.id,
        transaction_reference=transaction.transaction_reference,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        provider=transaction.provider,
    )


def create_test_consumer():
    consumer = MLFeatureEventConsumer.__new__(
        MLFeatureEventConsumer
    )

    consumer.topic = "ml-feature-events"
    consumer.model_name = "isolation_forest"
    consumer.consumer = None
    consumer._feature_window = deque(maxlen=100)

    return consumer


def test_process_event_runs_ml_risk_pipeline_and_persists_result():
    db = SessionLocal()

    try:
        payment_intent, transaction = create_transaction(db)
        event = create_event(payment_intent, transaction)

        consumer = create_test_consumer()

        result = consumer.process_event(
            db=db,
            event=event,
        )

        assert result is not None
        assert result.transaction_id == transaction.id
        assert result.transaction_reference == (
            transaction.transaction_reference
        )
        assert result.model_name == "isolation_forest"
        assert isinstance(result.risk_score, Decimal)

        persisted = (
            db.query(RiskScore)
            .filter(
                RiskScore.transaction_id == transaction.id
            )
            .first()
        )

        assert persisted is not None
        assert persisted.transaction_id == transaction.id
        assert persisted.transaction_reference == (
            transaction.transaction_reference
        )
        assert persisted.model_name == "isolation_forest"

    finally:
        db.close()


def test_process_event_is_idempotent_for_same_transaction():
    db = SessionLocal()

    try:
        payment_intent, transaction = create_transaction(db)
        event = create_event(payment_intent, transaction)

        consumer = create_test_consumer()

        first = consumer.process_event(
            db=db,
            event=event,
        )

        second = consumer.process_event(
            db=db,
            event=event,
        )

        assert first.id == second.id
        assert first.transaction_id == second.transaction_id

        records = (
            db.query(RiskScore)
            .filter(
                RiskScore.transaction_id == transaction.id
            )
            .all()
        )

        assert len(records) == 1

    finally:
        db.close()


def test_feature_window_contains_engineered_features():
    db = SessionLocal()

    try:
        payment_intent, transaction = create_transaction(db)
        event = create_event(payment_intent, transaction)

        consumer = create_test_consumer()

        consumer.process_event(
            db=db,
            event=event,
        )

        assert len(consumer._feature_window) == 1

        features = consumer._feature_window[0]

        assert isinstance(features, pd.DataFrame)
        assert len(features) == 1

        assert features.iloc[0]["transaction_id"] == str(
            transaction.id
        )
        assert features.iloc[0]["amount"] == 500.0
        assert features.iloc[0]["is_success"] == 1
        assert features.iloc[0]["is_failed"] == 0
        assert features.iloc[0]["is_unknown"] == 0
        assert features.iloc[0]["is_processing"] == 0

    finally:
        db.close()