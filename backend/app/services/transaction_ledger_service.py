from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.payment import PaymentIntent, Transaction
from backend.app.models.transaction_ledger_model import TransactionLedger


class TransactionLedgerService:
    @staticmethod
    def create_ledger_entry(
        db: Session,
        payment_intent: PaymentIntent,
        transaction: Transaction,
    ) -> TransactionLedger:
        if transaction.payment_intent_id != payment_intent.id:
            raise ValueError(
                "Transaction does not belong to the provided PaymentIntent"
            )

        if transaction.status != "SUCCESS":
            raise ValueError(
                "Only SUCCESS transactions can create ledger entries. "
                f"Current status: {transaction.status}"
            )

        existing_entry = (
            db.query(TransactionLedger)
            .filter(
                TransactionLedger.transaction_id == transaction.id
            )
            .first()
        )

        if existing_entry is not None:
            return existing_entry

        ledger_entry = TransactionLedger(
            transaction_id=transaction.id,
            payment_intent_id=payment_intent.id,
            transaction_reference=transaction.transaction_reference,
            entry_type="PAYMENT",
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
        )

        db.add(ledger_entry)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()

            existing_entry = (
                db.query(TransactionLedger)
                .filter(
                    TransactionLedger.transaction_id == transaction.id
                )
                .first()
            )

            if existing_entry is None:
                raise

            return existing_entry

        db.refresh(ledger_entry)

        return ledger_entry

    @staticmethod
    def get_by_transaction_id(
        db: Session,
        transaction_id: UUID,
    ) -> TransactionLedger | None:
        return (
            db.query(TransactionLedger)
            .filter(
                TransactionLedger.transaction_id == transaction_id
            )
            .first()
        )