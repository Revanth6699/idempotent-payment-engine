from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.payment import Transaction
from backend.app.models.risk_score_model import RiskScore
from backend.app.schemas.risk_schemas import RiskAssessment


class RiskPersistenceService:
    """Persists and retrieves risk assessments for transactions."""

    @staticmethod
    def save(
        db: Session,
        assessment: RiskAssessment,
    ) -> RiskScore:
        """Persist a risk assessment for a transaction.

        A transaction can have only one persisted risk assessment.
        The database unique constraint on transaction_id provides
        the final protection against duplicate persistence.
        """

        transaction = db.scalar(
            select(Transaction).where(
                Transaction.id == assessment.transaction_id
            )
        )

        if transaction is None:
            raise ValueError(
                f"Transaction not found: {assessment.transaction_id}"
            )

        if transaction.transaction_reference != assessment.transaction_reference:
            raise ValueError(
                "Transaction reference does not match transaction ID."
            )

        existing = db.scalar(
            select(RiskScore).where(
                RiskScore.transaction_id == assessment.transaction_id
            )
        )

        if existing is not None:
            return existing

        risk_score = RiskScore(
            transaction_id=assessment.transaction_id,
            transaction_reference=assessment.transaction_reference,
            model_name=assessment.model_name,
            anomaly_score=assessment.anomaly_score,
            is_anomaly=assessment.is_anomaly,
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level,
        )

        db.add(risk_score)
        db.commit()
        db.refresh(risk_score)

        return risk_score

    @staticmethod
    def get_by_transaction_id(
        db: Session,
        transaction_id: UUID,
    ) -> RiskScore | None:
        """Retrieve the persisted risk assessment for a transaction."""

        return db.scalar(
            select(RiskScore).where(
                RiskScore.transaction_id == transaction_id
            )
        )