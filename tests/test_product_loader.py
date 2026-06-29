import json
from pathlib import Path

import pytest

from app.loaders.product_loader import ProductLoader
from app.models import Product
from app.utils.exceptions import DataSourceNotFound, DuplicateRecord, InvalidDataset, ValidationError


def test_load_success(tmp_path: Path, sample_products: list[dict]) -> None:
    path = tmp_path / "products.json"
    path.write_text(json.dumps(sample_products), encoding="utf-8")
    loader = ProductLoader(path=path)
    result = loader.load()
    assert len(result) == 1
    p = result[0]
    assert isinstance(p, Product)
    assert p.product_id == "PRD-001"
    assert p.price_inr == 999
    assert p.in_stock is True


def test_duplicate_product_id(tmp_path: Path, sample_products: list[dict]) -> None:
    data = sample_products * 2
    path = tmp_path / "products.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    loader = ProductLoader(path=path)
    with pytest.raises(DuplicateRecord, match="PRD-001"):
        loader.load()


def test_bad_price_type(tmp_path: Path, sample_products: list[dict]) -> None:
    sample_products[0]["price_inr"] = "not-a-number"
    path = tmp_path / "products.json"
    path.write_text(json.dumps(sample_products), encoding="utf-8")
    loader = ProductLoader(path=path)
    with pytest.raises(ValidationError, match="price_inr must be numeric"):
        loader.load()


def test_bad_in_stock_type(tmp_path: Path, sample_products: list[dict]) -> None:
    sample_products[0]["in_stock"] = "yes"
    path = tmp_path / "products.json"
    path.write_text(json.dumps(sample_products), encoding="utf-8")
    loader = ProductLoader(path=path)
    with pytest.raises(ValidationError, match="in_stock must be a boolean"):
        loader.load()


def test_missing_file(tmp_path: Path) -> None:
    loader = ProductLoader(path=tmp_path / "nonexistent.json")
    with pytest.raises(DataSourceNotFound):
        loader.load()


def test_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "products.json"
    path.write_text("{bad", encoding="utf-8")
    loader = ProductLoader(path=path)
    with pytest.raises(InvalidDataset, match="Malformed JSON"):
        loader.load()
