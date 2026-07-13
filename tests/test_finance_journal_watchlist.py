from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from scripts.finance_journal_watchlist import (
    load_watchlist,
    validate_watchlist,
    validate_watchlist_file,
)


VALID = {
    "source": {
        "name": "EDITH local literature corpus",
        "checked_on": "2026-07-13",
        "search_scope": "JF, JFE, and RFS records",
        "search_methods": ["EDITH literature CLI BM25 search"],
        "journals": [
            {
                "code": "JF",
                "name": "The Journal of Finance",
                "local_records": 3229,
                "local_year_range": "1990-2026",
            }
        ],
        "notes": ["No internet search was used."],
    },
    "papers": [
        {
            "id": "edith-jf-30427",
            "edith_paper_id": 30427,
            "title": "(Re-)Imag(in)ing Price Trends",
            "authors": ["Jingwen Jiang", "Bryan Kelly", "Dacheng Xiu"],
            "venue": "JF",
            "journal_name": "The Journal of Finance",
            "year": 2023,
            "year_source": "edith_local_db",
            "doi": "10.1111/jofi.13268",
            "field": "asset_pricing",
            "priority": "core",
            "topics": ["return_prediction", "technical_analysis"],
            "methods": ["cnn", "machine_learning"],
            "methodology_type": "ML-Computational",
            "keywords": "Machine Learning, Deep Learning, CNN",
        }
    ],
}


class FinanceJournalWatchlistValidationTests(unittest.TestCase):
    def test_valid_watchlist_has_no_errors(self) -> None:
        self.assertEqual(validate_watchlist(copy.deepcopy(VALID)), [])

    def test_wrong_journal_name_is_rejected(self) -> None:
        data = copy.deepcopy(VALID)
        data["papers"][0]["journal_name"] = "Journal of Financial Economics"

        errors = validate_watchlist(data)

        self.assertTrue(
            any(error.startswith("edith-jf-30427: journal_name:") for error in errors),
            errors,
        )

    def test_duplicate_doi_is_rejected(self) -> None:
        data = copy.deepcopy(VALID)
        second = copy.deepcopy(data["papers"][0])
        second.update(
            {
                "id": "edith-jf-99999",
                "edith_paper_id": 99999,
                "title": "A Different Finance Paper",
            }
        )
        data["papers"].append(second)

        errors = validate_watchlist(data)

        self.assertTrue(
            any(error.startswith("edith-jf-99999: doi: duplicate") for error in errors),
            errors,
        )

    def test_watchlist_file_loads_and_validates(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / "data" / "finance_journal_ai_watchlist.yaml"

        data = load_watchlist(path)
        errors = validate_watchlist_file(path)

        self.assertGreaterEqual(len(data["papers"]), 30)
        self.assertEqual(errors, [])

    def test_malformed_yaml_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "watchlist.yaml"
            path.write_text("[", encoding="utf-8")

            errors = validate_watchlist_file(path)

        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
