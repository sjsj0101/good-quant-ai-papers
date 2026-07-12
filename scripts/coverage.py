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
COVERAGE_STATUSES = frozenset(
    {"complete", "no-eligible-papers", "pending", "unavailable"}
)
PENDING_TRACK_STATES = frozenset(
    {"source_mapped", "partial", "blocked", "unpublished"}
)
COVERAGE_FIELDS = (
    "venue",
    "year",
    "status",
    "checked_on",
    "eligible_paper_count",
    "tracks_checked",
    "tracks_pending",
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
    allow_empty: bool = False,
) -> bool:
    if not isinstance(value, list) or (not value and not allow_empty):
        requirement = "must be a list" if allow_empty else "must be a non-empty list"
        _error(errors, label, field, requirement)
        return False
    if any(not _non_empty(item) for item in value):
        _error(errors, label, field, "must contain only non-empty strings")
        return False
    if len(value) != len(set(value)):
        _error(errors, label, field, "must not contain duplicate values")
        return False
    return True


def _validate_pending_tracks(
    value: object,
    *,
    label: str,
    checked_tracks: set[str],
    errors: list[str],
) -> set[str]:
    if not isinstance(value, list):
        _error(errors, label, "tracks_pending", "must be a list")
        return set()

    pending_tracks: set[str] = set()
    for item_index, item in enumerate(value):
        item_label = f"tracks_pending[{item_index}]"
        if not isinstance(item, dict):
            _error(errors, label, item_label, "must be a mapping")
            continue

        required = {"track", "state", "note"}
        for field in sorted(required - set(item)):
            _error(errors, label, f"{item_label}.{field}", "required field is missing")
        for field in sorted(set(item) - required, key=str):
            _error(errors, label, f"{item_label}.{field}", "field is not allowed")

        track = item.get("track")
        state = item.get("state")
        note = item.get("note")

        if not isinstance(track, str) or track not in TRACKS:
            choices = ", ".join(sorted(TRACKS))
            _error(
                errors,
                label,
                f"{item_label}.track",
                f"{track!r} is not allowed; choose one of: {choices}",
            )
        elif track in pending_tracks:
            _error(errors, label, f"{item_label}.track", "must not duplicate another pending track")
        elif track in checked_tracks and state != "partial":
            _error(
                errors,
                label,
                f"{item_label}.track",
                "may duplicate tracks_checked only with state 'partial'",
            )
        elif track not in checked_tracks and state == "partial":
            _error(
                errors,
                label,
                f"{item_label}.track",
                "state 'partial' requires the track to also appear in tracks_checked",
            )
        else:
            pending_tracks.add(track)

        if not isinstance(state, str) or state not in PENDING_TRACK_STATES:
            choices = ", ".join(sorted(PENDING_TRACK_STATES))
            _error(
                errors,
                label,
                f"{item_label}.state",
                f"{state!r} is not allowed; choose one of: {choices}",
            )

        if not _non_empty(note):
            _error(errors, label, f"{item_label}.note", "must be a non-empty string")

    return pending_tracks


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

        eligible_count = record.get("eligible_paper_count")
        if type(eligible_count) is not int or eligible_count < 0:
            _error(
                errors,
                label,
                "eligible_paper_count",
                "must be a non-negative integer",
            )

        tracks_valid = _string_list(
            record.get("tracks_checked"),
            label=label,
            field="tracks_checked",
            errors=errors,
            allow_empty=True,
        )
        checked_tracks: set[str] = set()
        if tracks_valid:
            for track in record["tracks_checked"]:
                if track not in TRACKS:
                    _error(errors, label, "tracks_checked", f"unknown track {track!r}")
                else:
                    checked_tracks.add(track)

        if (
            tracks_valid
            and not record.get("tracks_checked")
            and status not in {"pending", "unavailable"}
        ):
            _error(
                errors,
                label,
                "tracks_checked",
                "may be empty only for pending or unavailable coverage",
            )

        _validate_pending_tracks(
            record.get("tracks_pending"),
            label=label,
            checked_tracks=checked_tracks,
            errors=errors,
        )

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
    paper_tracks_by_unit: dict[tuple[int, str], set[str]] = {}
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
        track = paper.get("track")
        if isinstance(track, str):
            paper_tracks_by_unit.setdefault(key, set()).add(track)

    for key, record in valid_rows.items():
        status = record.get("status")
        count = counts[key]
        label = f"{key[0]}-{key[1]}"
        if record.get("eligible_paper_count") != count:
            _error(
                errors,
                label,
                "eligible_paper_count",
                f"must equal cataloged paper count {count}",
            )
        unchecked_paper_tracks = paper_tracks_by_unit.get(key, set()) - set(
            record.get("tracks_checked", [])
        )
        if unchecked_paper_tracks:
            tracks = ", ".join(sorted(unchecked_paper_tracks))
            _error(
                errors,
                label,
                "tracks_checked",
                f"missing cataloged paper track(s): {tracks}",
            )
        if status == "complete" and count == 0:
            _error(errors, label, "status", "complete requires at least one paper")
        if status == "no-eligible-papers" and count != 0:
            _error(
                errors,
                label,
                "status",
                "no-eligible-papers requires zero papers",
            )
        if status == "unavailable" and count != 0:
            _error(errors, label, "status", "unavailable requires zero papers")
    return errors


def validate_coverage_file(path: Path, papers: Sequence[dict]) -> list[str]:
    try:
        records = load_coverage(path)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        return [f"<coverage>: file: could not load {path}: {error}"]
    return validate_coverage(records, papers)
