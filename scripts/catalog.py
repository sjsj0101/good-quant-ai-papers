"""Load and validate the YAML paper catalog."""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import yaml


REQUIRED_FIELDS = (
    "id",
    "title",
    "authors",
    "venue",
    "year",
    "track",
    "presentation",
    "official_url",
    "paper_url",
    "topics",
    "summary",
    "why_it_matters",
    "status",
    "verified_on",
)

VENUES = frozenset(
    {
        "ICML",
        "NeurIPS",
        "ICLR",
        "KDD",
        "AAAI",
        "IJCAI",
        "WWW",
        "WSDM",
        "SIGIR",
        "AISTATS",
        "ACM ICAIF",
    }
)
TRACKS = frozenset({"main", "workshop", "position", "affinity"})
PRESENTATIONS = frozenset({"oral", "spotlight", "poster", "not-specified"})
STATUSES = frozenset({"accepted", "published"})
TOPICS = frozenset(
    {
        "asset-allocation",
        "portfolio-optimization",
        "alpha-modeling",
        "financial-forecasting",
        "factor-investing",
        "risk-management",
        "market-regimes",
        "market-microstructure",
        "execution",
        "derivatives",
        "market-simulation",
        "synthetic-data",
        "alternative-data",
        "financial-agents",
        "evaluation",
    }
)
ASSET_CLASSES = frozenset(
    {
        "equities",
        "fixed-income",
        "derivatives",
        "FX",
        "commodities",
        "crypto",
        "multi-asset",
    }
)
DATA_FREQUENCIES = frozenset(
    {"tick", "intraday", "daily", "weekly", "monthly", "mixed", "not-applicable"}
)

OPTIONAL_STRING_FIELDS = frozenset(
    {"arxiv_id", "openreview_id", "doi", "notes"}
)
URL_FIELDS = ("official_url", "paper_url", "code_url", "project_url")
OPTIONAL_LIST_FIELDS = frozenset({"tasks", "methods", "datasets"})
ALLOWED_FIELDS = (
    frozenset(REQUIRED_FIELDS)
    | OPTIONAL_STRING_FIELDS
    | frozenset({"code_url", "project_url", "asset_classes", "data_frequency"})
    | OPTIONAL_LIST_FIELDS
)

_ID_PATTERN = re.compile(r"^[0-9]{4}-[a-z0-9]+(?:-[a-z0-9]+){2,}$")
_DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_INVALID_PERCENT_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")


class _CatalogLoader(yaml.SafeLoader):
    """Safe YAML loader that preserves dates and rejects duplicate keys."""

    def construct_mapping(
        self, node: yaml.MappingNode, deep: bool = False
    ) -> dict:
        self.flatten_mapping(node)
        seen: dict[object, yaml.error.Mark] = {}
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                first_mark = seen.get(key)
            except TypeError:
                continue
            if first_mark is not None:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    (
                        f"found duplicate key {key!r}; first occurrence is at "
                        f"line {first_mark.line + 1}, column {first_mark.column + 1}"
                    ),
                    key_node.start_mark,
                )
            seen[key] = key_node.start_mark
        return super().construct_mapping(node, deep=deep)


_CatalogLoader.yaml_implicit_resolvers = {
    key: [
        resolver
        for resolver in resolvers
        if resolver[0] != "tag:yaml.org,2002:timestamp"
    ]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_catalog(path: Path) -> list[dict]:
    """Load records from a YAML catalog at *path*.

    Dates remain ISO-formatted strings so the in-memory representation matches
    the public JSON Schema rather than PyYAML's implicit ``date`` conversion.
    """

    with path.open("r", encoding="utf-8") as stream:
        records = yaml.load(stream, Loader=_CatalogLoader)
    if not isinstance(records, list):
        raise ValueError("catalog root must be a YAML list")
    return records


def _record_label(record: object, index: int) -> str:
    if isinstance(record, dict):
        record_id = record.get("id")
        if isinstance(record_id, str) and record_id.strip():
            return record_id
    return f"<record {index + 1}>"


def _add_error(errors: list[str], record_id: str, field: str, message: str) -> None:
    errors.append(f"{record_id}: {field}: {message}")


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_string_list(
    value: object,
    *,
    record_id: str,
    field: str,
    errors: list[str],
) -> bool:
    if not isinstance(value, list) or not value:
        _add_error(errors, record_id, field, "must be a non-empty list")
        return False
    if any(not _is_non_empty_string(item) for item in value):
        _add_error(errors, record_id, field, "must contain only non-empty strings")
        return False
    if len(value) != len(set(value)):
        _add_error(errors, record_id, field, "must not contain duplicate values")
        return False
    return True


def _validate_enum(
    value: object,
    *,
    record_id: str,
    field: str,
    allowed: frozenset[str],
    errors: list[str],
) -> None:
    if not isinstance(value, str) or value not in allowed:
        choices = ", ".join(sorted(allowed))
        _add_error(
            errors,
            record_id,
            field,
            f"{value!r} is not allowed; choose one of: {choices}",
        )


def _is_http_url(value: object) -> bool:
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        return False
    if _INVALID_PERCENT_ESCAPE.search(value):
        return False
    try:
        parsed = urlsplit(value)
        if parsed.netloc.endswith(":"):
            return False
        _ = parsed.port  # Access validates an explicitly supplied port.
        return parsed.scheme.lower() in {"http", "https"} and bool(parsed.hostname)
    except ValueError:
        return False


def _normalized_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"[^\W_]+", normalized, flags=re.UNICODE))


