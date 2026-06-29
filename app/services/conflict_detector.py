import logging
from app.models.context import CampaignAnalysisContext
from app.models.evidence import Conflict

logger = logging.getLogger(__name__)


class ConflictDetector:
    def detect(self, context: CampaignAnalysisContext) -> list[Conflict]:
        conflicts: list[Conflict] = []

        if context.campaign is None:
            logger.warning("ConflictDetector: no campaign in context")
            return conflicts

        conflicts.extend(self._detect_promise_landing_mismatch(context))
        conflicts.extend(self._detect_review_contradiction(context))
        conflicts.extend(self._detect_approved_strategy_conflict(context))
        conflicts.extend(self._detect_performance_expectation_conflict(context))

        logger.info("ConflictDetector: %d conflicts found", len(conflicts))
        return conflicts

    def _detect_promise_landing_mismatch(self, context: CampaignAnalysisContext) -> list[Conflict]:
        results: list[Conflict] = []
        campaign = context.campaign
        if campaign is None:
            return results

        for variant in campaign.creative_variants:
            headline_lower = variant.headline.lower()
            landing_lower = variant.landing_page_headline.lower()

            headline_words = set(self._tokenize(headline_lower))
            landing_words = set(self._tokenize(landing_lower))

            common = headline_words & landing_words
            if not common:
                results.append(Conflict(
                    category="promise_landing_mismatch",
                    severity="medium",
                    description=f"Creative variant {variant.variant}: headline and landing page headline share no common keywords",
                    evidence=f"Headline: '{variant.headline}' | Landing page headline: '{variant.landing_page_headline}'",
                    recommendation="Align landing page headline with ad promise to maintain message consistency",
                ))

        return results

    def _detect_review_contradiction(self, context: CampaignAnalysisContext) -> list[Conflict]:
        results: list[Conflict] = []
        campaign = context.campaign
        if campaign is None or not context.reviews:
            return results

        low_ratings = [r for r in context.reviews if r.rating <= 2]
        if not low_ratings:
            return results

        for variant in campaign.creative_variants:
            for review in low_ratings:
                review_lower = review.text.lower()
                headline_words = self._tokenize(variant.headline.lower())

                matches = [w for w in headline_words if len(w) > 3 and w in review_lower]
                if len(matches) >= 2:
                    results.append(Conflict(
                        category="review_contradiction",
                        severity="high",
                        description=f"Customer review contradicts promise in variant {variant.variant}",
                        evidence=f"Ad says: '{variant.headline}' | Review ({review.rating}/5): '{review.text}'",
                        recommendation="Review ad promise against actual customer experience",
                    ))
                    break

        return results

    def _detect_approved_strategy_conflict(self, context: CampaignAnalysisContext) -> list[Conflict]:
        results: list[Conflict] = []
        campaign = context.campaign
        if campaign is None or not context.approved_campaigns:
            return results

        successful = [a for a in context.approved_campaigns if a.outcome == "success"]
        if not successful:
            return results

        for variant in campaign.creative_variants:
            for approved in successful:
                learnings_lower = approved.learnings.lower()
                headline_lower = variant.headline.lower()

                if "dramatic" in learnings_lower or "bold" in learnings_lower:
                    if "reverse" in headline_lower or "guaranteed" in headline_lower or "proven" in headline_lower:
                        results.append(Conflict(
                            category="approved_strategy_conflict",
                            severity="high",
                            description=f"Current variant '{variant.variant}' contradicts learning from approved campaign '{approved.name}'",
                            evidence=f"Approved learning: '{approved.learnings}' | Current headline: '{variant.headline}'",
                            recommendation="Revisit approved campaign learnings before launching bold claims",
                        ))
                        break

        return results

    def _detect_performance_expectation_conflict(self, context: CampaignAnalysisContext) -> list[Conflict]:
        results: list[Conflict] = []
        if not context.metrics or not context.orders:
            return results

        for metric in context.metrics:
            matching_orders = [o for o in context.orders
                               if o.period == metric.period]
            if not matching_orders:
                continue

            total_attributed = sum(o.attributed_orders for o in matching_orders)
            if metric.conversions > 0 and total_attributed > 0:
                if abs(metric.conversions - total_attributed) / max(metric.conversions, total_attributed) > 0.2:
                    results.append(Conflict(
                        category="performance_data_mismatch",
                        severity="medium",
                        description=f"Performance metrics and order attribution differ by >20% for period {metric.period}",
                        evidence=f"Metrics conversions={metric.conversions}, Orders attributed={total_attributed}",
                        recommendation="Investigate conversion tracking discrepancy",
                    ))

        return results

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [w.strip(".,!?;:'\"()[]") for w in text.split()]
