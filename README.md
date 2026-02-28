# RunStack – Garmin Performance Engine

Python CLI + analytics engine on top of Garmin Connect.

## Features

- Garmin Connect authentication via `garminconnect`
- Environment variable credentials (`GARMIN_EMAIL`, `GARMIN_PASSWORD`) with `.env` support
- Session persistence via `garth` token dump/load to reduce repeated full logins
- Activity export pipeline to CSV (`export` mode, and default mode)
- FIT download + parsing pipeline for full time-series fields:
  - `timestamp`
  - `heart_rate`
  - `cadence`
  - `distance`
  - `speed`
  - `altitude`
- Performance analytics (`analyze` mode):
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
└── main.py
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Update `.env` with your Garmin credentials.

## Usage

### 1) Export recent activity summaries (existing behavior)

```bash
garmin-dashboard --days 7 --limit 10 --activity-type running --csv-path data/activities.csv
```

Equivalent explicit subcommand:

```bash
garmin-dashboard export --days 7 --limit 10 --activity-type running --csv-path data/activities.csv
```

### 2) Analyze one activity from FIT data

```bash
garmin-dashboard analyze --activity-id 21989714581
```

This will:

1. Download FIT to `data/fit/<activity_id>.fit`
2. Parse record-level FIT metrics
3. Compute performance analytics
4. Print a summary
5. Save parsed time-series CSV to `data/fit/<activity_id>_timeseries.csv`

## Notes

- Session cache defaults to `.session/garmin_session.json`.
- Garmin scraping endpoints may vary; FIT files are the authoritative source for full time-series data.
- This project uses the unofficial Garmin Connect flow, not Garmin Health API.
