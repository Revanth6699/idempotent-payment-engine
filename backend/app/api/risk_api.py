from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.risk_schemas import RiskAssessmentResponse
from backend.app.services.risk_persistence_service import (
    RiskPersistenceService,
)


router = APIRouter(
    prefix="/risk",
    tags=["Risk"],
)


@router.get(
    "/transactions/{transaction_id}",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_200_OK,
)
def get_transaction_risk(
    transaction_id: UUID,
    db: Session = Depends(get_db),
) -> RiskAssessmentResponse:
    """
    Return the persisted risk assessment for a transaction.
    """

    risk_assessment = RiskPersistenceService.get_by_transaction_id(
        db=db,
        transaction_id=transaction_id,
    )

    if risk_assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk assessment not found for transaction",
        )

    return risk_assessment