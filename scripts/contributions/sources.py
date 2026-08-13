"""Extract base bibliographic metadata from a small set of paper sources."""

from __future__ import annotations

import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Protocol
from urllib.parse import parse_qs, quote, unquote, urlsplit

from scripts.catalog import VENUES

from .http import HttpResponse, SafeFetcher, SourceError, validated_https_url
from .models import BaseMetadata


ALLOWED_SOURCE_HOSTS = frozenset(
    {
        "openreview.net",
        "api.openreview.net",
        "api2.openreview.net",
        "arxiv.org",
        "export.arxiv.org",
        "doi.org",
        "api.crossref.org",
        "icml.cc",
        "neurips.cc",
        "iclr.cc",
        "kdd.org",
        "aaai.org",
        "ijcai.org",
        "thewebconf.org",
        "wsdm-conference.org",
        "sigir.org",
        "aistats.org",
        "icaif.org",
    }
)
_OFFICIAL_HOSTS = ALLOWED_SOURCE_HOSTS - frozenset(
    {
        "openreview.net",
        "api.openreview.net",
        "api2.openreview.net",
        "arxiv.org",
        "export.arxiv.org",
        "doi.org",
        "api.crossref.org",
    }
)
_VENUE_ALIASES = (
    ("international conference on machine learning", "ICML"),
    ("advances in neural information processing systems", "NeurIPS"),
    ("neural information processing systems", "NeurIPS"),
    ("international conference on learning representations", "ICLR"),
    ("knowledge discovery and data mining", "KDD"),
    ("association for the advancement of artificial intelligence", "AAAI"),
    ("international joint conference on artificial intelligence", "IJCAI"),
    ("international world wide web conference", "WWW"),
    ("the web conference", "WWW"),
    ("web search and data mining", "WSDM"),
    ("information retrieval", "SIGIR"),
    ("artificial intelligence and statistics", "AISTATS"),
    ("international conference on ai in finance", "ACM ICAIF"),
    ("acm icaif", "ACM ICAIF"),
    ("neurips", "NeurIPS"),
    ("aistats", "AISTATS"),
    ("sigir", "SIGIR"),
    ("ijcai", "IJCAI"),
    ("aaai", "AAAI"),
    ("icml", "ICML"),
    ("iclr", "ICLR"),
    ("wsdm", "WSDM"),
    ("icaif", "ACM ICAIF"),
    ("kdd", "KDD"),
)
_YEAR_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
_ARXIV_ID_RE = re.compile(r"(?:[a-z-]+(?:\.[A-Z]{2})?/\d{7}|\d{4}\.\d{4,5})(?:v\d+)?$", re.I)


class Fetcher(Protocol):
    def get(self, url: str, *, accepted_hosts: frozenset[str]) -> HttpResponse:
        ...


def _clean(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.replace("\r", " ").replace("\n", " ").split())
    return text or None


def _openreview_value(value: object) -> object:
    if isinstance(value, dict) and set(value) >= {"value"}:
        return value["value"]
    return value


def _authors(value: object) -> tuple[str, ...]:
    value = _openreview_value(value)
    if not isinstance(value, list):
        return ()
    cleaned = tuple(filter(None, (_clean(item) for item in value)))
    return tuple(dict.fromkeys(cleaned))


def _controlled_venue(value: object) -> str | None:
    text = _clean(value)
    if text is None:
        return None
    normalized = unicodedata.normalize("NFKC", text).casefold()
    for alias, venue in _VENUE_ALIASES:
        if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", normalized):
            if venue not in VENUES:
                raise SourceError("invalid-venue-map")
            return venue
    return None


def _year(*values: object) -> int | None:
    for value in values:
        text = _clean(value)
        if text:
            match = _YEAR_RE.search(text)
            if match:
                return int(match.group(1))
    return None


