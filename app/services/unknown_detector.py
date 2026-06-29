import logging

from app.models import CreativeVariant
from app.models.context import CampaignAnalysisContext
from app.models.evidence import UnknownFinding

logger = logging.getLogger(__name__)


class UnknownDetector:
    def detect(self, context: CampaignAnalysisContext) -> list[UnknownFinding]:
        findings: list[UnknownFinding] = []

        if context.campaign is None:
            logger.warning("UnknownDetector: no campaign in context")
            return findings

        findings.extend(self._check_missing_funnel(context))
        findings.extend(self._check_missing_metrics(context))
        findings.extend(self._check_missing_product(context))
        findings.extend(self._check_missing_reviews(context))
        findings.extend(self._check_missing_study_citation(context))
        findings.extend(self._check_missing_approval_history(context))

        logger.info("UnknownDetector: %d unknown findings", len(findings))
        return findings

    def _check_missing_funnel(self, context: CampaignAnalysisContext) -> list[UnknownFinding]:
        results: list[UnknownFinding] = []
        for order in context.orders:
            if order.funnel is None:
                results.append(UnknownFinding(
                    description=f"Funnel data missing for campaign period {order.period}",
                    impact="Cannot diagnose where drop-offs occur in the conversion funnel",
                    suggested_next_step="Implement checkout event tracking and attribute funnel stages",
                ))
        if not context.orders:
            results.append(UnknownFinding(
                description="No order data available",
                impact="Cannot measure conversion performance or ROI",
                suggested_next_step="Connect order attribution system to campaign tracking",
            ))
        return results

    def _check_missing_metrics(self, context: CampaignAnalysisContext) -> list[UnknownFinding]:
        results: list[UnknownFinding] = []
        if not context.metrics:
            results.append(UnknownFinding(
                description="No performance metrics available",
                impact="Cannot evaluate campaign effectiveness or ROAS",
                suggested_next_step="Ensure ad platform metrics are exported and linked to campaign IDs",
            ))
        return results

    def _check_missing_product(self, context: CampaignAnalysisContext) -> list[UnknownFinding]:
        results: list[UnknownFinding] = []
        if context.product is None:
            results.append(UnknownFinding(
                description="Product information not found",
                impact="Cannot verify product details, pricing, or availability",
                suggested_next_step="Verify product ID mapping between campaigns and product catalog",
            ))
        return results

    def _check_missing_reviews(self, context: CampaignAnalysisContext) -> list[UnknownFinding]:
        results: list[UnknownFinding] = []
        if not context.reviews:
            results.append(UnknownFinding(
                description="No customer reviews available for this product",
                impact="Cannot assess customer sentiment or identify promise-reality gaps",
                suggested_next_step="Integrate product review feed or add review collection mechanism",
            ))
        return results

    def _check_missing_study_citation(self, context: CampaignAnalysisContext) -> list[UnknownFinding]:
        results: list[UnknownFinding] = []
        campaign = context.campaign
        if campaign is None:
            return results

        for variant in campaign.creative_variants:
            if variant.study_citation is None and self._has_proof_claim(variant):
                results.append(UnknownFinding(
                    description=f"Study citation missing for variant {variant.variant} with proof claim",
                    impact="'Clinically proven' or similar claims lack scientific substantiation",
                    suggested_next_step="Either add study citation to the creative or soften the claim language",
                ))

        return results

    def _check_missing_approval_history(self, context: CampaignAnalysisContext) -> list[UnknownFinding]:
        results: list[UnknownFinding] = []
        campaign = context.campaign
        if campaign is None:
            return results

        approved = [a for a in context.approved_campaigns if a.product_id == campaign.product_id]
        if not approved:
            results.append(UnknownFinding(
                description="No prior approved campaigns found for this product",
                impact="Cannot reference past learnings or avoid previously identified pitfalls",
                suggested_next_step="Document and archive approved campaigns for future reference",
            ))
        return results

    @staticmethod
    def _has_proof_claim(variant: CreativeVariant) -> bool:
        text = f"{variant.headline} {variant.primary_text}".lower()
        proof_terms = {"clinically proven", "scientifically proven", "proven to"}
        return any(term in text for term in proof_terms)
