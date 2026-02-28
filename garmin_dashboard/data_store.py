from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd


def save_activities_to_csv(activities: list[dict[str, Any]], csv_path: Path) -> None:
    """Persist activity metadata to CSV."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [_flatten_activity(activity) for activity in activities]
    if not rows:
        csv_path.write_text("", encoding="utf-8")
        return

    fieldnames = sorted({key for row in rows for key in row.keys()})
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_timeseries_to_csv(df: pd.DataFrame, csv_path: Path) -> None:
    """Persist a FIT-derived time-series DataFrame to CSV."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)


def _flatten_activity(activity: dict[str, Any]) -> dict[str, Any]:
    activity_type = activity.get("activityType", {})
    if isinstance(activity_type, dict):
        type_key = activity_type.get("typeKey")
    else:
        type_key = activity_type

    return {
        "activity_id": activity.get("activityId"),
        "activity_name": activity.get("activityName"),
        "activity_type": type_key,
        "start_time_local": activity.get("startTimeLocal"),
        "distance_m": activity.get("distance"),
        "duration_s": activity.get("duration"),
        "moving_duration_s": activity.get("movingDuration"),
        "average_hr": activity.get("averageHR"),
        "max_hr": activity.get("maxHR"),
        "average_cadence": activity.get("averageRunCadence"),
        "calories": activity.get("calories"),
    }
