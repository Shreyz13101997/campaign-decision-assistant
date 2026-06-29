import json
from pathlib import Path

import pytest

from app.loaders.reviews_loader import ReviewsLoader
from app.models import Review
from app.utils.exceptions import DataSourceNotFound, InvalidDataset, ValidationError


def test_load_success(tmp_path: Path, sample_reviews: list[dict]) -> None:
    path = tmp_path / "reviews.json"
    path.write_text(json.dumps(sample_reviews), encoding="utf-8")
    loader = ReviewsLoader(path=path)
    result = loader.load()
    assert len(result) == 2
    assert all(isinstance(r, Review) for r in result)
    assert result[0].product_id == "PRD-001"
    assert result[0].rating == 5


def test_invalid_rating_range(tmp_path: Path, sample_reviews: list[dict]) -> None:
    sample_reviews[0]["rating"] = 6
    path = tmp_path / "reviews.json"
    path.write_text(json.dumps(sample_reviews), encoding="utf-8")
    loader = ReviewsLoader(path=path)
    with pytest.raises(ValidationError, match="rating must be an integer 1-5"):
        loader.load()


def test_rating_not_int(tmp_path: Path, sample_reviews: list[dict]) -> None:
    sample_reviews[0]["rating"] = "five"
    path = tmp_path / "reviews.json"
    path.write_text(json.dumps(sample_reviews), encoding="utf-8")
    loader = ReviewsLoader(path=path)
    with pytest.raises(ValidationError, match="rating must be an integer 1-5"):
        loader.load()


def test_missing_file(tmp_path: Path) -> None:
    loader = ReviewsLoader(path=tmp_path / "nonexistent.json")
    with pytest.raises(DataSourceNotFound):
        loader.load()


def test_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "reviews.json"
    path.write_text("[{broken}", encoding="utf-8")
    loader = ReviewsLoader(path=path)
    with pytest.raises(InvalidDataset):
        loader.load()
