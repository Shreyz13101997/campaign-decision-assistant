from pathlib import Path

import pytest

from app.loaders.performance_loader import PerformanceLoader
from app.models import PerformanceMetric
from app.utils.exceptions import DataSourceNotFound, InvalidDataset, ValidationError


def test_load_success(tmp_path: Path, sample_metrics_csv: str) -> None:
    path = tmp_path / "performance_metrics.csv"
    path.write_text(sample_metrics_csv, encoding="utf-8")
    loader = PerformanceLoader(path=path)
    result = loader.load()
    assert len(result) == 1
    m = result[0]
    assert isinstance(m, PerformanceMetric)
    assert m.campaign_id == "CMP-001"
    assert m.impressions == 10000
    assert m.clicks == 500
    assert m.ctr_pct == 5.0
    assert m.conversions == 50
    assert m.conversion_rate_pct == 10.0
    assert m.spend_inr == 25000.0


def test_missing_file(tmp_path: Path) -> None:
    loader = PerformanceLoader(path=tmp_path / "nonexistent.csv")
    with pytest.raises(DataSourceNotFound):
        loader.load()


def test_missing_columns(tmp_path: Path) -> None:
    path = tmp_path / "performance_metrics.csv"
    path.write_text("campaign_id,period\nCMP-001,v1\n", encoding="utf-8")
    loader = PerformanceLoader(path=path)
    with pytest.raises(InvalidDataset, match="Missing CSV columns"):
        loader.load()


def test_bad_numeric_value(tmp_path: Path, sample_metrics_csv: str) -> None:
    bad = sample_metrics_csv.replace("10000", "not_a_number")
    path = tmp_path / "performance_metrics.csv"
    path.write_text(bad, encoding="utf-8")
    loader = PerformanceLoader(path=path)
    with pytest.raises(ValidationError):
        loader.load()


def test_reload(tmp_path: Path, sample_metrics_csv: str) -> None:
    path = tmp_path / "performance_metrics.csv"
    path.write_text(sample_metrics_csv, encoding="utf-8")
    loader = PerformanceLoader(path=path)
    loader.load()
    result = loader.reload()
    assert len(result) == 1
