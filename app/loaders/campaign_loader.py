import json
import logging
import time
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.loaders.base_loader import BaseLoader
from app.models import Campaign, CreativeVariant, Flight
from app.utils.exceptions import (
    DataSourceNotFound,
    DuplicateRecord,
    InvalidDataset,
    ValidationError,
)

logger = logging.getLogger(__name__)

REQUIRED_CAMPAIGN_FIELDS = {"campaign_id", "name", "product_id", "status", "objective", "channel", "flight", "brief"}
REQUIRED_FLIGHT_FIELDS = {"start"}
REQUIRED_VARIANT_FIELDS = {"variant", "period", "headline", "primary_text", "landing_page", "landing_page_headline"}


class CampaignLoader(BaseLoader[Campaign]):
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or Path(settings.data_directory) / "campaigns.json"
        self._campaigns: list[Campaign] = []
        self._loaded = False

    def load(self) -> list[Campaign]:
        t0 = time.perf_counter()

        if not self.path.exists():
            raise DataSourceNotFound(str(self.path))

        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw: list[dict] = json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidDataset("campaigns", f"Malformed JSON: {e}")

        if not isinstance(raw, list):
            raise InvalidDataset("campaigns", "Expected a JSON array")

        seen: set[str] = set()
        result: list[Campaign] = []

        for i, item in enumerate(raw):
            missing = REQUIRED_CAMPAIGN_FIELDS - item.keys()
            if missing:
                raise ValidationError("campaigns", i, f"Missing fields: {missing}")

            cid: str = item["campaign_id"]
            if cid in seen:
                raise DuplicateRecord("campaigns", cid)
            seen.add(cid)

            flight_raw = item["flight"]
            flight_missing = REQUIRED_FLIGHT_FIELDS - flight_raw.keys()
            if flight_missing:
                raise ValidationError("campaigns", i, f"Flight missing fields: {flight_missing}")

            flight = Flight(
                start=str(flight_raw["start"]),
                end=str(flight_raw["end"]) if flight_raw.get("end") else None,
            )

            variants = []
            for vi, v in enumerate(item.get("creative_variants", [])):
                v_missing = REQUIRED_VARIANT_FIELDS - v.keys()
                if v_missing:
                    raise ValidationError("campaigns", i, f"Creative variant {vi} missing fields: {v_missing}")
                variants.append(
                    CreativeVariant(
                        variant=str(v["variant"]),
                        period=str(v["period"]),
                        headline=str(v["headline"]),
                        primary_text=str(v["primary_text"]),
                        landing_page=str(v["landing_page"]),
                        landing_page_headline=str(v["landing_page_headline"]),
                        study_citation=str(v["study_citation"]) if v.get("study_citation") else None,
                    )
                )

            campaign = Campaign(
                campaign_id=cid,
                name=str(item["name"]),
                product_id=str(item["product_id"]),
                status=str(item["status"]),
                objective=str(item["objective"]),
                channel=str(item["channel"]),
                flight=flight,
                brief=str(item["brief"]),
                creative_variants=variants,
                notes=str(item["notes"]) if item.get("notes") else None,
            )
            result.append(campaign)

        self._campaigns = result
        self._loaded = True

        elapsed = time.perf_counter() - t0
        logger.info("CampaignLoader loaded %d records in %.3fs", len(result), elapsed)

        return result

    def reload(self) -> list[Campaign]:
        self._loaded = False
        return self.load()
