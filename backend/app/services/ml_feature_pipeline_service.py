from backend.app.events.payment_events import MLFeatureEvent
from backend.app.ml.feature_engineering_service import (
    FeatureEngineeringService,
)
from backend.app.schemas.ml_feature_schemas import MLFeatureRecord


class MLFeaturePipelineService:
    @staticmethod
    def generate_feature_record(
        event: MLFeatureEvent,
    ) -> MLFeatureRecord:
        dataframe = FeatureEngineeringService.build_features(event)

        record = dataframe.iloc[0].to_dict()

        return MLFeatureRecord(
            transaction_id=event.transaction_id,
            payment_intent_id=event.payment_intent_id,
            amount=record["amount"],
            is_success=record["is_success"],
            is_failed=record["is_failed"],
            is_unknown=record["is_unknown"],
            is_processing=record["is_processing"],
            provider=record["provider"],
            currency=record["currency"],
        )