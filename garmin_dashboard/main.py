from __future__ import annotations

import argparse
import logging
import os

from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .data_store import parse_fit_metrics, save_activities_to_csv
from .garmin_client import GarminConnectClient, GarminCredentials


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch Garmin Connect activities and export them to CSV"
    )
    parser.add_argument("--days", type=int, default=14, help="Lookback window in days")
    parser.add_argument(
        "--limit", type=int, default=50, help="Maximum activities to pull from Garmin"
    )
    parser.add_argument(
        "--activity-type",
        default="running",
        help="Only keep activities with this Garmin typeKey (e.g. running)",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=Path("data/activities.csv"),
        help="Output CSV path",
    )
    parser.add_argument(
        "--session-file",
        type=Path,
        default=Path(".session/garmin_session.json"),
        help="Path for persisted Garmin login session",
    )
    parser.add_argument(
        "--include-fit",
        action="store_true",
        help="Download and parse FIT files for extra metrics",
    )
    parser.add_argument(
        "--fit-dir",
        type=Path,
        default=Path("data/fit"),
        help="Directory to store downloaded FIT files",
    )
    return parser


def _require_env_var(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _filter_activities(
    activities: list[dict[str, Any]], *, days: int, activity_type: str
) -> list[dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    filtered: list[dict[str, Any]] = []
    for item in activities:
        type_key = (item.get("activityType") or {}).get("typeKey", "")
        if type_key != activity_type:
            continue

        # Garmin usually provides local timestamps like "2024-01-03 06:40:12"
        start_raw = item.get("startTimeLocal")
        if isinstance(start_raw, str):
            try:
                start_dt = datetime.fromisoformat(start_raw.replace(" ", "T"))
                # Treat local timestamp as UTC-naive fallback for filtering only.
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            except ValueError:
                start_dt = cutoff
        else:
            start_dt = cutoff

        if start_dt >= cutoff:
            filtered.append(item)

    return filtered


def _enrich_with_fit(
    client: GarminConnectClient, activities: list[dict[str, Any]], fit_dir: Path
) -> None:
    for activity in activities:
        activity_id = activity.get("activityId")
        if not activity_id:
            continue

        fit_path = client.download_fit(activity_id, fit_dir)
        if not fit_path:
            continue

        metrics = parse_fit_metrics(fit_path)
        activity.update(metrics)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args()
    load_dotenv()

    credentials = GarminCredentials(
        email=_require_env_var("GARMIN_EMAIL"),
        password=_require_env_var("GARMIN_PASSWORD"),
    )

    client = GarminConnectClient(credentials, session_file=args.session_file)
    client.login()

    activities = client.get_recent_activities(start=0, limit=args.limit)
    filtered = _filter_activities(
        activities, days=args.days, activity_type=args.activity_type
    )

    if args.include_fit:
        _enrich_with_fit(client, filtered, args.fit_dir)

    save_activities_to_csv(filtered, args.csv_path)
    logging.info("Saved %s activities to %s", len(filtered), args.csv_path)


if __name__ == "__main__":
    main()
