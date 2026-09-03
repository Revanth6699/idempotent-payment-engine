import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class TransactionLedger(Base):
    __tablename__ = "transaction_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    payment_intent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_intents.id"),
        nullable=False,
        index=True,
    )

    transaction_reference: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    entry_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    transaction: Mapped["Transaction"] = relationship()
    payment_intent: Mapped["PaymentIntent"] = relationship()