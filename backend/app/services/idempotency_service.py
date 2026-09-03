from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.payment import PaymentIntent
from backend.app.schemas.payment_schemas import PaymentIntentCreate


class IdempotencyService:
    @staticmethod
    def get_or_create_payment_intent(
        db: Session,
        payment_data: PaymentIntentCreate,
    ) -> PaymentIntent:
        existing_payment = (
            db.query(PaymentIntent)
            .filter(
                PaymentIntent.idempotency_key
                == payment_data.idempotency_key
            )
            .first()
        )

        if existing_payment is not None:
            return existing_payment

        payment_intent = PaymentIntent(
            merchant_reference=payment_data.merchant_reference,
            idempotency_key=payment_data.idempotency_key,
            amount=payment_data.amount,
            currency=payment_data.currency.upper(),
            status="CREATED",
        )

        db.add(payment_intent)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()

            existing_payment = (
                db.query(PaymentIntent)
                .filter(
                    PaymentIntent.idempotency_key
                    == payment_data.idempotency_key
                )
                .first()
            )

            if existing_payment is None:
                raise

            return existing_payment

        db.refresh(payment_intent)

        return payment_intent