from app.models.evidence import (
    Conflict,
    EvidenceBundle,
    EvidenceItem,
    RecommendationDraft,
    RuleViolation,
    UnknownFinding,
)
from app.services.recommendation_planner import RecommendationPlanner


def test_clean_data_generates_default() -> None:
    bundle = EvidenceBundle(
        findings=(EvidenceItem(source="test", record_id="1", finding="OK",
                                severity="info", confidence="high"),),
    )
    planner = RecommendationPlanner()
    result = planner.plan(bundle)
    assert isinstance(result, RecommendationDraft)
    assert len(result.recommended_actions) >= 1
    assert result.priority == "low"
    assert not result.human_review_required


def test_violation_triggers_high_priority() -> None:
    bundle = EvidenceBundle(
        violations=(RuleViolation(rule_id="CR-01", severity="violation",
                                  creative_variant="v1", campaign_id="CMP-001",
                                  reason="Disease claim detected"),),
    )
    planner = RecommendationPlanner()
    result = planner.plan(bundle)
    assert result.priority == "high"
    assert result.human_review_required


def test_violation_action_generated() -> None:
    bundle = EvidenceBundle(
        violations=(RuleViolation(rule_id="CR-01", severity="violation",
                                  creative_variant="v1", campaign_id="CMP-001",
                                  reason="Disease claim detected"),),
    )
    planner = RecommendationPlanner()
    result = planner.plan(bundle)
    actions = " ".join(result.recommended_actions).lower()
    assert "remove" in actions or "fix" in actions


def test_unknown_action_generated() -> None:
    bundle = EvidenceBundle(
        unknowns=(UnknownFinding(description="Missing metrics",
                                  impact="Can't measure",
                                  suggested_next_step="Add tracking"),),
    )
    planner = RecommendationPlanner()
    result = planner.plan(bundle)
    actions = " ".join(result.recommended_actions).lower()
    assert "tracking" in actions or "add" in actions
