from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func

from backend.app.core.database import SessionLocal
from backend.app.models.payment import PaymentIntent
from backend.app.schemas.payment_schemas import PaymentIntentCreate
from backend.app.services.idempotency_service import IdempotencyService


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
            .filter(PaymentIntent.idempotency_key == idempotency_key)
            .scalar()
        )

    finally:
        db.close()

    assert len(set(returned_ids)) == 1
    assert database_count == 1