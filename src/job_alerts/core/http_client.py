from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass(frozen=True)
class HttpConfig:
    timeoutSeconds: float = 20.0
    maxRetries: int = 3
    minDelaySeconds: float = 0.2
    maxDelaySeconds: float = 0.6
    userAgent: str = (
        "JobAlertsBot/0.1 (+local; respectful polling; contact: none)"
    )


class HttpClient:
    def __init__(self, config: Optional[HttpConfig] = None) -> None:
        self.config = config or HttpConfig()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.userAgent})

    def getText(self, url: str, headers: Optional[Dict[str, str]] = None) -> str:
        response = self._get(url, headers=headers)
        return response.text

    def getJson(self, url: str, headers: Optional[Dict[str, str]] = None) -> Any:
        response = self._get(url, headers=headers)
        return response.json()

    def _get(self, url: str, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        lastError: Optional[Exception] = None

        for attempt in range(self.config.maxRetries + 1):
            # polite jitter between requests
            time.sleep(random.uniform(self.config.minDelaySeconds, self.config.maxDelaySeconds))

            try:
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=self.config.timeoutSeconds,
                )

                # retry on transient server errors / rate limit
                if response.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(
                        f"Transient HTTP {response.status_code} for {url}",
                        response=response,
                    )

                response.raise_for_status()
                return response

            except Exception as error:
                lastError = error
                if attempt < self.config.maxRetries:
                    backoffSeconds = (2 ** attempt) * 0.8 + random.uniform(0, 0.4)
                    time.sleep(backoffSeconds)
                else:
                    break

        raise RuntimeError(f"HTTP GET failed after retries for {url}: {lastError}")
