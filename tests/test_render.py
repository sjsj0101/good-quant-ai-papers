from __future__ import annotations

import contextlib
import copy
import io
import re
import tempfile
import unittest
from pathlib import Path

from scripts.catalog import load_catalog
from scripts.coverage import load_coverage
from scripts.render import (
    GENERATED_NOTICE,
    check_generated_files,
    main,
    render_outputs,
    render_readme,
    render_venue_pages,
)
from tests.test_coverage import make_coverage


ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_catalog(ROOT / "data" / "papers.yaml")
COVERAGE = load_coverage(ROOT / "data" / "coverage.yaml")


class ReadmeRenderingTests(unittest.TestCase):
    def test_readme_is_polished_browsable_and_complete(self) -> None:
        rendered = render_readme(CATALOG, COVERAGE)

        self.assertIn('<div align="center">\n\n# Good Quant AI Papers', rendered)
        self.assertIn(
            "Curated top-conference research for quantitative finance and asset management.",
            rendered,
        )
        self.assertIn(f"Papers-{len(CATALOG)}", rendered)
        self.assertIn("Venues-11", rendered)
        latest_checked_on = max(record["checked_on"] for record in COVERAGE).replace("-", "--")
        self.assertIn(f"Last verified-{latest_checked_on}", rendered)
        self.assertIn("License-CC BY 4.0", rendered)
        self.assertIn("sjsj0101/good-quant-ai-papers", rendered)
        self.assertIn("## Scope", rendered)
        self.assertIn("evidence-bounded lower-bound catalog", rendered)
        self.assertIn("Coverage rows are deliberately conservative", rendered)
        self.assertIn("workshop, position, and affinity papers", rendered)
        self.assertIn("General banking, credit scoring, fraud detection", rendered)
        self.assertIn("## At a Glance", rendered)
        self.assertIn(f"| Curated papers | {len(CATALOG)} |", rendered)
        self.assertIn("| Coverage units | 33 |", rendered)
        self.assertIn("| Covered years | 2024-2026 |", rendered)
        self.assertIn("## How to Use", rendered)
        self.assertIn("Start with [Browse by Year and Venue]", rendered)
        self.assertIn("## Coverage: 2024–2026", rendered)
        self.assertIn("| Venue | 2026 | 2025 | 2024 |", rendered)
        self.assertIn("| ICML |", rendered)
        self.assertIn("| NeurIPS |", rendered)
        self.assertIn("| ACM ICAIF |", rendered)
        self.assertIn("[20 papers](papers/2026/icml.md) · Pending", rendered)
        self.assertIn("## Browse by Year and Venue", rendered)
        self.assertIn("[ICML 2026](papers/2026/icml.md) — 20 papers", rendered)
        self.assertIn("[AISTATS 2025](papers/2025/aistats.md) — 1 paper", rendered)
        self.assertIn("## Browse by Topic", rendered)
        self.assertIn("Asset Allocation", rendered)
        self.assertIn("Market Microstructure", rendered)
        self.assertIn("## Data Files", rendered)
        self.assertIn("canonical paper records with authors", rendered)
        self.assertIn("venue-year audit status", rendered)
        self.assertIn("## Contributing", rendered)
        self.assertIn("[`data/papers.yaml`](data/papers.yaml)", rendered)
        self.assertIn("[`data/coverage.yaml`](data/coverage.yaml)", rendered)
        self.assertIn("## Paper Index", rendered)
        self.assertIn("### ICML 2026", rendered)
        self.assertIn("#### Main Conference (12)", rendered)
        self.assertIn("#### Position Papers (1)", rendered)
        self.assertIn("#### Workshops (7)", rendered)
        self.assertIn("## License", rendered)
        self.assertLess(rendered.index("## Browse by Year and Venue"), rendered.index("## Paper Index"))
        self.assertLess(rendered.index("## Contributing"), rendered.index("## Paper Index"))
        self.assertEqual(
            sum(line.startswith("| [") for line in rendered.splitlines()),
            len(CATALOG),
        )

    def test_readme_rows_link_titles_show_authors_and_label_tracks(self) -> None:
        rendered = render_readme(CATALOG, COVERAGE)

        self.assertIn(
            "[Signature-Informed Transformer for Asset Allocation]"
            "(<https://openreview.net/forum?id=eBM5ALLJNx>)",
            rendered,
        )
        self.assertIn("<sub>Yoontae Hwang, Stefan Zohren</sub>", rendered)
        self.assertIn("| Main<br><sub>Poster</sub> |", rendered)
        self.assertIn(
            "| Workshop<br><sub>Spotlight</sub><br><sub>"
            "Forecasting as a New Frontier of Intelligence</sub> |",
            rendered,
        )
        self.assertIn("| Position<br><sub>Poster</sub> |", rendered)
        self.assertIn(
            "| Paper | Track | Focus | Assets / Frequency | Why it matters |",
            rendered,
        )


