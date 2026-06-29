import json
from pathlib import Path

import pytest

from app.loaders.claim_rule_loader import ClaimRuleLoader
from app.models import ClaimRule, ClaimRulesDocument
from app.utils.exceptions import DataSourceNotFound, DuplicateRecord, InvalidDataset


def test_load_success(tmp_path: Path, sample_claim_rules: dict) -> None:
    path = tmp_path / "claim_rules.json"
    path.write_text(json.dumps(sample_claim_rules), encoding="utf-8")
    loader = ClaimRuleLoader(path=path)
    result = loader.load()
    assert len(result) == 1
    doc = result[0]
    assert isinstance(doc, ClaimRulesDocument)
    assert doc.version == "2026-01"
    assert len(doc.rules) == 1
    rule = doc.rules[0]
    assert isinstance(rule, ClaimRule)
    assert rule.rule_id == "CR-001"
    assert rule.severity == "violation"
    assert "cure" in rule.trigger_terms


def test_duplicate_rule_id(tmp_path: Path, sample_claim_rules: dict) -> None:
    sample_claim_rules["rules"].append(sample_claim_rules["rules"][0])
    path = tmp_path / "claim_rules.json"
    path.write_text(json.dumps(sample_claim_rules), encoding="utf-8")
    loader = ClaimRuleLoader(path=path)
    with pytest.raises(DuplicateRecord, match="CR-001"):
        loader.load()


def test_missing_file(tmp_path: Path) -> None:
    loader = ClaimRuleLoader(path=tmp_path / "nonexistent.json")
    with pytest.raises(DataSourceNotFound):
        loader.load()


def test_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "claim_rules.json"
    path.write_text("{bad", encoding="utf-8")
    loader = ClaimRuleLoader(path=path)
    with pytest.raises(InvalidDataset):
        loader.load()


def test_not_dict(tmp_path: Path) -> None:
    path = tmp_path / "claim_rules.json"
    path.write_text("[]", encoding="utf-8")
    loader = ClaimRuleLoader(path=path)
    with pytest.raises(InvalidDataset, match="Expected a JSON object"):
        loader.load()
