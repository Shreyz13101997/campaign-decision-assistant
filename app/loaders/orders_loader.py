import json
import logging
import time
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.loaders.base_loader import BaseLoader
from app.models import Funnel, OrderMetrics
from app.utils.exceptions import (
    DataSourceNotFound,
    InvalidDataset,
    ValidationError,
)

logger = logging.getLogger(__name__)

REQUIRED_ORDER_FIELDS = {"campaign_id", "period", "attributed_orders"}
REQUIRED_FUNNEL_FIELDS = {"sessions", "add_to_cart", "checkout_started", "purchased"}


class OrdersLoader(BaseLoader[OrderMetrics]):
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or Path(settings.data_directory) / "ecommerce_orders.json"
        self._orders: list[OrderMetrics] = []
        self._loaded = False

    def load(self) -> list[OrderMetrics]:
        t0 = time.perf_counter()

        if not self.path.exists():
            raise DataSourceNotFound(str(self.path))

        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw: list[dict] = json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidDataset("ecommerce_orders", f"Malformed JSON: {e}")

        if not isinstance(raw, list):
            raise InvalidDataset("ecommerce_orders", "Expected a JSON array")

        result: list[OrderMetrics] = []

        for i, item in enumerate(raw):
            missing = REQUIRED_ORDER_FIELDS - item.keys()
            if missing:
                raise ValidationError("ecommerce_orders", i, f"Missing fields: {missing}")

            funnel: Optional[Funnel] = None
            if item.get("funnel") is not None:
                funnel_raw = item["funnel"]
                f_missing = REQUIRED_FUNNEL_FIELDS - funnel_raw.keys()
                if f_missing:
                    raise ValidationError("ecommerce_orders", i, f"Funnel missing fields: {f_missing}")
                funnel = Funnel(
                    sessions=int(funnel_raw["sessions"]),
                    add_to_cart=int(funnel_raw["add_to_cart"]),
                    checkout_started=int(funnel_raw["checkout_started"]),
                    purchased=int(funnel_raw["purchased"]),
                )

            order = OrderMetrics(
                campaign_id=str(item["campaign_id"]),
                period=str(item["period"]),
                attributed_orders=int(item["attributed_orders"]),
                funnel=funnel,
            )
            result.append(order)

        self._orders = result
        self._loaded = True

        elapsed = time.perf_counter() - t0
        logger.info("OrdersLoader loaded %d records in %.3fs", len(result), elapsed)

        return result

    def reload(self) -> list[OrderMetrics]:
        self._loaded = False
        return self.load()
