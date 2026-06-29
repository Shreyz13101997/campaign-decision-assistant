import json
from pathlib import Path

import pytest

from app.loaders.campaign_loader import CampaignLoader
from app.models import Campaign, CreativeVariant, Flight
from app.utils.exceptions import DataSourceNotFound, DuplicateRecord, InvalidDataset, ValidationError


def test_load_success(tmp_path: Path, sample_campaigns: list[dict]) -> None:
    path = tmp_path / "campaigns.json"
    path.write_text(json.dumps(sample_campaigns), encoding="utf-8")
    loader = CampaignLoader(path=path)
    result = loader.load()
    assert len(result) == 1
    c = result[0]
    assert isinstance(c, Campaign)
    assert c.campaign_id == "CMP-001"
    assert c.name == "Test Campaign"
    assert isinstance(c.flight, Flight)
    assert c.flight.start == "2026-01-01"
    assert c.flight.end == "2026-01-31"
    assert len(c.creative_variants) == 1
    assert isinstance(c.creative_variants[0], CreativeVariant)


def test_reload(tmp_path: Path, sample_campaigns: list[dict]) -> None:
    path = tmp_path / "campaigns.json"
    path.write_text(json.dumps(sample_campaigns), encoding="utf-8")
    loader = CampaignLoader(path=path)
    loader.load()
    result = loader.reload()
    assert len(result) == 1


def test_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "nonexistent.json"
    loader = CampaignLoader(path=path)
    with pytest.raises(DataSourceNotFound):
        loader.load()


def test_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "campaigns.json"
    path.write_text("not json", encoding="utf-8")
    loader = CampaignLoader(path=path)
    with pytest.raises(InvalidDataset, match="Malformed JSON"):
        loader.load()


def test_duplicate_campaign_id(tmp_path: Path, sample_campaigns: list[dict]) -> None:
    data = sample_campaigns * 2
    path = tmp_path / "campaigns.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    loader = CampaignLoader(path=path)
    with pytest.raises(DuplicateRecord, match="CMP-001"):
        loader.load()


def test_missing_required_field(tmp_path: Path, sample_campaigns: list[dict]) -> None:
    del sample_campaigns[0]["name"]
    path = tmp_path / "campaigns.json"
    path.write_text(json.dumps(sample_campaigns), encoding="utf-8")
    loader = CampaignLoader(path=path)
    with pytest.raises(ValidationError, match="Missing fields"):
        loader.load()


def test_not_a_list(tmp_path: Path) -> None:
    path = tmp_path / "campaigns.json"
    path.write_text("{}", encoding="utf-8")
    loader = CampaignLoader(path=path)
    with pytest.raises(InvalidDataset, match="Expected a JSON array"):
        loader.load()


def test_unknown_campaign_lookup(tmp_path: Path, sample_campaigns: list[dict]) -> None:
    path = tmp_path / "campaigns.json"
    path.write_text(json.dumps(sample_campaigns), encoding="utf-8")
    loader = CampaignLoader(path=path)
    loader.load()
    assert all(c.campaign_id != "NONEXISTENT" for c in loader._campaigns)


def test_missing_flight_end(tmp_path: Path, sample_campaigns: list[dict]) -> None:
    sample_campaigns[0]["flight"] = {"start": "2026-01-01"}
    path = tmp_path / "campaigns.json"
    path.write_text(json.dumps(sample_campaigns), encoding="utf-8")
    loader = CampaignLoader(path=path)
    result = loader.load()
    assert result[0].flight.end is None
