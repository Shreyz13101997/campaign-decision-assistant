from app.models.evidence import (
    AnalysisResult,
    Conflict,
    EvidenceBundle,
    EvidenceItem,
    ProcessingMetadata,
    RecommendationDraft,
    RuleViolation,
    UnknownFinding,
)
from app.services.response_validator import ResponseValidator


def test_valid_result_passes() -> None:
    bundle = EvidenceBundle(
        findings=(EvidenceItem(source="test", record_id="1", finding="OK", severity="info", confidence="high"),),
        violations=(RuleViolation(rule_id="CR-01", severity="violation",
                                  creative_variant="v1", campaign_id="CMP-001",
                                  reason="Disease claim"),),
        conflicts=(Conflict(category="test", severity="medium",
                            description="Conflict desc", evidence="Evidence ref"),),
        unknowns=(UnknownFinding(description="Unknown",
                                  impact="Impact", suggested_next_step="Fix"),),
    )
    result = AnalysisResult(
        campaign_id="CMP-001",
        evidence_bundle=bundle,
        recommendation=RecommendationDraft(
            summary_points=("Test point",),
            recommended_actions=("[HIGH] Fix violation",),
            human_review_required=True,
        ),
        processing_metadata=ProcessingMetadata(),
        status="completed",
    )
    validator = ResponseValidator()
    report = validator.validate(result)
    assert report.is_valid
    assert len(report.errors) == 0


def test_missing_campaign_id_fails() -> None:
    result = AnalysisResult(
        campaign_id="unknown",
        evidence_bundle=EvidenceBundle(),
        recommendation=RecommendationDraft(),
        status="completed",
    )
    validator = ResponseValidator()
    report = validator.validate(result)
    assert not report.is_valid
    assert any("campaign_id" in e for e in report.errors)


def test_missing_source_on_finding_fails() -> None:
    bundle = EvidenceBundle(
        findings=(EvidenceItem(source="", record_id="1", finding="test",
                                severity="info", confidence="high"),),
    )
    result = AnalysisResult(
        campaign_id="CMP-001",
        evidence_bundle=bundle,
        recommendation=RecommendationDraft(summary_points=("x",), recommended_actions=("[LOW] x",)),
        status="completed",
    )
    validator = ResponseValidator()
    report = validator.validate(result)
    assert not report.is_valid


def test_violations_should_flag_human_review() -> None:
    bundle = EvidenceBundle(
        violations=(RuleViolation(rule_id="CR-01", severity="violation",
                                  creative_variant="v1", campaign_id="CMP-001",
                                  reason="Disease claim"),),
    )
    result = AnalysisResult(
        campaign_id="CMP-001",
        evidence_bundle=bundle,
        recommendation=RecommendationDraft(
            summary_points=("x",), recommended_actions=("[HIGH] x",),
            human_review_required=False,
        ),
        status="completed",
    )
    validator = ResponseValidator()
    report = validator.validate(result)
    assert len(report.warnings) > 0
