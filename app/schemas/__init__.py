from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    campaign_id: str
    question: str
    context: Optional[str] = None


class EvidenceItem(BaseModel):
    source: str
    detail: str


class AnalysisResponse(BaseModel):
    campaign_id: str
    summary: str
    evidence: list[EvidenceItem]
    unknowns: list[str]
    recommended_actions: list[str]
    status: str


class ApprovalRequest(BaseModel):
    run_id: int
    reviewer: str
    decision: str
    note: Optional[str] = None


class RunHistoryResponse(BaseModel):
    id: int
    campaign_id: str
    question: str
    status: str
    summary: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class ApprovalResponse(BaseModel):
    id: int
    run_id: int
    reviewer: str
    decision: str
    note: Optional[str]
    timestamp: datetime
