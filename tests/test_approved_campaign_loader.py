import json
from pathlib import Path

import pytest

from app.loaders.approved_campaign_loader import ApprovedCampaignLoader
from app.models import ApprovedCampaign, ApprovedCampaignMetrics
from app.utils.exceptions import DataSourceNotFound, DuplicateRecord, InvalidDataset, ValidationError


def test_load_success(tmp_path: Path, sample_approved: list[dict]) -> None:
    path = tmp_path / "approved_campaigns.json"
    path.write_text(json.dumps(sample_approved), encoding="utf-8")
    loader = ApprovedCampaignLoader(path=path)
    result = loader.load()
    assert len(result) == 1
    a = result[0]
    assert isinstance(a, ApprovedCampaign)
    assert a.approved_id == "APR-001"
    assert isinstance(a.metrics, ApprovedCampaignMetrics)
    assert a.metrics.ctr_pct == 2.5
    assert a.outcome == "success"


def test_duplicate_id(tmp_path: Path, sample_approved: list[dict]) -> None:
    data = sample_approved * 2
    path = tmp_path / "approved_campaigns.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    loader = ApprovedCampaignLoader(path=path)
    with pytest.raises(DuplicateRecord, match="APR-001"):
        loader.load()


def test_missing_file(tmp_path: Path) -> None:
    loader = ApprovedCampaignLoader(path=tmp_path / "nonexistent.json")
    with pytest.raises(DataSourceNotFound):
        loader.load()


def test_bad_metrics_type(tmp_path: Path, sample_approved: list[dict]) -> None:
    sample_approved[0]["metrics"]["ctr_pct"] = "not-a-float"
    path = tmp_path / "approved_campaigns.json"
    path.write_text(json.dumps(sample_approved), encoding="utf-8")
    loader = ApprovedCampaignLoader(path=path)
    with pytest.raises(ValidationError):
        loader.load()
