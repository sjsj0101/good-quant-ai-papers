from __future__ import annotations

import unittest

from scripts.contributions.issue_form import SubmissionError, parse_issue_form
from scripts.contributions.models import (
    BaseMetadata,
    DuplicateResult,
    InspectionResult,
    ResultError,
    Submission,
)


VALID_BODY = """### Paper URL

https://openreview.net/forum?id=abc123

### Scope acknowledgement

- [x] I understand maintainers decide scope and venue eligibility.
"""


def ready_result() -> InspectionResult:
    return InspectionResult(
        version=1,
        submission=Submission("https://openreview.net/forum?id=abc123"),
        metadata=BaseMetadata(
            submitted_url="https://openreview.net/forum?id=abc123",
            canonical_url="https://openreview.net/forum?id=abc123",
            title="Portfolio Learning",
            authors=("Ada A.", "Bo B."),
            venue="ICML",
            year=2025,
            paper_url="https://openreview.net/forum?id=abc123",
            official_url="https://openreview.net/forum?id=abc123",
            openreview_id="abc123",
            track="main",
            presentation="poster",
        ),
        missing_fields=(),
        duplicate=DuplicateResult(status="clear"),
        metadata_ready=True,
    )


class IssueFormTests(unittest.TestCase):
    def test_parses_one_https_url_and_checked_acknowledgement(self) -> None:
        self.assertEqual(
            parse_issue_form(VALID_BODY),
            Submission("https://openreview.net/forum?id=abc123"),
        )

    def test_rejects_http_url(self) -> None:
        with self.assertRaisesRegex(SubmissionError, "invalid-url"):
            parse_issue_form(VALID_BODY.replace("https://", "http://"))

    def test_rejects_multiple_urls(self) -> None:
        body = VALID_BODY.replace(
            "\n\n### Scope",
            " https://arxiv.org/abs/2401.00001\n\n### Scope",
        )
        with self.assertRaisesRegex(SubmissionError, "invalid-url"):
            parse_issue_form(body)

    def test_rejects_duplicate_required_heading(self) -> None:
        body = VALID_BODY + "\n### Paper URL\n\nhttps://doi.org/10.1000/example\n"
        with self.assertRaisesRegex(SubmissionError, "invalid-form"):
            parse_issue_form(body)

    def test_rejects_unchecked_acknowledgement(self) -> None:
        with self.assertRaisesRegex(SubmissionError, "scope-not-acknowledged"):
            parse_issue_form(VALID_BODY.replace("- [x]", "- [ ]"))

    def test_rejects_credentials_missing_host_and_fragment_url(self) -> None:
        invalid_urls = (
            "https://user@example.com/paper",
            "https:///paper",
            "https://example.com/paper#second",
        )
        for invalid_url in invalid_urls:
            with self.subTest(url=invalid_url), self.assertRaises(SubmissionError):
                parse_issue_form(
                    VALID_BODY.replace(
                        "https://openreview.net/forum?id=abc123", invalid_url
                    )
                )

    def test_rejects_non_string_body(self) -> None:
        for body in (None, 1, True, []):
            with self.subTest(body=body), self.assertRaises(SubmissionError):
                parse_issue_form(body)  # type: ignore[arg-type]


class ResultContractTests(unittest.TestCase):
    def test_result_round_trips_through_json_safe_dictionary(self) -> None:
        result = ready_result()
        payload = result.to_dict()

        self.assertEqual(InspectionResult.from_dict(payload), result)
        self.assertIsInstance(payload["metadata"]["authors"], list)
        serialized_names = repr(payload).casefold()
        for forbidden in ("abstract", "scope", "acceptance", "summary"):
            self.assertNotIn(forbidden, serialized_names)

    def test_rejects_non_integer_or_unsupported_version(self) -> None:
        payload = ready_result().to_dict()
        for version in (True, 1.0, "1", 2):
            with self.subTest(version=version), self.assertRaises(ResultError):
                InspectionResult.from_dict({**payload, "version": version})

    def test_rejects_string_authors_and_non_boolean_readiness(self) -> None:
        payload = ready_result().to_dict()
        metadata = dict(payload["metadata"])
        metadata["authors"] = "Ada A."
        with self.assertRaises(ResultError):
            InspectionResult.from_dict({**payload, "metadata": metadata})
        with self.assertRaises(ResultError):
            InspectionResult.from_dict({**payload, "metadata_ready": "true"})

    def test_rejects_unknown_or_missing_fields(self) -> None:
        payload = ready_result().to_dict()
        with self.assertRaises(ResultError):
            InspectionResult.from_dict({**payload, "record": {}})
        missing = dict(payload)
        missing.pop("duplicate")
        with self.assertRaises(ResultError):
            InspectionResult.from_dict(missing)


if __name__ == "__main__":
    unittest.main()
