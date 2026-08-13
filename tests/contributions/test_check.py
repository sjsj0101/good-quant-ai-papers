from __future__ import annotations

import dataclasses
import unittest

from scripts.contributions.check import (
    check_duplicates,
    inspect_submission,
    missing_base_fields,
    normalize_title,
)
from scripts.contributions.models import BaseMetadata, Submission


SUBMISSION = Submission("https://openreview.net/forum?id=new-paper")
COMPLETE = BaseMetadata(
    submitted_url=SUBMISSION.paper_url,
    canonical_url=SUBMISSION.paper_url,
    title="A New Portfolio Method",
    authors=("Ada A.",),
    venue="ICML",
    year=2025,
    paper_url=SUBMISSION.paper_url,
    official_url=SUBMISSION.paper_url,
    openreview_id="new-paper",
)
EXISTING = [
    {
        "id": "2025-icml-example-scalable-method",
        "title": "A Scalable Method for Robust Sparse Portfolio Optimization",
        "authors": ["Example Author"],
        "venue": "ICML",
        "year": 2025,
        "official_url": "https://example.org/Paper?ID=ABC",
        "paper_url": "https://arxiv.org/abs/2501.00001",
        "doi": "10.1000/portfolio",
        "openreview_id": "existing-review",
        "arxiv_id": "2501.00001",
    }
]


class ReadinessTests(unittest.TestCase):
    def test_complete_base_fields_are_the_only_readiness_gate(self) -> None:
        result = inspect_submission(SUBMISSION, COMPLETE, [])

        self.assertEqual(result.missing_fields, ())
        self.assertTrue(result.metadata_ready)
        self.assertEqual(result.duplicate.status, "clear")
        for forbidden in ("scope_assessment", "venue_verified", "record_complete"):
            self.assertFalse(hasattr(result, forbidden))

    def test_each_missing_or_invalid_base_field_is_reported(self) -> None:
        cases = {
            "title": dataclasses.replace(COMPLETE, title=" "),
            "authors": dataclasses.replace(COMPLETE, authors=()),
            "venue": dataclasses.replace(COMPLETE, venue="FinanceConf"),
            "year": dataclasses.replace(COMPLETE, year=2023),
            "paper_url": dataclasses.replace(COMPLETE, paper_url="http://example.org"),
        }
        for field, metadata in cases.items():
            with self.subTest(field=field):
                self.assertIn(field, missing_base_fields(metadata))
                self.assertFalse(inspect_submission(SUBMISSION, metadata, []).metadata_ready)

    def test_bool_year_is_invalid_even_though_bool_is_an_int_subclass(self) -> None:
        metadata = dataclasses.replace(COMPLETE, year=True)
        self.assertEqual(missing_base_fields(metadata), ("year",))


class DuplicateTests(unittest.TestCase):
    def test_exact_identifier_matches_block(self) -> None:
        cases = (
            dataclasses.replace(COMPLETE, doi="DOI:10.1000/PORTFOLIO"),
            dataclasses.replace(COMPLETE, openreview_id="EXISTING-REVIEW"),
            dataclasses.replace(COMPLETE, arxiv_id="2501.00001v3"),
        )
        for metadata in cases:
            with self.subTest(metadata=metadata):
                result = check_duplicates(metadata, EXISTING)
                self.assertEqual(result.status, "duplicate")
                self.assertEqual(result.matching_ids, (EXISTING[0]["id"],))

    def test_url_normalization_lowers_only_scheme_host_and_default_port(self) -> None:
        same = dataclasses.replace(
            COMPLETE,
            official_url="https://EXAMPLE.org:443/Paper?ID=ABC#fragment",
        )
        different_path_case = dataclasses.replace(
            COMPLETE,
            official_url="https://example.org/paper?ID=ABC",
        )

        self.assertEqual(check_duplicates(same, EXISTING).status, "duplicate")
        self.assertEqual(check_duplicates(different_path_case, EXISTING).status, "clear")

    def test_candidate_paper_url_matches_existing_official_url(self) -> None:
        metadata = dataclasses.replace(
            COMPLETE,
            paper_url="https://example.org/Paper?ID=ABC",
        )
        self.assertEqual(check_duplicates(metadata, EXISTING).status, "duplicate")

    def test_normalized_title_equality_is_duplicate(self) -> None:
        metadata = dataclasses.replace(
            COMPLETE,
            title="Ａ scalable method—for robust sparse portfolio optimization!",
        )
        self.assertEqual(check_duplicates(metadata, EXISTING).status, "duplicate")

    def test_conservative_similar_title_is_possible_not_duplicate(self) -> None:
        metadata = dataclasses.replace(
            COMPLETE,
            title="A Scalable Method for Robust Sparse Portfolio Optimisation",
        )
        result = check_duplicates(metadata, EXISTING)
        self.assertEqual(result.status, "possible")
        self.assertEqual(result.matching_ids, (EXISTING[0]["id"],))
        self.assertTrue(inspect_submission(SUBMISSION, metadata, EXISTING).metadata_ready)

    def test_short_or_merely_related_title_is_clear(self) -> None:
        cases = ("Portfolio Optimization", "A Different Study of Portfolio Optimization")
        for title in cases:
            with self.subTest(title=title):
                metadata = dataclasses.replace(COMPLETE, title=title)
                self.assertEqual(check_duplicates(metadata, EXISTING).status, "clear")

    def test_title_normalization_is_unicode_case_and_punctuation_insensitive(self) -> None:
        self.assertEqual(
            normalize_title("Ｆactor—Learning: For Markets!"),
            "factor learning for markets",
        )


if __name__ == "__main__":
    unittest.main()
