from __future__ import annotations

import dataclasses
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.catalog import load_catalog
from scripts.contributions.materialize import (
    MaterializeError,
    append_partial_record,
    branch_name,
    partial_record,
    render_pr_body,
)
from scripts.contributions.models import BaseMetadata, DuplicateResult, InspectionResult, Submission


def ready_result() -> InspectionResult:
    url = "https://openreview.net/forum?id=new-paper"
    return InspectionResult(
        version=1,
        submission=Submission(url),
        metadata=BaseMetadata(
            submitted_url=url,
            canonical_url=url,
            title="Portfolio Learning",
            authors=("Ada A.", "Bo B."),
            venue="ICML",
            year=2025,
            paper_url=url,
            official_url=url,
            openreview_id="new-paper",
        ),
        missing_fields=(),
        duplicate=DuplicateResult("clear"),
        metadata_ready=True,
    )


EXISTING_RECORD = {
    "id": "2024-icml-existing-paper-record",
    "title": "Existing Paper Record",
    "authors": ["Existing Author"],
    "venue": "ICML",
    "year": 2024,
    "track": "main",
    "presentation": "poster",
    "official_url": "https://icml.cc/existing",
    "paper_url": "https://icml.cc/existing",
    "topics": ["portfolio-optimization"],
    "summary": "Existing original summary.",
    "why_it_matters": "Existing original relevance.",
    "status": "published",
    "verified_on": "2026-08-01",
}


class MaterializeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.catalog = self.root / "papers.yaml"
        self.original = yaml.safe_dump(
            [EXISTING_RECORD], sort_keys=False, allow_unicode=True, width=1000
        )
        self.catalog.write_text(self.original, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_appends_only_reliable_base_metadata_and_keeps_valid_yaml(self) -> None:
        record_id = append_partial_record(self.catalog, ready_result())
        records = load_catalog(self.catalog)
        added = records[-1]

        self.assertEqual(record_id, "2025-icml-ada-a-portfolio-learning")
        self.assertEqual(added["id"], record_id)
        self.assertEqual(added["title"], "Portfolio Learning")
        self.assertEqual(added["authors"], ["Ada A.", "Bo B."])
        self.assertEqual(added["venue"], "ICML")
        self.assertEqual(added["year"], 2025)
        self.assertEqual(added["openreview_id"], "new-paper")
        for absent in ("topics", "summary", "why_it_matters", "status", "verified_on"):
            self.assertNotIn(absent, added)
        self.assertTrue(self.catalog.read_text(encoding="utf-8").startswith(self.original.rstrip() + "\n\n"))

    def test_not_ready_and_exact_duplicate_leave_catalog_byte_identical(self) -> None:
        ready = ready_result()
        cases = (
            dataclasses.replace(ready, metadata_ready=False, missing_fields=("venue",)),
            dataclasses.replace(ready, duplicate=DuplicateResult("duplicate", (EXISTING_RECORD["id"],))),
        )
        for result in cases:
            with self.subTest(result=result):
                before = self.catalog.read_bytes()
                with self.assertRaises(MaterializeError):
                    append_partial_record(self.catalog, result)
                self.assertEqual(self.catalog.read_bytes(), before)

    def test_rechecks_current_catalog_for_duplicate_before_append(self) -> None:
        current = dict(EXISTING_RECORD)
        current["id"] = "2025-icml-current-portfolio-learning"
        current["title"] = "Portfolio Learning"
        current["paper_url"] = "https://example.org/other"
        current["official_url"] = "https://example.org/other"
        self.catalog.write_text(yaml.safe_dump([current], sort_keys=False), encoding="utf-8")
        before = self.catalog.read_bytes()

        with self.assertRaisesRegex(MaterializeError, "duplicate"):
            append_partial_record(self.catalog, ready_result())
        self.assertEqual(self.catalog.read_bytes(), before)

    def test_rejects_generated_id_collision_even_without_duplicate_match(self) -> None:
        collision = dict(EXISTING_RECORD)
        collision["id"] = "2025-icml-ada-a-portfolio-learning"
        self.catalog.write_text(yaml.safe_dump([collision], sort_keys=False), encoding="utf-8")
        before = self.catalog.read_bytes()

        with self.assertRaisesRegex(MaterializeError, "id-collision"):
            append_partial_record(self.catalog, ready_result())
        self.assertEqual(self.catalog.read_bytes(), before)

    def test_partial_record_refuses_inconsistent_ready_flag(self) -> None:
        inconsistent = dataclasses.replace(
            ready_result(),
            metadata=dataclasses.replace(ready_result().metadata, authors=()),
        )
        with self.assertRaises(MaterializeError):
            partial_record(inconsistent)

    def test_branch_and_record_ids_are_shell_inert(self) -> None:
        result = dataclasses.replace(
            ready_result(),
            metadata=dataclasses.replace(
                ready_result().metadata,
                title="Alpha; $(touch /tmp/x) \"Strategy\"",
                authors=("Zoë / 张",),
            ),
        )
        record = partial_record(result)
        branch = branch_name(17, record["id"])
        self.assertRegex(record["id"], r"^[a-z0-9-]+$")
        self.assertRegex(branch, r"^contrib/issue-[0-9]+-[a-z0-9-]+$")
        for unsafe in ("$", "(", ")", ";", '"', "'", " /", "/tmp"):
            self.assertNotIn(unsafe, branch)

    def test_pr_body_lists_missing_schema_fields_and_possible_matches(self) -> None:
        possible = dataclasses.replace(
            ready_result(),
            duplicate=DuplicateResult("possible", ("2025-icml-similar-paper",)),
        )
        body = render_pr_body(7, possible)

        self.assertIn("Issue #7", body)
        self.assertIn("2025-icml-similar-paper", body)
        for field in ("track", "presentation", "topics", "summary", "why_it_matters", "status", "verified_on"):
            self.assertIn(f"`{field}`", body)
        self.assertIn("python3 scripts/validate.py", body)
        self.assertIn("python3 scripts/render.py", body)
        self.assertNotIn("generated summary", body.casefold())


if __name__ == "__main__":
    unittest.main()
