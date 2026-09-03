from backend.app.events.payment_events import (
    PaymentEvent,
    ReconciliationEvent,
)
from backend.app.events.payment_event_producer import PaymentEventProducer
from backend.app.models.payment import PaymentIntent, Transaction


class TransactionEventService:
    @staticmethod
    def publish_payment_event(
        payment_intent: PaymentIntent,
        transaction: Transaction,
    ) -> None:
        event = PaymentEvent(
            payment_intent_id=payment_intent.id,
            transaction_id=transaction.id,
            transaction_reference=transaction.transaction_reference,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
            provider=transaction.provider,
        )

        producer = PaymentEventProducer()

        try:
            producer.publish_payment_event(event)
        finally:
            producer.close()

    @staticmethod
    def publish_reconciliation_event(
        transaction: Transaction,
        previous_status: str,
        provider_transaction_id: str | None = None,
    ) -> None:
        event = ReconciliationEvent(
            transaction_id=transaction.id,
            transaction_reference=transaction.transaction_reference,
            previous_status=previous_status,
            reconciled_status=transaction.status,
            provider=transaction.provider,
            provider_transaction_id=provider_transaction_id,
        )

        producer = PaymentEventProducer()

        try:
            producer.publish_reconciliation_event(event)
        finally:
            producer.close()