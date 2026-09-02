from sqlalchemy.orm import Session

from backend.app.models.payment import (
    PaymentIntent,
    ReconciliationRecord,
    Transaction,
)
from backend.app.processors.simulator_processor import (
    ProcessorStatus,
    SimulatorProcessor,
)


class ReconciliationService:
    @staticmethod
    def reconcile_transaction(
        db: Session,
        payment_intent: PaymentIntent,
        transaction: Transaction,
    ) -> Transaction:
        if transaction.status != "UNKNOWN":
            raise ValueError(
                f"Only UNKNOWN transactions can be reconciled. "
                f"Current status: {transaction.status}"
            )

        reconciliation = (
            db.query(ReconciliationRecord)
            .filter(
                ReconciliationRecord.transaction_id == transaction.id
            )
            .first()
        )

        if reconciliation is None:
            reconciliation = ReconciliationRecord(
                transaction_id=transaction.id,
                status="PENDING",
            )
            db.add(reconciliation)
            db.flush()

        reconciliation.status = "PROCESSING"
        db.flush()

        processor = SimulatorProcessor(
            outcome=ProcessorStatus.UNKNOWN
        )


        processor_result = processor.reconcile(
            transaction.transaction_reference
        )

        reconciliation.processor_status = processor_result.status.value
        reconciliation.provider_transaction_id = (
            processor_result.provider_transaction_id
        )

        if processor_result.status == ProcessorStatus.SUCCESS:
            transaction.status = "SUCCESS"
            transaction.provider_transaction_id = (
                processor_result.provider_transaction_id
            )
            payment_intent.status = "SUCCESS"
            reconciliation.status = "RESOLVED"

        elif processor_result.status == ProcessorStatus.FAILED:
            transaction.status = "FAILED"
            payment_intent.status = "FAILED"
            reconciliation.status = "RESOLVED"

        elif processor_result.status == ProcessorStatus.UNKNOWN:
            transaction.status = "UNKNOWN"
            payment_intent.status = "UNKNOWN"
            reconciliation.status = "PENDING"

        else:
            raise ValueError(
                f"Unsupported processor reconciliation status: "
                f"{processor_result.status}"
            )

        db.commit()
        db.refresh(transaction)

        return transaction