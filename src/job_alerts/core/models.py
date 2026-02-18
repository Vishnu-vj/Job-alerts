from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RoleFilter:
    includeTitleKeywords: List[str] = field(default_factory=list)
    excludeTitleKeywords: List[str] = field(default_factory=list)

    includeLocations: List[str] = field(default_factory=list)
    excludeLocations: List[str] = field(default_factory=list)

    includeTeams: List[str] = field(default_factory=list)
    excludeTeams: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourceConfig:
    id: str
    company: str
    url: str
    platform: Optional[str] = None  # "greenhouse", "lever", "workday", "generic"
    enabled: bool = True
    roleFilter: RoleFilter = field(default_factory=RoleFilter)


@dataclass(frozen=True)
class JobPosting:
    sourceId: str            # stable id from ATS if possible
    company: str
    title: str
    location: str
    url: str

    team: Optional[str] = None
    postedAt: Optional[datetime] = None

    firstSeenAt: datetime = field(default_factory=lambda: datetime.utcnow())

    # extra metadata (safe place for raw fields)
    raw: Dict[str, Any] = field(default_factory=dict)

    def uniqueKey(self) -> str:
        # must be stable: company + sourceId is enough if sourceId is ATS stable
        return f"{self.company}::{self.sourceId}"
