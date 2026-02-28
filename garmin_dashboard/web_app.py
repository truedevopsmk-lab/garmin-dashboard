from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from .analytics import compute_performance_metrics
from .data_store import save_activities_to_csv, save_timeseries_to_csv
from .fit_parser import parse_fit_to_dataframe
from .garmin_client import GarminConnectClient, GarminCredentials
from .main import _filter_activities


def _build_client(email: str, password: str, session_file: Path) -> GarminConnectClient:
    credentials = GarminCredentials(email=email, password=password)
    client = GarminConnectClient(credentials, session_file=session_file)
    client.login()
    return client


def _credentials_form() -> tuple[str, str, Path]:
    st.sidebar.header("Garmin Login")
    email = st.sidebar.text_input("Garmin Email", value="")
    password = st.sidebar.text_input("Garmin Password", value="", type="password")
    session_file = st.sidebar.text_input(
        "Session file", value=".session/garmin_session.json"
    )
    return email, password, Path(session_file)


def render_export(client: GarminConnectClient) -> None:
    st.subheader("Export Activities")
    days = st.number_input("Lookback days", min_value=1, max_value=365, value=14)
    limit = st.number_input("Max activities", min_value=1, max_value=200, value=50)
    activity_type = st.text_input("Activity type", value="running")
    csv_path = Path(st.text_input("CSV output path", value="data/activities.csv"))

    if st.button("Fetch and Export Activities"):
        activities = client.get_recent_activities(start=0, limit=int(limit))
        filtered = _filter_activities(
            activities,
            days=int(days),
            activity_type=activity_type,
        )
        save_activities_to_csv(filtered, csv_path)
        st.success(f"Saved {len(filtered)} activities to {csv_path}")
        st.dataframe(pd.DataFrame(filtered))


def render_analyze(client: GarminConnectClient) -> None:
    st.subheader("Analyze Activity from FIT")
    activity_id = st.number_input("Activity ID", min_value=1, step=1)
    fit_dir = Path(st.text_input("FIT directory", value="data/fit"))
    timeseries_csv = Path(
        st.text_input("Time-series CSV path", value="data/fit/activity_timeseries.csv")
    )

    if st.button("Analyze Activity"):
        fit_path = client.download_fit(int(activity_id), fit_dir)
        if fit_path is None:
            st.error("Unable to download FIT file for this activity.")
            return

        df = parse_fit_to_dataframe(fit_path)
        metrics = compute_performance_metrics(df)
        save_timeseries_to_csv(df, timeseries_csv)

        metric_cols = st.columns(3)
        metric_cols[0].metric("Avg HR", metrics["avg_hr"])
        metric_cols[1].metric("Max HR", metrics["max_hr"])
        metric_cols[2].metric("HR Drift %", metrics["hr_drift_pct"])

        metric_cols = st.columns(3)
        metric_cols[0].metric("Pace / HR Ratio", metrics["pace_hr_ratio"])
        metric_cols[1].metric("Cadence Consistency %", metrics["cadence_consistency_pct"])
        metric_cols[2].metric("Aerobic Decoupling %", metrics["aerobic_decoupling_pct"])

        st.caption(f"FIT file: {fit_path}")
        st.caption(f"Saved time-series CSV: {timeseries_csv}")
        st.dataframe(df)


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="RunStack Garmin Dashboard", layout="wide")
    st.title("RunStack – Garmin Performance Engine")

    email, password, session_file = _credentials_form()
    if not email or not password:
        st.info("Enter Garmin credentials in the sidebar to continue.")
        return

    try:
        client = _build_client(email, password, session_file)
    except Exception as exc:
        st.error(f"Login failed: {exc}")
        return

    tab_export, tab_analyze = st.tabs(["Export", "Analyze"])

    with tab_export:
        render_export(client)

    with tab_analyze:
        render_analyze(client)


if __name__ == "__main__":
    main()
