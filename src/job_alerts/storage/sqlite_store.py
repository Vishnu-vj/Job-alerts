from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from job_alerts.core.models import JobPosting


@dataclass(frozen=True)
class SqliteStoreConfig:
    dbPath: str = "state/state.sqlite"


class SqliteStore:
    def __init__(self, config: Optional[SqliteStoreConfig] = None) -> None:
        self.config = config or SqliteStoreConfig()
        os.makedirs(os.path.dirname(self.config.dbPath), exist_ok=True)
        self.connection = sqlite3.connect(self.config.dbPath)
        self.connection.execute("PRAGMA journal_mode=WAL;")
        self._ensureSchema()

    def _ensureSchema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_jobs (
              unique_key TEXT PRIMARY KEY,
              company TEXT NOT NULL,
              source_id TEXT NOT NULL,
              title TEXT NOT NULL,
              location TEXT NOT NULL,
              url TEXT NOT NULL,
              first_seen_at TEXT NOT NULL,
              last_seen_at TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def has(self, uniqueKey: str) -> bool:
        cursor = self.connection.execute(
            "SELECT 1 FROM seen_jobs WHERE unique_key = ? LIMIT 1;",
            (uniqueKey,),
        )
        row = cursor.fetchone()
        return row is not None

    def markSeen(self, jobs: Iterable[JobPosting]) -> None:
        nowText = datetime.utcnow().isoformat()

        self.connection.executemany(
            """
            INSERT INTO seen_jobs (
              unique_key, company, source_id, title, location, url, first_seen_at, last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(unique_key) DO UPDATE SET
              title = excluded.title,
              location = excluded.location,
              url = excluded.url,
              last_seen_at = excluded.last_seen_at;
            """,
            [
                (
                    job.uniqueKey(),
                    job.company,
                    job.sourceId,
                    job.title,
                    job.location,
                    job.url,
                    job.firstSeenAt.isoformat(),
                    nowText,
                )
                for job in jobs
            ],
        )
        self.connection.commit()

    def close(self) -> None:
        try:
            self.connection.close()
        except Exception:
            pass
