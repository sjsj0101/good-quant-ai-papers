from __future__ import annotations

import contextlib
import copy
import io
import tempfile
import unittest
from pathlib import Path

from scripts.catalog import load_catalog
from scripts.render import (
    check_generated_files,
    main,
    render_outputs,
    render_readme,
    render_venue_pages,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_catalog(ROOT / "data" / "papers.yaml")


class ReadmeRenderingTests(unittest.TestCase):
    def test_readme_is_polished_browsable_and_complete(self) -> None:
        rendered = render_readme(CATALOG)

        self.assertIn('<div align="center">\n\n# Good Quant AI Papers', rendered)
        self.assertIn(
            "Curated top-conference research for quantitative finance and asset management.",
            rendered,
        )
        self.assertIn("Papers-23", rendered)
        self.assertIn("Venues-1", rendered)
        self.assertIn("Last verified-2026--07--11", rendered)
        self.assertIn("License-CC BY 4.0", rendered)
        self.assertIn("sjsj0101/good-quant-ai-papers", rendered)
        self.assertIn("## Scope", rendered)
        self.assertIn("officially accepted computer-science conference work", rendered)
        self.assertIn("General banking, credit scoring, fraud detection", rendered)
        self.assertIn("## Browse by Topic", rendered)
        self.assertIn("Asset Allocation", rendered)
        self.assertIn("Market Microstructure", rendered)
        self.assertIn("## ICML 2026", rendered)
        self.assertIn("### Main Conference (13)", rendered)
        self.assertIn("### Position Papers (1)", rendered)
        self.assertIn("### Workshops (9)", rendered)
        self.assertIn("## Browse by Year and Venue", rendered)
        self.assertIn("[ICML 2026](papers/2026/icml.md) — 23 papers", rendered)
        self.assertIn("## Contributing", rendered)
        self.assertIn("## License", rendered)
        self.assertEqual(rendered.count("| ["), 23)

    def test_readme_rows_link_titles_show_authors_and_label_tracks(self) -> None:
        rendered = render_readme(CATALOG)

        self.assertIn(
            "[Signature-Informed Transformer for Asset Allocation]"
            "(<https://openreview.net/forum?id=eBM5ALLJNx>)",
            rendered,
        )
        self.assertIn("<sub>Yoontae Hwang, Stefan Zohren</sub>", rendered)
        self.assertIn("| Main<br><sub>Poster</sub> |", rendered)
        self.assertIn("| Workshop<br><sub>Spotlight</sub> |", rendered)
        self.assertIn("| Position<br><sub>Poster</sub> |", rendered)
        self.assertIn(
            "| Paper | Track | Focus | Assets / Frequency | Why it matters |",
            rendered,
        )


class VenueRenderingTests(unittest.TestCase):
    def test_venue_page_has_every_record_sorted_by_title_within_tracks(self) -> None:
        pages = render_venue_pages(list(reversed(CATALOG)))

        self.assertEqual(list(pages), [Path("papers/2026/icml.md")])
        rendered = pages[Path("papers/2026/icml.md")]
        headings = {
            "main": "## Main Conference (13)",
            "position": "## Position Papers (1)",
            "workshop": "## Workshops (9)",
        }
        starts = {track: rendered.index(heading) for track, heading in headings.items()}
        ends = {
            "main": starts["position"],
            "position": starts["workshop"],
            "workshop": len(rendered),
        }

        for track in ("main", "position", "workshop"):
            section = rendered[starts[track] : ends[track]]
            records = sorted(
                (record for record in CATALOG if record["track"] == track),
                key=lambda record: record["title"].casefold(),
            )
            positions = [section.index(record["title"]) for record in records]
            self.assertEqual(positions, sorted(positions), track)

        for record in CATALOG:
            self.assertIn(
                f"[{record['title']}](<{record['paper_url']}>)",
                rendered,
                record["id"],
            )

    def test_venue_page_exposes_full_human_readable_metadata(self) -> None:
        rendered = render_venue_pages(CATALOG)[Path("papers/2026/icml.md")]

        self.assertIn("# ICML 2026", rendered)
        self.assertIn(
            "**Catalog ID:** 2026-icml-hwang-signature-informed-transformer",
            rendered,
        )
        self.assertIn("**Authors:** Yoontae Hwang, Stefan Zohren", rendered)
        self.assertIn("**Venue / year:** ICML · 2026", rendered)
        self.assertIn("**Track / presentation:** Main · Poster", rendered)
        self.assertIn("**Status / verified:** Accepted · 2026-07-11", rendered)
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

        readme = render_readme([record])
        venue = render_venue_pages([record])[Path("papers/2026/icml.md")]

        self.assertIn(r"[Alpha \| Beta \[Study\]]", readme)
        self.assertIn(r"Ada \| Lovelace", readme)
        self.assertIn(r"Signal \| portfolio fit.", readme)
        self.assertIn(r"Safer \| clearer.", readme)
        self.assertIn("[Code](<https://example.org/code>)", venue)
        self.assertIn("[Project](<https://example.org/project>)", venue)
        self.assertIn(r"**Notes:** Accepted \| camera-ready.", venue)


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
            outputs = render_outputs(CATALOG)
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


if __name__ == "__main__":
    unittest.main()
