#!/usr/bin/env python3
"""Render deterministic Markdown indexes from the paper catalog."""

from __future__ import annotations

import argparse
import html
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence
from urllib.parse import urlencode

import yaml

if __package__:
    from .catalog import VENUE_ORDER, load_catalog, validate_catalog
    from .coverage import COVERAGE_YEARS, load_coverage, validate_coverage
else:
    from catalog import VENUE_ORDER, load_catalog, validate_catalog
    from coverage import COVERAGE_YEARS, load_coverage, validate_coverage


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "sjsj0101/good-quant-ai-papers"
REPOSITORY_URL = f"https://github.com/{REPOSITORY}"
GENERATED_NOTICE = (
    "<!-- Generated from data/papers.yaml and data/coverage.yaml by "
    "scripts/render.py. Do not edit directly. -->"
)

TRACK_ORDER = ("main", "position", "workshop", "affinity")
TRACK_LABELS = {
    "main": "Main",
    "position": "Position",
    "workshop": "Workshop",
    "affinity": "Affinity",
}
TRACK_HEADINGS = {
    "main": "Main Conference",
    "position": "Position Papers",
    "workshop": "Workshops",
    "affinity": "Affinity Tracks",
}
COVERAGE_LABELS = {
    "complete": "Complete",
    "no-eligible-papers": "No eligible papers",
    "pending": "Pending",
}


