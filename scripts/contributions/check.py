"""Check base-metadata readiness and duplicates without judging paper scope."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from urllib.parse import urlsplit, urlunsplit

from scripts.catalog import VENUES

from .models import (
    RESULT_VERSION,
    BaseMetadata,
    DuplicateResult,
    InspectionResult,
    Submission,
)


BASE_FIELDS = ("title", "authors", "venue", "year", "paper_url")
_IDENTIFIER_FIELDS = ("doi", "openreview_id", "arxiv_id")
_URL_FIELDS = ("canonical_url", "official_url", "paper_url")
_POSSIBLE_TITLE_RATIO = 0.96
_POSSIBLE_TITLE_MIN_TOKENS = 6


def normalize_title(value: str) -> str:
    """Return a Unicode- and punctuation-insensitive title key."""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"[^\W_]+", normalized, flags=re.UNICODE))


def _valid_https_url(value: object) -> bool:
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        return False
    try:
        parsed = urlsplit(value)
        parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme.casefold() == "https"
        and parsed.hostname is not None
        and parsed.username is None
        and parsed.password is None
    )


def missing_base_fields(metadata: BaseMetadata) -> tuple[str, ...]:
    """List unusable required bibliographic fields in stable display order."""

    missing: list[str] = []
    if not isinstance(metadata.title, str) or not metadata.title.strip():
        missing.append("title")
    if (
        not isinstance(metadata.authors, tuple)
        or not metadata.authors
        or any(not isinstance(author, str) or not author.strip() for author in metadata.authors)
    ):
        missing.append("authors")
    if metadata.venue not in VENUES:
        missing.append("venue")
    if type(metadata.year) is not int or metadata.year not in range(2024, 2027):
        missing.append("year")
    if not _valid_https_url(metadata.paper_url):
        missing.append("paper_url")
    return tuple(missing)


def _identifier(field: str, value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().casefold()
    if field == "doi":
        normalized = re.sub(r"^(?:doi:\s*|https?://doi\.org/)", "", normalized)
    elif field == "arxiv_id":
        normalized = re.sub(r"v\d+$", "", normalized)
    return normalized or None


def _normalized_url(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except ValueError:
        return None
    if not parsed.scheme or not parsed.hostname:
        return None
    host = parsed.hostname.casefold()
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    netloc = host
    if port is not None and not (
        parsed.scheme.casefold() == "https" and port == 443
    ):
        netloc += f":{port}"
    return urlunsplit(
        (
            parsed.scheme.casefold(),
            netloc,
            parsed.path or "/",
            parsed.query,
            "",
        )
    )


def _record_id(record: dict) -> str | None:
    value = record.get("id")
    return value if isinstance(value, str) and value.strip() else None


def _exact_match(metadata: BaseMetadata, record: dict) -> bool:
    for field in _IDENTIFIER_FIELDS:
        candidate = _identifier(field, getattr(metadata, field))
        existing = _identifier(field, record.get(field))
        if candidate is not None and existing is not None and candidate == existing:
            return True
    candidate_urls = {
        normalized
        for field in _URL_FIELDS
        if (normalized := _normalized_url(getattr(metadata, field))) is not None
    }
    record_urls = {
        normalized
        for field in ("official_url", "paper_url")
        if (normalized := _normalized_url(record.get(field))) is not None
    }
    if candidate_urls & record_urls:
        return True
    candidate_title = normalize_title(metadata.title or "")
    existing_title = record.get("title")
    return (
        bool(candidate_title)
        and isinstance(existing_title, str)
        and candidate_title == normalize_title(existing_title)
    )


def _possible_title_match(metadata: BaseMetadata, record: dict) -> bool:
    candidate = normalize_title(metadata.title or "")
    existing_value = record.get("title")
    if not isinstance(existing_value, str):
        return False
    existing = normalize_title(existing_value)
    if (
        len(candidate.split()) < _POSSIBLE_TITLE_MIN_TOKENS
        or len(existing.split()) < _POSSIBLE_TITLE_MIN_TOKENS
    ):
        return False
    return SequenceMatcher(None, candidate, existing).ratio() >= _POSSIBLE_TITLE_RATIO


def check_duplicates(
    metadata: BaseMetadata,
    records: list[dict],
) -> DuplicateResult:
    """Return exact or conservative title matches against the current catalog."""

    exact_ids = tuple(
        record_id
        for record in records
        if _exact_match(metadata, record)
        if (record_id := _record_id(record)) is not None
    )
    if exact_ids:
        return DuplicateResult("duplicate", tuple(dict.fromkeys(exact_ids)))
    possible_ids = tuple(
        record_id
        for record in records
        if _possible_title_match(metadata, record)
        if (record_id := _record_id(record)) is not None
    )
    if possible_ids:
        return DuplicateResult("possible", tuple(dict.fromkeys(possible_ids)))
    return DuplicateResult("clear")


def inspect_submission(
    submission: Submission,
    metadata: BaseMetadata,
    records: list[dict],
) -> InspectionResult:
    """Build the deterministic result used by both GitHub workflows."""

    missing = missing_base_fields(metadata)
    duplicate = check_duplicates(metadata, records)
    return InspectionResult(
        version=RESULT_VERSION,
        submission=submission,
        metadata=metadata,
        missing_fields=missing,
        duplicate=duplicate,
        metadata_ready=not missing and duplicate.status != "duplicate",
    )
