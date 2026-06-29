import logging

from app.models.evidence import AnalysisResult

logger = logging.getLogger(__name__)


class ValidationReport:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def merge(self, other: "ValidationReport") -> "ValidationReport":
        merged = ValidationReport()
        merged.errors = self.errors + other.errors
        merged.warnings = self.warnings + other.warnings
        return merged


class ResponseValidator:
    def validate(self, result: AnalysisResult) -> ValidationReport:
        report = ValidationReport()

        self._validate_campaign_id(result, report)
        self._validate_evidence(result, report)
        self._validate_recommendations(result, report)
        self._validate_unknowns(result, report)
        self._validate_human_review_flag(result, report)

        if report.is_valid:
            logger.info("ResponseValidator: validation passed")
        else:
            logger.warning("ResponseValidator: %d errors, %d warnings",
                           len(report.errors), len(report.warnings))

        return report

    def _validate_campaign_id(self, result: AnalysisResult, report: ValidationReport) -> None:
        if not result.campaign_id or result.campaign_id == "unknown":
            report.errors.append("campaign_id must be present and not 'unknown'")

    def _validate_evidence(self, result: AnalysisResult, report: ValidationReport) -> None:
        bundle = result.evidence_bundle

        for finding in bundle.findings:
            if not finding.source:
                report.errors.append(f"EvidenceItem missing source: {finding.finding[:50]}")
            if not finding.finding:
                report.errors.append(f"EvidenceItem missing finding text: {finding.source}")

        for violation in bundle.violations:
            if not violation.rule_id:
                report.errors.append("RuleViolation missing rule_id")
            if not violation.reason:
                report.errors.append(f"RuleViolation {violation.rule_id} missing reason")

        for conflict in bundle.conflicts:
            if not conflict.description:
                report.errors.append("Conflict missing description")
            if not conflict.evidence:
                report.errors.append(f"Conflict '{conflict.description[:40]}' missing evidence reference")

    def _validate_recommendations(self, result: AnalysisResult, report: ValidationReport) -> None:
        rec = result.recommendation

        if not rec.recommended_actions:
            report.warnings.append("No recommended actions generated")
        if not rec.summary_points:
            report.warnings.append("No summary points generated")

        for action in rec.recommended_actions:
            if len(action) < 5:
                report.errors.append(f"Recommendation too short: '{action}'")

    def _validate_unknowns(self, result: AnalysisResult, report: ValidationReport) -> None:
        for unknown in result.evidence_bundle.unknowns:
            if not unknown.description:
                report.errors.append("UnknownFinding missing description")
            if not unknown.suggested_next_step:
                report.warnings.append(f"UnknownFinding '{unknown.description[:40]}' missing next step")

    def _validate_human_review_flag(self, result: AnalysisResult, report: ValidationReport) -> None:
        bundle = result.evidence_bundle

        has_violations = len(bundle.violations) > 0
        needs_review = result.recommendation.human_review_required

        if has_violations and not needs_review:
            report.warnings.append("human_review_required should be True when violations exist")
