import logging

from app.models.context import CampaignAnalysisContext
from app.models.evidence import (
    Conflict,
    EvidenceBundle,
    EvidenceItem,
    RuleViolation,
    UnknownFinding,
)

logger = logging.getLogger(__name__)


class EvidenceBuilder:
    def build(self, context: CampaignAnalysisContext,
              violations: list[RuleViolation],
              conflicts: list[Conflict],
              unknowns: list[UnknownFinding]) -> EvidenceBundle:
        findings: list[EvidenceItem] = []
        summary_points: list[str] = []
        sources_used: set[str] = set()

        findings.extend(self._build_metric_findings(context))
        findings.extend(self._build_order_findings(context))
        findings.extend(self._build_review_findings(context))
        findings.extend(self._build_approved_findings(context))
        findings.extend(self._build_rule_violation_findings(violations))
        findings.extend(self._build_conflict_findings(conflicts))
        findings.extend(self._build_unknown_findings(unknowns))

        summary_points.extend(self._generate_summary_points(context, violations, conflicts, unknowns))

        for finding in findings:
            sources_used.add(finding.source)

        bundle = EvidenceBundle(
            findings=tuple(findings),
            violations=tuple(violations),
            conflicts=tuple(conflicts),
            unknowns=tuple(unknowns),
            summary_points=tuple(summary_points),
            sources_used=tuple(sorted(sources_used)),
        )

        logger.info("EvidenceBuilder: %d findings, %d summary points", len(findings), len(summary_points))
        return bundle

    def _build_metric_findings(self, context: CampaignAnalysisContext) -> list[EvidenceItem]:
        results: list[EvidenceItem] = []
        for m in context.metrics:
            results.append(EvidenceItem(
                source="performance_metrics",
                record_id=f"{m.campaign_id}/{m.period}",
                finding=f"CTR={m.ctr_pct}%, Conv={m.conversion_rate_pct}%, Spend=₹{m.spend_inr:,.0f}",
                severity="info",
                confidence="high",
                reference_path=f"campaign_id={m.campaign_id}, period={m.period}",
            ))
        return results

    def _build_order_findings(self, context: CampaignAnalysisContext) -> list[EvidenceItem]:
        results: list[EvidenceItem] = []
        for o in context.orders:
            funnel_info = ""
            if o.funnel is not None:
                funnel_info = f" (sessions={o.funnel.sessions}, atc={o.funnel.add_to_cart}, purchased={o.funnel.purchased})"
            results.append(EvidenceItem(
                source="ecommerce_orders",
                record_id=f"{o.campaign_id}/{o.period}",
                finding=f"Attributed orders={o.attributed_orders}{funnel_info}",
                severity="info",
                confidence="high",
                reference_path=f"campaign_id={o.campaign_id}, period={o.period}",
            ))
        return results

    def _build_review_findings(self, context: CampaignAnalysisContext) -> list[EvidenceItem]:
        results: list[EvidenceItem] = []
        for r in context.reviews:
            severity = "info"
            if r.rating <= 2:
                severity = "warning"
            elif r.rating >= 4:
                severity = "info"

            results.append(EvidenceItem(
                source="reviews",
                record_id=f"{r.product_id}/{r.date}",
                finding=f"Rating={r.rating}/5: \"{r.text[:80]}\"",
                severity=severity,
                confidence="high",
                reference_path=f"product_id={r.product_id}, date={r.date}",
            ))
        return results

    def _build_approved_findings(self, context: CampaignAnalysisContext) -> list[EvidenceItem]:
        results: list[EvidenceItem] = []
        for a in context.approved_campaigns:
            results.append(EvidenceItem(
                source="approved_campaigns",
                record_id=a.approved_id,
                finding=f"Outcome={a.outcome}, CTR={a.metrics.ctr_pct}%, Conv={a.metrics.conversion_rate_pct}% | {a.learnings[:100]}",
                severity="info",
                confidence="high",
                reference_path=f"product_id={a.product_id}",
            ))
        return results

    def _build_rule_violation_findings(self, violations: list[RuleViolation]) -> list[EvidenceItem]:
        results: list[EvidenceItem] = []
        for v in violations:
            results.append(EvidenceItem(
                source="rule_engine",
                record_id=v.rule_id,
                finding=f"[{v.severity}] {v.reason}" + (f" (matched: '{v.matched_text}')" if v.matched_text else ""),
                severity=v.severity,
                confidence="high",
                reference_path=f"campaign_id={v.campaign_id}, variant={v.creative_variant}",
            ))
        return results

    def _build_conflict_findings(self, conflicts: list[Conflict]) -> list[EvidenceItem]:
        results: list[EvidenceItem] = []
        for c in conflicts:
            results.append(EvidenceItem(
                source=f"conflict_{c.category}",
                record_id=c.category,
                finding=c.description[:120],
                severity=c.severity,
                confidence="medium",
            ))
        return results

    def _build_unknown_findings(self, unknowns: list[UnknownFinding]) -> list[EvidenceItem]:
        results: list[EvidenceItem] = []
        for u in unknowns:
            results.append(EvidenceItem(
                source="unknown_detector",
                record_id=u.description[:40],
                finding=u.description,
                severity="info",
                confidence="low",
            ))
        return results

    def _generate_summary_points(self, context: CampaignAnalysisContext,
                                  violations: list[RuleViolation],
                                  conflicts: list[Conflict],
                                  unknowns: list[UnknownFinding]) -> list[str]:
        points: list[str] = []

        if context.campaign:
            points.append(f"Analyzing campaign '{context.campaign.name}' ({context.campaign.campaign_id})")
            points.append(f"Channel: {context.campaign.channel}, Objective: {context.campaign.objective}")

        if context.product:
            points.append(f"Product: {context.product.name} (₹{context.product.price_inr})")
            points.append(f"Category: {context.product.category}")

        if context.metrics:
            ctrs = [m.ctr_pct for m in context.metrics]
            convs = [m.conversion_rate_pct for m in context.metrics]
            points.append(f"CTR range: {min(ctrs):.1f}%-{max(ctrs):.1f}%")
            points.append(f"Conversion rate range: {min(convs):.1f}%-{max(convs):.1f}%")

        if context.reviews:
            avg_rating = sum(r.rating for r in context.reviews) / len(context.reviews)
            points.append(f"Avg customer rating: {avg_rating:.1f}/5 ({len(context.reviews)} reviews)")

        if violations:
            violation_severities = {}
            for v in violations:
                violation_severities[v.severity] = violation_severities.get(v.severity, 0) + 1
            severity_strs = [f"{count} {sev}" for sev, count in violation_severities.items()]
            points.append(f"Rule violations: {', '.join(severity_strs)}")

        if conflicts:
            points.append(f"Conflicts detected: {len(conflicts)}")

        if unknowns:
            points.append(f"Unknowns identified: {len(unknowns)}")

        return points
