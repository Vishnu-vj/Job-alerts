from __future__ import annotations

from typing import List, Tuple

from job_alerts.core.models import JobPosting
from job_alerts.storage.sqlite_store import SqliteStore


def splitNewAndSeen(jobs: List[JobPosting], store: SqliteStore) -> Tuple[List[JobPosting], List[JobPosting]]:
    newJobs: List[JobPosting] = []
    seenJobs: List[JobPosting] = []

    for job in jobs:
        if store.has(job.uniqueKey()):
            seenJobs.append(job)
        else:
            newJobs.append(job)

    return newJobs, seenJobs
