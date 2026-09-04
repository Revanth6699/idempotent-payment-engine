from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func

from backend.app.core.database import SessionLocal
from backend.app.models.payment import PaymentIntent, Transaction
from backend.app.schemas.payment_schemas import PaymentIntentCreate
from backend.app.services.idempotency_service import IdempotencyService
from backend.app.services.transaction_orchestrator_service import (
    TransactionOrchestratorService,
)


def create_payment_intent(idempotency_key: str):
    db = SessionLocal()

    try:
        payment_data = PaymentIntentCreate(
            merchant_reference="CONCURRENT-TEST",
            idempotency_key=idempotency_key,
            amount=Decimal("100.00"),
            currency="INR",
        )

        payment_intent = IdempotencyService.get_or_create_payment_intent(
            db,
            payment_data,
        )

        return payment_intent.id

    finally:
        db.close()


def test_concurrent_idempotency():
    """
    Multiple concurrent requests using the same idempotency key
    must return the same PaymentIntent.
    """

    idempotency_key = "CONCURRENT-" + uuid4().hex

    with ThreadPoolExecutor(max_workers=5) as executor:
        returned_ids = list(
            executor.map(
                lambda _: create_payment_intent(idempotency_key),
                range(5),
            )
        )

    db = SessionLocal()

    try:
        database_count = (
            db.query(func.count(PaymentIntent.id))
            .filter(
                PaymentIntent.idempotency_key == idempotency_key
            )
            .scalar()
        )

    finally:
        db.close()

    assert len(set(returned_ids)) == 1
    assert database_count == 1


def create_transaction(payment_intent_id):
    db = SessionLocal()

    try:
        transaction = TransactionOrchestratorService.start_transaction(
            db=db,
            payment_intent_id=payment_intent_id,
            provider="SIMULATOR",
            outcome="SUCCESS",
        )

        return transaction.id

    finally:
        db.close()


def test_concurrent_transaction_idempotency():
    """
    Multiple concurrent transaction-start requests for the same
    PaymentIntent must result in only one financial Transaction.
    """

    setup_db = SessionLocal()

    try:
        run_id = uuid4().hex[:12]

        payment_intent = PaymentIntent(
            merchant_reference=f"CONCURRENT-IDEMP-{run_id}",
            idempotency_key=f"CONCURRENT-IDEMP-{run_id}",
            amount=Decimal("100.00"),
            currency="INR",
            status="CREATED",
        )

        setup_db.add(payment_intent)
        setup_db.commit()
        setup_db.refresh(payment_intent)

        payment_intent_id = payment_intent.id

    finally:
        setup_db.close()

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(
            executor.map(
                create_transaction,
                [payment_intent_id] * 10,
            )
        )

    transaction_ids = [
        result
        for result in results
        if result is not None
    ]

    assert len(transaction_ids) == 10
    assert len(set(transaction_ids)) == 1

    verification_db = SessionLocal()

    try:
        transaction_count = (
            verification_db.query(func.count(Transaction.id))
            .filter(
                Transaction.payment_intent_id == payment_intent_id
            )
            .scalar()
        )

        assert transaction_count == 1

    finally:
        verification_db.close()