def _json_object(body: bytes) -> dict[str, object]:
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise SourceError("invalid-response") from None
    if not isinstance(value, dict):
        raise SourceError("invalid-response")
    return value


def _from_openreview(url: str, fetcher: Fetcher) -> BaseMetadata:
    parsed = urlsplit(url)
    ids = parse_qs(parsed.query, strict_parsing=False).get("id", [])
    if len(ids) != 1 or not ids[0].strip():
        raise SourceError("invalid-source-url")
    note_id = ids[0].strip()
    api_url = f"https://api2.openreview.net/notes?id={quote(note_id, safe='')}"
    response = fetcher.get(api_url, accepted_hosts=ALLOWED_SOURCE_HOSTS)
    payload = _json_object(response.body)
    notes = payload.get("notes")
    if not isinstance(notes, list) or len(notes) != 1 or not isinstance(notes[0], dict):
        raise SourceError("metadata-unavailable")
    note = notes[0]
    content = note.get("content")
    if not isinstance(content, dict):
        content = {}
    title = _clean(_openreview_value(content.get("title")))
    author_names = _authors(content.get("authors"))
    venue_text = _openreview_value(content.get("venue"))
    canonical = f"https://openreview.net/forum?id={quote(note_id, safe='')}"
    return BaseMetadata(
        submitted_url=url,
        canonical_url=canonical,
        title=title,
        authors=author_names,
        venue=_controlled_venue(venue_text),
        year=_year(venue_text),
        paper_url=canonical,
        official_url=canonical,
        openreview_id=note_id,
    )


def _from_arxiv(url: str, fetcher: Fetcher) -> BaseMetadata:
    raw_id = unquote(urlsplit(url).path.removeprefix("/abs/")).strip("/")
    if not _ARXIV_ID_RE.fullmatch(raw_id):
        raise SourceError("invalid-source-url")
    arxiv_id = re.sub(r"v\d+$", "", raw_id, flags=re.I)
    api_url = f"https://export.arxiv.org/api/query?id_list={quote(arxiv_id, safe='')}"
    response = fetcher.get(api_url, accepted_hosts=ALLOWED_SOURCE_HOSTS)
    try:
        root = ET.fromstring(response.body)
    except ET.ParseError:
        raise SourceError("invalid-response") from None
    atom = "{http://www.w3.org/2005/Atom}"
    arxiv = "{http://arxiv.org/schemas/atom}"
    entry = root.find(f"{atom}entry")
    if entry is None:
        raise SourceError("metadata-unavailable")
    author_names = tuple(
        name
        for author in entry.findall(f"{atom}author")
        if (name := _clean(author.findtext(f"{atom}name"))) is not None
    )
    journal_ref = _clean(entry.findtext(f"{arxiv}journal_ref"))
    published = _clean(entry.findtext(f"{atom}published"))
    canonical = f"https://arxiv.org/abs/{arxiv_id}"
    return BaseMetadata(
        submitted_url=url,
        canonical_url=canonical,
        title=_clean(entry.findtext(f"{atom}title")),
        authors=tuple(dict.fromkeys(author_names)),
        venue=_controlled_venue(journal_ref),
        year=_year(journal_ref, published),
        paper_url=canonical,
        doi=_clean(entry.findtext(f"{arxiv}doi")),
        arxiv_id=arxiv_id,
    )