class VenueRenderingTests(unittest.TestCase):
    def test_venue_page_has_every_record_sorted_by_title_within_tracks(self) -> None:
        pages = render_venue_pages(list(reversed(CATALOG)), COVERAGE)

        def venue_page_path(record: dict) -> Path:
            slug = "-".join(re.findall(r"[a-z0-9]+", record["venue"].casefold()))
            return Path(f"papers/{record['year']}/{slug}.md")

        expected_paths = {venue_page_path(record) for record in CATALOG}
        self.assertEqual(set(pages), expected_paths)

        track_labels = {
            "main": "Main Conference",
            "position": "Position Papers",
            "workshop": "Workshops",
            "affinity": "Affinity Tracks",
        }
        records_by_page = {
            path: [
                record for record in CATALOG if venue_page_path(record) == path
            ]
            for path in expected_paths
        }

        for path, page_records in records_by_page.items():
            with self.subTest(path=path):
                rendered = pages[path]
                track_records = {
                    track: sorted(
                        (
                            record
                            for record in page_records
                            if record["track"] == track
                        ),
                        key=lambda record: (
                            record["title"].casefold(),
                            record["id"],
                        ),
                    )
                    for track in track_labels
                }
                populated_tracks = [
                    track for track in track_labels if track_records[track]
                ]
                headings = {
                    track: (
                        f"## {track_labels[track]} "
                        f"({len(track_records[track])})"
                    )
                    for track in populated_tracks
                }
                starts = {
                    track: rendered.index(headings[track])
                    for track in populated_tracks
                }

                self.assertEqual(
                    [starts[track] for track in populated_tracks],
                    sorted(starts.values()),
                )
                for index, track in enumerate(populated_tracks):
                    next_start = (
                        starts[populated_tracks[index + 1]]
                        if index + 1 < len(populated_tracks)
                        else len(rendered)
                    )
                    section = rendered[starts[track] : next_start]
                    positions = [
                        section.index(record["title"])
                        for record in track_records[track]
                    ]
                    self.assertEqual(
                        positions,
                        sorted(positions),
                        f"{path}: {track}",
                    )

                for record in page_records:
                    self.assertIn(
                        f"[{record['title']}](<{record['paper_url']}>)",
                        rendered,
                        record["id"],
                    )

    def test_venue_page_exposes_full_human_readable_metadata(self) -> None:
        rendered = render_venue_pages(CATALOG, COVERAGE)[
            Path("papers/2026/icml.md")
        ]

        self.assertIn("# ICML 2026", rendered)
        self.assertIn("**Cataloged eligible papers:** 20", rendered)
        self.assertIn("**Tracks checked:** Main · Workshop · Position", rendered)
        self.assertIn("**Tracks pending:** Workshop", rendered)
        self.assertIn("Affinity-event or poster roster", rendered)
        self.assertIn(
            "**Catalog ID:** 2026-icml-hwang-signature-informed-transformer",
            rendered,
        )
        self.assertIn("**Authors:** Yoontae Hwang, Stefan Zohren", rendered)
        self.assertIn("**Venue / year:** ICML · 2026", rendered)
        self.assertIn("**Track / presentation:** Main · Poster", rendered)
        self.assertIn("**Status / verified:** Accepted · 2026-07-12", rendered)
        self.assertIn("**Topics:** Asset Allocation · Portfolio Optimization", rendered)
        self.assertIn("**Assets / frequency:** Not specified", rendered)
        self.assertIn("**Focus:** Learns multi-asset allocations", rendered)
        self.assertIn("**Why it matters:** Connects market-path geometry", rendered)
        self.assertIn("[Official venue record]", rendered)
        self.assertIn("[Paper]", rendered)
        self.assertIn("**Notes:** Forecast@ICML26", rendered)

    def test_markdown_table_content_is_escaped_and_optional_links_are_rendered(self) -> None:
        record = copy.deepcopy(CATALOG[0])
        record.update(
            {
                "title": "Alpha | Beta [Study]",
                "authors": ["Ada | Lovelace"],
                "summary": "Signal | portfolio fit.",
                "why_it_matters": "Safer | clearer.",
                "topics": ["alpha-modeling"],
                "code_url": "https://example.org/code",
                "project_url": "https://example.org/project",
                "notes": "Accepted | camera-ready.",
            }
        )

        readme = render_readme([record], COVERAGE)
        venue = render_venue_pages([record], COVERAGE)[
            Path("papers/2026/icml.md")
        ]

        self.assertIn(r"[Alpha \| Beta \[Study\]]", readme)
        self.assertIn(r"Ada \| Lovelace", readme)
        self.assertIn(r"Signal \| portfolio fit.", readme)
        self.assertIn(r"Safer \| clearer.", readme)
        self.assertIn("[Code](<https://example.org/code>)", venue)
        self.assertIn("[Project](<https://example.org/project>)", venue)
        self.assertIn(r"**Notes:** Accepted \| camera-ready.", venue)

    def test_free_text_metadata_preserves_source_terminology(self) -> None:
        record = copy.deepcopy(CATALOG[0])
        record.update(
            {
                "tasks": ["CVaR99 estimation"],
                "methods": ["TailFM-X"],
                "datasets": ["Fama–French factors"],
            }
        )

        rendered = render_venue_pages([record], COVERAGE)[
            Path("papers/2026/icml.md")
        ]

        self.assertIn("**Tasks:** CVaR99 estimation", rendered)
        self.assertIn("**Methods:** TailFM-X", rendered)
        self.assertIn("**Datasets:** Fama–French factors", rendered)

    def test_multi_venue_matrix_and_subvenue_metadata(self) -> None:
        main = copy.deepcopy(CATALOG[0])
        main.update(
            {
                "id": "2025-neurips-doe-portfolio-learning",
                "title": "Portfolio Learning",
                "authors": ["Jane Doe"],
                "venue": "NeurIPS",
                "year": 2025,
                "track": "main",
                "official_url": "https://neurips.cc/virtual/2025/poster/100",
                "paper_url": "https://example.org/portfolio-learning",
            }
        )
        workshop = copy.deepcopy(main)
        workshop.update(
            {
                "id": "2025-neurips-roe-market-simulation",
                "title": "Market Simulation",
                "authors": ["Richard Roe"],
                "track": "workshop",
                "subvenue": "Workshop on Financial AI",
                "official_url": "https://neurips.cc/virtual/2025/workshop/200",
                "paper_url": "https://example.org/market-simulation",
            }
        )
        coverage = make_coverage()

        readme = render_readme([workshop, main], coverage)
        venue = render_venue_pages([workshop, main], coverage)[
            Path("papers/2025/neurips.md")
        ]

        self.assertLess(readme.index("| ICML |"), readme.index("| NeurIPS |"))
        self.assertIn("Workshop on Financial AI", readme)
        self.assertIn("**Coverage status:** Pending", venue)
        self.assertIn("**Checked on:** 2026-07-11", venue)
        self.assertIn("**Official audit sources:**", venue)
        self.assertIn("**Subvenue:** Workshop on Financial AI", venue)


