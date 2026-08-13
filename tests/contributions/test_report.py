from __future__ import annotations

import dataclasses
import unittest

from scripts.contributions.models import BaseMetadata, DuplicateResult, InspectionResult, Submission
from scripts.contributions.report import (
    REPORT_MARKER,
    ReportError,
    render_problem_report,
    render_report,
    state_label,
)


def result(
    *,
    title: str = "Portfolio Learning",
    missing: tuple[str, ...] = (),
    duplicate: str = "clear",
) -> InspectionResult:
    url = "https://openreview.net/forum?id=abc123"
    metadata = BaseMetadata(
        submitted_url=url,
        canonical_url=url,
        title=title,
        authors=("Ada A.", "Bo B."),
        venue="ICML",
        year=2025,
        paper_url=url,
        official_url=url,
        openreview_id="abc123",
    )
    return InspectionResult(
        version=1,
        submission=Submission(url),
        metadata=metadata,
        missing_fields=missing,
        duplicate=DuplicateResult(duplicate, ("2025-icml-existing-paper",) if duplicate != "clear" else ()),
        metadata_ready=not missing and duplicate != "duplicate",
    )


class ReportTests(unittest.TestCase):
    def test_report_contains_only_base_facts_duplicates_and_next_action(self) -> None:
        report = render_report(result())

        self.assertEqual(report.count(REPORT_MARKER), 1)
        self.assertIn("Portfolio Learning", report)
        self.assertIn("Ada A., Bo B.", report)
        self.assertIn("ICML", report)
        self.assertIn("2025", report)
        self.assertIn("Maintainer review", report)
        for forbidden in ("scope assessment", "acceptance verified", "summary suggestion"):
            self.assertNotIn(forbidden, report.casefold())

    def test_report_lists_missing_fields_and_duplicate_ids(self) -> None:
        missing_report = render_report(result(missing=("venue", "year")))
        duplicate_report = render_report(result(duplicate="duplicate"))

        self.assertIn("venue, year", missing_report)
        self.assertIn("2025-icml-existing-paper", duplicate_report)

    def test_untrusted_metadata_cannot_create_mentions_bare_links_or_strikethrough(self) -> None:
        adversarial = "@owner https://evil.test ~strike~ <script>alert(1)</script>"
        report = render_report(result(title=adversarial))

        self.assertNotIn("@owner", report)
        self.assertNotIn("https://evil.test", report)
        self.assertNotIn("~strike~", report)
        self.assertNotIn("<script>", report)
        self.assertIn("https://openreview.net/forum?id=abc123", report)

    def test_state_label_uses_exactly_three_machine_states(self) -> None:
        self.assertEqual(state_label(result()), "metadata-ready")
        self.assertEqual(state_label(result(missing=("venue",))), "needs-metadata")
        self.assertEqual(state_label(result(duplicate="duplicate")), "duplicate")

    def test_problem_report_accepts_only_public_safe_codes(self) -> None:
        report = render_problem_report("unsupported-source")
        self.assertEqual(report.count(REPORT_MARKER), 1)
        self.assertIn("recognized paper source", report)
        with self.assertRaises(ReportError):
            render_problem_report("Bearer secret raw response")


if __name__ == "__main__":
    unittest.main()
