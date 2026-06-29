import json
import logging
import time
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.loaders.base_loader import BaseLoader
from app.models import Review
from app.utils.exceptions import (
    DataSourceNotFound,
    InvalidDataset,
    ValidationError,
)

logger = logging.getLogger(__name__)

REQUIRED_REVIEW_FIELDS = {"product_id", "rating", "date", "text"}


class ReviewsLoader(BaseLoader[Review]):
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or Path(settings.data_directory) / "reviews.json"
        self._reviews: list[Review] = []
        self._loaded = False

    def load(self) -> list[Review]:
        t0 = time.perf_counter()

        if not self.path.exists():
            raise DataSourceNotFound(str(self.path))

        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw: list[dict] = json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidDataset("reviews", f"Malformed JSON: {e}")

        if not isinstance(raw, list):
            raise InvalidDataset("reviews", "Expected a JSON array")

        result: list[Review] = []

        for i, item in enumerate(raw):
            missing = REQUIRED_REVIEW_FIELDS - item.keys()
            if missing:
                raise ValidationError("reviews", i, f"Missing fields: {missing}")

            if not isinstance(item["rating"], int) or not (1 <= item["rating"] <= 5):
                raise ValidationError("reviews", i, "rating must be an integer 1-5")

            review = Review(
                product_id=str(item["product_id"]),
                rating=int(item["rating"]),
                date=str(item["date"]),
                text=str(item["text"]),
            )
            result.append(review)

        self._reviews = result
        self._loaded = True

        elapsed = time.perf_counter() - t0
        logger.info("ReviewsLoader loaded %d records in %.3fs", len(result), elapsed)

        return result

    def reload(self) -> list[Review]:
        self._loaded = False
        return self.load()
