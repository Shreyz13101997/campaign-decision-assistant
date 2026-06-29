import json
from pathlib import Path

import pytest

from app.loaders.orders_loader import OrdersLoader
from app.models import Funnel, OrderMetrics
from app.utils.exceptions import DataSourceNotFound, InvalidDataset, ValidationError


def test_load_success(tmp_path: Path, sample_orders: list[dict]) -> None:
    path = tmp_path / "ecommerce_orders.json"
    path.write_text(json.dumps(sample_orders), encoding="utf-8")
    loader = OrdersLoader(path=path)
    result = loader.load()
    assert len(result) == 1
    o = result[0]
    assert isinstance(o, OrderMetrics)
    assert o.campaign_id == "CMP-001"
    assert o.attributed_orders == 100
    assert isinstance(o.funnel, Funnel)
    assert o.funnel.sessions == 5000
    assert o.funnel.purchased == 100


def test_null_funnel(tmp_path: Path, sample_orders: list[dict]) -> None:
    sample_orders[0]["funnel"] = None
    path = tmp_path / "ecommerce_orders.json"
    path.write_text(json.dumps(sample_orders), encoding="utf-8")
    loader = OrdersLoader(path=path)
    result = loader.load()
    assert result[0].funnel is None


def test_missing_file(tmp_path: Path) -> None:
    loader = OrdersLoader(path=tmp_path / "nonexistent.json")
    with pytest.raises(DataSourceNotFound):
        loader.load()


def test_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "ecommerce_orders.json"
    path.write_text("not json", encoding="utf-8")
    loader = OrdersLoader(path=path)
    with pytest.raises(InvalidDataset):
        loader.load()
