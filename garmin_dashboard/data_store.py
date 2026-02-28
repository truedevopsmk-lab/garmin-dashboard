from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean
from typing import Any


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


def parse_fit_metrics(fit_path: Path) -> dict[str, float | int | None]:
    """Extract basic metrics from a FIT file using fitparse."""
    try:
        from fitparse import FitFile
    except ImportError as exc:  # pragma: no cover - dependency/runtime concern
        raise RuntimeError("fitparse is required for FIT parsing") from exc

    fit_file = FitFile(str(fit_path))

    heart_rates: list[int] = []
    cadences: list[int] = []

    for record in fit_file.get_messages("record"):
        for field in record:
            if field.name == "heart_rate" and field.value is not None:
                heart_rates.append(int(field.value))
            elif field.name == "cadence" and field.value is not None:
                cadences.append(int(field.value))

    return {
        "fit_avg_heart_rate": round(mean(heart_rates), 2) if heart_rates else None,
        "fit_max_heart_rate": max(heart_rates) if heart_rates else None,
        "fit_avg_cadence": round(mean(cadences), 2) if cadences else None,
        "fit_max_cadence": max(cadences) if cadences else None,
    }
