"""Validate the EDITH-backed finance-journal AI watchlist."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml


VALID_VENUES = {
    "JF": "The Journal of Finance",
    "JFE": "Journal of Financial Economics",
    "RFS": "The Review of Financial Studies",
}
VALID_PRIORITIES = {"core", "core_caution", "secondary", "context"}
VALID_YEAR_SOURCES = {"edith_local_db"}
VALID_METADATA_QUALITY = {"year_needs_review"}

REQUIRED_PAPER_FIELDS = {
    "id",
    "edith_paper_id",
    "title",
    "authors",
    "venue",
    "journal_name",
    "year",
    "year_source",
    "field",
    "priority",
    "topics",
    "methods",
    "methodology_type",
    "keywords",
}
OPTIONAL_PAPER_FIELDS = {"doi", "metadata_quality"}
TOPIC_VALUE_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


def load_watchlist(path: Path) -> dict[str, Any]:
    """Load *path* as YAML and return the watchlist mapping."""

    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a YAML mapping")
    return data


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normal_date(value: Any) -> bool:
    return isinstance(value, date) or _is_non_empty_string(value)


def _normal_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _validate_string_list(
    paper_id: str, field: str, value: Any, errors: list[str], *, slug: bool = False
) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{paper_id}: {field}: expected a non-empty list")
        return
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not _is_non_empty_string(item):
            errors.append(f"{paper_id}: {field}[{index}]: expected a non-empty string")
            continue
        if item in seen:
            errors.append(f"{paper_id}: {field}: duplicate value {item!r}")
        seen.add(item)
        if slug and not TOPIC_VALUE_RE.match(item):
            errors.append(
                f"{paper_id}: {field}[{index}]: expected lowercase snake_case, got {item!r}"
            )


def validate_watchlist(data: dict[str, Any]) -> list[str]:
    """Return validation errors for a finance-journal AI watchlist mapping."""

    errors: list[str] = []
    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("source: expected a mapping")
    else:
        if not _is_non_empty_string(source.get("name")):
            errors.append("source.name: expected a non-empty string")
        if not _normal_date(source.get("checked_on")):
            errors.append("source.checked_on: expected an ISO date or date string")
        if not _is_non_empty_string(source.get("search_scope")):
            errors.append("source.search_scope: expected a non-empty string")
        _validate_string_list("source", "search_methods", source.get("search_methods"), errors)
        _validate_string_list("source", "notes", source.get("notes"), errors)

        journals = source.get("journals")
        if not isinstance(journals, list) or not journals:
            errors.append("source.journals: expected a non-empty list")
        else:
            seen_codes: set[str] = set()
            for index, journal in enumerate(journals):
                prefix = f"source.journals[{index}]"
                if not isinstance(journal, dict):
                    errors.append(f"{prefix}: expected a mapping")
                    continue
                code = journal.get("code")
                if code not in VALID_VENUES:
                    errors.append(f"{prefix}.code: expected one of {sorted(VALID_VENUES)}")
                    continue
                if code in seen_codes:
                    errors.append(f"{prefix}.code: duplicate code {code!r}")
                seen_codes.add(code)
                if journal.get("name") != VALID_VENUES[code]:
                    errors.append(f"{prefix}.name: does not match venue code {code}")
                if not isinstance(journal.get("local_records"), int) or journal[
                    "local_records"
                ] <= 0:
                    errors.append(f"{prefix}.local_records: expected positive integer")
                if not _is_non_empty_string(journal.get("local_year_range")):
                    errors.append(f"{prefix}.local_year_range: expected non-empty string")

    papers = data.get("papers")
    if not isinstance(papers, list) or not papers:
        return errors + ["papers: expected a non-empty list"]

    seen_ids: set[str] = set()
    seen_edith_ids: set[int] = set()
    seen_titles: set[str] = set()
    seen_dois: set[str] = set()
    for index, paper in enumerate(papers):
        fallback_id = f"papers[{index}]"
        if not isinstance(paper, dict):
            errors.append(f"{fallback_id}: expected a mapping")
            continue
        paper_id = paper.get("id", fallback_id)
        if not _is_non_empty_string(paper_id):
            errors.append(f"{fallback_id}: id: expected a non-empty string")
            paper_id = fallback_id

        missing = REQUIRED_PAPER_FIELDS - set(paper)
        for field in sorted(missing):
            errors.append(f"{paper_id}: {field}: required")
        unexpected = set(paper) - REQUIRED_PAPER_FIELDS - OPTIONAL_PAPER_FIELDS
        for field in sorted(unexpected):
            errors.append(f"{paper_id}: {field}: unexpected field")

        venue = paper.get("venue")
        if venue not in VALID_VENUES:
            errors.append(f"{paper_id}: venue: expected one of {sorted(VALID_VENUES)}")
        elif paper.get("journal_name") != VALID_VENUES[venue]:
            errors.append(f"{paper_id}: journal_name: does not match venue {venue}")

        if _is_non_empty_string(paper_id) and isinstance(venue, str):
            expected_prefix = f"edith-{venue.lower()}-"
            if not paper_id.startswith(expected_prefix):
                errors.append(f"{paper_id}: id: expected prefix {expected_prefix!r}")
        if paper_id in seen_ids:
            errors.append(f"{paper_id}: id: duplicate")
        seen_ids.add(paper_id)

        edith_paper_id = paper.get("edith_paper_id")
        if not isinstance(edith_paper_id, int) or edith_paper_id <= 0:
            errors.append(f"{paper_id}: edith_paper_id: expected positive integer")
        elif edith_paper_id in seen_edith_ids:
            errors.append(f"{paper_id}: edith_paper_id: duplicate")
        else:
            seen_edith_ids.add(edith_paper_id)

        title = paper.get("title")
        if not _is_non_empty_string(title):
            errors.append(f"{paper_id}: title: expected a non-empty string")
        else:
            normalized = _normal_title(title)
            if normalized in seen_titles:
                errors.append(f"{paper_id}: title: duplicate normalized title")
            seen_titles.add(normalized)

        _validate_string_list(paper_id, "authors", paper.get("authors"), errors)
        _validate_string_list(paper_id, "topics", paper.get("topics"), errors, slug=True)
        _validate_string_list(paper_id, "methods", paper.get("methods"), errors, slug=True)

        if not isinstance(paper.get("year"), int):
            errors.append(f"{paper_id}: year: expected integer EDITH local year")
        if paper.get("year_source") not in VALID_YEAR_SOURCES:
            errors.append(
                f"{paper_id}: year_source: expected one of {sorted(VALID_YEAR_SOURCES)}"
            )
        if paper.get("priority") not in VALID_PRIORITIES:
            errors.append(
                f"{paper_id}: priority: expected one of {sorted(VALID_PRIORITIES)}"
            )
        for field in ("field", "methodology_type", "keywords"):
            if not _is_non_empty_string(paper.get(field)):
                errors.append(f"{paper_id}: {field}: expected a non-empty string")

        doi = paper.get("doi")
        if doi is not None:
            if not _is_non_empty_string(doi):
                errors.append(f"{paper_id}: doi: expected a non-empty string")
            elif doi in seen_dois:
                errors.append(f"{paper_id}: doi: duplicate")
            else:
                seen_dois.add(doi)

        metadata_quality = paper.get("metadata_quality")
        if metadata_quality is not None and metadata_quality not in VALID_METADATA_QUALITY:
            errors.append(
                f"{paper_id}: metadata_quality: expected one of "
                f"{sorted(VALID_METADATA_QUALITY)}"
            )

    return errors


def validate_watchlist_file(path: Path) -> list[str]:
    """Return validation errors for the watchlist file at *path*."""

    try:
        data = load_watchlist(path)
    except Exception as exc:  # pragma: no cover - exercised by CLI users.
        return [str(exc)]
    return validate_watchlist(data)
