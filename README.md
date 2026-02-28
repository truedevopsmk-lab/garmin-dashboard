# Garmin Dashboard Exporter

Python project that logs into Garmin Connect, fetches recent run/workout activities, and exports them to CSV. It can also optionally download and parse FIT files for extra metrics (heart rate/cadence).

## Features

- Garmin Connect authentication via `garminconnect`
- Environment variable credentials (`GARMIN_EMAIL`, `GARMIN_PASSWORD`)
- Session persistence via `garth` token dump/load to reduce repeated full logins
- Modular code layout:
  - `garmin_dashboard/garmin_client.py`
  - `garmin_dashboard/data_store.py`
  - `garmin_dashboard/main.py`
- Optional FIT parsing with `fitparse`

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Update `.env` with your Garmin credentials.

## Usage

```bash
garmin-dashboard --days 14 --limit 50 --activity-type running --csv-path data/activities.csv
```

### Include FIT metrics

```bash
garmin-dashboard --include-fit --fit-dir data/fit --csv-path data/activities_with_fit.csv
```

## Notes

- Session data is stored at `.session/garmin_session.json` by default.
- FIT download behavior can vary by Garmin activity type and API compatibility.
