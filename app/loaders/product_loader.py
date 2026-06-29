import json
import logging
import time
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.loaders.base_loader import BaseLoader
from app.models import Product
from app.utils.exceptions import (
    DataSourceNotFound,
    DuplicateRecord,
    InvalidDataset,
    ValidationError,
)

logger = logging.getLogger(__name__)

REQUIRED_PRODUCT_FIELDS = {"product_id", "name", "category", "price_inr", "in_stock", "price_last_changed", "description"}


class ProductLoader(BaseLoader[Product]):
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or Path(settings.data_directory) / "products.json"
        self._products: list[Product] = []
        self._loaded = False

    def load(self) -> list[Product]:
        t0 = time.perf_counter()

        if not self.path.exists():
            raise DataSourceNotFound(str(self.path))

        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw: list[dict] = json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidDataset("products", f"Malformed JSON: {e}")

        if not isinstance(raw, list):
            raise InvalidDataset("products", "Expected a JSON array")

        seen: set[str] = set()
        result: list[Product] = []

        for i, item in enumerate(raw):
            missing = REQUIRED_PRODUCT_FIELDS - item.keys()
            if missing:
                raise ValidationError("products", i, f"Missing fields: {missing}")

            pid: str = item["product_id"]
            if pid in seen:
                raise DuplicateRecord("products", pid)
            seen.add(pid)

            if not isinstance(item["price_inr"], (int, float)):
                raise ValidationError("products", i, "price_inr must be numeric")
            if not isinstance(item["in_stock"], bool):
                raise ValidationError("products", i, "in_stock must be a boolean")

            product = Product(
                product_id=pid,
                name=str(item["name"]),
                category=str(item["category"]),
                price_inr=int(item["price_inr"]),
                in_stock=bool(item["in_stock"]),
                price_last_changed=str(item["price_last_changed"]),
                description=str(item["description"]),
            )
            result.append(product)

        self._products = result
        self._loaded = True

        elapsed = time.perf_counter() - t0
        logger.info("ProductLoader loaded %d records in %.3fs", len(result), elapsed)

        return result

    def reload(self) -> list[Product]:
        self._loaded = False
        return self.load()
