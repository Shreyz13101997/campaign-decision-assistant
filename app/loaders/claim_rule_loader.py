import json
import logging
import time
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.loaders.base_loader import BaseLoader
from app.models import ClaimRule, ClaimRulesDocument
from app.utils.exceptions import (
    DataSourceNotFound,
    DuplicateRecord,
    InvalidDataset,
    ValidationError,
)

logger = logging.getLogger(__name__)

REQUIRED_RULE_FIELDS = {"id", "title", "description", "severity"}


class ClaimRuleLoader(BaseLoader[ClaimRulesDocument]):
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or Path(settings.data_directory) / "claim_rules.json"
        self._document: Optional[ClaimRulesDocument] = None
        self._loaded = False

    def load(self) -> list[ClaimRulesDocument]:
        t0 = time.perf_counter()

        if not self.path.exists():
            raise DataSourceNotFound(str(self.path))

        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw: dict = json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidDataset("claim_rules", f"Malformed JSON: {e}")

        if not isinstance(raw, dict):
            raise InvalidDataset("claim_rules", "Expected a JSON object")

        required_top = {"version", "disclaimer_required_text", "rules"}
        top_missing = required_top - raw.keys()
        if top_missing:
            raise InvalidDataset("claim_rules", f"Missing top-level fields: {top_missing}")

        rules_raw: list[dict] = raw["rules"]
        if not isinstance(rules_raw, list):
            raise InvalidDataset("claim_rules", "Expected 'rules' to be a JSON array")

        seen: set[str] = set()
        rules: list[ClaimRule] = []

        for i, item in enumerate(rules_raw):
            missing = REQUIRED_RULE_FIELDS - item.keys()
            if missing:
                raise ValidationError("claim_rules", i, f"Missing rule fields: {missing}")

            rid: str = item["id"]
            if rid in seen:
                raise DuplicateRecord("claim_rules", rid)
            seen.add(rid)

            trigger_terms_raw = item.get("trigger_terms")
            if trigger_terms_raw is not None and not isinstance(trigger_terms_raw, list):
                raise ValidationError("claim_rules", i, "trigger_terms must be a list")

            rule = ClaimRule(
                rule_id=rid,
                title=str(item["title"]),
                description=str(item["description"]),
                trigger_terms=tuple(str(t) for t in trigger_terms_raw) if trigger_terms_raw else (),
                severity=str(item["severity"]),
                trigger_context=tuple(str(c) for c in item["trigger_context"]) if item.get("trigger_context") else None,
                requires_field=str(item["requires_field"]) if item.get("requires_field") else None,
                applies_when=str(item["applies_when"]) if item.get("applies_when") else None,
                requires=str(item["requires"]) if item.get("requires") else None,
            )
            rules.append(rule)

        document = ClaimRulesDocument(
            version=str(raw["version"]),
            disclaimer_required_text=str(raw["disclaimer_required_text"]),
            notes=str(raw.get("notes", "")),
            rules=tuple(rules),
        )

        self._document = document
        self._loaded = True

        elapsed = time.perf_counter() - t0
        logger.info("ClaimRuleLoader loaded %d rules in %.3fs", len(rules), elapsed)

        return [document]

    def reload(self) -> list[ClaimRulesDocument]:
        self._loaded = False
        return self.load()
