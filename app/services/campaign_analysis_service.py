import logging
import time

from app.loaders.registry import LoaderRegistry
from app.models.evidence import AnalysisResult, ProcessingMetadata
from app.services.conflict_detector import ConflictDetector
from app.services.context_builder import ContextBuilder
from app.services.evidence_builder import EvidenceBuilder
from app.services.recommendation_planner import RecommendationPlanner
from app.services.response_validator import ResponseValidator
from app.services.rule_engine import RuleEngine
from app.services.unknown_detector import UnknownDetector

logger = logging.getLogger(__name__)


class CampaignAnalysisService:
    def __init__(self, registry: LoaderRegistry) -> None:
        self._context_builder = ContextBuilder(registry)
        self._rule_engine = RuleEngine()
        self._conflict_detector = ConflictDetector()
        self._unknown_detector = UnknownDetector()
        self._evidence_builder = EvidenceBuilder()
        self._recommendation_planner = RecommendationPlanner()
        self._validator = ResponseValidator()

    def analyze(self, campaign_id: str) -> AnalysisResult:
        logger.info("CampaignAnalysisService: starting analysis for %s", campaign_id)

        context = self._context_builder.build(campaign_id)
        if context.campaign is None:
            return AnalysisResult(
                campaign_id=campaign_id,
                status="failed",
                summary_points=(f"Campaign '{campaign_id}' not found in data sources.",),
            )

        t0 = time.perf_counter()
        violations = self._rule_engine.evaluate(context)
        rule_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        conflicts = self._conflict_detector.detect(context)
        conflict_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        unknowns = self._unknown_detector.detect(context)
        unknown_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        evidence = self._evidence_builder.build(context, violations, conflicts, unknowns)
        evidence_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        recommendation = self._recommendation_planner.plan(evidence)
        plan_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        result = AnalysisResult(
            campaign_id=campaign_id,
            summary_points=evidence.summary_points,
            evidence_bundle=evidence,
            recommendation=recommendation,
            processing_metadata=ProcessingMetadata(
                rule_engine_ms=round(rule_ms, 2),
                conflict_detector_ms=round(conflict_ms, 2),
                unknown_detector_ms=round(unknown_ms, 2),
                evidence_builder_ms=round(evidence_ms, 2),
                recommendation_planner_ms=round(plan_ms, 2),
            ),
            status="completed",
        )
        validator_ms = (time.perf_counter() - t0) * 1000

        result = AnalysisResult(
            campaign_id=campaign_id,
            summary_points=evidence.summary_points,
            evidence_bundle=evidence,
            recommendation=recommendation,
            processing_metadata=ProcessingMetadata(
                rule_engine_ms=round(rule_ms, 2),
                conflict_detector_ms=round(conflict_ms, 2),
                unknown_detector_ms=round(unknown_ms, 2),
                evidence_builder_ms=round(evidence_ms, 2),
                recommendation_planner_ms=round(plan_ms, 2),
                validator_ms=round(validator_ms, 2),
            ),
            status="completed",
        )

        report = self._validator.validate(result)
        if not report.is_valid:
            logger.warning("Validation errors: %s", report.errors)
            result = AnalysisResult(
                campaign_id=campaign_id,
                summary_points=evidence.summary_points,
                evidence_bundle=evidence,
                recommendation=recommendation,
                processing_metadata=result.processing_metadata,
                status="completed_with_warnings",
            )

        logger.info("CampaignAnalysisService: analysis complete for %s", campaign_id)
        return result
