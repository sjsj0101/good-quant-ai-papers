from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.contributions.http import HttpResponse, SourceError
from scripts.contributions.sources import extract_metadata


FIXTURES = Path(__file__).with_name("fixtures")


class FixtureFetcher:
    def __init__(self, responses: dict[str, tuple[str, bytes]]) -> None:
        self.responses = responses
        self.requested: list[str] = []

    def get(self, url: str, *, accepted_hosts: frozenset[str]) -> HttpResponse:
        self.requested.append(url)
        if url not in self.responses:
            raise AssertionError(f"unexpected URL: {url}")
        final_url, body = self.responses[url]
        return HttpResponse(url=final_url, status=200, headers={}, body=body)


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


class SourceExtractionTests(unittest.TestCase):
    def test_extracts_openreview_base_metadata_without_acceptance_decision(self) -> None:
        submitted = "https://openreview.net/forum?id=abc123"
        api = "https://api2.openreview.net/notes?id=abc123"
        result = extract_metadata(
            submitted,
            FixtureFetcher({api: (api, fixture("openreview-note.json"))}),
        )

        self.assertEqual(result.title, "Portfolio Learning")
        self.assertEqual(result.authors, ("Ada A.", "Bo B."))
        self.assertEqual(result.venue, "ICML")
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.openreview_id, "abc123")
        self.assertEqual(result.paper_url, submitted)
        self.assertFalse(hasattr(result, "venue_verified"))
        self.assertFalse(hasattr(result, "abstract"))

    def test_extracts_arxiv_metadata_without_copying_abstract(self) -> None:
        submitted = "https://arxiv.org/abs/2401.00001"
        api = "https://export.arxiv.org/api/query?id_list=2401.00001"
        result = extract_metadata(
            submitted,
            FixtureFetcher({api: (api, fixture("arxiv-entry.xml"))}),
        )

        self.assertEqual(result.title, "Market Simulation with Agents")
        self.assertEqual(result.authors, ("Chen C.", "Dee D."))
        self.assertEqual(result.venue, "ICML")
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.arxiv_id, "2401.00001")
        self.assertEqual(result.doi, "10.1000/market-sim")
        self.assertNotIn("abstract", json.dumps(result.to_dict()).casefold())

    def test_extracts_crossref_metadata_and_controlled_venue_alias(self) -> None:
        submitted = "https://doi.org/10.1000/portfolio-doi"
        api = "https://api.crossref.org/works/10.1000%2Fportfolio-doi"
        result = extract_metadata(
            submitted,
            FixtureFetcher({api: (api, fixture("crossref-work.json"))}),
        )

        self.assertEqual(result.title, "Decision-Focused Portfolios")
        self.assertEqual(result.authors, ("Eve Example", "Fin Research Group"))
        self.assertEqual(result.venue, "NeurIPS")
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.doi, "10.1000/portfolio-doi")

    def test_extracts_official_page_citation_metadata(self) -> None:
        submitted = "https://icml.cc/virtual/2026/poster/123"
        result = extract_metadata(
            submitted,
            FixtureFetcher(
                {submitted: (submitted, fixture("official-paper.html"))}
            ),
        )

        self.assertEqual(result.title, "Risk-Aware Asset Allocation")
        self.assertEqual(result.authors, ("Grace G.", "Hao H."))
        self.assertEqual(result.venue, "ICML")
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.official_url, submitted)
        self.assertEqual(result.paper_url, "https://icml.cc/media/paper.pdf")

    def test_missing_fields_remain_missing_instead_of_using_placeholders(self) -> None:
        api = "https://api2.openreview.net/notes?id=missing"
        payload = json.dumps(
            {"notes": [{"id": "missing", "content": {"title": {"value": "Only title"}}}]}
        ).encode()
        result = extract_metadata(
            "https://openreview.net/forum?id=missing",
            FixtureFetcher({api: (api, payload)}),
        )
        self.assertEqual(result.title, "Only title")
        self.assertEqual(result.authors, ())
        self.assertIsNone(result.venue)
        self.assertIsNone(result.year)

    def test_rejects_unsupported_or_malformed_source_without_fetching(self) -> None:
        fetcher = FixtureFetcher({})
        for url in (
            "https://example.com/paper",
            "http://openreview.net/forum?id=abc123",
            "https://openreview.net.evil.test/forum?id=abc123",
        ):
            with self.subTest(url=url), self.assertRaises(SourceError):
                extract_metadata(url, fetcher)
        self.assertEqual(fetcher.requested, [])


if __name__ == "__main__":
    unittest.main()
