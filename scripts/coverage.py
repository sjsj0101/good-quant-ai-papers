"""Validate the 2024–2026 venue coverage ledger."""

from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Sequence

import yaml

if __package__:
    from .catalog import (
        HTTP_URL_PATTERN,
        TRACKS,
        VENUE_ORDER,
        VENUES,
        load_yaml_list,
    )
else:
    from catalog import (
        HTTP_URL_PATTERN,
        TRACKS,
        VENUE_ORDER,
        VENUES,
        load_yaml_list,
    )


COVERAGE_YEARS = (2024, 2025, 2026)
COVERAGE_STATUSES = frozenset({"complete", "no-eligible-papers", "pending"})
COVERAGE_FIELDS = (
    "venue",
    "year",
    "status",
    "checked_on",
    "tracks_checked",
    "official_sources",
    "notes",
)
_HTTP_URL_RE = re.compile(HTTP_URL_PATTERN)
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def _label(record: object, index: int) -> str:
    if isinstance(record, dict):
        venue = record.get("venue")
        year = record.get("year")
        if isinstance(venue, str) and type(year) is int:
            return f"{year}-{venue}"
    return f"<coverage {index + 1}>"


def _non_empty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _error(errors: list[str], label: str, field: str, message: str) -> None:
    errors.append(f"{label}: {field}: {message}")


def _string_list(
    value: object,
    *,
    label: str,
    field: str,
    errors: list[str],
) -> bool:
    if not isinstance(value, list) or not value:
        _error(errors, label, field, "must be a non-empty list")
        return False
    if any(not _non_empty(item) for item in value):
        _error(errors, label, field, "must contain only non-empty strings")
        return False
    if len(value) != len(set(value)):
        _error(errors, label, field, "must not contain duplicate values")
        return False
    return True


def load_coverage(path: Path) -> list[dict]:
    return load_yaml_list(path, "coverage")


def validate_coverage(records: list[dict], papers: Sequence[dict]) -> list[str]:
    """Validate record shape, exact matrix coverage, and paper-count consistency."""
    if not isinstance(records, list):
        return ["<coverage>: records: must be a list"]

    errors: list[str] = []
    expected = {
        (year, venue) for year in COVERAGE_YEARS for venue in VENUE_ORDER
    }
    seen: dict[tuple[int, str], str] = {}
    valid_rows: dict[tuple[int, str], dict] = {}

    for index, record in enumerate(records):
        label = _label(record, index)
        if not isinstance(record, dict):
            _error(errors, label, "record", "must be a mapping")
            continue
        for field in COVERAGE_FIELDS:
            if field not in record:
                _error(errors, label, field, "required field is missing")
        for field in sorted(set(record) - set(COVERAGE_FIELDS), key=str):
            _error(errors, label, str(field), "field is not allowed")

        venue = record.get("venue")
        year = record.get("year")
        status = record.get("status")
        if not isinstance(venue, str) or venue not in VENUES:
            _error(errors, label, "venue", f"{venue!r} is not allowed")
        if type(year) is not int or year not in COVERAGE_YEARS:
            _error(errors, label, "year", f"must be one of {COVERAGE_YEARS}")
        if not isinstance(status, str) or status not in COVERAGE_STATUSES:
            choices = ", ".join(sorted(COVERAGE_STATUSES))
            _error(errors, label, "status", f"choose one of: {choices}")

        checked_on = record.get("checked_on")
        if not _non_empty(checked_on):
            _error(errors, label, "checked_on", "must be a non-empty string")
        else:
            try:
                if not _DATE_RE.fullmatch(checked_on):
                    raise ValueError
                date.fromisoformat(checked_on)
            except ValueError:
                _error(errors, label, "checked_on", "must be a valid ISO date")

        if _string_list(
            record.get("tracks_checked"),
            label=label,
            field="tracks_checked",
            errors=errors,
        ):
            for track in record["tracks_checked"]:
                if track not in TRACKS:
                    _error(errors, label, "tracks_checked", f"unknown track {track!r}")

        if _string_list(
            record.get("official_sources"),
            label=label,
            field="official_sources",
            errors=errors,
        ):
            for source in record["official_sources"]:
                if _HTTP_URL_RE.fullmatch(source) is None:
                    _error(
                        errors,
                        label,
                        "official_sources",
                        f"invalid HTTP(S) URL {source!r}",
                    )

        if not _non_empty(record.get("notes")):
            _error(errors, label, "notes", "must be a non-empty string")

        if type(year) is int and isinstance(venue, str):
            key = (year, venue)
            first = seen.get(key)
            if first is not None:
                _error(errors, label, "unit", f"duplicate coverage unit; first is {first}")
            else:
                seen[key] = label
                if key in expected:
                    valid_rows[key] = record

    for year in COVERAGE_YEARS:
        for venue in VENUE_ORDER:
            if (year, venue) not in seen:
                _error(
                    errors,
                    "<coverage>",
                    "unit",
                    f"missing coverage unit: {venue} {year}",
                )

    counts: Counter[tuple[int, str]] = Counter()
    for paper in papers:
        if not isinstance(paper, dict):
            continue
        year = paper.get("year")
        venue = paper.get("venue")
        paper_id = paper.get("id", "<paper>")
        if type(year) is not int or not isinstance(venue, str):
            _error(errors, str(paper_id), "coverage", "has no coverage unit")
            continue
        key = (year, venue)
        if key not in expected:
            _error(errors, str(paper_id), "coverage", "has no coverage unit")
            continue
        counts[key] += 1

    for key, record in valid_rows.items():
        status = record.get("status")
        count = counts[key]
        label = f"{key[0]}-{key[1]}"
        if status == "complete" and count == 0:
            _error(errors, label, "status", "complete requires at least one paper")
        if status == "no-eligible-papers" and count != 0:
            _error(
                errors,
                label,
                "status",
                "no-eligible-papers requires zero papers",
            )
    return errors


def validate_coverage_file(path: Path, papers: Sequence[dict]) -> list[str]:
    try:
        records = load_coverage(path)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        return [f"<coverage>: file: could not load {path}: {error}"]
    return validate_coverage(records, papers)
