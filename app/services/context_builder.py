import logging
import time
from typing import Optional

from app.loaders.registry import LoaderRegistry
from app.models.context import CampaignAnalysisContext, RetrievalMetadata

logger = logging.getLogger(__name__)


class ContextBuilder:
    def __init__(self, registry: LoaderRegistry) -> None:
        self._registry = registry

    def build(self, campaign_id: str) -> CampaignAnalysisContext:
        t0 = time.perf_counter()
        warnings: list[str] = []
        sources_used: list[str] = []
        missing_sources: list[str] = []
        failed_sources: list[str] = []

        campaign = self._registry.get_campaign(campaign_id)
        if campaign is not None:
            sources_used.append("campaigns")
        else:
            missing_sources.append("campaigns")

        product = None
        if campaign is not None:
            product = self._registry.get_product(campaign.product_id)
            if product is not None:
                sources_used.append("products")
            else:
                missing_sources.append("products")

        metrics = list(self._registry.get_metrics(campaign_id))
        if metrics:
            sources_used.append("performance_metrics")
        else:
            missing_sources.append("performance_metrics")

        orders = list(self._registry.get_orders(campaign_id))
        if orders:
            sources_used.append("ecommerce_orders")
        else:
            missing_sources.append("ecommerce_orders")

        product_id = campaign.product_id if campaign else None
        reviews = list(self._registry.get_reviews(product_id)) if product_id else []
        if reviews:
            sources_used.append("reviews")
        else:
            missing_sources.append("reviews")

        approved = list(self._registry.get_approved_campaigns(product_id)) if product_id else []
        if approved:
            sources_used.append("approved_campaigns")
        else:
            missing_sources.append("approved_campaigns")

        claim_rules = list(self._registry.get_claim_rules())
        disclaimer_doc = self._registry.get_claim_rules_document()
        disclaimer_required_text = disclaimer_doc.disclaimer_required_text if disclaimer_doc else None
        if claim_rules:
            sources_used.append("claim_rules")
        else:
            missing_sources.append("claim_rules")

        duration = (time.perf_counter() - t0) * 1000

        metadata = RetrievalMetadata(
            sources_used=tuple(sources_used),
            missing_sources=tuple(missing_sources),
            failed_sources=tuple(failed_sources),
            retrieval_duration_ms=round(duration, 2),
            warnings=tuple(warnings),
        )

        return CampaignAnalysisContext(
            campaign=campaign,
            product=product,
            metrics=tuple(metrics),
            orders=tuple(orders),
            reviews=tuple(reviews),
            approved_campaigns=tuple(approved),
            claim_rules=tuple(claim_rules),
            disclaimer_required_text=disclaimer_required_text,
            retrieval_metadata=metadata,
        )
