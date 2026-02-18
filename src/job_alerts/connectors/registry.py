from __future__ import annotations

from typing import Dict

from job_alerts.connectors.base import BaseConnector
from job_alerts.connectors.greenhouse import GreenhouseConnector


class ConnectorRegistry:
    def __init__(self) -> None:
        self._byName: Dict[str, BaseConnector] = {
            "greenhouse": GreenhouseConnector(),
            # "generic": GenericHtmlConnector(),  # next
            # "lever": LeverConnector(),          # later
            # "workday": WorkdayConnector(),      # later
        }

    def get(self, platform: str) -> BaseConnector:
        platformKey = (platform or "").strip().lower()
        if platformKey not in self._byName:
            raise ValueError(f"Unknown/unimplemented platform connector: {platformKey}")
        return self._byName[platformKey]
