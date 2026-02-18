from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

import yaml

from job_alerts.core.models import RoleFilter, SourceConfig


class ConfigError(Exception):
    pass


def _requireString(data: Dict[str, Any], key: str) -> str:
    value = data.get(key)
    if value is None or not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Missing/invalid required field: '{key}'")
    return value.strip()


def _optionalString(data: Dict[str, Any], key: str) -> Optional[str]:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigError(f"Invalid field '{key}': must be a string")
    trimmed = value.strip()
    return trimmed if trimmed else None


def _optionalBool(data: Dict[str, Any], key: str, defaultValue: bool) -> bool:
    value = data.get(key)
    if value is None:
        return defaultValue
    if not isinstance(value, bool):
        raise ConfigError(f"Invalid field '{key}': must be a boolean")
    return value


def _listOfStrings(value: Any, fieldName: str) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise ConfigError(f"Invalid '{fieldName}': must be a list of strings")
    return [x.strip() for x in value if x.strip()]


def _parseRoleFilter(data: Dict[str, Any]) -> RoleFilter:
    return RoleFilter(
        includeTitleKeywords=_listOfStrings(data.get("includeTitleKeywords"), "includeTitleKeywords"),
        excludeTitleKeywords=_listOfStrings(data.get("excludeTitleKeywords"), "excludeTitleKeywords"),
        includeLocations=_listOfStrings(data.get("includeLocations"), "includeLocations"),
        excludeLocations=_listOfStrings(data.get("excludeLocations"), "excludeLocations"),
        includeTeams=_listOfStrings(data.get("includeTeams"), "includeTeams"),
        excludeTeams=_listOfStrings(data.get("excludeTeams"), "excludeTeams"),
    )


def loadSources(configPath: str) -> List[SourceConfig]:
    with open(configPath, "r", encoding="utf-8") as fileHandle:
        raw = yaml.safe_load(fileHandle)

    if not isinstance(raw, dict):
        raise ConfigError("config root must be a mapping")

    sources = raw.get("sources")
    if not isinstance(sources, list):
        raise ConfigError("config must contain 'sources' as a list")

    parsed: List[SourceConfig] = []
    seenIds: set[str] = set()

    for index, item in enumerate(sources):
        if not isinstance(item, dict):
            raise ConfigError(f"sources[{index}] must be a mapping/object")

        sourceId = _requireString(item, "id")
        if sourceId in seenIds:
            raise ConfigError(f"Duplicate source id: {sourceId}")
        seenIds.add(sourceId)

        company = _requireString(item, "company")
        url = _requireString(item, "url")

        platform = _optionalString(item, "platform")
        enabled = _optionalBool(item, "enabled", True)

        roleFilterRaw = item.get("roleFilter") or {}
        if not isinstance(roleFilterRaw, dict):
            raise ConfigError(f"sources[{index}].roleFilter must be an object")

        parsed.append(
            SourceConfig(
                id=sourceId,
                company=company,
                url=url,
                platform=platform,
                enabled=enabled,
                roleFilter=_parseRoleFilter(roleFilterRaw),
            )
        )

    return parsed


def dumpExample(source: SourceConfig) -> Dict[str, Any]:
    # useful for debugging; not required for runtime
    return asdict(source)
