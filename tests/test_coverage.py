from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.catalog import HTTP_URL_PATTERN, TRACKS, VENUE_ORDER
from scripts.coverage import (
    COVERAGE_FIELDS,
    COVERAGE_STATUSES,
    COVERAGE_YEARS,
    PENDING_TRACK_STATES,
    validate_coverage,
)
from tests.test_validate import VALID


def make_coverage() -> list[dict]:
    return [
        {
            "venue": venue,
            "year": year,
            "status": "pending",
            "checked_on": "2026-07-11",
            "eligible_paper_count": 0,
            "tracks_checked": ["main"],
            "tracks_pending": [],
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

    def test_pending_unit_may_have_empty_tracks_checked_with_pending_state(self) -> None:
        coverage = make_coverage()
        coverage[0]["tracks_checked"] = []
        coverage[0]["tracks_pending"] = [
            {
                "track": "main",
                "state": "source_mapped",
                "note": "Main roster was source-mapped but no rows were screened.",
            }
        ]

        self.assertEqual(validate_coverage(coverage, []), [])

    def test_complete_unit_rejects_empty_tracks_checked(self) -> None:
        coverage = make_coverage()
        unit = next(
            row
            for row in coverage
            if row["venue"] == "ICML" and row["year"] == 2026
        )
        unit["status"] = "complete"
        unit["eligible_paper_count"] = 1
        unit["tracks_checked"] = []

        paper = copy.deepcopy(VALID)
        errors = validate_coverage(coverage, [paper])

        self.assertTrue(
            any(
                "may be empty only for pending or unavailable coverage" in error
                for error in errors
            ),
            errors,
        )

    def test_pending_track_can_duplicate_checked_only_when_partial(self) -> None:
        coverage = make_coverage()
        coverage[0]["tracks_pending"] = [
            {
                "track": "main",
                "state": "source_mapped",
                "note": "Main roster remains unresolved.",
            }
        ]

        errors = validate_coverage(coverage, [])

        self.assertTrue(
            any(
                "may duplicate tracks_checked only with state 'partial'" in error
                for error in errors
            ),
            errors,
        )

    def test_partial_pending_track_must_also_be_checked(self) -> None:
        coverage = make_coverage()
        coverage[0]["tracks_pending"] = [
            {
                "track": "workshop",
                "state": "partial",
                "note": "Workshop roster is partly screened.",
            }
        ]

        errors = validate_coverage(coverage, [])

        self.assertTrue(
            any(
                "state 'partial' requires the track to also appear in tracks_checked"
                in error
                for error in errors
            ),
            errors,
        )

    def test_cataloged_paper_track_must_be_in_tracks_checked(self) -> None:
        coverage = make_coverage()
        unit = next(
            row
            for row in coverage
            if row["venue"] == "ICML" and row["year"] == 2026
        )
        unit["eligible_paper_count"] = 1
        unit["tracks_checked"] = []

        errors = validate_coverage(coverage, [copy.deepcopy(VALID)])

        self.assertTrue(
            any("missing cataloged paper track(s): main" in error for error in errors),
            errors,
        )

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
        unit["eligible_paper_count"] = 1
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

    def test_list_valued_paper_year_returns_a_coverage_error(self) -> None:
        paper = copy.deepcopy(VALID)
        paper["id"] = "malformed-year-paper"
        paper["year"] = [2026]

        errors = validate_coverage(make_coverage(), [paper])

        self.assertEqual(
            errors,
            ["malformed-year-paper: coverage: has no coverage unit"],
        )

    def test_list_valued_paper_venue_returns_a_coverage_error(self) -> None:
        paper = copy.deepcopy(VALID)
        paper["id"] = "malformed-venue-paper"
        paper["venue"] = ["ICML"]

        errors = validate_coverage(make_coverage(), [paper])

        self.assertEqual(
            errors,
            ["malformed-venue-paper: coverage: has no coverage unit"],
        )

    def test_schema_matches_runtime_constants(self) -> None:
        schema_path = (
            Path(__file__).resolve().parents[1] / "schema" / "coverage.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual(schema["required"], list(COVERAGE_FIELDS))
        self.assertEqual(properties["venue"]["enum"], list(VENUE_ORDER))
        self.assertEqual(properties["year"]["enum"], list(COVERAGE_YEARS))
        self.assertEqual(properties["status"]["enum"], sorted(COVERAGE_STATUSES))
        self.assertEqual(set(properties["tracks_checked"]["items"]["enum"]), TRACKS)
        self.assertEqual(
            set(properties["tracks_pending"]["items"]["properties"]["track"]["enum"]),
            TRACKS,
        )
        self.assertEqual(
            set(properties["tracks_pending"]["items"]["properties"]["state"]["enum"]),
            PENDING_TRACK_STATES,
        )
        self.assertEqual(schema["$defs"]["http_url"]["pattern"], HTTP_URL_PATTERN)
