from dataclasses import dataclass
from enum import Enum
import uuid


class ProcessorStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass
class ProcessorResult:
    status: ProcessorStatus
    provider_transaction_id: str | None = None


class SimulatorProcessor:
    _transactions: dict[str, ProcessorResult] = {}

    def __init__(self, outcome: ProcessorStatus = ProcessorStatus.SUCCESS):
        self.outcome = outcome

    def process(self, transaction_reference: str) -> ProcessorResult:
        if self.outcome == ProcessorStatus.SUCCESS:
            result = ProcessorResult(
                status=ProcessorStatus.SUCCESS,
                provider_transaction_id=f"SIM-{uuid.uuid4().hex.upper()}",
            )

        elif self.outcome == ProcessorStatus.FAILED:
            result = ProcessorResult(
                status=ProcessorStatus.FAILED,
            )

        elif self.outcome == ProcessorStatus.UNKNOWN:
            result = ProcessorResult(
                status=ProcessorStatus.UNKNOWN,
            )

        else:
            raise ValueError(
                f"Unsupported simulator outcome: {self.outcome}"
            )

        self._transactions[transaction_reference] = result

        return result

    def reconcile(self, transaction_reference: str) -> ProcessorResult:
        result = self._transactions.get(transaction_reference)

        if result is None:
            raise ValueError(
                f"Transaction not found at processor: "
                f"{transaction_reference}"
            )

        if result.status == ProcessorStatus.UNKNOWN:
            result = ProcessorResult(
                status=ProcessorStatus.SUCCESS,
                provider_transaction_id=f"SIM-{uuid.uuid4().hex.upper()}",
            )
            self._transactions[transaction_reference] = result

        return result