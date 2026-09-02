from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from backend.app.core.database import SessionLocal
from backend.app.models.payment import PaymentIntent
from backend.app.services.idempotency_service import IdempotencyService


def create_transaction(payment_intent_id):
    db = SessionLocal()

    try:
        transaction = IdempotencyService.get_or_create_transaction(
            db=db,
            payment_intent_id=payment_intent_id,
            provider="SIMULATOR",
        )

        db.commit()
        db.refresh(transaction)

        return transaction.id

    finally:
        db.close()


def test_concurrent_idempotency():
    setup_db = SessionLocal()

    try:
        payment_intent = PaymentIntent(
            merchant_reference="CONCURRENT-IDEMP-001",
            idempotency_key="CONCURRENT-IDEMP-001",
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
        transaction_ids = list(
            executor.map(
                create_transaction,
                [payment_intent_id] * 10,
            )
        )

    assert len(transaction_ids) == 10
    assert len(set(transaction_ids)) == 1

    verification_db = SessionLocal()

    try:
        transactions = (
            verification_db.query(PaymentIntent)
            .filter(PaymentIntent.id == payment_intent_id)
            .one()
            .transactions
        )

        assert len(transactions) == 1

    finally:
        verification_db.close()