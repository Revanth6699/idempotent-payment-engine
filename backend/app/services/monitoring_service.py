from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from kafka import KafkaAdminClient
from kafka.errors import KafkaError

from backend.app.schemas.monitoring_schemas import (
    ComponentHealth,
    MonitoringStatusResponse,
)


class MonitoringService:
    SERVICE_NAME = "idempotent-payment-engine"
    REDPANDA_BOOTSTRAP_SERVERS = "localhost:19092"

    @staticmethod
    def check_database(db: Session) -> ComponentHealth:
        try:
            db.execute(text("SELECT 1"))

            return ComponentHealth(
                status="healthy",
                detail="PostgreSQL connection is healthy",
            )

        except SQLAlchemyError:
            return ComponentHealth(
                status="unhealthy",
                detail="PostgreSQL connection is unavailable",
            )

    @classmethod
    def check_redpanda(cls) -> ComponentHealth:
        admin_client = None

        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=cls.REDPANDA_BOOTSTRAP_SERVERS,
                request_timeout_ms=2000,
            )

            admin_client.list_topics()

            return ComponentHealth(
                status="healthy",
                detail="Redpanda connection is healthy",
            )

        except (KafkaError, OSError):
            return ComponentHealth(
                status="unhealthy",
                detail="Redpanda connection is unavailable",
            )

        finally:
            if admin_client is not None:
                admin_client.close()

    @classmethod
    def get_status(cls, db: Session) -> MonitoringStatusResponse:
        database = cls.check_database(db)
        redpanda = cls.check_redpanda()

        overall_status = (
            "healthy"
            if database.status == "healthy"
            and redpanda.status == "healthy"
            else "degraded"
        )

        return MonitoringStatusResponse(
            status=overall_status,
            service=cls.SERVICE_NAME,
            database=database,
            redpanda=redpanda,
        )