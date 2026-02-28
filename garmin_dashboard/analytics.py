from __future__ import annotations

from typing import Any

import pandas as pd


def compute_performance_metrics(df: pd.DataFrame) -> dict[str, float | int | None]:
    """Compute run-performance metrics from FIT time-series data."""
    if df.empty:
        return {
            "avg_hr": None,
            "max_hr": None,
            "hr_drift_pct": None,
            "pace_hr_ratio": None,
            "cadence_consistency_pct": None,
            "aerobic_decoupling_pct": None,
        }

    heart_rate = pd.to_numeric(df.get("heart_rate"), errors="coerce")
    cadence = pd.to_numeric(df.get("cadence"), errors="coerce")
    speed = pd.to_numeric(df.get("speed"), errors="coerce")

    avg_hr = _round_or_none(heart_rate.mean())
    max_hr = _round_or_none(heart_rate.max())

    hr_drift_pct = _compute_hr_drift(heart_rate)
    pace_hr_ratio = _compute_pace_hr_ratio(speed, heart_rate)
    cadence_consistency_pct = _compute_cadence_consistency(cadence)
    aerobic_decoupling_pct = _compute_aerobic_decoupling(speed, heart_rate)

    return {
        "avg_hr": avg_hr,
        "max_hr": max_hr,
        "hr_drift_pct": hr_drift_pct,
        "pace_hr_ratio": pace_hr_ratio,
        "cadence_consistency_pct": cadence_consistency_pct,
        "aerobic_decoupling_pct": aerobic_decoupling_pct,
    }


def _compute_hr_drift(heart_rate: pd.Series) -> float | None:
    clean = heart_rate.dropna()
    if len(clean) < 4:
        return None

    midpoint = len(clean) // 2
    first = clean.iloc[:midpoint].mean()
    second = clean.iloc[midpoint:].mean()
    if pd.isna(first) or first == 0:
        return None
    return _round_or_none(((second - first) / first) * 100)


def _compute_pace_hr_ratio(speed: pd.Series, heart_rate: pd.Series) -> float | None:
    clean_speed = speed.dropna()
    clean_hr = heart_rate.dropna()
    if clean_speed.empty or clean_hr.empty:
        return None

    avg_speed = clean_speed.mean()
    avg_hr = clean_hr.mean()
    if pd.isna(avg_speed) or pd.isna(avg_hr) or avg_hr == 0:
        return None

    # Faster speed per beat usually implies better efficiency.
    return _round_or_none(avg_speed / avg_hr)


def _compute_cadence_consistency(cadence: pd.Series) -> float | None:
    clean = cadence.dropna()
    if len(clean) < 2:
        return None

    avg = clean.mean()
    std = clean.std()
    if pd.isna(avg) or avg == 0 or pd.isna(std):
        return None

    # 100% means perfectly stable cadence.
    consistency = max(0.0, 100.0 - ((std / avg) * 100.0))
    return _round_or_none(consistency)


def _compute_aerobic_decoupling(speed: pd.Series, heart_rate: pd.Series) -> float | None:
    temp_df = pd.DataFrame({"speed": speed, "heart_rate": heart_rate}).dropna()
    if len(temp_df) < 4:
        return None

    temp_df["eff"] = temp_df["speed"] / temp_df["heart_rate"]
    midpoint = len(temp_df) // 2
    first_eff = temp_df["eff"].iloc[:midpoint].mean()
    second_eff = temp_df["eff"].iloc[midpoint:].mean()

    if pd.isna(first_eff) or first_eff == 0 or pd.isna(second_eff):
        return None

    # Positive means efficiency dropped in second half.
    return _round_or_none(((first_eff - second_eff) / first_eff) * 100)


def _round_or_none(value: Any, ndigits: int = 2) -> float | int | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), ndigits)
