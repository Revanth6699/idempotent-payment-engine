from __future__ import annotations

from uuid import UUID

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.ml.anomaly_detection_service import AnomalyDetectionService
from backend.app.models.payment import Transaction
from backend.app.schemas.anomaly_schemas import AnomalyModelName
from backend.app.schemas.risk_schemas import RiskAssessment
from backend.app.services.risk_assessment_service import RiskAssessmentService
from backend.app.services.risk_persistence_service import RiskPersistenceService


class RiskAssessmentPipelineService:
    """Connects anomaly detection to risk assessment and persistence."""

    @staticmethod
    def assess_and_persist(
        db: Session,
        features: pd.DataFrame,
        transaction_ids: list[UUID],
        model_name: AnomalyModelName,
    ) -> list[RiskAssessment]:
        """Run the selected anomaly model and persist risk assessments.

        Each feature row must correspond to one transaction ID at the
        same position in transaction_ids.
        """

        if len(features) != len(transaction_ids):
            raise ValueError(
                "features and transaction_ids must contain the same number of rows"
            )

        if not transaction_ids:
            raise ValueError(
                "transaction_ids must not be empty"
            )

        transactions = db.scalars(
            select(Transaction).where(
                Transaction.id.in_(transaction_ids)
            )
        ).all()

        transactions_by_id = {
            transaction.id: transaction
            for transaction in transactions
        }

        missing_transaction_ids = [
            transaction_id
            for transaction_id in transaction_ids
            if transaction_id not in transactions_by_id
        ]

        if missing_transaction_ids:
            raise ValueError(
                f"Transactions not found: {missing_transaction_ids}"
            )

        detection_result = AnomalyDetectionService.detect(
            features=features,
            model_name=model_name,
        )

        if len(detection_result.predictions) != len(transaction_ids):
            raise ValueError(
                "Anomaly prediction count does not match transaction count"
            )

        assessments: list[RiskAssessment] = []

        for transaction_id, prediction in zip(
            transaction_ids,
            detection_result.predictions,
        ):
            transaction = transactions_by_id[transaction_id]

            assessment = RiskAssessmentService.assess(
                transaction_id=transaction.id,
                transaction_reference=transaction.transaction_reference,
                prediction=prediction,
            )

            RiskPersistenceService.save(
                db=db,
                assessment=assessment,
            )

            assessments.append(assessment)

        return assessments