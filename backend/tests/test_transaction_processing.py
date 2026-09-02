from decimal import Decimal

from backend.app.core.database import SessionLocal
from backend.app.models.payment import PaymentIntent
from backend.app.processors.payment_processor import (
    PaymentProcessorSimulator,
    ProcessorStatus,
)
from backend.app.schemas.payment_schemas import PaymentIntentCreate
from backend.app.services.payment_service import PaymentService
from backend.app.services.transaction_orchestrator_service import (
    TransactionOrchestratorService,
)
from backend.app.services.transaction_processing_service import (
    TransactionProcessingService,
)


def test_processor_state_transitions():
    db = SessionLocal()

    try:
        outcomes = [
            (
                "TEST-SUCCESS-001",
                "TEST-IDEMP-SUCCESS-001",
                ProcessorStatus.SUCCESS,
            ),
            (
                "TEST-FAILED-001",
                "TEST-IDEMP-FAILED-001",
                ProcessorStatus.FAILED,
            ),
            (
                "TEST-UNKNOWN-001",
                "TEST-IDEMP-UNKNOWN-001",
                ProcessorStatus.UNKNOWN,
            ),
        ]

        print("Testing processor state transitions...")

        for merchant_reference, idempotency_key, outcome in outcomes:
            payment_intent = PaymentService.create_payment_intent(
                db,
                PaymentIntentCreate(
                    merchant_reference=merchant_reference,
                    idempotency_key=idempotency_key,
                    amount=Decimal("100.00"),
                    currency="INR",
                ),
            )

            transaction = TransactionOrchestratorService.start_transaction(
                db,
                payment_intent.id,
                "SIMULATED_PROVIDER",
            )

            processor_result = PaymentProcessorSimulator.process_payment(
                transaction.id,
                transaction.amount,
                transaction.currency,
                outcome,
            )

            updated_transaction = (
                TransactionProcessingService.apply_processor_result(
                    db,
                    transaction.id,
                    processor_result,
                )
            )

            updated_payment_intent = db.get(
                PaymentIntent,
                payment_intent.id,
            )

            print(
                f"Result: {outcome.value} | "
                f"Transaction: {updated_transaction.status} | "
                f"PaymentIntent: {updated_payment_intent.status}"
            )

    finally:
        db.close()