def _crossref_authors(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    result: list[str] = []
    for author in value:
        if not isinstance(author, dict):
            continue
        literal = _clean(author.get("name"))
        if literal is None:
            literal = _clean(
                " ".join(
                    part
                    for part in (_clean(author.get("given")), _clean(author.get("family")))
                    if part
                )
            )
        if literal:
            result.append(literal)
    return tuple(dict.fromkeys(result))


def _crossref_year(message: dict[str, object]) -> int | None:
    for field in ("published", "published-print", "published-online", "issued"):
        value = message.get(field)
        if not isinstance(value, dict):
            continue
        parts = value.get("date-parts")
        if (
            isinstance(parts, list)
            and parts
            and isinstance(parts[0], list)
            and parts[0]
            and type(parts[0][0]) is int
        ):
            return parts[0][0]
    return None


def _first_string(value: object) -> str | None:
    if isinstance(value, list) and value:
        return _clean(value[0])
    return _clean(value)


def _from_crossref(url: str, fetcher: Fetcher) -> BaseMetadata:
    doi = unquote(urlsplit(url).path.lstrip("/")).strip()
    if not doi or any(character.isspace() for character in doi):
        raise SourceError("invalid-source-url")
    api_url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
    response = fetcher.get(api_url, accepted_hosts=ALLOWED_SOURCE_HOSTS)
    payload = _json_object(response.body)
    message = payload.get("message")
    if not isinstance(message, dict):
        raise SourceError("metadata-unavailable")
    canonical_doi = _clean(message.get("DOI")) or doi
    container = _first_string(message.get("container-title"))
    canonical = f"https://doi.org/{canonical_doi}"
    return BaseMetadata(
        submitted_url=url,
        canonical_url=canonical,
        title=_first_string(message.get("title")),
        authors=_crossref_authors(message.get("author")),
        venue=_controlled_venue(container),
        year=_crossref_year(message),
        paper_url=canonical,
        doi=canonical_doi,
    )


class _CitationMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.values: dict[str, list[str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "meta":
            return
        attributes = {key.casefold(): value for key, value in attrs if value is not None}
        name = (attributes.get("name") or attributes.get("property") or "").casefold()
        content = _clean(attributes.get("content"))
        if name.startswith("citation_") and content:
            self.values.setdefault(name, []).append(content)


def _valid_link(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return None
    return value


def _from_citation_meta(url: str, fetcher: Fetcher) -> BaseMetadata:
    response = fetcher.get(url, accepted_hosts=ALLOWED_SOURCE_HOSTS)
    try:
        text = response.body.decode("utf-8")
    except UnicodeDecodeError:
        raise SourceError("invalid-response") from None
    parser = _CitationMetaParser()
    try:
        parser.feed(text)
    except Exception:
        raise SourceError("invalid-response") from None
    get = lambda name: parser.values.get(name, [])
    title = get("citation_title")[0] if get("citation_title") else None
    conference = get("citation_conference_title")[0] if get("citation_conference_title") else None
    published = get("citation_publication_date")[0] if get("citation_publication_date") else None
    pdf = _valid_link(get("citation_pdf_url")[0] if get("citation_pdf_url") else None)
    doi = get("citation_doi")[0] if get("citation_doi") else None
    final_url = response.url
    return BaseMetadata(
        submitted_url=url,
        canonical_url=final_url,
        title=title,
        authors=tuple(dict.fromkeys(get("citation_author"))),
        venue=_controlled_venue(conference),
        year=_year(conference, published),
        paper_url=pdf or final_url,
        official_url=final_url,
        doi=doi,
    )


def _host_matches(host: str, trusted: frozenset[str]) -> bool:
    return any(host == item or host.endswith(f".{item}") for item in trusted)


def extract_metadata(url: str, fetcher: Fetcher | None = None) -> BaseMetadata:
    """Extract base metadata without making scope or acceptance decisions."""

    parsed = validated_https_url(url, ALLOWED_SOURCE_HOSTS)
    host = parsed.hostname.casefold() if parsed.hostname else ""
    active_fetcher: Fetcher = fetcher or SafeFetcher()
    if host == "openreview.net":
        return _from_openreview(url, active_fetcher)
    if host == "arxiv.org":
        return _from_arxiv(url, active_fetcher)
    if host == "doi.org":
        return _from_crossref(url, active_fetcher)
    if _host_matches(host, _OFFICIAL_HOSTS):
        return _from_citation_meta(url, active_fetcher)
    raise SourceError("unsupported-source")
