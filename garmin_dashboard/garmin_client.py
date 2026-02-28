from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import logging


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GarminCredentials:
    email: str
    password: str


class GarminConnectClient:
    """Thin wrapper around garminconnect with session persistence and helpers."""

    def __init__(self, credentials: GarminCredentials, session_file: Path) -> None:
        self._credentials = credentials
        self._session_file = session_file
        self._api: Any | None = None

    def login(self) -> None:
        """Authenticate to Garmin Connect.

        Attempts to restore a persisted OAuth session before doing a full login.
        """
        try:
            from garminconnect import Garmin
        except ImportError as exc:  # pragma: no cover - dependency/runtime concern
            raise RuntimeError(
                "garminconnect is required. Install dependencies before running."
            ) from exc

        self._api = Garmin(self._credentials.email, self._credentials.password)

        restored = False
        if self._session_file.exists():
            try:
                import garth

                garth.load(str(self._session_file))
                self._api.login()
                restored = True
                logger.info("Restored Garmin session from %s", self._session_file)
            except Exception as exc:  # pragma: no cover - network/runtime concern
                logger.warning("Unable to restore persisted Garmin session: %s", exc)

        if not restored:
            self._api.login()
            logger.info("Performed fresh Garmin Connect login")

        self._persist_session()

    def _persist_session(self) -> None:
        self._session_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            import garth

            garth.dump(str(self._session_file))
            logger.info("Saved Garmin session to %s", self._session_file)
        except Exception as exc:  # pragma: no cover - runtime concern
            logger.warning("Failed to persist Garmin session: %s", exc)

    @property
    def api(self) -> Any:
        if self._api is None:
            raise RuntimeError("Client is not logged in. Call login() first.")
        return self._api

    def get_recent_activities(self, *, start: int = 0, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieve recent activities from Garmin Connect."""
        activities: Iterable[dict[str, Any]] = self.api.get_activities(start, limit)
        return list(activities)

    def download_fit(self, activity_id: int | str, output_dir: Path) -> Path | None:
        """Download FIT file for an activity if available.

        Returns path to downloaded file, or None when a FIT payload cannot be retrieved.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        fit_bytes = None

        # API compatibility handling for multiple garminconnect versions.
        try:
            fit_bytes = self.api.download_activity(activity_id, dl_fmt="fit")
        except TypeError:
            try:
                from garminconnect import Garmin

                fit_bytes = self.api.download_activity(
                    activity_id, dl_fmt=Garmin.ActivityDownloadFormat.ORIGINAL
                )
            except Exception:
                fit_bytes = None
        except Exception:
            fit_bytes = None

        if not fit_bytes:
            logger.warning("No FIT data available for activity %s", activity_id)
            return None

        out_file = output_dir / f"{activity_id}.fit"
        out_file.write_bytes(fit_bytes)
        return out_file
