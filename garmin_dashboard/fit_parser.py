from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def parse_fit_to_dataframe(file_path: str | Path) -> pd.DataFrame:
    """Parse a FIT file into a pandas DataFrame of record-level time-series metrics."""
    try:
        from fitparse import FitFile
    except ImportError as exc:  # pragma: no cover - dependency/runtime concern
        raise RuntimeError("fitparse is required for FIT parsing") from exc

    fit_path = Path(file_path)
    fit_file = FitFile(str(fit_path))

    rows: list[dict[str, Any]] = []
    wanted_fields = {
        "timestamp",
        "heart_rate",
        "cadence",
        "distance",
        "speed",
        "altitude",
    }

    for record in fit_file.get_messages("record"):
        row: dict[str, Any] = {}
        for field in record:
            if field.name in wanted_fields:
                row[field.name] = field.value

        if row:
            rows.append(row)

    if not rows:
        return pd.DataFrame(
            columns=["timestamp", "heart_rate", "cadence", "distance", "speed", "altitude"]
        )

    df = pd.DataFrame(rows)
    column_order = ["timestamp", "heart_rate", "cadence", "distance", "speed", "altitude"]
    for col in column_order:
        if col not in df.columns:
            df[col] = pd.NA

    return df[column_order]
