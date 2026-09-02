from backend.app.models.payment import PaymentIntent, Transaction


class TransactionStateService:
    ALLOWED_TRANSITIONS = {
        "CREATED": {"PROCESSING"},
        "PROCESSING": {"SUCCESS", "FAILED", "UNKNOWN"},
        "UNKNOWN": {"RECONCILING"},
        "RECONCILING": {"SUCCESS", "FAILED"},
        "SUCCESS": set(),
        "FAILED": set(),
    }

    @classmethod
    def transition_transaction(
        cls,
        transaction: Transaction,
        new_status: str,
    ) -> None:
        current_status = transaction.status

        allowed_statuses = cls.ALLOWED_TRANSITIONS.get(
            current_status,
            set(),
        )

        if new_status not in allowed_statuses:
            raise ValueError(
                f"Invalid transaction state transition: "
                f"{current_status} -> {new_status}"
            )

        transaction.status = new_status

    @staticmethod
    def sync_payment_intent_status(
        payment_intent: PaymentIntent,
        transaction: Transaction,
    ) -> None:
        if transaction.status == "SUCCESS":
            payment_intent.status = "SUCCESS"

        elif transaction.status == "FAILED":
            payment_intent.status = "FAILED"

        elif transaction.status == "UNKNOWN":
            payment_intent.status = "UNKNOWN"

        elif transaction.status == "RECONCILING":
            payment_intent.status = "RECONCILING"

        elif transaction.status == "PROCESSING":
            payment_intent.status = "PROCESSING"