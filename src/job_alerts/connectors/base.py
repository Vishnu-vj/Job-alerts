from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from job_alerts.core.http_client import HttpClient
from job_alerts.core.models import JobPosting, SourceConfig


class BaseConnector(ABC):
    @abstractmethod
    def fetchJobs(self, httpClient: HttpClient, source: SourceConfig) -> List[JobPosting]:
        raise NotImplementedError
