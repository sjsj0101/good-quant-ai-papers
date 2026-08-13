"""Strict, JSON-safe contracts for paper suggestion inspection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


RESULT_VERSION = 1
_BASE_FIELDS = frozenset({"title", "authors", "venue", "year", "paper_url"})
_DUPLICATE_STATES = frozenset({"clear", "possible", "duplicate"})


class ResultError(ValueError):
    """Raised when a persisted inspection artifact is malformed."""


def _object(value: object, *, fields: frozenset[str], name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ResultError(f"invalid {name}")
    return value


def _string(value: object, *, name: str, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ResultError(f"invalid {name}")
    return value


def _strings(value: object, *, name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ResultError(f"invalid {name}")
    items: list[str] = []
    for item in value:
        parsed = _string(item, name=name)
        assert parsed is not None
        items.append(parsed)
    return tuple(items)


def _optional_year(value: object) -> int | None:
    if value is None:
        return None
    if type(value) is not int:
        raise ResultError("invalid metadata.year")
    return value


@dataclass(frozen=True)
class Submission:
    paper_url: str

    def to_dict(self) -> dict[str, object]:
        return {"paper_url": self.paper_url}

    @classmethod
    def from_dict(cls, value: object) -> "Submission":
        data = _object(
            value,
            fields=frozenset({"paper_url"}),
            name="submission",
        )
        paper_url = _string(data["paper_url"], name="submission.paper_url")
        assert paper_url is not None
        return cls(paper_url=paper_url)


@dataclass(frozen=True)
class BaseMetadata:
    submitted_url: str
    canonical_url: str | None
    title: str | None
    authors: tuple[str, ...]
    venue: str | None
    year: int | None
    paper_url: str | None
    official_url: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    openreview_id: str | None = None
    track: str | None = None
    subvenue: str | None = None
    presentation: str | None = None
    errors: tuple[str, ...] = ()

    _FIELDS = frozenset(
        {
            "submitted_url",
            "canonical_url",
            "title",
            "authors",
            "venue",
            "year",
            "paper_url",
            "official_url",
            "doi",
            "arxiv_id",
            "openreview_id",
            "track",
            "subvenue",
            "presentation",
            "errors",
        }
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "submitted_url": self.submitted_url,
            "canonical_url": self.canonical_url,
            "title": self.title,
            "authors": list(self.authors),
            "venue": self.venue,
            "year": self.year,
            "paper_url": self.paper_url,
            "official_url": self.official_url,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "openreview_id": self.openreview_id,
            "track": self.track,
            "subvenue": self.subvenue,
            "presentation": self.presentation,
            "errors": list(self.errors),
        }

    @classmethod
    def from_dict(cls, value: object) -> "BaseMetadata":
        data = _object(value, fields=cls._FIELDS, name="metadata")
        submitted_url = _string(
            data["submitted_url"], name="metadata.submitted_url"
        )
        assert submitted_url is not None
        return cls(
            submitted_url=submitted_url,
            canonical_url=_string(
                data["canonical_url"], name="metadata.canonical_url", optional=True
            ),
            title=_string(data["title"], name="metadata.title", optional=True),
            authors=_strings(data["authors"], name="metadata.authors"),
            venue=_string(data["venue"], name="metadata.venue", optional=True),
            year=_optional_year(data["year"]),
            paper_url=_string(
                data["paper_url"], name="metadata.paper_url", optional=True
            ),
            official_url=_string(
                data["official_url"], name="metadata.official_url", optional=True
            ),
            doi=_string(data["doi"], name="metadata.doi", optional=True),
            arxiv_id=_string(
                data["arxiv_id"], name="metadata.arxiv_id", optional=True
            ),
            openreview_id=_string(
                data["openreview_id"], name="metadata.openreview_id", optional=True
            ),
            track=_string(data["track"], name="metadata.track", optional=True),
            subvenue=_string(
                data["subvenue"], name="metadata.subvenue", optional=True
            ),
            presentation=_string(
                data["presentation"], name="metadata.presentation", optional=True
            ),
            errors=_strings(data["errors"], name="metadata.errors"),
        )


@dataclass(frozen=True)
class DuplicateResult:
    status: str
    matching_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {"status": self.status, "matching_ids": list(self.matching_ids)}

    @classmethod
    def from_dict(cls, value: object) -> "DuplicateResult":
        data = _object(
            value,
            fields=frozenset({"status", "matching_ids"}),
            name="duplicate",
        )
        status = _string(data["status"], name="duplicate.status")
        if status not in _DUPLICATE_STATES:
            raise ResultError("invalid duplicate.status")
        assert status is not None
        return cls(
            status=status,
            matching_ids=_strings(
                data["matching_ids"], name="duplicate.matching_ids"
            ),
        )


@dataclass(frozen=True)
class InspectionResult:
    version: int
    submission: Submission
    metadata: BaseMetadata
    missing_fields: tuple[str, ...]
    duplicate: DuplicateResult
    metadata_ready: bool

    _FIELDS = frozenset(
        {
            "version",
            "submission",
            "metadata",
            "missing_fields",
            "duplicate",
            "metadata_ready",
        }
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "submission": self.submission.to_dict(),
            "metadata": self.metadata.to_dict(),
            "missing_fields": list(self.missing_fields),
            "duplicate": self.duplicate.to_dict(),
            "metadata_ready": self.metadata_ready,
        }

    @classmethod
    def from_dict(cls, value: object) -> "InspectionResult":
        data = _object(value, fields=cls._FIELDS, name="inspection result")
        if type(data["version"]) is not int or data["version"] != RESULT_VERSION:
            raise ResultError("unsupported inspection result version")
        if type(data["metadata_ready"]) is not bool:
            raise ResultError("invalid metadata_ready")
        missing_fields = _strings(data["missing_fields"], name="missing_fields")
        if any(field not in _BASE_FIELDS for field in missing_fields):
            raise ResultError("invalid missing_fields")
        return cls(
            version=RESULT_VERSION,
            submission=Submission.from_dict(data["submission"]),
            metadata=BaseMetadata.from_dict(data["metadata"]),
            missing_fields=missing_fields,
            duplicate=DuplicateResult.from_dict(data["duplicate"]),
            metadata_ready=data["metadata_ready"],
        )
