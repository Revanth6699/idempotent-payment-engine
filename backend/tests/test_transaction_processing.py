from decimal import Decimal
from uuid import uuid4

from backend.app.core.database import SessionLocal
from backend.app.models.payment import PaymentIntent
from backend.app.processors.simulator_processor import ProcessorStatus
from backend.app.schemas.payment_schemas import PaymentIntentCreate
from backend.app.services.payment_service import PaymentService
from backend.app.services.transaction_orchestrator_service import (
    TransactionOrchestratorService,
)


def test_processor_state_transitions():
    db = SessionLocal()

    try:
        run_id = uuid4().hex[:12]

        outcomes = [
            (
                f"TEST-SUCCESS-{run_id}",
                f"TEST-IDEMP-SUCCESS-{run_id}",
                ProcessorStatus.SUCCESS,
                "SUCCESS",
            ),
            (
                f"TEST-FAILED-{run_id}",
                f"TEST-IDEMP-FAILED-{run_id}",
                ProcessorStatus.FAILED,
                "FAILED",
            ),
            (
                f"TEST-UNKNOWN-{run_id}",
                f"TEST-IDEMP-UNKNOWN-{run_id}",
                ProcessorStatus.UNKNOWN,
                "UNKNOWN",
            ),
        ]

        print("Testing processor state transitions...")

        for (
            merchant_reference,
            idempotency_key,
            outcome,
            expected_status,
        ) in outcomes:
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
                db=db,
                payment_intent_id=payment_intent.id,
                provider="SIMULATED_PROVIDER",
                outcome=outcome.value,
            )

            updated_payment_intent = db.get(
                PaymentIntent,
                payment_intent.id,
            )

            assert transaction.status == expected_status
            assert updated_payment_intent.status == expected_status

            print(
                f"Result: {outcome.value} | "
                f"Transaction: {transaction.status} | "
                f"PaymentIntent: {updated_payment_intent.status}"
            )

    finally:
        db.close()