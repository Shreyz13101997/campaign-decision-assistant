import logging
from typing import Optional

from app.loaders.approved_campaign_loader import ApprovedCampaignLoader
from app.loaders.campaign_loader import CampaignLoader
from app.loaders.claim_rule_loader import ClaimRuleLoader
from app.loaders.orders_loader import OrdersLoader
from app.loaders.performance_loader import PerformanceLoader
from app.loaders.product_loader import ProductLoader
from app.loaders.reviews_loader import ReviewsLoader
from app.models import (
    ApprovedCampaign,
    Campaign,
    ClaimRule,
    ClaimRulesDocument,
    OrderMetrics,
    PerformanceMetric,
    Product,
    Review,
)

logger = logging.getLogger(__name__)


class LoaderRegistry:
    def __init__(self) -> None:
        self._campaign_loader = CampaignLoader()
        self._product_loader = ProductLoader()
        self._reviews_loader = ReviewsLoader()
        self._performance_loader = PerformanceLoader()
        self._orders_loader = OrdersLoader()
        self._approved_loader = ApprovedCampaignLoader()
        self._claim_rule_loader = ClaimRuleLoader()

        self._campaigns: list[Campaign] = []
        self._products: list[Product] = []
        self._reviews: list[Review] = []
        self._metrics: list[PerformanceMetric] = []
        self._orders: list[OrderMetrics] = []
        self._approved: list[ApprovedCampaign] = []
        self._claim_doc: Optional[ClaimRulesDocument] = None

        self._loaded = False

    def load_all(self) -> None:
        logger.info("LoaderRegistry: loading all data sources")
        self._campaigns = self._campaign_loader.load()
        self._products = self._product_loader.load()
        self._reviews = self._reviews_loader.load()
        self._metrics = self._performance_loader.load()
        self._orders = self._orders_loader.load()
        self._approved = self._approved_loader.load()
        docs = self._claim_rule_loader.load()
        self._claim_doc = docs[0] if docs else None
        self._loaded = True
        logger.info("LoaderRegistry: all data sources loaded")

    def reload_all(self) -> None:
        self._loaded = False
        self.load_all()

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        self._ensure_loaded()
        for c in self._campaigns:
            if c.campaign_id == campaign_id:
                return c
        return None

    def get_campaigns_by_product(self, product_id: str) -> list[Campaign]:
        self._ensure_loaded()
        return [c for c in self._campaigns if c.product_id == product_id]

    def get_product(self, product_id: str) -> Optional[Product]:
        self._ensure_loaded()
        for p in self._products:
            if p.product_id == product_id:
                return p
        return None

    def get_all_products(self) -> list[Product]:
        self._ensure_loaded()
        return list(self._products)

    def get_reviews(self, product_id: str) -> list[Review]:
        self._ensure_loaded()
        return [r for r in self._reviews if r.product_id == product_id]

    def get_metrics(self, campaign_id: str) -> list[PerformanceMetric]:
        self._ensure_loaded()
        return [m for m in self._metrics if m.campaign_id == campaign_id]

    def get_orders(self, campaign_id: str) -> list[OrderMetrics]:
        self._ensure_loaded()
        return [o for o in self._orders if o.campaign_id == campaign_id]

    def get_approved_campaigns(self, product_id: str) -> list[ApprovedCampaign]:
        self._ensure_loaded()
        return [a for a in self._approved if a.product_id == product_id]

    def get_all_approved_campaigns(self) -> list[ApprovedCampaign]:
        self._ensure_loaded()
        return list(self._approved)

    def get_claim_rules(self) -> list[ClaimRule]:
        self._ensure_loaded()
        if self._claim_doc is None:
            return []
        return list(self._claim_doc.rules)

    def get_claim_rules_document(self) -> Optional[ClaimRulesDocument]:
        self._ensure_loaded()
        return self._claim_doc

    def get_all_campaigns(self) -> list[Campaign]:
        self._ensure_loaded()
        return list(self._campaigns)

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load_all()
