"""Render one safe, managed Issue report for a paper suggestion."""

from __future__ import annotations

import html

from .models import DuplicateResult, InspectionResult


REPORT_MARKER = "<!-- paper-suggestion-report:v1 -->"
MACHINE_STATES = frozenset({"metadata-ready", "needs-metadata", "duplicate"})
_PROBLEM_MESSAGES = {
    "invalid-form": "The Issue Form structure is invalid. Please reopen the paper suggestion form.",
    "invalid-url": "Paper URL must contain exactly one HTTPS link without credentials or a fragment.",
    "scope-not-acknowledged": "The scope acknowledgement must be checked.",
    "unsupported-source": "The link is not a recognized paper source. Use OpenReview, arXiv, DOI, or a supported official conference page.",
    "invalid-source-url": "The recognized source link does not contain a usable paper identifier.",
    "source-unavailable": "The paper source is temporarily unavailable. Edit or reopen the Issue to retry.",
    "unsafe-address": "The paper source did not resolve to a public network address.",
    "response-too-large": "The source response is too large for metadata extraction.",
    "too-many-redirects": "The source used too many redirects.",
    "invalid-redirect": "The source returned an invalid redirect.",
    "upstream-http-error": "The paper source returned an HTTP error.",
    "invalid-response": "The paper source returned metadata in an unsupported format.",
    "metadata-unavailable": "The paper source did not provide usable bibliographic metadata.",
}


class ReportError(ValueError):
    """Raised when a report cannot be rendered from safe public values."""


def _plain(value: object) -> str:
    text = " ".join(str(value).replace("\r", " ").replace("\n", " ").split())
    text = html.escape(text, quote=False)
    for character in ("\\", "`", "*", "_", "[", "]", "|", "<", ">"):
        text = text.replace(character, f"\\{character}")
    return (
        text.replace("@", "@\u200b")
        .replace("https://", "https:\u200b//")
        .replace("http://", "http:\u200b//")
        .replace("~", "~\u200b")
    )


def _destination(url: str) -> str:
    return url.replace("<", "%3C").replace(">", "%3E")


def _link(label: str, url: str | None) -> str:
    if not url:
        return "—"
    return f"[{_plain(label)}](<{_destination(url)}>)"


def state_label(result: InspectionResult) -> str:
    """Return exactly one automation-owned Issue state."""

    if result.duplicate.status == "duplicate":
        return "duplicate"
    return "metadata-ready" if result.metadata_ready else "needs-metadata"


def _fact_rows(result: InspectionResult) -> list[str]:
    metadata = result.metadata
    authors = ", ".join(metadata.authors) if metadata.authors else "—"
    return [
        "| Field | Extracted value |",
        "| --- | --- |",
        f"| Title | {_plain(metadata.title or '—')} |",
        f"| Authors | {_plain(authors)} |",
        f"| Conference | {_plain(metadata.venue or '—')} |",
        f"| Year | {_plain(metadata.year if metadata.year is not None else '—')} |",
        f"| Submitted link | {_link('Open submitted link', metadata.submitted_url)} |",
        f"| Canonical link | {_link('Open canonical link', metadata.canonical_url)} |",
        f"| Paper link | {_link('Open paper link', metadata.paper_url)} |",
        f"| DOI | {_plain(metadata.doi or '—')} |",
        f"| arXiv ID | {_plain(metadata.arxiv_id or '—')} |",
        f"| OpenReview ID | {_plain(metadata.openreview_id or '—')} |",
    ]


def _duplicate_section(duplicate: DuplicateResult) -> list[str]:
    if duplicate.status == "clear":
        return ["## Duplicate check", "", "No catalog match found."]
    ids = ", ".join(_plain(value) for value in duplicate.matching_ids)
    if duplicate.status == "possible":
        return [
            "## Duplicate check",
            "",
            f"Possible title match requiring maintainer review: {ids}.",
        ]
    return ["## Duplicate check", "", f"Exact catalog match: {ids}."]


def _next_action(result: InspectionResult) -> str:
    if result.duplicate.status == "duplicate":
        return "No PR will be created because this paper already exists in the catalog."
    if result.missing_fields:
        fields = ", ".join(_plain(field) for field in result.missing_fields)
        return f"Missing base fields: {fields}. Edit the link or resolve the metadata before approval."
    possible = (
        " Resolve the possible title match before proceeding."
        if result.duplicate.status == "possible"
        else ""
    )
    return (
        "Maintainer review: confirm quantitative-finance or asset-management scope, "
        "target conference, track, and acceptance; then apply `approved`." + possible
    )


def render_report(result: InspectionResult) -> str:
    """Render extracted facts without automated scope or acceptance claims."""

    lines = [
        REPORT_MARKER,
        "## Paper metadata check",
        "",
        *_fact_rows(result),
        "",
        *_duplicate_section(result.duplicate),
        "",
    ]
    if result.metadata.errors:
        lines.extend(
            [
                "## Source status",
                "",
                ", ".join(_plain(code) for code in result.metadata.errors),
                "",
            ]
        )
    lines.extend(["## Next action", "", _next_action(result), ""])
    return "\n".join(lines)


def render_problem_report(code: str) -> str:
    """Render a form-level failure from an allowlisted safe error code."""

    message = _PROBLEM_MESSAGES.get(code)
    if message is None:
        raise ReportError("invalid-problem-code")
    return "\n".join(
        (
            REPORT_MARKER,
            "## Paper metadata check",
            "",
            message,
            "",
            "## Next action",
            "",
            "Correct the Issue Form and save the Issue to run metadata extraction again.",
            "",
        )
    )
