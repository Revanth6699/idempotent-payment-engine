from sqlalchemy.orm import Session

from backend.app.models.payment import PaymentIntent, Transaction
from backend.app.processors.simulator_processor import (
    ProcessorStatus,
    SimulatorProcessor,
)
from backend.app.services.transaction_state_service import (
    TransactionStateService,
)


class TransactionProcessingService:
    @staticmethod
    def process_transaction(
        db: Session,
        payment_intent: PaymentIntent,
        transaction: Transaction,
    ) -> Transaction:
        if transaction.status != "PROCESSING":
            raise ValueError(
                f"Transaction cannot accept a processor result from "
                f"status {transaction.status}"
            )

        processor = SimulatorProcessor()
        processor_result = processor.process(transaction.transaction_reference)

        if processor_result.status == ProcessorStatus.SUCCESS:
            TransactionStateService.transition_transaction(
                transaction,
                "SUCCESS",
            )

            transaction.provider_transaction_id = (
                processor_result.provider_transaction_id
            )

        elif processor_result.status == ProcessorStatus.FAILED:
            TransactionStateService.transition_transaction(
                transaction,
                "FAILED",
            )

        elif processor_result.status == ProcessorStatus.UNKNOWN:
            TransactionStateService.transition_transaction(
                transaction,
                "UNKNOWN",
            )

        else:
            raise ValueError(
                f"Unsupported processor status: {processor_result.status}"
            )

        TransactionStateService.sync_payment_intent_status(
            payment_intent,
            transaction,
        )

        db.commit()
        db.refresh(transaction)

        return transaction