def _venue_slug(venue: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", venue.casefold()))


def _clean_inline(value: object) -> str:
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    return " ".join(part.strip() for part in text.split("\n") if part.strip())


def _escape_markdown(value: object) -> str:
    """Escape catalog prose for safe use in an inline Markdown context."""

    text = html.escape(_clean_inline(value), quote=False)
    for character in ("\\", "`", "*", "_", "[", "]", "|"):
        text = text.replace(character, f"\\{character}")
    return text


def _link_destination(url: str) -> str:
    return url.replace("<", "%3C").replace(">", "%3E")


def _markdown_link(label: object, url: str) -> str:
    return f"[{_escape_markdown(label)}](<{_link_destination(url)}>)"


def _display_label(value: str) -> str:
    if value == "FX":
        return value
    return value.replace("-", " ").title()


def _topic_label(topic: str) -> str:
    return _display_label(topic)


def _topic_link(topic: str) -> str:
    query = urlencode(
        {"q": f'path:data/papers.yaml "{topic}"', "type": "code"}
    )
    return f"[{_topic_label(topic)}]({REPOSITORY_URL}/search?{query})"


def _track_sort_key(track: str) -> tuple:
    try:
        return (TRACK_ORDER.index(track), "")
    except ValueError:
        return (len(TRACK_ORDER), track.casefold())


def _coverage_by_key(coverage: Iterable[dict]) -> dict[tuple[int, str], dict]:
    return {(row["year"], row["venue"]): row for row in coverage}


def _venue_sort_key(venue: str) -> tuple[int, str]:
    try:
        return (VENUE_ORDER.index(venue), "")
    except ValueError:
        return (len(VENUE_ORDER), venue.casefold())


def _sorted_records(records: Iterable[dict]) -> list[dict]:
    return sorted(
        records,
        key=lambda record: (
            -record["year"],
            _venue_sort_key(record["venue"]),
            _track_sort_key(record["track"]),
            record["title"].casefold(),
            record["id"],
        ),
    )


def _records_by_venue(records: Iterable[dict]) -> dict[tuple[int, str], list[dict]]:
    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for record in records:
        grouped[(record["year"], record["venue"])].append(record)
    return {
        key: sorted(
            grouped[key],
            key=lambda record: (
                _track_sort_key(record["track"]),
                record["title"].casefold(),
                record["id"],
            ),
        )
        for key in sorted(
            grouped, key=lambda item: (-item[0], _venue_sort_key(item[1]))
        )
    }


def _assets_and_frequency(record: dict, *, missing: str) -> str:
    values: list[str] = []
    asset_classes = record.get("asset_classes")
    if asset_classes:
        values.append(", ".join(_display_label(item) for item in asset_classes))
    frequency = record.get("data_frequency")
    if frequency:
        values.append(_display_label(frequency))
    return " · ".join(values) if values else missing


def _track_cell(record: dict) -> str:
    track = TRACK_LABELS.get(record["track"], _display_label(record["track"]))
    parts = [track, f"<sub>{_display_label(record['presentation'])}</sub>"]
    if record.get("subvenue"):
        parts.append(f"<sub>{_escape_markdown(record['subvenue'])}</sub>")
    return "<br>".join(parts)


def _paper_cell(record: dict) -> str:
    title = _markdown_link(record["title"], record["paper_url"])
    authors = _escape_markdown(", ".join(record["authors"]))
    return f"{title}<br><sub>{authors}</sub>"


def _paper_table(records: Iterable[dict]) -> list[str]:
    lines = [
        "| Paper | Track | Focus | Assets / Frequency | Why it matters |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in sorted(
        records, key=lambda item: (item["title"].casefold(), item["id"])
    ):
        lines.append(
            "| "
            + " | ".join(
                (
                    _paper_cell(record),
                    _track_cell(record),
                    _escape_markdown(record["summary"]),
                    _escape_markdown(
                        _assets_and_frequency(record, missing="—")
                    ),
                    _escape_markdown(record["why_it_matters"]),
                )
            )
            + " |"
        )
    return lines


def _badge(alt: str, image_path: str, target: str) -> str:
    image = f"https://img.shields.io/badge/{image_path}?style=flat-square"
    return f"[![{alt}]({image})]({target})"


def _render_coverage_matrix(
    records: Iterable[dict], coverage: Iterable[dict]
) -> list[str]:
    counts = Counter((record["year"], record["venue"]) for record in records)
    by_key = _coverage_by_key(coverage)
    years = tuple(sorted(COVERAGE_YEARS, reverse=True))
    lines = [
        "## Coverage: 2024–2026",
        "",
        "| Venue | " + " | ".join(str(year) for year in years) + " |",
        "| --- | " + " | ".join("---:" for _ in years) + " |",
    ]
    for venue in VENUE_ORDER:
        cells: list[str] = []
        for year in years:
            count = counts[(year, venue)]
            noun = "paper" if count == 1 else "papers"
            count_text = f"{count} {noun}"
            if count:
                path = f"papers/{year}/{_venue_slug(venue)}.md"
                count_text = f"[{count_text}]({path})"
            status = COVERAGE_LABELS[by_key[(year, venue)]["status"]]
            cells.append(f"{count_text} · {status}")
        lines.append(
            f"| {_escape_markdown(venue)} | " + " | ".join(cells) + " |"
        )
    return lines


def render_readme(records: list[dict], coverage: list[dict]) -> str:
    """Return the repository README generated from validated *records*."""

    ordered = _sorted_records(records)
    grouped = _records_by_venue(ordered)
    paper_count = len(ordered)
    venue_count = len(VENUE_ORDER)
    last_verified = max(
        [record["verified_on"] for record in ordered]
        + [row["checked_on"] for row in coverage],
        default="Not available",
    )
    badge_date = last_verified.replace("-", "--").replace(" ", "_")
    latest_page = (
        f"papers/{ordered[0]['year']}/{_venue_slug(ordered[0]['venue'])}.md"
        if ordered
        else "data/papers.yaml"
    )

    lines = [
        GENERATED_NOTICE,
        "",
        '<div align="center">',
        "",
        "# Good Quant AI Papers",
        "",
        "Curated top-conference research for quantitative finance and asset management.",
        "",
        " ".join(
            (
                _badge(
                    f"Papers-{paper_count}",
                    f"Papers-{paper_count}-0B7285",
                    latest_page,
                ),
                _badge(
                    f"Venues-{venue_count}",
                    f"Venues-{venue_count}-364FC7",
                    "#browse-by-year-and-venue",
                ),
                _badge(
                    f"Last verified-{badge_date}",
                    f"Last_verified-{badge_date}-5F3DC4",
                    "data/papers.yaml",
                ),
                _badge(
                    "License-CC BY 4.0",
                    "License-CC_BY_4.0-2B8A3E",
                    "LICENSE",
                ),
            )
        ),
        "",
        "</div>",
        "",
        "## Scope",
        "",
        (
            "This catalog admits only officially accepted computer-science "
            "conference work with a direct contribution to quantitative investing, "
            "trading, portfolio construction, derivatives, or market-risk decisions. "
            "Every entry must have a verified venue record; an unverified preprint is "
            "not eligible. Main-conference, workshop, and position papers are labeled "
            "explicitly."
        ),
        "",
        (
            "**Included:** asset allocation, alpha and factor modeling, market regimes, "
            "microstructure and execution, derivatives, market simulation, financial "
            "decision agents, and investment-linked alternative data."
        ),
        "",
        (
            "**Excluded:** General banking, credit scoring, fraud detection, payments, "
            "accounting QA, regulatory technology, and generic financial NLP without a "
            "clear investment, trading, portfolio, or market-risk contribution."
        ),
        "",
        (
            "The catalog stores original one-sentence editorial summaries and "
            "links—not paper PDFs or copied abstracts."
        ),
    ]

    lines.extend(["", *_render_coverage_matrix(ordered, coverage), ""])
    lines.extend(["## Browse by Topic", ""])
    topics = sorted({topic for record in ordered for topic in record["topics"]})
    lines.append(" · ".join(_topic_link(topic) for topic in topics) or "No topics yet.")

    for (year, venue), venue_records in grouped.items():
        lines.extend(["", f"## {_escape_markdown(venue)} {year}", ""])
        tracks = {record["track"] for record in venue_records}
        for track in sorted(tracks, key=_track_sort_key):
            track_records = [
                record for record in venue_records if record["track"] == track
            ]
            heading = TRACK_HEADINGS.get(track, _display_label(track))
            lines.extend(
                [
                    f"### {heading} ({len(track_records)})",
                    "",
                    *_paper_table(track_records),
                    "",
                ]
            )

    lines.extend(["## Browse by Year and Venue", ""])
    for (year, venue), venue_records in grouped.items():
        relative_path = f"papers/{year}/{_venue_slug(venue)}.md"
        lines.append(
            f"- **{year}** · [{_escape_markdown(venue)} {year}]"
            f"({relative_path}) — {len(venue_records)} papers"
        )
    if not grouped:
        lines.append("No venue pages yet.")

    lines.extend(
        [
            "",
            "## Contributing",
            "",
            (
                f"Contributions to [`{REPOSITORY}`]({REPOSITORY_URL}) are welcome. "
                "Add or correct metadata in [`data/papers.yaml`](data/papers.yaml), "
                "provide an official venue source, and write original summary prose. "
                "Do not edit generated indexes by hand."
            ),
            "",
            "```bash",
            "python3 scripts/validate.py",
            "python3 scripts/render.py",
            "python3 scripts/render.py --check",
            "```",
            "",
            "See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the complete submission checklist.",
            "",
            "## License",
            "",
            (
                "Catalog metadata and original editorial prose are licensed under "
                "[Creative Commons Attribution 4.0 International](LICENSE). Linked "
                "papers and third-party resources remain under their respective terms."
            ),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _metadata_line(label: str, value: object) -> str:
    return f"**{label}:** {_escape_markdown(value)}"


def _optional_list_line(record: dict, field: str, label: str) -> Optional[str]:
    values = record.get(field)
    if not values:
        return None
    return _metadata_line(label, " · ".join(_clean_inline(value) for value in values))


def _venue_record_block(record: dict) -> list[str]:
    track = TRACK_LABELS.get(record["track"], _display_label(record["track"]))
    presentation = _display_label(record["presentation"])
    status = _display_label(record["status"])
    topics = " · ".join(_topic_label(topic) for topic in record["topics"])
    lines = [
        f"### {_markdown_link(record['title'], record['paper_url'])}",
        "",
        _metadata_line("Catalog ID", record["id"]),
        "",
        _metadata_line("Authors", ", ".join(record["authors"])),
        "",
        _metadata_line("Venue / year", f"{record['venue']} · {record['year']}"),
        "",
        _metadata_line("Track / presentation", f"{track} · {presentation}"),
    ]
    if record.get("subvenue"):
        lines.extend(["", _metadata_line("Subvenue", record["subvenue"])])
    lines.extend(
        [
            "",
            _metadata_line(
                "Status / verified", f"{status} · {record['verified_on']}"
            ),
            "",
            _metadata_line("Topics", topics),
            "",
            _metadata_line(
                "Assets / frequency",
                _assets_and_frequency(record, missing="Not specified"),
            ),
        ]
    )

    for field, label in (
        ("tasks", "Tasks"),
        ("methods", "Methods"),
        ("datasets", "Datasets"),
    ):
        optional_line = _optional_list_line(record, field, label)
        if optional_line:
            lines.extend(["", optional_line])

    identifiers: list[str] = []
    for field, label in (
        ("arxiv_id", "arXiv"),
        ("openreview_id", "OpenReview"),
        ("doi", "DOI"),
    ):
        if record.get(field):
            identifiers.append(f"{label} {_escape_markdown(record[field])}")
    if identifiers:
        lines.extend(["", f"**Identifiers:** {' · '.join(identifiers)}"])

    lines.extend(
        [
            "",
            _metadata_line("Focus", record["summary"]),
            "",
            _metadata_line("Why it matters", record["why_it_matters"]),
        ]
    )

    if record.get("notes"):
        lines.extend(["", _metadata_line("Notes", record["notes"])])

    links = [
        _markdown_link("Official venue record", record["official_url"]),
        _markdown_link("Paper", record["paper_url"]),
    ]
    if record.get("code_url"):
        links.append(_markdown_link("Code", record["code_url"]))
    if record.get("project_url"):
        links.append(_markdown_link("Project", record["project_url"]))
    lines.extend(["", f"**Links:** {' · '.join(links)}", "", "---"])
    return lines


def _render_venue_page(
    year: int, venue: str, records: list[dict], coverage_record: dict
) -> str:
    source_links = " · ".join(
        _markdown_link(f"Source {index}", url)
        for index, url in enumerate(coverage_record["official_sources"], start=1)
    )
    coverage_lines = [
        _metadata_line(
            "Coverage status", COVERAGE_LABELS[coverage_record["status"]]
        ),
        "",
        _metadata_line("Checked on", coverage_record["checked_on"]),
        "",
        f"**Official audit sources:** {source_links}",
        "",
        _metadata_line("Coverage notes", coverage_record["notes"]),
    ]
    lines = [
        GENERATED_NOTICE,
        "",
        f"# {_escape_markdown(venue)} {year}",
        "",
        *coverage_lines,
        "",
        (
            f"{len(records)} verified papers curated for direct relevance to "
            "quantitative finance and asset management. Tracks are separated so "
            "main-conference, position, and workshop status remains visible."
        ),
        "",
        "[← Back to the main index](../../README.md)",
        "",
    ]
    tracks = {record["track"] for record in records}
    for track in sorted(tracks, key=_track_sort_key):
        track_records = sorted(
            (record for record in records if record["track"] == track),
            key=lambda record: (record["title"].casefold(), record["id"]),
        )
        heading = TRACK_HEADINGS.get(track, _display_label(track))
        lines.extend([f"## {heading} ({len(track_records)})", ""])
        for record in track_records:
            lines.extend(_venue_record_block(record))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_venue_pages(
    records: list[dict], coverage: list[dict]
) -> dict[Path, str]:
    """Return all generated venue pages, keyed by repository-relative path."""

    pages: dict[Path, str] = {}
    by_key = _coverage_by_key(coverage)
    for (year, venue), venue_records in _records_by_venue(records).items():
        path = Path("papers", str(year), f"{_venue_slug(venue)}.md")
        pages[path] = _render_venue_page(
            year, venue, venue_records, by_key[(year, venue)]
        )
    return pages


def render_outputs(records: list[dict], coverage: list[dict]) -> dict[Path, str]:
    """Return every generated repository file in deterministic path order."""

    outputs = {Path("README.md"): render_readme(records, coverage)}
    outputs.update(render_venue_pages(records, coverage))
    return outputs


def check_generated_files(root: Path, outputs: Mapping[Path, str]) -> list[str]:
    """Return missing, stale, and unexpected generated-file problems."""

    problems: list[str] = []
    expected = set(outputs)
    for relative_path in sorted(expected, key=lambda path: path.as_posix()):
        path = root / relative_path
        if not path.is_file():
            problems.append(f"missing: {relative_path.as_posix()}")
            continue
        try:
            actual = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            problems.append(f"unreadable: {relative_path.as_posix()}: {error}")
            continue
        if actual != outputs[relative_path]:
            problems.append(f"stale: {relative_path.as_posix()}")

    papers_dir = root / "papers"
    actual_venue_pages = (
        {
            path.relative_to(root)
            for path in papers_dir.rglob("*.md")
            if path.is_file()
        }
        if papers_dir.exists()
        else set()
    )
    for relative_path in sorted(
        actual_venue_pages - expected, key=lambda path: path.as_posix()
    ):
        problems.append(f"unexpected: {relative_path.as_posix()}")
    return problems


def _write_outputs(root: Path, outputs: Mapping[Path, str]) -> None:
    for relative_path in sorted(outputs, key=lambda path: path.as_posix()):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(outputs[relative_path], encoding="utf-8")


def _remove_obsolete_generated_venue_pages(
    root: Path, outputs: Mapping[Path, str]
) -> list[str]:
    expected = set(outputs)
    papers_dir = root / "papers"
    if not papers_dir.exists():
        return []

    problems: list[str] = []
    for path in sorted(papers_dir.rglob("*.md")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root)
        if relative_path in expected:
            continue
        try:
            with path.open("r", encoding="utf-8") as stream:
                first_line = stream.readline().rstrip("\r\n")
        except (OSError, UnicodeError):
            continue
        if first_line != GENERATED_NOTICE:
            continue
        try:
            path.unlink()
        except OSError as error:
            problems.append(
                f"could not remove {relative_path.as_posix()}: {error}"
            )
    return problems


def main(
    argv: Optional[Sequence[str]] = None, *, root: Optional[Path] = None
) -> int:
    parser = argparse.ArgumentParser(
        description="Render deterministic Markdown indexes from data/papers.yaml."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if generated Markdown is missing, stale, or unexpected",
    )
    args = parser.parse_args(argv)
    repository_root = ROOT if root is None else Path(root)
    catalog_path = repository_root / "data" / "papers.yaml"
    coverage_path = repository_root / "data" / "coverage.yaml"

    try:
        records = load_catalog(catalog_path)
        coverage = load_coverage(coverage_path)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        print(f"Metadata error: {error}")
        return 1

    errors = validate_catalog(records) + validate_coverage(coverage, records)
    if errors:
        print("\n".join(errors))
        return 1

    outputs = render_outputs(records, coverage)
    if args.check:
        problems = check_generated_files(repository_root, outputs)
        if problems:
            print("Generated files are not current:")
            print("\n".join(problems))
            return 1
        print("Generated files are current")
        return 0

    cleanup_problems = _remove_obsolete_generated_venue_pages(
        repository_root, outputs
    )
    if cleanup_problems:
        print("Could not remove obsolete generated venue pages:")
        print("\n".join(cleanup_problems))
        return 1
    _write_outputs(repository_root, outputs)
    print(f"Rendered {len(outputs)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
