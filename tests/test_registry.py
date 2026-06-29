import json
from pathlib import Path

import pytest

from app.core.config import settings
from app.loaders.registry import LoaderRegistry
from app.models import (
    ApprovedCampaign,
    Campaign,
    ClaimRule,
    OrderMetrics,
    PerformanceMetric,
    Product,
    Review,
)


@pytest.fixture
def registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
             sample_campaigns: list[dict], sample_products: list[dict],
             sample_reviews: list[dict], sample_orders: list[dict],
             sample_approved: list[dict], sample_claim_rules: dict,
             sample_metrics_csv: str) -> LoaderRegistry:
    (tmp_path / "campaigns.json").write_text(json.dumps(sample_campaigns), encoding="utf-8")
    (tmp_path / "products.json").write_text(json.dumps(sample_products), encoding="utf-8")
    (tmp_path / "reviews.json").write_text(json.dumps(sample_reviews), encoding="utf-8")
    (tmp_path / "ecommerce_orders.json").write_text(json.dumps(sample_orders), encoding="utf-8")
    (tmp_path / "approved_campaigns.json").write_text(json.dumps(sample_approved), encoding="utf-8")
    (tmp_path / "claim_rules.json").write_text(json.dumps(sample_claim_rules), encoding="utf-8")
    (tmp_path / "performance_metrics.csv").write_text(sample_metrics_csv, encoding="utf-8")

    monkeypatch.setattr(settings, "data_directory", str(tmp_path))
    reg = LoaderRegistry()
    reg.load_all()
    return reg


def test_registry_get_campaign(registry: LoaderRegistry) -> None:
    c = registry.get_campaign("CMP-001")
    assert c is not None
    assert isinstance(c, Campaign)
    assert c.name == "Test Campaign"
    assert registry.get_campaign("NONEXISTENT") is None


def test_registry_get_campaigns_by_product(registry: LoaderRegistry) -> None:
    camps = registry.get_campaigns_by_product("PRD-001")
    assert len(camps) == 1


def test_registry_get_product(registry: LoaderRegistry) -> None:
    p = registry.get_product("PRD-001")
    assert p is not None
    assert isinstance(p, Product)
    assert p.name == "Test Product"
    assert registry.get_product("BAD") is None


def test_registry_get_reviews(registry: LoaderRegistry) -> None:
    reviews = registry.get_reviews("PRD-001")
    assert len(reviews) == 2
    assert all(isinstance(r, Review) for r in reviews)
    assert registry.get_reviews("NOPROD") == []


def test_registry_get_metrics(registry: LoaderRegistry) -> None:
    metrics = registry.get_metrics("CMP-001")
    assert len(metrics) == 1
    assert all(isinstance(m, PerformanceMetric) for m in metrics)
    assert registry.get_metrics("NOCAMP") == []


def test_registry_get_orders(registry: LoaderRegistry) -> None:
    orders = registry.get_orders("CMP-001")
    assert len(orders) == 1
    assert all(isinstance(o, OrderMetrics) for o in orders)
    assert registry.get_orders("NOCAMP") == []


def test_registry_get_approved(registry: LoaderRegistry) -> None:
    approved = registry.get_approved_campaigns("PRD-001")
    assert len(approved) == 1
    assert all(isinstance(a, ApprovedCampaign) for a in approved)
    assert registry.get_approved_campaigns("NOPROD") == []


def test_registry_get_claim_rules(registry: LoaderRegistry) -> None:
    rules = registry.get_claim_rules()
    assert len(rules) == 1
    assert all(isinstance(r, ClaimRule) for r in rules)


def test_registry_reload(registry: LoaderRegistry) -> None:
    registry.reload_all()
    assert registry.get_campaign("CMP-001") is not None


def test_registry_get_all(registry: LoaderRegistry) -> None:
    assert len(registry.get_all_campaigns()) == 1
    assert len(registry.get_all_products()) == 1
    assert len(registry.get_all_approved_campaigns()) == 1


def test_registry_unknown_campaign_returns_none(registry: LoaderRegistry) -> None:
    assert registry.get_campaign("NONEXISTENT") is None
    assert registry.get_product("NONEXISTENT") is None
    assert registry.get_reviews("NONEXISTENT") == []
    assert registry.get_metrics("NONEXISTENT") == []
    assert registry.get_orders("NONEXISTENT") == []
    assert registry.get_approved_campaigns("NONEXISTENT") == []
