import json
import csv
import io
from pathlib import Path
from typing import Generator

import pytest

from app.core.config import settings


@pytest.fixture
def data_dir() -> Path:
    return Path(settings.data_directory)


@pytest.fixture
def sample_campaigns() -> list[dict]:
    return [
        {
            "campaign_id": "CMP-001",
            "name": "Test Campaign",
            "product_id": "PRD-001",
            "status": "active",
            "objective": "conversions",
            "channel": "Meta Ads",
            "flight": {"start": "2026-01-01", "end": "2026-01-31"},
            "brief": "Test brief",
            "creative_variants": [
                {
                    "variant": "v1",
                    "period": "2026-01-01..2026-01-15",
                    "headline": "Test Headline",
                    "primary_text": "Test text",
                    "landing_page": "lp_test",
                    "landing_page_headline": "LP Test",
                }
            ],
        }
    ]


@pytest.fixture
def sample_products() -> list[dict]:
    return [
        {
            "product_id": "PRD-001",
            "name": "Test Product",
            "category": "Test",
            "price_inr": 999,
            "in_stock": True,
            "price_last_changed": "2026-01-01",
            "description": "A test product.",
        }
    ]


@pytest.fixture
def sample_reviews() -> list[dict]:
    return [
        {"product_id": "PRD-001", "rating": 5, "date": "2026-01-15", "text": "Great product!"},
        {"product_id": "PRD-001", "rating": 3, "date": "2026-01-20", "text": "It's okay."},
    ]


@pytest.fixture
def sample_orders() -> list[dict]:
    return [
        {
            "campaign_id": "CMP-001",
            "period": "v1",
            "attributed_orders": 100,
            "funnel": {"sessions": 5000, "add_to_cart": 300, "checkout_started": 200, "purchased": 100},
        }
    ]


@pytest.fixture
def sample_approved() -> list[dict]:
    return [
        {
            "approved_id": "APR-001",
            "name": "Test Approved",
            "product_id": "PRD-001",
            "outcome": "success",
            "metrics": {"ctr_pct": 2.5, "conversion_rate_pct": 3.0},
            "learnings": "Test learning",
            "approved_by": "Tester",
            "approved_at": "2026-01-15",
        }
    ]


@pytest.fixture
def sample_claim_rules() -> dict:
    return {
        "version": "2026-01",
        "disclaimer_required_text": "Disclaimer text.",
        "notes": "Test notes.",
        "rules": [
            {
                "id": "CR-001",
                "title": "No disease claims",
                "description": "Test",
                "trigger_terms": ["cure", "treat"],
                "trigger_context": ["disease"],
                "severity": "violation",
            }
        ],
    }


@pytest.fixture
def sample_metrics_csv() -> str:
    header = "campaign_id,period,period_start,period_end,impressions,clicks,ctr_pct,conversions,conversion_rate_pct,spend_inr"
    row = "CMP-001,v1,2026-01-01,2026-01-15,10000,500,5.0,50,10.0,25000.0"
    return f"{header}\n{row}\n"
