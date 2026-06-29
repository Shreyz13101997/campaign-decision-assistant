import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas import AnalysisRequest, AnalysisResponse, ApprovalRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest, db: Session = Depends(get_db)) -> AnalysisResponse:
    logger.info("Analysis requested", extra={"campaign_id": request.campaign_id})
    return AnalysisResponse(
        campaign_id=request.campaign_id,
        summary="Analysis pending — not yet implemented.",
        evidence=[],
        unknowns=[],
        recommended_actions=[],
        status="pending",
    )


@router.get("/history")
async def get_history(db: Session = Depends(get_db)) -> dict:
    logger.info("History requested")
    return {"history": [], "message": "History retrieval not yet implemented."}


@router.post("/approve")
async def approve(request: ApprovalRequest, db: Session = Depends(get_db)) -> dict:
    logger.info("Approval requested", extra={"run_id": request.run_id})
    return {"status": "approved", "run_id": request.run_id, "message": "Approval not yet implemented."}


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy"}
