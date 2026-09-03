from decimal import Decimal

import pandas as pd

from backend.app.events.payment_events import MLFeatureEvent


class FeatureEngineeringService:
    @staticmethod
    def build_features(event: MLFeatureEvent) -> pd.DataFrame:
        amount = Decimal(event.amount)

        features = {
            "transaction_id": str(event.transaction_id),
            "payment_intent_id": str(event.payment_intent_id),
            "amount": float(amount),
            "is_success": int(event.status == "SUCCESS"),
            "is_failed": int(event.status == "FAILED"),
            "is_unknown": int(event.status == "UNKNOWN"),
            "is_processing": int(event.status == "PROCESSING"),
            "provider": event.provider,
            "currency": event.currency,
        }

        return pd.DataFrame([features])