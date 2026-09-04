from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.schemas.monitoring_schemas import MonitoringStatusResponse
from backend.app.services.monitoring_service import MonitoringService


router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"],
)


@router.get(
    "/status",
    response_model=MonitoringStatusResponse,
)
def get_monitoring_status(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> MonitoringStatusResponse:
    """
    Return authenticated backend component health status.
    """

    return MonitoringService.get_status(db=db)