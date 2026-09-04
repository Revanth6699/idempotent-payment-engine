from decimal import Decimal
from uuid import uuid4

import pytest

from backend.app.core.database import SessionLocal
from backend.app.models.payment import PaymentIntent, Transaction
from backend.app.models.risk_score_model import RiskScore
from backend.app.schemas.risk_schemas import RiskAssessment
from backend.app.services.risk_persistence_service import RiskPersistenceService


def create_transaction(db):
    payment_intent = PaymentIntent(
        merchant_reference=f"RISK-TEST-{uuid4().hex}",
        idempotency_key=f"RISK-IDEMP-{uuid4().hex}",
        amount=Decimal("250.00"),
        currency="INR",
        status="SUCCESS",
    )

    db.add(payment_intent)
    db.flush()

    transaction = Transaction(
        payment_intent_id=payment_intent.id,
        transaction_reference=f"TXN-RISK-{uuid4().hex.upper()}",
        provider="SIMULATED_PROVIDER",
        amount=payment_intent.amount,
        currency=payment_intent.currency,
        status="SUCCESS",
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


def build_assessment(transaction):
    return RiskAssessment(
        transaction_id=transaction.id,
        transaction_reference=transaction.transaction_reference,
        model_name="isolation_forest",
        anomaly_score=0.85,
        is_anomaly=True,
        risk_score=91.50,
        risk_level="CRITICAL",
    )


def test_save_risk_assessment():
    db = SessionLocal()

    try:
        transaction = create_transaction(db)
        assessment = build_assessment(transaction)

        result = RiskPersistenceService.save(
            db=db,
            assessment=assessment,
        )

        assert result.id is not None
        assert result.transaction_id == transaction.id
        assert result.transaction_reference == transaction.transaction_reference
        assert result.model_name == "isolation_forest"
        assert result.anomaly_score == pytest.approx(0.85)
        assert result.is_anomaly is True
        assert float(result.risk_score) == pytest.approx(91.50)
        assert result.risk_level == "CRITICAL"

    finally:
        db.close()


def test_get_by_transaction_id():
    db = SessionLocal()

    try:
        transaction = create_transaction(db)
        assessment = build_assessment(transaction)

        saved = RiskPersistenceService.save(
            db=db,
            assessment=assessment,
        )

        result = RiskPersistenceService.get_by_transaction_id(
            db=db,
            transaction_id=transaction.id,
        )

        assert result is not None
        assert result.id == saved.id
        assert result.transaction_id == transaction.id
        assert result.risk_level == "CRITICAL"

    finally:
        db.close()


def test_save_returns_existing_risk_assessment():
    db = SessionLocal()

    try:
        transaction = create_transaction(db)
        assessment = build_assessment(transaction)

        first = RiskPersistenceService.save(
            db=db,
            assessment=assessment,
        )

        second = RiskPersistenceService.save(
            db=db,
            assessment=assessment,
        )

        assert second.id == first.id
        assert second.transaction_id == first.transaction_id

        count = (
            db.query(RiskScore)
            .filter(
                RiskScore.transaction_id == transaction.id
            )
            .count()
        )

        assert count == 1

    finally:
        db.close()


def test_save_rejects_missing_transaction():
    db = SessionLocal()

    try:
        assessment = RiskAssessment(
            transaction_id=uuid4(),
            transaction_reference="TXN-MISSING",
            model_name="isolation_forest",
            anomaly_score=0.75,
            is_anomaly=True,
            risk_score=80.00,
            risk_level="HIGH",
        )

        with pytest.raises(
            ValueError,
            match="Transaction not found",
        ):
            RiskPersistenceService.save(
                db=db,
                assessment=assessment,
            )

    finally:
        db.close()


def test_save_rejects_transaction_reference_mismatch():
    db = SessionLocal()

    try:
        transaction = create_transaction(db)

        assessment = RiskAssessment(
            transaction_id=transaction.id,
            transaction_reference="WRONG-REFERENCE",
            model_name="isolation_forest",
            anomaly_score=0.75,
            is_anomaly=True,
            risk_score=80.00,
            risk_level="HIGH",
        )

        with pytest.raises(
            ValueError,
            match="Transaction reference does not match transaction ID",
        ):
            RiskPersistenceService.save(
                db=db,
                assessment=assessment,
            )

    finally:
        db.close()


def test_get_by_transaction_id_returns_none_when_not_found():
    db = SessionLocal()

    try:
        result = RiskPersistenceService.get_by_transaction_id(
            db=db,
            transaction_id=uuid4(),
        )

        assert result is None

    finally:
        db.close()