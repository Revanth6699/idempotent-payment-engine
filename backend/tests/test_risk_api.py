from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.risk_schemas import RiskAssessment
from backend.app.services.risk_persistence_service import RiskPersistenceService


client = TestClient(app)


def test_get_transaction_risk_returns_persisted_assessment(monkeypatch):
    expected_transaction_id = uuid4()

    risk_assessment = RiskAssessment(
        transaction_id=expected_transaction_id,
        transaction_reference="TXN-RISK-001",
        model_name="isolation_forest",
        anomaly_score=0.42,
        is_anomaly=True,
        risk_score=73.15,
        risk_level="HIGH",
    )

    def mock_get_by_transaction_id(db, transaction_id):
        assert transaction_id == expected_transaction_id
        return risk_assessment

    monkeypatch.setattr(
        RiskPersistenceService,
        "get_by_transaction_id",
        mock_get_by_transaction_id,
    )

    response = client.get(
        f"/risk/transactions/{expected_transaction_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["transaction_id"] == str(expected_transaction_id)
    assert data["transaction_reference"] == "TXN-RISK-001"
    assert data["model_name"] == "isolation_forest"
    assert data["anomaly_score"] == 0.42
    assert data["is_anomaly"] is True
    assert data["risk_score"] == 73.15
    assert data["risk_level"] == "HIGH"


def test_get_transaction_risk_returns_404_when_not_found(monkeypatch):
    transaction_id = uuid4()

    def mock_get_by_transaction_id(db, transaction_id):
        return None

    monkeypatch.setattr(
        RiskPersistenceService,
        "get_by_transaction_id",
        mock_get_by_transaction_id,
    )

    response = client.get(
        f"/risk/transactions/{transaction_id}"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == (
        "Risk assessment not found for transaction"
    )


def test_get_transaction_risk_rejects_invalid_transaction_id():
    response = client.get(
        "/risk/transactions/not-a-valid-uuid"
    )

    assert response.status_code == 422