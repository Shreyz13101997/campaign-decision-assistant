import csv
import logging
import time
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.loaders.base_loader import BaseLoader
from app.models import PerformanceMetric
from app.utils.exceptions import (
    DataSourceNotFound,
    InvalidDataset,
    ValidationError,
)

logger = logging.getLogger(__name__)

REQUIRED_CSV_COLUMNS = {
    "campaign_id", "period", "period_start", "period_end",
    "impressions", "clicks", "ctr_pct", "conversions",
    "conversion_rate_pct", "spend_inr",
}


class PerformanceLoader(BaseLoader[PerformanceMetric]):
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or Path(settings.data_directory) / "performance_metrics.csv"
        self._metrics: list[PerformanceMetric] = []
        self._loaded = False

    def load(self) -> list[PerformanceMetric]:
        t0 = time.perf_counter()

        if not self.path.exists():
            raise DataSourceNotFound(str(self.path))

        result: list[PerformanceMetric] = []

        try:
            with self.path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    raise InvalidDataset("performance_metrics", "Empty or missing header row")

                header_set = {h.strip() for h in reader.fieldnames}
                missing = REQUIRED_CSV_COLUMNS - header_set
                if missing:
                    raise InvalidDataset("performance_metrics", f"Missing CSV columns: {missing}")

                for i, row in enumerate(reader):
                    row = {k.strip(): v.strip() if v else "" for k, v in row.items()}

                    try:
                        metric = PerformanceMetric(
                            campaign_id=str(row["campaign_id"]),
                            period=str(row["period"]),
                            period_start=str(row["period_start"]),
                            period_end=str(row["period_end"]),
                            impressions=int(row["impressions"]),
                            clicks=int(row["clicks"]),
                            ctr_pct=float(row["ctr_pct"]),
                            conversions=int(row["conversions"]),
                            conversion_rate_pct=float(row["conversion_rate_pct"]),
                            spend_inr=float(row["spend_inr"]),
                        )
                    except (ValueError, KeyError) as e:
                        raise ValidationError("performance_metrics", i, str(e))

                    result.append(metric)
        except csv.Error as e:
            raise InvalidDataset("performance_metrics", f"CSV parse error: {e}")

        self._metrics = result
        self._loaded = True

        elapsed = time.perf_counter() - t0
        logger.info("PerformanceLoader loaded %d records in %.3fs", len(result), elapsed)

        return result

    def reload(self) -> list[PerformanceMetric]:
        self._loaded = False
        return self.load()
