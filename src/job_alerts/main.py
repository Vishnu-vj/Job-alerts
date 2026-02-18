from __future__ import annotations

import argparse
import os
from typing import List

from dotenv import load_dotenv

from job_alerts.connectors.registry import ConnectorRegistry
from job_alerts.core.config_loader import ConfigError, loadSources
from job_alerts.core.diff_engine import splitNewAndSeen
from job_alerts.core.filter_engine import filterJobs
from job_alerts.core.http_client import HttpClient, HttpConfig
from job_alerts.core.models import JobPosting, SourceConfig
from job_alerts.notify.discord_webhook import DiscordWebhookNotifier
from job_alerts.storage.sqlite_store import SqliteStore, SqliteStoreConfig


def buildParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="job-alerts", description="Job alerts watcher")
    parser.add_argument("--config", default="config/sources.yaml", help="Path to sources.yaml")
    parser.add_argument("--only-enabled", action="store_true", help="Use only enabled sources")
    parser.add_argument("--dry-run", action="store_true", help="Do not send Discord notifications")
    parser.add_argument("--state-db", default="state/state.sqlite", help="SQLite path for seen jobs")
    parser.add_argument("--max-preview", type=int, default=5, help="Preview max new jobs per source")
    return parser


def selectSources(sources: List[SourceConfig], onlyEnabled: bool) -> List[SourceConfig]:
    return [s for s in sources if (s.enabled or not onlyEnabled)]


def main() -> None:
    load_dotenv()

    args = buildParser().parse_args()

    if not os.path.exists(args.config):
        raise SystemExit(f"Config file not found: {args.config}")

    try:
        sources = loadSources(args.config)
    except ConfigError as error:
        raise SystemExit(f"Config error: {error}") from error

    chosenSources = selectSources(sources, onlyEnabled=args.only_enabled)
    if not chosenSources:
        print("No sources selected.")
        return

    httpClient = HttpClient(HttpConfig())
    registry = ConnectorRegistry()
    store = SqliteStore(SqliteStoreConfig(dbPath=args.state_db))
    notifier = DiscordWebhookNotifier()

    print(f"Loaded {len(sources)} sources. Selected {len(chosenSources)} sources.")

    if not args.dry_run and not notifier.isConfigured():
        print("DISCORD_WEBHOOK_URL not set. Run with --dry-run or set the env var.")
        return

    totalNew = 0

    for source in chosenSources:
        platform = (source.platform or "").strip().lower()
        if not platform:
            print(f"\nSkipping {source.company} [{source.id}] — platform is not set (auto-detect later).")
            continue

        try:
            connector = registry.get(platform)
        except Exception:
            print(f"\nSkipping {source.company} [{source.id}] — connector not implemented: {platform}")
            continue

        try:
            fetchedJobs = connector.fetchJobs(httpClient=httpClient, source=source)
            matchedJobs = filterJobs(fetchedJobs, source.roleFilter)

            newJobs, _ = splitNewAndSeen(matchedJobs, store)
            totalNew += len(newJobs)

            print(f"\n{source.company} [{source.id}]")
            print(f"  fetched: {len(fetchedJobs)}  matched: {len(matchedJobs)}  new: {len(newJobs)}")

            # Persist first, so re-runs don't double-alert if Discord errors mid-way
            store.markSeen(newJobs)

            previewCount = min(len(newJobs), args.max_preview)
            for job in newJobs[:previewCount]:
                print(f"  + {job.title} ({job.location})")
                print(f"    {job.url}")

            if newJobs and not args.dry_run:
                notifier.sendNewJobs(newJobs)

        except Exception as error:
            print(f"\nError processing {source.company} [{source.id}]: {error}")

    store.close()
    print(f"\nDone. Total new jobs this run: {totalNew}")


if __name__ == "__main__":
    main()
