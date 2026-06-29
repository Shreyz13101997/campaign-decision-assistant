from dataclasses import dataclass, field
from typing import Optional

from app.models import (
    ApprovedCampaign,
    Campaign,
    ClaimRule,
    OrderMetrics,
    PerformanceMetric,
    Product,
    Review,
)


@dataclass(frozen=True)
class RetrievalMetadata:
    sources_used: tuple[str, ...] = ()
    missing_sources: tuple[str, ...] = ()
    failed_sources: tuple[str, ...] = ()
    retrieval_duration_ms: float = 0.0
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class CampaignAnalysisContext:
    campaign: Optional[Campaign]
    product: Optional[Product]
    metrics: tuple[PerformanceMetric, ...] = ()
    orders: tuple[OrderMetrics, ...] = ()
    reviews: tuple[Review, ...] = ()
    approved_campaigns: tuple[ApprovedCampaign, ...] = ()
    claim_rules: tuple[ClaimRule, ...] = ()
    disclaimer_required_text: Optional[str] = None
    retrieval_metadata: RetrievalMetadata = field(default_factory=RetrievalMetadata)

    @property
    def campaign_id(self) -> str:
        if self.campaign is None:
            return "unknown"
        return self.campaign.campaign_id

    @property
    def product_id(self) -> str:
        if self.product is None:
            return "unknown"
        return self.product.product_id

    def missing_sources(self) -> tuple[str, ...]:
        missing: list[str] = []
        if self.campaign is None:
            missing.append("campaign")
        if self.product is None:
            missing.append("product")
        if not self.metrics:
            missing.append("metrics")
        if not self.orders:
            missing.append("orders")
        if not self.reviews:
            missing.append("reviews")
        if not self.approved_campaigns:
            missing.append("approved_campaigns")
        if not self.claim_rules:
            missing.append("claim_rules")
        return tuple(missing)

    def is_complete(self) -> bool:
        return len(self.missing_sources()) == 0

    def validate(self) -> None:
        if self.campaign is None:
            raise ValueError("CampaignAnalysisContext must have a campaign")
