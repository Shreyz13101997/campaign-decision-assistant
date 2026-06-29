import json
from pathlib import Path

import pytest

from app.loaders.registry import LoaderRegistry
from app.models.evidence import AnalysisResult, EvidenceBundle, RecommendationDraft
from app.services.campaign_analysis_service import CampaignAnalysisService


def _create_data_files(data_dir: Path) -> None:
    campaigns = [
        {
            "campaign_id": "CMP-001", "name": "Test Campaign",
            "product_id": "PRD-001", "status": "active",
            "objective": "conversions", "channel": "Meta Ads",
            "flight": {"start": "2026-01-01", "end": "2026-01-31"},
            "brief": "Test",
            "creative_variants": [
                {
                    "variant": "v1", "period": "2026-01-01..2026-01-15",
                    "headline": "Energy Support",
                    "primary_text": "Daily energy support.",
                    "landing_page": "lp_v1",
                    "landing_page_headline": "Energy Support",
                }
            ],
        }
    ]
    products = [
        {
            "product_id": "PRD-001", "name": "Test Product",
            "category": "Essentials", "price_inr": 999,
            "in_stock": True, "price_last_changed": "2026-01-01",
            "description": "Test product.",
        }
    ]
    reviews = [
        {"product_id": "PRD-001", "rating": 4, "date": "2026-01-15", "text": "Good product."},
    ]
    orders = [
        {
            "campaign_id": "CMP-001", "period": "v1", "attributed_orders": 100,
            "funnel": {"sessions": 1000, "add_to_cart": 200, "checkout_started": 150, "purchased": 100},
        }
    ]
    approved = [
        {
            "approved_id": "APR-001", "name": "Past Success",
            "product_id": "PRD-001", "outcome": "success",
            "metrics": {"ctr_pct": 3.0, "conversion_rate_pct": 4.0},
            "learnings": "Consistent messaging works best.",
            "approved_by": "Test", "approved_at": "2026-01-10",
        }
    ]
    metrics_csv = "campaign_id,period,period_start,period_end,impressions,clicks,ctr_pct,conversions,conversion_rate_pct,spend_inr\nCMP-001,v1,2026-01-01,2026-01-15,5000,250,5.0,50,10.0,12500.0\n"
    claim_rules = {
        "version": "2026-01", "disclaimer_required_text": "Disclaimer.",
        "notes": "", "rules": [],
    }

    (data_dir / "campaigns.json").write_text(json.dumps(campaigns), encoding="utf-8")
    (data_dir / "products.json").write_text(json.dumps(products), encoding="utf-8")
    (data_dir / "reviews.json").write_text(json.dumps(reviews), encoding="utf-8")
    (data_dir / "ecommerce_orders.json").write_text(json.dumps(orders), encoding="utf-8")
    (data_dir / "approved_campaigns.json").write_text(json.dumps(approved), encoding="utf-8")
    (data_dir / "claim_rules.json").write_text(json.dumps(claim_rules), encoding="utf-8")
    (data_dir / "performance_metrics.csv").write_text(metrics_csv, encoding="utf-8")


def test_analyze_returns_complete_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _create_data_files(tmp_path)
    monkeypatch.setattr("app.core.config.settings.data_directory", str(tmp_path))
    reg = LoaderRegistry()
    service = CampaignAnalysisService(reg)

    result = service.analyze("CMP-001")
    assert isinstance(result, AnalysisResult)
    assert result.campaign_id == "CMP-001"
    assert result.status in ("completed", "completed_with_warnings")
    assert isinstance(result.evidence_bundle, EvidenceBundle)
    assert isinstance(result.recommendation, RecommendationDraft)
    assert len(result.summary_points) > 0


def test_analyze_unknown_campaign_returns_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _create_data_files(tmp_path)
    monkeypatch.setattr("app.core.config.settings.data_directory", str(tmp_path))
    reg = LoaderRegistry()
    service = CampaignAnalysisService(reg)

    result = service.analyze("NONEXISTENT")
    assert result.status == "failed"
    assert "not found" in " ".join(result.summary_points).lower()
