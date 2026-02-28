from __future__ import annotations

import argparse
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .analytics import compute_performance_metrics
from .data_store import save_activities_to_csv, save_timeseries_to_csv
from .fit_parser import parse_fit_to_dataframe
from .garmin_client import GarminConnectClient, GarminCredentials


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch Garmin Connect activities and export them to CSV"
    )
    parser.add_argument(
        "--session-file",
        type=Path,
        default=Path(".session/garmin_session.json"),
        help="Path for persisted Garmin login session",
    )

    subparsers = parser.add_subparsers(dest="command")

    export_parser = subparsers.add_parser(
        "export", help="Export recent Garmin activities to CSV"
    )
    _add_export_arguments(export_parser)

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Download FIT for one activity, parse time-series, and compute analytics",
    )
    analyze_parser.add_argument(
        "--activity-id", type=int, required=True, help="Garmin activity ID to analyze"
    )
    analyze_parser.add_argument(
        "--fit-dir",
        type=Path,
        default=Path("data/fit"),
        help="Directory to store downloaded FIT files",
    )
    analyze_parser.add_argument(
        "--timeseries-csv-path",
        type=Path,
        default=None,
        help="Optional path for parsed FIT time-series CSV",
    )

    _add_export_arguments(parser)

    return parser


def _add_export_arguments(parser: argparse.ArgumentParser) -> None:
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


def _require_env_var(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _build_client(session_file: Path) -> GarminConnectClient:
    credentials = GarminCredentials(
        email=_require_env_var("GARMIN_EMAIL"),
        password=_require_env_var("GARMIN_PASSWORD"),
    )
    client = GarminConnectClient(credentials, session_file=session_file)
    client.login()
    return client


def _filter_activities(
    activities: list[dict[str, Any]], *, days: int, activity_type: str
) -> list[dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    filtered: list[dict[str, Any]] = []
    for item in activities:
        type_key = (item.get("activityType") or {}).get("typeKey", "")
        if type_key != activity_type:
            continue

        start_raw = item.get("startTimeLocal")
        if isinstance(start_raw, str):
            try:
                start_dt = datetime.fromisoformat(start_raw.replace(" ", "T"))
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            except ValueError:
                start_dt = cutoff
        else:
            start_dt = cutoff

        if start_dt >= cutoff:
            filtered.append(item)

    return filtered


def run_export(args: argparse.Namespace) -> None:
    client = _build_client(args.session_file)
    activities = client.get_recent_activities(start=0, limit=args.limit)
    filtered = _filter_activities(
        activities, days=args.days, activity_type=args.activity_type
    )
    save_activities_to_csv(filtered, args.csv_path)
    logging.info("Saved %s activities to %s", len(filtered), args.csv_path)


def run_analyze(args: argparse.Namespace) -> None:
    client = _build_client(args.session_file)

    fit_path = client.download_fit(args.activity_id, args.fit_dir)
    if fit_path is None:
        raise RuntimeError(f"Could not download FIT data for activity {args.activity_id}")

    df = parse_fit_to_dataframe(fit_path)
    metrics = compute_performance_metrics(df)

    timeseries_path = args.timeseries_csv_path
    if timeseries_path is None:
        timeseries_path = args.fit_dir / f"{args.activity_id}_timeseries.csv"

    save_timeseries_to_csv(df, timeseries_path)

    print(f"Activity ID: {args.activity_id}")
    print(f"Avg HR: {metrics['avg_hr']}")
    print(f"Max HR: {metrics['max_hr']}")
    print(f"HR Drift: {metrics['hr_drift_pct']}%")
    print(f"Pace/HR Ratio: {metrics['pace_hr_ratio']}")
    print(f"Cadence Stability: {metrics['cadence_consistency_pct']}%")
    print(f"Aerobic Decoupling: {metrics['aerobic_decoupling_pct']}%")
    print(f"Saved time-series CSV: {timeseries_path}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        run_analyze(args)
        return

    run_export(args)


if __name__ == "__main__":
    main()
