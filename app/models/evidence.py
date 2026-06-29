from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class RuleViolation:
    rule_id: str
    severity: str
    creative_variant: str
    campaign_id: str
    reason: str
    matched_text: Optional[str] = None


@dataclass(frozen=True)
class Conflict:
    category: str
    severity: str
    description: str
    evidence: str
    recommendation: Optional[str] = None


@dataclass(frozen=True)
class UnknownFinding:
    description: str
    impact: str
    suggested_next_step: str


@dataclass(frozen=True)
class EvidenceItem:
    source: str
    record_id: str
    finding: str
    severity: str
    confidence: str
    reference_path: Optional[str] = None


@dataclass(frozen=True)
class EvidenceBundle:
    findings: tuple[EvidenceItem, ...] = ()
    violations: tuple[RuleViolation, ...] = ()
    conflicts: tuple[Conflict, ...] = ()
    unknowns: tuple[UnknownFinding, ...] = ()
    summary_points: tuple[str, ...] = ()
    sources_used: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecommendationDraft:
    summary_points: tuple[str, ...] = ()
    recommended_actions: tuple[str, ...] = ()
    human_review_required: bool = False
    priority: str = "medium"


@dataclass(frozen=True)
class ProcessingMetadata:
    rule_engine_ms: float = 0.0
    conflict_detector_ms: float = 0.0
    unknown_detector_ms: float = 0.0
    evidence_builder_ms: float = 0.0
    recommendation_planner_ms: float = 0.0
    validator_ms: float = 0.0


@dataclass(frozen=True)
class AnalysisResult:
    campaign_id: str
    summary_points: tuple[str, ...] = ()
    evidence_bundle: EvidenceBundle = field(default_factory=EvidenceBundle)
    recommendation: RecommendationDraft = field(default_factory=RecommendationDraft)
    processing_metadata: ProcessingMetadata = field(default_factory=ProcessingMetadata)
    status: str = "pending"
