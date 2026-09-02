from sqlalchemy.orm import Session

from backend.app.models.payment import PaymentIntent
from backend.app.schemas.payment_schemas import PaymentIntentCreate


class PaymentService:
    @staticmethod
    def create_payment_intent(
        db: Session,
        payment_data: PaymentIntentCreate,
    ) -> PaymentIntent:
        payment_intent = PaymentIntent(
            merchant_reference=payment_data.merchant_reference,
            idempotency_key=payment_data.idempotency_key,
            amount=payment_data.amount,
            currency=payment_data.currency.upper(),
            status="CREATED",
        )

        db.add(payment_intent)
        db.commit()
        db.refresh(payment_intent)

        return payment_intent