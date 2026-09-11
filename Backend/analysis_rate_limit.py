from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path


DEFAULT_RATE_LIMIT_SECONDS = 60 * 60
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "analysis_rate_limits.db"


class AnalysisRateLimiter:
    def __init__(
        self,
        db_path: str | Path | None = None,
        window_seconds: int | None = None,
    ) -> None:
        configured_path = os.getenv("CAM_RATE_LIMIT_DB")
        self.db_path = Path(db_path or configured_path or DEFAULT_DB_PATH)
        configured_window = os.getenv("CAM_ANALYSIS_RATE_LIMIT_SECONDS")
        self.window_seconds = int(
            window_seconds
            if window_seconds is not None
            else configured_window or DEFAULT_RATE_LIMIT_SECONDS
        )
        self._initialize()

    @property
    def enabled(self) -> bool:
        return self.window_seconds > 0

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=5)
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_rate_limits (
                    client_id TEXT PRIMARY KEY,
                    last_request_at REAL NOT NULL
                )
                """
            )

    def acquire(self, client_id: str, now: float | None = None) -> tuple[bool, int]:
        if not self.enabled:
            return True, 0

        request_time = now if now is not None else time.time()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT last_request_at FROM analysis_rate_limits WHERE client_id = ?",
                (client_id,),
            ).fetchone()

            if row is not None:
                elapsed = request_time - float(row[0])
                if elapsed < self.window_seconds:
                    retry_after = max(1, int(self.window_seconds - elapsed + 0.999))
                    return False, retry_after

            connection.execute(
                """
                INSERT INTO analysis_rate_limits (client_id, last_request_at)
                VALUES (?, ?)
                ON CONFLICT(client_id)
                DO UPDATE SET last_request_at = excluded.last_request_at
                """,
                (client_id, request_time),
            )
            connection.execute(
                "DELETE FROM analysis_rate_limits WHERE last_request_at < ?",
                (request_time - self.window_seconds * 2,),
            )

        return True, 0