def _venue_slug(venue: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", venue.casefold()))


def _validate_record(record: dict, index: int, errors: list[str]) -> str:
    record_id = _record_label(record, index)

    for field in REQUIRED_FIELDS:
        if field not in record:
            _add_error(errors, record_id, field, "required field is missing")

    for field in sorted(set(record) - ALLOWED_FIELDS, key=str):
        _add_error(errors, record_id, str(field), "field is not allowed")

    for field in (
        "id",
        "title",
        "venue",
        "track",
        "presentation",
        "summary",
        "why_it_matters",
        "status",
        "verified_on",
    ):
        if field in record and not _is_non_empty_string(record[field]):
            _add_error(errors, record_id, field, "must be a non-empty string")

    year = record.get("year")
    if "year" in record and type(year) is not int:
        _add_error(errors, record_id, "year", "must be an integer")

    if "authors" in record:
        _validate_string_list(
            record["authors"], record_id=record_id, field="authors", errors=errors
        )

    topics_valid = False
    if "topics" in record:
        topics_valid = _validate_string_list(
            record["topics"], record_id=record_id, field="topics", errors=errors
        )
    if topics_valid:
        for topic in record["topics"]:
            if topic not in TOPICS:
                _validate_enum(
                    topic,
                    record_id=record_id,
                    field="topics",
                    allowed=TOPICS,
                    errors=errors,
                )

    for field, allowed in (
        ("venue", VENUES),
        ("track", TRACKS),
        ("presentation", PRESENTATIONS),
        ("status", STATUSES),
    ):
        if field in record and _is_non_empty_string(record[field]):
            _validate_enum(
                record[field],
                record_id=record_id,
                field=field,
                allowed=allowed,
                errors=errors,
            )

    if "data_frequency" in record:
        _validate_enum(
            record["data_frequency"],
            record_id=record_id,
            field="data_frequency",
            allowed=DATA_FREQUENCIES,
            errors=errors,
        )

    for field in URL_FIELDS:
        if field in record and not _is_http_url(record[field]):
            _add_error(errors, record_id, field, "must be an absolute HTTP(S) URL")

    verified_on = record.get("verified_on")
    if _is_non_empty_string(verified_on):
        try:
            if not _DATE_PATTERN.fullmatch(verified_on):
                raise ValueError
            date.fromisoformat(verified_on)
        except ValueError:
            _add_error(
                errors,
                record_id,
                "verified_on",
                "must be a valid ISO date in YYYY-MM-DD format",
            )

    stable_id = record.get("id")
    if _is_non_empty_string(stable_id):
        if not _ID_PATTERN.fullmatch(stable_id):
            _add_error(
                errors,
                record_id,
                "id",
                "must be a lowercase slug shaped as <year>-<venue>-<first-author>-<short-title>",
            )
        elif type(year) is int and _is_non_empty_string(record.get("venue")):
            expected_prefix = f"{year}-{_venue_slug(record['venue'])}-"
            if not stable_id.startswith(expected_prefix):
                _add_error(
                    errors,
                    record_id,
                    "id",
                    f"must start with {expected_prefix!r} to match year and venue",
                )

    for field in sorted(OPTIONAL_STRING_FIELDS):
        if field in record and not _is_non_empty_string(record[field]):
            _add_error(errors, record_id, field, "must be a non-empty string")

    for field in sorted(OPTIONAL_LIST_FIELDS):
        if field in record:
            _validate_string_list(
                record[field], record_id=record_id, field=field, errors=errors
            )

    if "asset_classes" in record:
        assets_valid = _validate_string_list(
            record["asset_classes"],
            record_id=record_id,
            field="asset_classes",
            errors=errors,
        )
        if assets_valid:
            for asset_class in record["asset_classes"]:
                if asset_class not in ASSET_CLASSES:
                    _validate_enum(
                        asset_class,
                        record_id=record_id,
                        field="asset_classes",
                        allowed=ASSET_CLASSES,
                        errors=errors,
                    )

    return record_id


def validate_catalog(records: list[dict]) -> list[str]:
    """Return deterministic, human-readable validation errors for *records*."""

    errors: list[str] = []
    if not isinstance(records, list):
        return ["<catalog>: records: must be a list"]

    seen: dict[str, dict[object, str]] = {
        "id": {},
        "title": {},
        "official_url": {},
        "paper_url": {},
    }

    for index, record in enumerate(records):
        record_id = _record_label(record, index)
        if not isinstance(record, dict):
            _add_error(errors, record_id, "record", "must be a mapping")
            continue

        record_id = _validate_record(record, index, errors)
        duplicate_values = {
            "id": record.get("id") if _is_non_empty_string(record.get("id")) else None,
            "title": (
                _normalized_title(record["title"])
                if _is_non_empty_string(record.get("title"))
                else None
            ),
            "official_url": (
                record.get("official_url")
                if _is_non_empty_string(record.get("official_url"))
                else None
            ),
            "paper_url": (
                record.get("paper_url")
                if _is_non_empty_string(record.get("paper_url"))
                else None
            ),
        }
        for field, value in duplicate_values.items():
            if value is None or value == "":
                continue
            first_record_id = seen[field].get(value)
            if first_record_id is not None:
                _add_error(
                    errors,
                    record_id,
                    field,
                    f"duplicate value already used by {first_record_id}",
                )
            else:
                seen[field][value] = record_id

    return errors


def validate_file(path: Path) -> list[str]:
    """Load and validate *path*, returning file-level errors when loading fails."""

    try:
        records = load_catalog(path)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        return [f"<catalog>: file: could not load {path}: {error}"]
    return validate_catalog(records)
