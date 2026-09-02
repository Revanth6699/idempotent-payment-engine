from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.payment import PaymentIntent, Transaction
from backend.app.services.transaction_processing_service import (
    TransactionProcessingService,
)


class TransactionOrchestratorService:
    @staticmethod
    def start_transaction(
        db: Session,
        payment_intent_id: UUID,
        provider: str,
    ) -> Transaction:
        payment_intent = (
            db.query(PaymentIntent)
            .filter(PaymentIntent.id == payment_intent_id)
            .first()
        )

        if payment_intent is None:
            raise ValueError("PaymentIntent not found")

        if payment_intent.status != "CREATED":
            raise ValueError(
                f"PaymentIntent cannot start transaction from "
                f"status {payment_intent.status}"
            )

        existing_transaction = (
            db.query(Transaction)
            .filter(Transaction.payment_intent_id == payment_intent.id)
            .first()
        )

        if existing_transaction is not None:
            return existing_transaction

        transaction = Transaction(
            payment_intent_id=payment_intent.id,
            transaction_reference=f"TXN-{UUID(int=payment_intent.id.int).hex.upper()}",
            provider=provider,
            amount=payment_intent.amount,
            currency=payment_intent.currency,
            status="PROCESSING",
        )

        db.add(transaction)
        db.flush()

        return TransactionProcessingService.process_transaction(
            db=db,
            payment_intent=payment_intent,
            transaction=transaction,
        )