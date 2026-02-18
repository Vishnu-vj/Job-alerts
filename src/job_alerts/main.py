from __future__ import annotations

import argparse
import os
from typing import List

from dotenv import load_dotenv

from job_alerts.core.config_loader import ConfigError, loadSources
from job_alerts.core.models import SourceConfig


def buildParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="job-alerts", description="Job alerts watcher")
    parser.add_argument(
        "--config",
        default="config/sources.yaml",
        help="Path to sources.yaml",
    )
    parser.add_argument(
        "--only-enabled",
        action="store_true",
        help="Show only enabled sources (default behavior in pipeline)",
    )
    return parser


def showSources(sources: List[SourceConfig], onlyEnabled: bool) -> None:
    selectedSources = [s for s in sources if (s.enabled or not onlyEnabled)]

    if not selectedSources:
        print("No sources found (or none enabled).")
        return

    print(f"Loaded {len(sources)} sources. Selected {len(selectedSources)} sources.\n")
    for source in selectedSources:
        platformText = source.platform or "auto"
        print(f"- {source.company} [{source.id}]")
        print(f"  url: {source.url}")
        print(f"  platform: {platformText}")
        print(f"  enabled: {source.enabled}")
        if source.roleFilter.includeTitleKeywords:
            print(f"  includeTitleKeywords: {source.roleFilter.includeTitleKeywords}")
        if source.roleFilter.excludeTitleKeywords:
            print(f"  excludeTitleKeywords: {source.roleFilter.excludeTitleKeywords}")
        if source.roleFilter.includeLocations:
            print(f"  includeLocations: {source.roleFilter.includeLocations}")
        if source.roleFilter.excludeLocations:
            print(f"  excludeLocations: {source.roleFilter.excludeLocations}")
        print("")


def main() -> None:
    load_dotenv()

    parser = buildParser()
    args = parser.parse_args()

    configPath = args.config
    if not os.path.exists(configPath):
        raise SystemExit(f"Config file not found: {configPath}")

    try:
        sources = loadSources(configPath)
    except ConfigError as error:
        raise SystemExit(f"Config error: {error}") from error

    showSources(sources, onlyEnabled=args.only_enabled)


if __name__ == "__main__":
    main()
