import logging

from app.models.evidence import (
    Conflict,
    EvidenceBundle,
    RecommendationDraft,
    RuleViolation,
    UnknownFinding,
)

logger = logging.getLogger(__name__)


class RecommendationPlanner:
    def plan(self, bundle: EvidenceBundle) -> RecommendationDraft:
        actions: list[str] = []
        summary_points: list[str] = []
        human_review = False
        priorities: list[int] = []

        actions.extend(self._actions_from_violations(bundle.violations))
        actions.extend(self._actions_from_conflicts(bundle.conflicts))
        actions.extend(self._actions_from_unknowns(bundle.unknowns))
        actions.extend(self._actions_from_findings(bundle))

        if any(v.severity == "violation" for v in bundle.violations):
            human_review = True

        if bundle.violations:
            priorities.append(1)
        if bundle.conflicts:
            priorities.append(2)
        if bundle.unknowns:
            priorities.append(3)

        if not actions:
            actions.append("No issues detected. Consider monitoring performance and iterating on creative.")
            summary_points.append("Campaign appears compliant with no critical issues identified.")
        else:
            summary_points.append(f"Found {len(bundle.violations)} rule violations, {len(bundle.conflicts)} conflicts, {len(bundle.unknowns)} unknowns.")
            summary_points.append(f"{len(actions)} recommended actions generated.")

        priority = self._resolve_priority(priorities)

        return RecommendationDraft(
            summary_points=tuple(summary_points),
            recommended_actions=tuple(actions),
            human_review_required=human_review,
            priority=priority,
        )

    def _actions_from_violations(self, violations: tuple[RuleViolation, ...]) -> list[str]:
        actions: list[str] = []
        seen_rules: set[str] = set()

        for v in violations:
            if v.rule_id in seen_rules:
                continue
            seen_rules.add(v.rule_id)

            if v.severity == "violation":
                if "disease" in v.rule_id.lower() or "disease" in v.reason.lower():
                    actions.append(f"[HIGH] Remove disease-related claim from variant {v.creative_variant}")
                elif "aging" in v.rule_id.lower():
                    actions.append(f"[HIGH] Remove aging-reversal language from variant {v.creative_variant}")
                elif v.rule_id == "CR-04" or "guarantee" in v.reason.lower():
                    actions.append(f"[HIGH] Remove guarantee/timeline language from variant {v.creative_variant}")
                else:
                    actions.append(f"[HIGH] Fix violation {v.rule_id} in variant {v.creative_variant}: {v.reason}")
            elif v.severity == "violation_if_unsubstantiated":
                actions.append(f"[MEDIUM] Add study citation to variant {v.creative_variant} to substantiate proof claim")
            elif v.severity == "review":
                actions.append(f"[LOW] Review variant {v.creative_variant} for compliance: {v.reason}")

        return actions

    def _actions_from_conflicts(self, conflicts: tuple[Conflict, ...]) -> list[str]:
        actions: list[str] = []
        seen_categories: set[str] = set()

        for c in conflicts:
            if c.category in seen_categories:
                continue
            seen_categories.add(c.category)

            if c.severity == "high":
                prefix = "[HIGH]"
            elif c.severity == "medium":
                prefix = "[MEDIUM]"
            else:
                prefix = "[LOW]"

            if c.recommendation:
                actions.append(f"{prefix} {c.recommendation}")

        return actions

    def _actions_from_unknowns(self, unknowns: tuple[UnknownFinding, ...]) -> list[str]:
        actions: list[str] = []
        seen_descriptions: set[str] = set()

        for u in unknowns:
            key = u.description[:50]
            if key in seen_descriptions:
                continue
            seen_descriptions.add(key)
            actions.append(f"[INFO] {u.suggested_next_step}")

        return actions

    def _actions_from_findings(self, bundle: EvidenceBundle) -> list[str]:
        return []

    def _resolve_priority(self, priorities: list[int]) -> str:
        if not priorities:
            return "low"
        if 1 in priorities:
            return "high"
        if 2 in priorities:
            return "medium"
        return "low"
