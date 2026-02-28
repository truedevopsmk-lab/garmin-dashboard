# RunStack – Garmin Performance Engine

RunStack includes both:

- a CLI for export/analyze workflows
- a Streamlit web application for interactive use

## Features

- Garmin Connect authentication via `garminconnect`
- Environment variable credentials (`GARMIN_EMAIL`, `GARMIN_PASSWORD`) with `.env` support
- Session persistence via `garth` token dump/load to reduce repeated full logins
- Activity export pipeline to CSV
- FIT download + parsing pipeline for full time-series fields:
  - `timestamp`
  - `heart_rate`
  - `cadence`
  - `distance`
  - `speed`
  - `altitude`
- Performance analytics:
  - Average HR
  - Max HR
  - HR drift (first half vs second half)
  - Pace vs HR ratio
  - Cadence consistency
  - Aerobic decoupling

## Project Structure

```text
garmin_dashboard/
├── analytics.py
├── data_store.py
├── fit_parser.py
├── garmin_client.py
├── main.py
└── web_app.py
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Update `.env` with your Garmin credentials.

## CLI Usage

### Export recent activity summaries

```bash
garmin-dashboard --days 7 --limit 10 --activity-type running --csv-path data/activities.csv
```

Equivalent explicit subcommand:

```bash
garmin-dashboard export --days 7 --limit 10 --activity-type running --csv-path data/activities.csv
```

### Analyze one activity from FIT data

```bash
garmin-dashboard analyze --activity-id 21989714581
```

This downloads FIT, parses time-series metrics, computes analytics, and saves the parsed CSV.

## Web App Usage

### Option A: console script

```bash
garmin-dashboard-web
```

### Option B: streamlit directly

```bash
streamlit run garmin_dashboard/web_app.py
```

In the app:

1. Enter Garmin credentials in the sidebar.
2. Use the **Export** tab to fetch/filter and save activity CSV.
3. Use the **Analyze** tab to download FIT, compute metrics, and save time-series CSV.

## Notes

- Session cache defaults to `.session/garmin_session.json`.
- Garmin scraping endpoints may vary; FIT files are the authoritative source for full time-series data.
- This project uses the unofficial Garmin Connect flow, not Garmin Health API.
