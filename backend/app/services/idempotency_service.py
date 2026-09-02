from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.payment import PaymentIntent, Transaction


class IdempotencyService:
    @staticmethod
    def get_or_create_transaction(
        db: Session,
        payment_intent_id: UUID,
        provider: str,
    ) -> Transaction:
        """
        Return the existing transaction for a PaymentIntent or create exactly
        one transaction while holding a database row lock on the PaymentIntent.

        The PaymentIntent row is locked before checking/creating the
        transaction. This prevents concurrent requests for the same logical
        payment from creating multiple transactions.
        """

        payment_intent = db.execute(
            select(PaymentIntent)
            .where(PaymentIntent.id == payment_intent_id)
            .with_for_update()
        ).scalar_one_or_none()

        if payment_intent is None:
            raise ValueError(
                f"PaymentIntent not found: {payment_intent_id}"
            )

        existing_transaction = db.execute(
            select(Transaction)
            .where(Transaction.payment_intent_id == payment_intent_id)
            .order_by(Transaction.created_at)
        ).scalars().first()

        if existing_transaction is not None:
            return existing_transaction

        transaction = Transaction(
            payment_intent_id=payment_intent.id,
            transaction_reference=f"TXN-{payment_intent.id.hex[:24].upper()}",
            provider=provider,
            amount=payment_intent.amount,
            currency=payment_intent.currency,
            status="CREATED",
        )

        db.add(transaction)
        db.flush()

        return transaction