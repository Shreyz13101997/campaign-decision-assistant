from app.models import (
    ApprovedCampaign, ApprovedCampaignMetrics, Campaign, CreativeVariant,
    Flight, Funnel, OrderMetrics, Review,
)
from app.models.context import CampaignAnalysisContext, RetrievalMetadata
from app.services.unknown_detector import UnknownDetector


def _campaign() -> Campaign:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Energy", primary_text="Good.",
        landing_page="lp", landing_page_headline="Energy",
    )
    return Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )


def _make_context(campaign: Campaign | None = None,
                  reviews: tuple[Review, ...] = (),
                  orders: tuple[OrderMetrics, ...] = (),
                  metrics: tuple = (),
                  approved: tuple = (),
                  ) -> CampaignAnalysisContext:
    return CampaignAnalysisContext(
        campaign=campaign,
        product=None,
        reviews=reviews,
        orders=orders,
        metrics=metrics,
        approved_campaigns=approved,
        retrieval_metadata=RetrievalMetadata(),
    )


def test_no_unknowns_with_complete_data() -> None:
    campaign = _campaign()
    order = OrderMetrics(
        campaign_id="CMP-001", period="v1", attributed_orders=100,
        funnel=Funnel(sessions=1000, add_to_cart=200, checkout_started=150, purchased=100),
    )
    review = Review(product_id="PRD-001", rating=4, date="2026-01-15", text="Good.")
    detector = UnknownDetector()
    unknowns = detector.detect(
        _make_context(campaign=campaign, orders=(order,), reviews=(review,))
    )
    funnel_findings = [u for u in unknowns if "Funnel" in u.description]
    metrics_findings = [u for u in unknowns if "metrics" in u.description]
    reviews_findings = [u for u in unknowns if "reviews" in u.description]
    assert len(funnel_findings) == 0
    assert len(metrics_findings) >= 1
    assert len(reviews_findings) == 0


def test_missing_funnel_detected() -> None:
    order = OrderMetrics(campaign_id="CMP-001", period="v1", attributed_orders=100, funnel=None)
    detector = UnknownDetector()
    unknowns = detector.detect(_make_context(campaign=_campaign(), orders=(order,)))
    assert any("Funnel data missing" in u.description for u in unknowns)


def test_missing_metrics_detected() -> None:
    detector = UnknownDetector()
    unknowns = detector.detect(_make_context(campaign=_campaign()))
    assert any("No performance metrics" in u.description for u in unknowns)


def test_missing_reviews_detected() -> None:
    detector = UnknownDetector()
    unknowns = detector.detect(_make_context(campaign=_campaign()))
    assert any("No customer reviews" in u.description for u in unknowns)


def test_missing_study_citation_detected() -> None:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Clinically Proven Formula",
        primary_text="Scientifically proven to work.",
        landing_page="lp", landing_page_headline="Health",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )
    detector = UnknownDetector()
    unknowns = detector.detect(_make_context(campaign=campaign))
    assert any("study citation" in u.description.lower() for u in unknowns)


def test_no_campaign_returns_empty() -> None:
    detector = UnknownDetector()
    assert detector.detect(_make_context()) == []


def test_missing_approved_detected() -> None:
    detector = UnknownDetector()
    unknowns = detector.detect(_make_context(campaign=_campaign()))
    assert any("approved" in u.description.lower() or "prior" in u.description.lower()
               for u in unknowns)
