from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from scripts.catalog import load_catalog, validate_catalog, validate_file


VALID = {
    "id": "2026-icml-hwang-signature-informed-transformer",
    "title": "Signature-Informed Transformer for Asset Allocation",
    "authors": ["Yoontae Hwang", "Stefan Zohren"],
    "venue": "ICML",
    "year": 2026,
    "track": "main",
    "presentation": "poster",
    "official_url": "https://icml.cc/virtual/2026/poster/62694",
    "paper_url": "https://openreview.net/forum?id=eBM5ALLJNx",
    "topics": ["asset-allocation", "portfolio-optimization"],
    "summary": (
        "End-to-end asset allocation with path signatures and a risk-aware objective."
    ),
    "why_it_matters": "Aligns training with downstream portfolio risk.",
    "status": "accepted",
    "verified_on": "2026-07-11",
}


class CatalogValidationTests(unittest.TestCase):
    def test_valid_record_has_no_errors(self) -> None:
        self.assertEqual(validate_catalog([copy.deepcopy(VALID)]), [])

    def test_missing_required_field_identifies_record_and_field(self) -> None:
        record = copy.deepcopy(VALID)
        del record["summary"]

        errors = validate_catalog([record])

        self.assertTrue(
            any(
                error.startswith(f"{VALID['id']}: summary:")
                and "required" in error
                for error in errors
            ),
            errors,
        )

    def test_invalid_enum_identifies_field_and_allowed_values(self) -> None:
        record = copy.deepcopy(VALID)
        record["track"] = "conference"

        errors = validate_catalog([record])

        self.assertTrue(
            any(
                error.startswith(f"{VALID['id']}: track:")
                and "conference" in error
                for error in errors
            ),
            errors,
        )

    def test_invalid_optional_enum_type_is_rejected(self) -> None:
        record = copy.deepcopy(VALID)
        record["data_frequency"] = ["daily"]

        errors = validate_catalog([record])

        self.assertTrue(
            any(
                error.startswith(f"{VALID['id']}: data_frequency:")
                for error in errors
            ),
            errors,
        )

    def test_non_string_unknown_fields_return_errors_instead_of_raising(self) -> None:
        record = copy.deepcopy(VALID)
        record["unexpected"] = True
        record[1] = "unexpected"

        errors = validate_catalog([record])

        self.assertTrue(
            any(error.startswith(f"{VALID['id']}: 1:") for error in errors),
            errors,
        )
        self.assertTrue(
            any(error.startswith(f"{VALID['id']}: unexpected:") for error in errors),
            errors,
        )

    def test_malformed_url_is_rejected(self) -> None:
        record = copy.deepcopy(VALID)
        record["official_url"] = "icml.cc/virtual/2026/poster/62694"

        errors = validate_catalog([record])

        self.assertTrue(
            any(
                error.startswith(f"{VALID['id']}: official_url:")
                and "HTTP(S)" in error
                for error in errors
            ),
            errors,
        )

    def test_invalid_list_valued_url_returns_an_error_instead_of_raising(self) -> None:
        record = copy.deepcopy(VALID)
        record["official_url"] = ["https://icml.cc/virtual/2026/poster/62694"]

        errors = validate_catalog([record])

        self.assertTrue(
            any(error.startswith(f"{VALID['id']}: official_url:") for error in errors),
            errors,
        )

    def test_url_with_invalid_port_is_rejected(self) -> None:
        record = copy.deepcopy(VALID)
        record["official_url"] = "https://icml.cc:not-a-port/poster/62694"

        errors = validate_catalog([record])

        self.assertTrue(
            any(error.startswith(f"{VALID['id']}: official_url:") for error in errors),
            errors,
        )

    def test_url_with_malformed_percent_escape_is_rejected(self) -> None:
        record = copy.deepcopy(VALID)
        record["official_url"] = "https://icml.cc/virtual/%zz/poster/62694"

        errors = validate_catalog([record])

        self.assertTrue(
            any(error.startswith(f"{VALID['id']}: official_url:") for error in errors),
            errors,
        )

    def test_normalized_title_duplicate_is_rejected(self) -> None:
        duplicate = copy.deepcopy(VALID)
        duplicate.update(
            {
                "id": "2026-icml-doe-duplicate-record",
                "title": "  signature informed transformer for asset allocation!  ",
                "official_url": "https://icml.cc/virtual/2026/poster/99999",
                "paper_url": "https://openreview.net/forum?id=duplicate",
            }
        )

        errors = validate_catalog([copy.deepcopy(VALID), duplicate])

        self.assertTrue(
            any(
                error.startswith(f"{duplicate['id']}: title:")
                and "duplicate" in error
                for error in errors
            ),
            errors,
        )

    def test_duplicate_id_is_rejected(self) -> None:
        duplicate = copy.deepcopy(VALID)
        duplicate.update(
            {
                "title": "A Different Paper",
                "official_url": "https://icml.cc/virtual/2026/poster/99999",
                "paper_url": "https://openreview.net/forum?id=duplicate",
            }
        )

        errors = validate_catalog([copy.deepcopy(VALID), duplicate])

        self.assertTrue(
            any(
                error.startswith(f"{VALID['id']}: id:")
                and "duplicate" in error
                for error in errors
            ),
            errors,
        )

    def test_duplicate_official_url_is_rejected(self) -> None:
        duplicate = copy.deepcopy(VALID)
        duplicate.update(
            {
                "id": "2026-icml-doe-different-paper",
                "title": "A Different Paper",
                "paper_url": "https://openreview.net/forum?id=duplicate",
            }
        )

        errors = validate_catalog([copy.deepcopy(VALID), duplicate])

        self.assertTrue(
            any(
                error.startswith(f"{duplicate['id']}: official_url:")
                and "duplicate" in error
                for error in errors
            ),
            errors,
        )

    def test_duplicate_paper_url_is_rejected(self) -> None:
        duplicate = copy.deepcopy(VALID)
        duplicate.update(
            {
                "id": "2026-icml-doe-different-paper",
                "title": "A Different Paper",
                "official_url": "https://icml.cc/virtual/2026/poster/99999",
            }
        )

        errors = validate_catalog([copy.deepcopy(VALID), duplicate])

        self.assertTrue(
            any(
                error.startswith(f"{duplicate['id']}: paper_url:")
                and "duplicate" in error
                for error in errors
            ),
            errors,
        )

    def test_load_catalog_returns_list_and_keeps_iso_date_as_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "papers.yaml")
            path.write_text(
                "- id: sample\n"
                "  year: 2026\n"
                "  verified_on: 2026-07-11\n",
                encoding="utf-8",
            )

            records = load_catalog(path)

        self.assertIsInstance(records, list)
        self.assertEqual(records[0]["year"], 2026)
        self.assertEqual(records[0]["verified_on"], "2026-07-11")

    def test_validate_file_loads_and_validates_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "papers.yaml")
            path.write_text("[]\n", encoding="utf-8")

            errors = validate_file(path)

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
