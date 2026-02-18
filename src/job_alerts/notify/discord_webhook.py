from __future__ import annotations

import os
from typing import List, Optional

import requests

from job_alerts.core.models import JobPosting


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


class DiscordWebhookNotifier:
    def __init__(self, webhookUrl: Optional[str] = None) -> None:
        self.webhookUrl = webhookUrl or os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    def isConfigured(self) -> bool:
        return bool(self.webhookUrl)

    def sendNewJobs(self, jobs: List[JobPosting]) -> None:
        if not jobs:
            return
        if not self.webhookUrl:
            raise RuntimeError("DISCORD_WEBHOOK_URL is not set")

        # Keep messages readable: send one message per job (simple + reliable)
        for job in jobs:
            titleText = _truncate(job.title or "Untitled", 180)
            locationText = _truncate(job.location or "Unknown", 120)

            content = (
                f"**New job posted: {job.company}**\n"
                f"**{titleText}**\n"
                f"{locationText}\n"
                f"{job.url}"
            )

            response = requests.post(self.webhookUrl, json={"content": content}, timeout=15)
            response.raise_for_status()
