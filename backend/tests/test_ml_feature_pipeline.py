from decimal import Decimal
from uuid import uuid4

from backend.app.events.payment_events import MLFeatureEvent
from backend.app.ml.feature_engineering_service import (
    FeatureEngineeringService,
)
from backend.app.services.ml_feature_pipeline_service import (
    MLFeaturePipelineService,
)


def build_event() -> MLFeatureEvent:
    return MLFeatureEvent(
        payment_intent_id=uuid4(),
        transaction_id=uuid4(),
        transaction_reference="TXN-ML-TEST-001",
        amount=Decimal("500.00"),
        currency="INR",
        status="SUCCESS",
        provider="SIMULATED_PROVIDER",
    )


def test_feature_engineering():
    event = build_event()

    dataframe = FeatureEngineeringService.build_features(event)

    assert len(dataframe) == 1
    assert dataframe.iloc[0]["amount"] == 500.00
    assert dataframe.iloc[0]["is_success"] == 1
    assert dataframe.iloc[0]["is_failed"] == 0
    assert dataframe.iloc[0]["is_unknown"] == 0
    assert dataframe.iloc[0]["is_processing"] == 0
    assert dataframe.iloc[0]["currency"] == "INR"


def test_ml_feature_pipeline_record():
    event = build_event()

    record = MLFeaturePipelineService.generate_feature_record(event)

    assert record.transaction_id == event.transaction_id
    assert record.payment_intent_id == event.payment_intent_id
    assert record.amount == 500.00
    assert record.is_success == 1
    assert record.is_failed == 0
    assert record.is_unknown == 0
    assert record.is_processing == 0