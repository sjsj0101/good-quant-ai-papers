from __future__ import annotations

import contextlib
import copy
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.catalog as catalog_module
import scripts.validate as validate_cli
from scripts.catalog import URL_FIELDS, load_catalog, validate_catalog, validate_file


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

    def test_duplicate_yaml_key_reports_key_and_source_line_by_file_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "papers.yaml")
            path.write_text(
                "- id: 2026-icml-doe-duplicate-field\n"
                "  summary: First summary.\n"
                "  summary: Second summary.\n",
                encoding="utf-8",
            )

            errors = validate_file(path)
            stdout = io.StringIO()
            with mock.patch.object(validate_cli, "CATALOG_PATH", path):
                with contextlib.redirect_stdout(stdout):
                    status = validate_cli.main()

        self.assertEqual(len(errors), 1, errors)
        self.assertIn("<catalog>: file:", errors[0])
        self.assertIn("duplicate key 'summary'", errors[0])
        self.assertIn("line 3", errors[0])
        self.assertEqual(status, 1)
        self.assertIn(errors[0], stdout.getvalue())

    def test_schema_and_runtime_share_url_contract_for_every_url_field(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "schema" / "paper.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        url_contract = schema["$defs"]["http_url"]
        pattern = re.compile(url_contract["pattern"])
        valid_urls = (
            "https://example.com/paper",
            "http://192.0.2.1:8080/a%20b?download=1#results",
            "https://user:pass@example.com/x",
            "https://sub.example.org:65535/path",
        )
        invalid_urls = (
            "http://user@:80/x",
            "https:///x",
            "https://@example.com/x",
            "https://[:::]/x",
            "https://[example.com]/x",
            "https://[2001:db8::1]/x",
            "https://[fe80::1%25eth0]/x",
            "https://[example.com/x",
            "https://example.com]/x",
            "https://example.com/a b",
            "https://example.com:not-a-port/x",
            "https://example.com:65536/x",
            "https://example.com:/x",
            "https://example.com/%zz",
        )

        for field in URL_FIELDS:
            self.assertEqual(
                schema["properties"][field],
                {"$ref": "#/$defs/http_url"},
                field,
            )
            for value in valid_urls:
                with self.subTest(field=field, value=value, expected="valid"):
                    self.assertIsNotNone(pattern.search(value))
                    record = copy.deepcopy(VALID)
                    record[field] = value
                    errors = validate_catalog([record])
                    self.assertFalse(
                        any(
                            error.startswith(f"{VALID['id']}: {field}:")
                            for error in errors
                        ),
                        errors,
                    )

            for value in invalid_urls:
                with self.subTest(field=field, value=value, expected="invalid"):
                    self.assertIsNone(pattern.search(value))
                    record = copy.deepcopy(VALID)
                    record[field] = value
                    errors = validate_catalog([record])
                    self.assertTrue(
                        any(
                            error.startswith(f"{VALID['id']}: {field}:")
                            for error in errors
                        ),
                        errors,
                    )

        self.assertEqual(
            url_contract["pattern"],
            getattr(catalog_module, "HTTP_URL_PATTERN", None),
        )


if __name__ == "__main__":
    unittest.main()
