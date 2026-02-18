from __future__ import annotations

from typing import List

from job_alerts.core.models import JobPosting, RoleFilter


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def _matchesAny(text: str, keywords: List[str]) -> bool:
    haystack = _normalize(text)
    for keyword in keywords:
        needle = _normalize(keyword)
        if needle and needle in haystack:
            return True
    return False


def _passesInclude(text: str, includeKeywords: List[str]) -> bool:
    if not includeKeywords:
        return True
    return _matchesAny(text, includeKeywords)


def _passesExclude(text: str, excludeKeywords: List[str]) -> bool:
    if not excludeKeywords:
        return True
    return not _matchesAny(text, excludeKeywords)


def filterJobs(jobs: List[JobPosting], roleFilter: RoleFilter) -> List[JobPosting]:
    filtered: List[JobPosting] = []

    for job in jobs:
        titleText = job.title or ""
        locationText = job.location or ""
        teamText = job.team or ""

        if not _passesInclude(titleText, roleFilter.includeTitleKeywords):
            continue
        if not _passesExclude(titleText, roleFilter.excludeTitleKeywords):
            continue

        if not _passesInclude(locationText, roleFilter.includeLocations):
            continue
        if not _passesExclude(locationText, roleFilter.excludeLocations):
            continue

        if not _passesInclude(teamText, roleFilter.includeTeams):
            continue
        if not _passesExclude(teamText, roleFilter.excludeTeams):
            continue

        filtered.append(job)

    return filtered
