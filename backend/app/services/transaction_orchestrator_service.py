from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.payment import PaymentIntent, Transaction
from backend.app.services.transaction_processing_service import (
    TransactionProcessingService,
)
from backend.app.services.transaction_state_service import (
    TransactionStateService,
)
from backend.app.processors.simulator_processor import ProcessorStatus


class TransactionOrchestratorService:
    @staticmethod
    def start_transaction(
        db: Session,
        payment_intent_id: UUID,
        provider: str,
        outcome: str = "SUCCESS",
    ) -> Transaction:
        payment_intent = (
            db.query(PaymentIntent)
            .filter(PaymentIntent.id == payment_intent_id)
            .with_for_update()
            .first()
        )

        if payment_intent is None:
            raise ValueError("PaymentIntent not found")

        existing_transaction = (
            db.query(Transaction)
            .filter(Transaction.payment_intent_id == payment_intent.id)
            .first()
        )

        if existing_transaction is not None:
            return existing_transaction

        if payment_intent.status != "CREATED":
            raise ValueError(
                f"PaymentIntent cannot start transaction from "
                f"status {payment_intent.status}"
            )

        transaction = Transaction(
            payment_intent_id=payment_intent.id,
            transaction_reference=(
                f"TXN-{UUID(int=payment_intent.id.int).hex.upper()}"
            ),
            provider=provider,
            amount=payment_intent.amount,
            currency=payment_intent.currency,
            status="CREATED",
        )

        db.add(transaction)
        db.flush()

        TransactionStateService.transition_transaction(
            transaction,
            "PROCESSING",
        )

        try:
            processor_outcome = ProcessorStatus(outcome.upper())
        except ValueError:
            db.rollback()
            raise ValueError(
                f"Unsupported processor outcome: {outcome}"
            )

        try:
            return TransactionProcessingService.process_transaction(
                db=db,
                payment_intent=payment_intent,
                transaction=transaction,
                processor_outcome=processor_outcome,
            )
        except Exception:
            db.rollback()
            raise