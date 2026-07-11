from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.catalog import HTTP_URL_PATTERN, VENUE_ORDER
from scripts.coverage import COVERAGE_YEARS, validate_coverage
from tests.test_validate import VALID


def make_coverage() -> list[dict]:
    return [
        {
            "venue": venue,
            "year": year,
            "status": "pending",
            "checked_on": "2026-07-11",
            "tracks_checked": ["main"],
            "official_sources": [
                f"https://example.org/{year}/{venue.lower().replace(' ', '-')}"
            ],
            "notes": "Official program availability reviewed for this coverage unit.",
        }
        for year in COVERAGE_YEARS
        for venue in VENUE_ORDER
    ]


class CoverageValidationTests(unittest.TestCase):
    def test_exact_33_pending_units_are_valid(self) -> None:
        self.assertEqual(validate_coverage(make_coverage(), []), [])

    def test_missing_unit_is_rejected(self) -> None:
        coverage = make_coverage()[:-1]
        errors = validate_coverage(coverage, [])
        self.assertTrue(any("missing coverage unit" in error for error in errors), errors)

    def test_duplicate_unit_is_rejected(self) -> None:
        coverage = make_coverage()
        coverage.append(copy.deepcopy(coverage[0]))
        errors = validate_coverage(coverage, [])
        self.assertTrue(
            any("duplicate coverage unit" in error for error in errors), errors
        )

    def test_complete_requires_a_matching_paper(self) -> None:
        coverage = make_coverage()
        unit = next(
            row
            for row in coverage
            if row["venue"] == "ICML" and row["year"] == 2026
        )
        unit["status"] = "complete"
        errors = validate_coverage(coverage, [])
        self.assertTrue(
            any("complete requires at least one paper" in error for error in errors),
            errors,
        )

    def test_no_eligible_papers_rejects_a_matching_paper(self) -> None:
        coverage = make_coverage()
        unit = next(
            row
            for row in coverage
            if row["venue"] == "ICML" and row["year"] == 2026
        )
        unit["status"] = "no-eligible-papers"
        errors = validate_coverage(coverage, [copy.deepcopy(VALID)])
        self.assertTrue(
            any(
                "no-eligible-papers requires zero papers" in error
                for error in errors
            ),
            errors,
        )

    def test_paper_outside_coverage_years_is_rejected(self) -> None:
        paper = copy.deepcopy(VALID)
        paper["year"] = 2023
        paper["id"] = "2023-icml-hwang-signature-informed-transformer"
        errors = validate_coverage(make_coverage(), [paper])
        self.assertTrue(any("has no coverage unit" in error for error in errors), errors)

    def test_schema_matches_runtime_constants(self) -> None:
        schema_path = (
            Path(__file__).resolve().parents[1] / "schema" / "coverage.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual(properties["venue"]["enum"], list(VENUE_ORDER))
        self.assertEqual(properties["year"]["enum"], list(COVERAGE_YEARS))
        self.assertEqual(schema["$defs"]["http_url"]["pattern"], HTTP_URL_PATTERN)
