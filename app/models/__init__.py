from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Flight:
    start: str
    end: Optional[str]


@dataclass(frozen=True)
class CreativeVariant:
    variant: str
    period: str
    headline: str
    primary_text: str
    landing_page: str
    landing_page_headline: str
    study_citation: Optional[str] = None


@dataclass(frozen=True)
class Campaign:
    campaign_id: str
    name: str
    product_id: str
    status: str
    objective: str
    channel: str
    flight: Flight
    brief: str
    creative_variants: list[CreativeVariant] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    category: str
    price_inr: int
    in_stock: bool
    price_last_changed: str
    description: str


@dataclass(frozen=True)
class Review:
    product_id: str
    rating: int
    date: str
    text: str


@dataclass(frozen=True)
class PerformanceMetric:
    campaign_id: str
    period: str
    period_start: str
    period_end: str
    impressions: int
    clicks: int
    ctr_pct: float
    conversions: int
    conversion_rate_pct: float
    spend_inr: float


@dataclass(frozen=True)
class Funnel:
    sessions: int
    add_to_cart: int
    checkout_started: int
    purchased: int


@dataclass(frozen=True)
class OrderMetrics:
    campaign_id: str
    period: str
    attributed_orders: int
    funnel: Optional[Funnel] = None


@dataclass(frozen=True)
class ApprovedCampaignMetrics:
    ctr_pct: float
    conversion_rate_pct: float


@dataclass(frozen=True)
class ApprovedCampaign:
    approved_id: str
    name: str
    product_id: str
    outcome: str
    metrics: ApprovedCampaignMetrics
    learnings: str
    approved_by: str
    approved_at: str


@dataclass(frozen=True)
class ClaimRule:
    rule_id: str
    title: str
    description: str
    trigger_terms: tuple[str, ...]
    severity: str
    trigger_context: Optional[tuple[str, ...]] = None
    requires_field: Optional[str] = None
    applies_when: Optional[str] = None
    requires: Optional[str] = None


@dataclass(frozen=True)
class ClaimRulesDocument:
    version: str
    disclaimer_required_text: str
    notes: str
    rules: tuple[ClaimRule, ...]
