from app.models import Campaign, CreativeVariant, Flight, PerformanceMetric, Review
from app.models.context import CampaignAnalysisContext, RetrievalMetadata
from app.models.evidence import Conflict, EvidenceItem, RuleViolation, UnknownFinding
from app.services.evidence_builder import EvidenceBuilder


def _make_context(metrics: tuple[PerformanceMetric, ...] = (),
                  reviews: tuple[Review, ...] = (),
                  ) -> CampaignAnalysisContext:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Energy", primary_text="Good.",
        landing_page="lp", landing_page_headline="Energy",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )
    return CampaignAnalysisContext(
        campaign=campaign,
        product=None,
        metrics=metrics,
        reviews=reviews,
        retrieval_metadata=RetrievalMetadata(),
    )


def test_bundle_creation() -> None:
    context = _make_context()
    builder = EvidenceBuilder()
    violation = RuleViolation(
        rule_id="CR-01", severity="violation",
        creative_variant="v1", campaign_id="CMP-001",
        reason="Disease claim detected.",
    )
    conflict = Conflict(
        category="promise_landing_mismatch", severity="medium",
        description="Headline differs from landing page.",
        evidence="Headline vs LP headline mismatch.",
    )
    unknown = UnknownFinding(
        description="No metrics found.",
        impact="Can't measure performance.",
        suggested_next_step="Add metrics.",
    )
    bundle = builder.build(context, [violation], [conflict], [unknown])
    assert len(bundle.findings) > 0
    assert len(bundle.violations) == 1
    assert len(bundle.conflicts) == 1
    assert len(bundle.unknowns) == 1
    assert len(bundle.summary_points) > 0
    assert len(bundle.sources_used) > 0


def test_metric_findings_built() -> None:
    metric = PerformanceMetric(
        campaign_id="CMP-001", period="v1",
        period_start="2026-01-01", period_end="2026-01-15",
        impressions=10000, clicks=500, ctr_pct=5.0,
        conversions=50, conversion_rate_pct=10.0, spend_inr=25000.0,
    )
    context = _make_context(metrics=(metric,))
    builder = EvidenceBuilder()
    bundle = builder.build(context, [], [], [])
    assert any("CTR=5.0%" in f.finding for f in bundle.findings)


def test_summary_points_generated() -> None:
    context = _make_context()
    builder = EvidenceBuilder()
    bundle = builder.build(context, [], [], [])
    assert any("Analyzing campaign" in s for s in bundle.summary_points)
