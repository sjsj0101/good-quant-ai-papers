"""Create a reviewable partial catalog record from approved base metadata."""

from __future__ import annotations

import os
import re
import tempfile
import unicodedata
from pathlib import Path

import yaml

from scripts.catalog import REQUIRED_FIELDS, load_catalog

from .check import check_duplicates, missing_base_fields
from .models import InspectionResult


PARTIAL_FIELD_ORDER = (
    "id",
    "title",
    "authors",
    "venue",
    "year",
    "track",
    "subvenue",
    "presentation",
    "official_url",
    "paper_url",
    "arxiv_id",
    "openreview_id",
    "doi",
)
_ID_RE = re.compile(r"^[0-9]{4}-[a-z0-9]+(?:-[a-z0-9]+){2,}$")
_BRANCH_RE = re.compile(r"^contrib/issue-[1-9][0-9]*-[a-z0-9]+(?:-[a-z0-9]+)+$")


class MaterializeError(ValueError):
    """Raised when a partial record must not be written."""


def _slug(value: str, *, fallback: str, limit: int) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").casefold()
    tokens = re.findall(r"[a-z0-9]+", ascii_text)[:limit]
    return "-".join(tokens) or fallback


def _record_id(result: InspectionResult) -> str:
    metadata = result.metadata
    assert metadata.year is not None
    assert metadata.venue is not None
    assert metadata.title is not None
    author = metadata.authors[0]
    venue = _slug(metadata.venue, fallback="venue", limit=3)
    first_author = _slug(author, fallback="author", limit=3)
    title = _slug(metadata.title, fallback="paper", limit=6)
    record_id = f"{metadata.year}-{venue}-{first_author}-{title}"
    if _ID_RE.fullmatch(record_id) is None:
        raise MaterializeError("invalid-record-id")
    return record_id


def _validate_result(result: InspectionResult) -> None:
    missing = missing_base_fields(result.metadata)
    expected_ready = not missing and result.duplicate.status != "duplicate"
    if (
        missing
        or result.missing_fields != missing
        or result.metadata_ready is not expected_ready
        or result.duplicate.status == "duplicate"
        or result.metadata.errors
    ):
        raise MaterializeError("metadata-not-ready")
    for match in result.duplicate.matching_ids:
        if _ID_RE.fullmatch(match) is None:
            raise MaterializeError("invalid-duplicate-id")


def partial_record(result: InspectionResult) -> dict[str, object]:
    """Return only source-backed base fields; never invent schema placeholders."""

    _validate_result(result)
    metadata = result.metadata
    values: dict[str, object] = {
        "id": _record_id(result),
        "title": metadata.title,
        "authors": list(metadata.authors),
        "venue": metadata.venue,
        "year": metadata.year,
        "track": metadata.track,
        "subvenue": metadata.subvenue,
        "presentation": metadata.presentation,
        "official_url": metadata.official_url,
        "paper_url": metadata.paper_url,
        "arxiv_id": metadata.arxiv_id,
        "openreview_id": metadata.openreview_id,
        "doi": metadata.doi,
    }
    return {
        field: values[field]
        for field in PARTIAL_FIELD_ORDER
        if values.get(field) is not None
    }


def append_partial_record(path: Path, result: InspectionResult) -> str:
    """Recheck the current catalog and append one YAML list item safely."""

    record = partial_record(result)
    record_id = record["id"]
    assert isinstance(record_id, str)
    try:
        records = load_catalog(path)
        original = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError):
        raise MaterializeError("invalid-catalog") from None
    current_duplicate = check_duplicates(result.metadata, records)
    if current_duplicate.status == "duplicate":
        raise MaterializeError("duplicate")
    if any(isinstance(item, dict) and item.get("id") == record_id for item in records):
        raise MaterializeError("id-collision")
    snippet = yaml.safe_dump(
        [record],
        sort_keys=False,
        allow_unicode=True,
        width=1000,
    ).rstrip() + "\n"
    candidate = snippet if not records else original.rstrip() + "\n\n" + snippet
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(candidate)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            parsed = load_catalog(temporary)
        except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError):
            raise MaterializeError("invalid-candidate") from None
        if len(parsed) != len(records) + 1 or parsed[-1] != record:
            raise MaterializeError("invalid-candidate")
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return record_id


def branch_name(issue_number: int, record_id: str) -> str:
    """Return the only branch shape the workflow may pass to git or gh."""

    if type(issue_number) is not int or issue_number <= 0 or _ID_RE.fullmatch(record_id) is None:
        raise MaterializeError("invalid-branch-input")
    value = f"contrib/issue-{issue_number}-{record_id}"[:180].rstrip("-")
    if _BRANCH_RE.fullmatch(value) is None:
        raise MaterializeError("invalid-branch")
    return value


def render_pr_body(issue_number: int, result: InspectionResult) -> str:
    """Explain the intentionally partial record and the unchanged merge gates."""

    record = partial_record(result)
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    possible = list(result.duplicate.matching_ids)
    lines = [
        "## Partial paper record",
        "",
        f"Source: Issue #{issue_number}",
        f"Record ID: `{record['id']}`",
        "",
        "This draft contains source-backed base bibliographic metadata only. "
        "A maintainer must complete the catalog record before merge.",
        "",
    ]
    if possible:
        lines.extend(
            [
                "Possible duplicate matches requiring review: "
                + ", ".join(f"`{value}`" for value in possible),
                "",
            ]
        )
    lines.extend(
        [
            "## Maintainer completion checklist",
            "",
            "- [ ] Confirm quantitative-finance or asset-management scope.",
            "- [ ] Confirm target conference, year, track, presentation, and acceptance.",
            "- [ ] Complete missing required fields: "
            + ", ".join(f"`{field}`" for field in missing)
            + ".",
            "- [ ] Add controlled topics and original editorial prose; do not copy the abstract.",
            "- [ ] Regenerate README, paper, and topic pages.",
            "",
            "```bash",
            "python3 scripts/validate.py",
            "python3 scripts/render.py",
            "python3 scripts/render.py --check",
            "python3 -m unittest discover -s tests -v",
            "git diff --check",
            "```",
            "",
        ]
    )
    return "\n".join(lines)
