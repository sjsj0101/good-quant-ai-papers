"""Parse GitHub's rendered paper-suggestion Issue Form body."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from .models import Submission


_REQUIRED_HEADINGS = ("Paper URL", "Scope acknowledgement")
_HEADING_RE = re.compile(r"^###\s+(.+?)\s*$", flags=re.MULTILINE)
_URL_RE = re.compile(r"https://[^\s<>]+")
_CHECKED_RE = re.compile(r"^\s*-\s*\[[xX]\]\s+\S", flags=re.MULTILINE)


class SubmissionError(ValueError):
    """A stable, public-safe Issue Form error."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _sections(body: str) -> dict[str, str]:
    matches = list(_HEADING_RE.finditer(body))
    counts = {
        heading: sum(match.group(1) == heading for match in matches)
        for heading in _REQUIRED_HEADINGS
    }
    if any(count != 1 for count in counts.values()):
        raise SubmissionError("invalid-form")
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group(1)] = body[start:end].strip()
    return sections


def _paper_url(raw: str) -> str:
    urls = _URL_RE.findall(raw)
    if len(urls) != 1 or raw != urls[0]:
        raise SubmissionError("invalid-url")
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as error:
        raise SubmissionError("invalid-url") from None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or port is not None and not 1 <= port <= 65535
    ):
        raise SubmissionError("invalid-url")
    return raw


def parse_issue_form(body: str) -> Submission:
    """Return the one submitted HTTPS URL from a stable Issue Form body."""

    if not isinstance(body, str):
        raise SubmissionError("invalid-form")
    sections = _sections(body)
    if _CHECKED_RE.search(sections["Scope acknowledgement"]) is None:
        raise SubmissionError("scope-not-acknowledged")
    return Submission(paper_url=_paper_url(sections["Paper URL"]))
