from app.models import Campaign, ClaimRule, CreativeVariant, Flight
from app.models.context import CampaignAnalysisContext, RetrievalMetadata
from app.models.evidence import RuleViolation
from app.services.rule_engine import RuleEngine


def _make_context(campaign: Campaign, rules: tuple[ClaimRule, ...] = (),
                  disclaimer: str | None = None) -> CampaignAnalysisContext:
    return CampaignAnalysisContext(
        campaign=campaign,
        product=None,
        claim_rules=rules,
        disclaimer_required_text=disclaimer,
        retrieval_metadata=RetrievalMetadata(),
    )


def test_no_violations_with_clean_copy() -> None:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Support Your Health",
        primary_text="Great product for wellness.",
        landing_page="lp_test", landing_page_headline="Health Support",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )
    engine = RuleEngine()
    violations = engine.evaluate(_make_context(campaign))
    assert len(violations) == 0


def test_disease_claim_detected() -> None:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Cure Your Illness",
        primary_text="This treats disease naturally.",
        landing_page="lp_test", landing_page_headline="Health",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )
    rule = ClaimRule(
        rule_id="CR-01", title="No disease claims",
        description="Copy must not claim to diagnose, treat, cure, or prevent disease.",
        trigger_terms=("cure", "treat", "prevent", "diagnose"),
        trigger_context=("disease", "illness", "condition"),
        severity="violation",
    )
    engine = RuleEngine()
    violations = engine.evaluate(_make_context(campaign, rules=(rule,)))
    assert len(violations) == 1
    assert violations[0].rule_id == "CR-01"
    assert violations[0].severity == "violation"


def test_aging_reversal_detected() -> None:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Reverse Biological Aging",
        primary_text="Turn back the clock naturally.",
        landing_page="lp_test", landing_page_headline="Health",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )
    rule = ClaimRule(
        rule_id="CR-02", title="No aging-reversal claims",
        description="Copy must not claim to reverse aging.",
        trigger_terms=("reverse aging", "reverse biological aging", "stop aging"),
        severity="violation",
    )
    engine = RuleEngine()
    violations = engine.evaluate(_make_context(campaign, rules=(rule,)))
    assert len(violations) == 1
    assert violations[0].rule_id == "CR-02"
    assert "reverse biological aging" in (violations[0].matched_text or "")


def test_proof_claim_needs_citation() -> None:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Clinically Proven",
        primary_text="Scientifically proven to work.",
        landing_page="lp_test", landing_page_headline="Health",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )
    rule = ClaimRule(
        rule_id="CR-03", title="Substantiation required",
        description="Proof claims need study citation.",
        trigger_terms=("clinically proven", "scientifically proven"),
        requires_field="study_citation",
        severity="violation_if_unsubstantiated",
    )
    engine = RuleEngine()
    violations = engine.evaluate(_make_context(campaign, rules=(rule,)))
    assert len(violations) == 1

def test_proof_claim_with_citation_passes() -> None:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Clinically Proven",
        primary_text="Works effectively.",
        landing_page="lp_test", landing_page_headline="Health",
        study_citation="Study 2025",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )
    rule = ClaimRule(
        rule_id="CR-03", title="Substantiation required",
        description="Proof claims need study citation.",
        trigger_terms=("clinically proven",),
        requires_field="study_citation",
        severity="violation_if_unsubstantiated",
    )
    engine = RuleEngine()
    violations = engine.evaluate(_make_context(campaign, rules=(rule,)))
    assert len(violations) == 0


def test_guarantee_detected() -> None:
    variant = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Guaranteed Results in 30 Days",
        primary_text="Money back guarantee.",
        landing_page="lp_test", landing_page_headline="Health",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[variant],
    )
    rule = ClaimRule(
        rule_id="CR-04", title="No guarantees",
        description="Must not guarantee outcomes.",
        trigger_terms=("guaranteed", "guarantee", "money back"),
        severity="violation",
    )
    engine = RuleEngine()
    violations = engine.evaluate(_make_context(campaign, rules=(rule,)))
    assert len(violations) >= 1


def test_multiple_variants_all_checked() -> None:
    v1 = CreativeVariant(
        variant="v1", period="2026-01",
        headline="Safe Headline",
        primary_text="Regular text.",
        landing_page="lp_test", landing_page_headline="Health",
    )
    v2 = CreativeVariant(
        variant="v2", period="2026-02",
        headline="Cure Disease Now",
        primary_text="Treat illness fast.",
        landing_page="lp_test", landing_page_headline="Health",
    )
    campaign = Campaign(
        campaign_id="CMP-001", name="Test", product_id="PRD-001",
        status="active", objective="conversions", channel="Meta",
        flight=Flight(start="2026-01-01", end="2026-01-31"),
        brief="Test", creative_variants=[v1, v2],
    )
    rule = ClaimRule(
        rule_id="CR-01", title="No disease claims",
        description="No disease claims.",
        trigger_terms=("cure", "treat"),
        trigger_context=("disease", "illness"),
        severity="violation",
    )
    engine = RuleEngine()
    violations = engine.evaluate(_make_context(campaign, rules=(rule,)))
    assert len(violations) == 1
    assert violations[0].creative_variant == "v2"


def test_no_campaign_returns_empty() -> None:
    context = CampaignAnalysisContext(
        campaign=None, product=None,
        retrieval_metadata=RetrievalMetadata(),
    )
    engine = RuleEngine()
    assert engine.evaluate(context) == []
