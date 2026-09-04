from unittest.mock import MagicMock, patch

from kafka.errors import KafkaError
from sqlalchemy.exc import SQLAlchemyError

from backend.app.schemas.monitoring_schemas import ComponentHealth
from backend.app.services.monitoring_service import MonitoringService


def test_check_database_returns_healthy() -> None:
    db = MagicMock()

    result = MonitoringService.check_database(db)

    assert result.status == "healthy"
    assert result.detail == "PostgreSQL connection is healthy"
    db.execute.assert_called_once()


def test_check_database_returns_unhealthy_when_database_fails() -> None:
    db = MagicMock()
    db.execute.side_effect = SQLAlchemyError("database unavailable")

    result = MonitoringService.check_database(db)

    assert result.status == "unhealthy"
    assert result.detail == "PostgreSQL connection is unavailable"


@patch("backend.app.services.monitoring_service.KafkaAdminClient")
def test_check_redpanda_returns_healthy(mock_admin_client) -> None:
    admin_client = MagicMock()
    mock_admin_client.return_value = admin_client
    admin_client.list_topics.return_value = ["payment-events"]

    result = MonitoringService.check_redpanda()

    assert result.status == "healthy"
    assert result.detail == "Redpanda connection is healthy"
    admin_client.list_topics.assert_called_once()
    admin_client.close.assert_called_once()


@patch("backend.app.services.monitoring_service.KafkaAdminClient")
def test_check_redpanda_returns_unhealthy_when_connection_fails(
    mock_admin_client,
) -> None:
    mock_admin_client.side_effect = KafkaError("Redpanda unavailable")

    result = MonitoringService.check_redpanda()

    assert result.status == "unhealthy"
    assert result.detail == "Redpanda connection is unavailable"


@patch.object(MonitoringService, "check_redpanda")
@patch.object(MonitoringService, "check_database")
def test_get_status_returns_healthy_when_all_components_are_healthy(
    mock_database,
    mock_redpanda,
) -> None:
    mock_database.return_value = ComponentHealth(
        status="healthy",
        detail="PostgreSQL connection is healthy",
    )
    mock_redpanda.return_value = ComponentHealth(
        status="healthy",
        detail="Redpanda connection is healthy",
    )

    result = MonitoringService.get_status(MagicMock())

    assert result.status == "healthy"
    assert result.service == "idempotent-payment-engine"


@patch.object(MonitoringService, "check_redpanda")
@patch.object(MonitoringService, "check_database")
def test_get_status_returns_degraded_when_component_is_unhealthy(
    mock_database,
    mock_redpanda,
) -> None:
    mock_database.return_value = ComponentHealth(
        status="healthy",
        detail="PostgreSQL connection is healthy",
    )
    mock_redpanda.return_value = ComponentHealth(
        status="unhealthy",
        detail="Redpanda connection is unavailable",
    )

    result = MonitoringService.get_status(MagicMock())

    assert result.status == "degraded"
    assert result.database.status == "healthy"
    assert result.redpanda.status == "unhealthy"