class FreshnessTests(unittest.TestCase):
    def test_check_reports_missing_stale_and_unexpected_generated_files(self) -> None:
        outputs = {
            Path("README.md"): "expected readme\n",
            Path("papers/2026/icml.md"): "expected venue\n",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("stale readme\n", encoding="utf-8")
            unexpected = root / "papers" / "2025" / "icml.md"
            unexpected.parent.mkdir(parents=True)
            unexpected.write_text("unexpected\n", encoding="utf-8")

            problems = check_generated_files(root, outputs)

        self.assertEqual(
            problems,
            [
                "stale: README.md",
                "missing: papers/2026/icml.md",
                "unexpected: papers/2025/icml.md",
            ],
        )

    def test_check_cli_returns_failure_for_stale_output_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "data"
            data.mkdir()
            (data / "papers.yaml").write_text(
                (ROOT / "data" / "papers.yaml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (data / "coverage.yaml").write_text(
                (ROOT / "data" / "coverage.yaml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            outputs = render_outputs(CATALOG, COVERAGE)
            for relative_path, content in outputs.items():
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            (root / "README.md").write_text("stale\n", encoding="utf-8")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                status = main(["--check"], root=root)

        self.assertEqual(status, 1)
        self.assertIn("stale: README.md", stdout.getvalue())

    def test_render_removes_only_obsolete_generated_venue_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "data"
            data.mkdir()
            (data / "papers.yaml").write_text(
                (ROOT / "data" / "papers.yaml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (data / "coverage.yaml").write_text(
                (ROOT / "data" / "coverage.yaml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            obsolete = root / "papers" / "2025" / "old-venue.md"
            obsolete.parent.mkdir(parents=True)
            obsolete.write_text(
                f"{GENERATED_NOTICE}\n\n# Obsolete generated page\n",
                encoding="utf-8",
            )
            manual = root / "papers" / "research-notes.md"
            manual.write_text("# Manual research notes\n", encoding="utf-8")

            render_stdout = io.StringIO()
            with contextlib.redirect_stdout(render_stdout):
                render_status = main([], root=root)

            self.assertEqual(render_status, 0)
            self.assertFalse(obsolete.exists())
            self.assertEqual(
                manual.read_text(encoding="utf-8"), "# Manual research notes\n"
            )

            check_stdout = io.StringIO()
            with contextlib.redirect_stdout(check_stdout):
                check_status = main(["--check"], root=root)

            self.assertEqual(check_status, 1)
            self.assertIn("unexpected: papers/research-notes.md", check_stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
