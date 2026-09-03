from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4


class ProcessorStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ProcessorResult:
    status: ProcessorStatus
    provider_transaction_id: str | None
    amount: Decimal
    currency: str
    message: str


class PaymentProcessorSimulator:
    """
    Simulates an external payment processor.

    The simulator does not guarantee idempotency.
    Idempotency is enforced by the payment engine itself.
    """

    PROVIDER_NAME = "SIMULATED_PROVIDER"

    @staticmethod
    def process_payment(
        transaction_id: UUID,
        amount: Decimal,
        currency: str,
        outcome: ProcessorStatus,
    ) -> ProcessorResult:
        if amount <= 0:
            raise ValueError("Transaction amount must be greater than zero")

        currency = currency.upper()

        if outcome == ProcessorStatus.SUCCESS:
            return ProcessorResult(
                status=ProcessorStatus.SUCCESS,
                provider_transaction_id=f"PROV-{uuid4().hex.upper()}",
                amount=amount,
                currency=currency,
                message="Payment processed successfully",
            )

        if outcome == ProcessorStatus.FAILED:
            return ProcessorResult(
                status=ProcessorStatus.FAILED,
                provider_transaction_id=None,
                amount=amount,
                currency=currency,
                message="Payment processor rejected the transaction",
            )

        if outcome == ProcessorStatus.UNKNOWN:
            return ProcessorResult(
                status=ProcessorStatus.UNKNOWN,
                provider_transaction_id=None,
                amount=amount,
                currency=currency,
                message="Processor outcome could not be confirmed",
            )

        raise ValueError(f"Unsupported processor outcome: {outcome}")



class PaymentProcessor:
    def process_payment(
        self,
        transaction_reference: str,
        amount: Decimal,
        currency: str,
    ) -> dict:
        provider_transaction_id = f"SIM-{uuid4().hex[:20].upper()}"

        return {
            "transaction_reference": transaction_reference,
            "provider": "SIMULATOR",
            "provider_transaction_id": provider_transaction_id,
            "amount": amount,
            "currency": currency.upper(),
            "status": "SUCCESS",
        }