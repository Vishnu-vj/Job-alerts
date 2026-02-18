from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from job_alerts.core.http_client import HttpClient
from job_alerts.core.models import JobPosting, SourceConfig
from job_alerts.connectors.base import BaseConnector


def _extractBoardToken(sourceUrl: str) -> Optional[str]:
    # Accept:
    # - https://job-boards.greenhouse.io/thetradedesk
    # - https://boards.greenhouse.io/thetradedesk
    parsed = urlparse(sourceUrl)
    pathParts = [p for p in parsed.path.split("/") if p]

    if not pathParts:
        return None

    # For both patterns above, token is first path part
    return pathParts[0]


def _parseIsoDatetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    # Greenhouse typically uses ISO8601 like "2026-02-10T..."
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


class GreenhouseConnector(BaseConnector):
    def fetchJobs(self, httpClient: HttpClient, source: SourceConfig) -> List[JobPosting]:
        boardToken = _extractBoardToken(source.url)
        if not boardToken:
            raise ValueError(f"Could not extract Greenhouse board token from url: {source.url}")

        apiUrl = f"https://boards-api.greenhouse.io/v1/boards/{boardToken}/jobs"
        payload = httpClient.getJson(apiUrl)

        if not isinstance(payload, dict) or "jobs" not in payload:
            raise ValueError("Unexpected Greenhouse response shape")

        jobs = payload.get("jobs")
        if not isinstance(jobs, list):
            raise ValueError("Unexpected Greenhouse 'jobs' type")

        results: List[JobPosting] = []
        for item in jobs:
            if not isinstance(item, dict):
                continue

            jobId = str(item.get("id", "")).strip()
            title = str(item.get("title", "")).strip()
            absoluteUrl = str(item.get("absolute_url", "")).strip()

            # location is an object like {"name": "Boston, MA"} in many boards
            locationName = ""
            location = item.get("location")
            if isinstance(location, dict):
                locationName = str(location.get("name", "")).strip()

            updatedAt = _parseIsoDatetime(item.get("updated_at"))
            postedAt = _parseIsoDatetime(item.get("created_at")) or updatedAt

            if not jobId or not title or not absoluteUrl:
                continue

            results.append(
                JobPosting(
                    sourceId=jobId,
                    company=source.company,
                    title=title,
                    location=locationName or "Unknown",
                    url=absoluteUrl,
                    team=None,
                    postedAt=postedAt,
                    raw=item,
                )
            )

        return results
