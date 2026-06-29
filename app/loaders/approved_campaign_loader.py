import json
import logging
import time
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.loaders.base_loader import BaseLoader
from app.models import ApprovedCampaign, ApprovedCampaignMetrics
from app.utils.exceptions import (
    DataSourceNotFound,
    DuplicateRecord,
    InvalidDataset,
    ValidationError,
)

logger = logging.getLogger(__name__)

REQUIRED_APPROVED_FIELDS = {"approved_id", "name", "product_id", "outcome", "metrics", "learnings", "approved_by",
                            "approved_at"}
REQUIRED_METRICS_FIELDS = {"ctr_pct", "conversion_rate_pct"}


class ApprovedCampaignLoader(BaseLoader[ApprovedCampaign]):
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or Path(settings.data_directory) / "approved_campaigns.json"
        self._approved: list[ApprovedCampaign] = []
        self._loaded = False

    def load(self) -> list[ApprovedCampaign]:
        t0 = time.perf_counter()

        if not self.path.exists():
            raise DataSourceNotFound(str(self.path))

        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw: list[dict] = json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidDataset("approved_campaigns", f"Malformed JSON: {e}")

        if not isinstance(raw, list):
            raise InvalidDataset("approved_campaigns", "Expected a JSON array")

        seen: set[str] = set()
        result: list[ApprovedCampaign] = []

        for i, item in enumerate(raw):
            missing = REQUIRED_APPROVED_FIELDS - item.keys()
            if missing:
                raise ValidationError("approved_campaigns", i, f"Missing fields: {missing}")

            aid: str = item["approved_id"]
            if aid in seen:
                raise DuplicateRecord("approved_campaigns", aid)
            seen.add(aid)

            metrics_raw = item["metrics"]
            m_missing = REQUIRED_METRICS_FIELDS - metrics_raw.keys()
            if m_missing:
                raise ValidationError("approved_campaigns", i, f"Metrics missing fields: {m_missing}")

            try:
                approved = ApprovedCampaign(
                    approved_id=aid,
                    name=str(item["name"]),
                    product_id=str(item["product_id"]),
                    outcome=str(item["outcome"]),
                    metrics=ApprovedCampaignMetrics(
                        ctr_pct=float(metrics_raw["ctr_pct"]),
                        conversion_rate_pct=float(metrics_raw["conversion_rate_pct"]),
                    ),
                    learnings=str(item["learnings"]),
                    approved_by=str(item["approved_by"]),
                    approved_at=str(item["approved_at"]),
                )
            except (ValueError, TypeError) as e:
                raise ValidationError("approved_campaigns", i, str(e))
            result.append(approved)

        self._approved = result
        self._loaded = True

        elapsed = time.perf_counter() - t0
        logger.info("ApprovedCampaignLoader loaded %d records in %.3fs", len(result), elapsed)

        return result

    def reload(self) -> list[ApprovedCampaign]:
        self._loaded = False
        return self.load()
