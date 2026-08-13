from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.contributions.cli import main
from scripts.contributions.http import HttpResponse
from scripts.contributions.models import InspectionResult
from scripts.contributions.report import REPORT_MARKER


VALID_BODY = """### Paper URL

https://openreview.net/forum?id=abc123

### Scope acknowledgement

- [x] I understand maintainers decide scope and venue eligibility.
"""


class FixtureFetcher:
    def __init__(self, body: bytes | None = None, error: Exception | None = None) -> None:
        self.body = body
        self.error = error

    def get(self, url: str, *, accepted_hosts: frozenset[str]) -> HttpResponse:
        if self.error:
            raise self.error
        assert self.body is not None
        return HttpResponse(url=url, status=200, headers={}, body=self.body)


class FakeGitHubClient:
    def __init__(self, *, authorized: bool = True) -> None:
        self.authorized = authorized
        self.synced: list[tuple[int, str, str]] = []
        self.actors: list[str] = []

    def sync_issue(self, issue_number: int, report: str, state: str) -> None:
        self.synced.append((issue_number, report, state))

    def actor_can_write(self, actor: str) -> bool:
        self.actors.append(actor)
        return self.authorized


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.event = self.root / "event.json"
        self.catalog = self.root / "papers.yaml"
        self.result = self.root / "result.json"
        self.report = self.root / "report.md"
        self.label = self.root / "label.txt"
        self.output = self.root / "github-output.txt"
        self.catalog.write_text("[]\n", encoding="utf-8")
        self._write_event()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_event(
        self,
        *,
        body: object = VALID_BODY,
        issue_number: object = 7,
        actor: object = "maintainer",
    ) -> None:
        self.event.write_text(
            json.dumps(
                {
                    "issue": {"number": issue_number, "title": "[Paper suggestion] Test", "body": body},
                    "sender": {"login": actor},
                }
            ),
            encoding="utf-8",
        )

    def _inspect_args(self) -> list[str]:
        return [
            "inspect-event",
            "--event", str(self.event),
            "--catalog", str(self.catalog),
            "--result", str(self.result),
            "--report", str(self.report),
            "--labels", str(self.label),
        ]

    def _openreview_fixture(self) -> bytes:
        return (Path(__file__).with_name("fixtures") / "openreview-note.json").read_bytes()

    def test_inspect_event_writes_strict_result_report_and_one_label(self) -> None:
        exit_code = main(self._inspect_args(), fetcher=FixtureFetcher(self._openreview_fixture()))

        self.assertEqual(exit_code, 0)
        result = InspectionResult.from_dict(json.loads(self.result.read_text(encoding="utf-8")))
        self.assertTrue(result.metadata_ready)
        self.assertEqual(self.label.read_text(encoding="utf-8"), "metadata-ready\n")
        self.assertEqual(self.report.read_text(encoding="utf-8").count(REPORT_MARKER), 1)

    def test_malformed_form_writes_problem_report_without_result(self) -> None:
        self._write_event(body=VALID_BODY.replace("- [x]", "- [ ]"))
        exit_code = main(self._inspect_args(), fetcher=FixtureFetcher(self._openreview_fixture()))

        self.assertEqual(exit_code, 0)
        self.assertFalse(self.result.exists())
        self.assertEqual(self.label.read_text(encoding="utf-8"), "needs-metadata\n")
        self.assertIn("acknowledgement", self.report.read_text(encoding="utf-8").casefold())

    def test_unsupported_source_writes_unresolved_result_and_needs_metadata(self) -> None:
        self._write_event(body=VALID_BODY.replace("https://openreview.net/forum?id=abc123", "https://example.com/paper"))
        exit_code = main(self._inspect_args(), fetcher=FixtureFetcher(b""))

        self.assertEqual(exit_code, 0)
        result = InspectionResult.from_dict(json.loads(self.result.read_text(encoding="utf-8")))
        self.assertFalse(result.metadata_ready)
        self.assertEqual(result.metadata.errors, ("unsupported-source",))
        self.assertEqual(self.label.read_text(encoding="utf-8"), "needs-metadata\n")

    def test_sync_issue_uses_strict_event_report_and_label(self) -> None:
        self.report.write_text(REPORT_MARKER + "\nreport\n", encoding="utf-8")
        self.label.write_text("metadata-ready\n", encoding="utf-8")
        github = FakeGitHubClient()
        exit_code = main(
            ["sync-issue", "--event", str(self.event), "--report", str(self.report), "--labels", str(self.label)],
            github_client=github,
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(github.synced, [(7, REPORT_MARKER + "\nreport\n", "metadata-ready")])

    def test_authorize_event_writes_only_boolean_output(self) -> None:
        github = FakeGitHubClient(authorized=True)
        exit_code = main(
            ["authorize-event", "--event", str(self.event), "--github-output", str(self.output)],
            github_client=github,
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "authorized=true\n")
        self.assertEqual(github.actors, ["maintainer"])

    def test_invalid_event_types_fail_without_github_calls(self) -> None:
        self._write_event(issue_number=True)
        self.report.write_text(REPORT_MARKER + "\nreport", encoding="utf-8")
        self.label.write_text("metadata-ready\n", encoding="utf-8")
        github = FakeGitHubClient()
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            exit_code = main(
                ["sync-issue", "--event", str(self.event), "--report", str(self.report), "--labels", str(self.label)],
                github_client=github,
            )
        self.assertNotEqual(exit_code, 0)
        self.assertEqual(github.synced, [])
        self.assertEqual(stderr.getvalue(), "contribution-error: invalid-event\n")

    def test_unexpected_exception_does_not_leak_request_response_or_token(self) -> None:
        secret = "Bearer TOPSECRET raw-response"
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            exit_code = main(self._inspect_args(), fetcher=FixtureFetcher(error=RuntimeError(secret)))
        self.assertNotEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "contribution-error: internal-error\n")
        self.assertNotIn("TOPSECRET", stderr.getvalue())
        self.assertFalse(self.result.exists())

    def test_materialize_writes_partial_record_pr_body_and_safe_outputs(self) -> None:
        self.assertEqual(
            main(self._inspect_args(), fetcher=FixtureFetcher(self._openreview_fixture())),
            0,
        )
        pr_body = self.root / "pr.md"
        exit_code = main(
            [
                "materialize",
                "--result", str(self.result),
                "--catalog", str(self.catalog),
                "--issue-number", "7",
                "--pr-body", str(pr_body),
                "--github-output", str(self.output),
            ]
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("Portfolio Learning", self.catalog.read_text(encoding="utf-8"))
        self.assertIn("Issue #7", pr_body.read_text(encoding="utf-8"))
        self.assertEqual(
            self.output.read_text(encoding="utf-8"),
            "record_id=2025-icml-ada-a-portfolio-learning\n"
            "branch=contrib/issue-7-2025-icml-ada-a-portfolio-learning\n",
        )

    def test_materialize_rejects_invalid_issue_before_catalog_write(self) -> None:
        self.assertEqual(
            main(self._inspect_args(), fetcher=FixtureFetcher(self._openreview_fixture())),
            0,
        )
        before = self.catalog.read_bytes()
        with contextlib.redirect_stderr(io.StringIO()):
            exit_code = main(
                [
                    "materialize",
                    "--result", str(self.result),
                    "--catalog", str(self.catalog),
                    "--issue-number", "0",
                    "--pr-body", str(self.root / "pr.md"),
                    "--github-output", str(self.output),
                ]
            )
        self.assertNotEqual(exit_code, 0)
        self.assertEqual(self.catalog.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
