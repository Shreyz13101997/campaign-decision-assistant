from app.models import (
    ApprovedCampaign, ApprovedCampaignMetrics, Campaign, CreativeVariant,
    Flight, Funnel, OrderMetrics, PerformanceMetric, Review,
)
from app.models.context import CampaignAnalysisContext, RetrievalMetadata
from app.services.conflict_detector import ConflictDetector


def _make_context(campaign: Campaign | None = None,
                  reviews: tuple[Review, ...] = (),
                  metrics: tuple[PerformanceMetric, ...] = (),
                  orders: tuple[OrderMetrics, ...] = (),
                  approved: tuple[ApprovedCampaign, ...] = (),
                  ) -> CampaignAnalysisContext:
    return CampaignAnalysisContext(
        campaign=campaign,
        product=None,
        reviews=reviews,
        metrics=metrics,
        orders=orders,
        approved_campaigns=approved,
        retrieval_metadata=RetrievalMetadata(),
    )


def test_no_conflicts_with_clean_data() -> None:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Energy Support",
        primary_text="Daily energy.",
        landing_page="lp_v1",
        landing_page_headline="Energy Support",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )
    detector = ConflictDetector()
    conflicts = detector.detect(_make_context(campaign=campaign))
    assert len(conflicts) == 0


def test_promise_landing_mismatch_detected() -> None:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Feel Amazing Energy",
        primary_text="Great product.",
        landing_page="lp_v1",
        landing_page_headline="Completely Different Topic",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )
    detector = ConflictDetector()
    conflicts = detector.detect(_make_context(campaign=campaign))
    matches = [c for c in conflicts if c.category == "promise_landing_mismatch"]
    assert len(matches) >= 1


def test_review_contradiction_detected() -> None:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Amazing Energy Boost",
        primary_text="Feel the difference.",
        landing_page="lp_v1",
        landing_page_headline="Energy Boost",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )
    review = Review(product_id="PRD-001", rating=1, date="2026-01-15",
                    text="No energy boost at all. Felt nothing.")
    detector = ConflictDetector()
    conflicts = detector.detect(_make_context(campaign=campaign, reviews=(review,)))
    matches = [c for c in conflicts if c.category == "review_contradiction"]
    assert len(matches) >= 1


def test_no_conflict_with_good_reviews() -> None:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Energy Support",
        primary_text="Great product.",
        landing_page="lp_v1",
        landing_page_headline="Energy Support",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )
    review = Review(product_id="PRD-001", rating=5, date="2026-01-15",
                    text="Amazing energy support! Highly recommend.")
    detector = ConflictDetector()
    conflicts = detector.detect(_make_context(campaign=campaign, reviews=(review,)))
    matches = [c for c in conflicts if c.category == "review_contradiction"]
    assert len(matches) == 0


def test_no_campaign_returns_empty() -> None:
    detector = ConflictDetector()
    assert detector.detect(_make_context()) == []
