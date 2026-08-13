from __future__ import annotations

import unittest

from scripts.contributions.github import ApiResponse, GitHubClient, GitHubError
from scripts.contributions.report import REPORT_MARKER


REPOSITORY = "acme/papers"
API_ROOT = f"https://api.github.com/repos/{REPOSITORY}"


class FakeTransport:
    def __init__(self, responses: list[ApiResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[tuple[str, str, object, dict[str, str]]] = []

    def request(
        self,
        method: str,
        url: str,
        payload: object,
        headers: dict[str, str],
    ) -> ApiResponse:
        self.requests.append((method, url, payload, headers))
        if not self.responses:
            raise AssertionError(f"unexpected request: {method} {url}")
        return self.responses.pop(0)


class GitHubSyncTests(unittest.TestCase):
    def test_paginates_updates_marker_and_reconciles_only_machine_state(self) -> None:
        comments = f"{API_ROOT}/issues/7/comments?per_page=100"
        comments_next = f"{comments}&page=2"
        labels = f"{API_ROOT}/issues/7/labels?per_page=100"
        labels_next = f"{labels}&page=2"
        transport = FakeTransport(
            [
                ApiResponse(200, {"link": f'<{comments_next}>; rel="next"'}, []),
                ApiResponse(200, {}, [{"id": 42, "body": REPORT_MARKER + "\nold"}]),
                ApiResponse(200, {}, {}),
                ApiResponse(200, {"link": f'<{labels_next}>; rel="next"'}, []),
                ApiResponse(200, {}, [{"name": "metadata-ready"}, {"name": "approved"}]),
                ApiResponse(204, {}, None),
                ApiResponse(200, {}, [{"name": "duplicate"}]),
            ]
        )
        client = GitHubClient(REPOSITORY, "token-value", transport=transport)

        client.sync_issue(7, REPORT_MARKER + "\nnew report", "duplicate")

        methods_urls = [(method, url) for method, url, _, _ in transport.requests]
        self.assertIn(("GET", comments_next), methods_urls)
        self.assertIn(("PATCH", f"{API_ROOT}/issues/comments/42"), methods_urls)
        self.assertIn(("GET", labels_next), methods_urls)
        self.assertIn(("DELETE", f"{API_ROOT}/issues/7/labels/metadata-ready"), methods_urls)
        self.assertNotIn(("DELETE", f"{API_ROOT}/issues/7/labels/approved"), methods_urls)
        self.assertIn(("POST", f"{API_ROOT}/issues/7/labels"), methods_urls)
        for _, _, _, headers in transport.requests:
            self.assertEqual(headers["Authorization"], "Bearer token-value")
            self.assertEqual(headers["X-GitHub-Api-Version"], "2022-11-28")

    def test_creates_comment_when_marker_does_not_exist(self) -> None:
        transport = FakeTransport(
            [
                ApiResponse(200, {}, []),
                ApiResponse(201, {}, {"id": 5}),
                ApiResponse(200, {}, []),
                ApiResponse(200, {}, [{"name": "metadata-ready"}]),
            ]
        )
        client = GitHubClient(REPOSITORY, "token", transport=transport)
        client.sync_issue(3, REPORT_MARKER + "\nreport", "metadata-ready")
        self.assertIn(
            ("POST", f"{API_ROOT}/issues/3/comments"),
            [(method, url) for method, url, _, _ in transport.requests],
        )

    def test_rejects_bad_marker_or_state_before_api_call(self) -> None:
        for report, state in (
            ("no marker", "metadata-ready"),
            (REPORT_MARKER + REPORT_MARKER, "metadata-ready"),
            (REPORT_MARKER, "approved"),
        ):
            transport = FakeTransport([])
            with self.subTest(report=report, state=state), self.assertRaises(GitHubError):
                GitHubClient(REPOSITORY, "token", transport=transport).sync_issue(1, report, state)
            self.assertEqual(transport.requests, [])

    def test_rejects_untrusted_pagination_url(self) -> None:
        transport = FakeTransport(
            [ApiResponse(200, {"link": '<https://evil.test/page=2>; rel="next"'}, [])]
        )
        with self.assertRaisesRegex(GitHubError, "unsafe-pagination"):
            GitHubClient(REPOSITORY, "token", transport=transport).sync_issue(
                1, REPORT_MARKER + "\nreport", "metadata-ready"
            )
        self.assertEqual(len(transport.requests), 1)


class GitHubPermissionTests(unittest.TestCase):
    def test_write_maintain_and_admin_are_authorized(self) -> None:
        for permission in ("write", "maintain", "admin"):
            with self.subTest(permission=permission):
                transport = FakeTransport([ApiResponse(200, {}, {"permission": permission})])
                self.assertTrue(
                    GitHubClient(REPOSITORY, "token", transport=transport).actor_can_write("reviewer")
                )

    def test_read_and_unknown_permissions_are_not_authorized(self) -> None:
        for permission in ("read", "triage", "unknown"):
            with self.subTest(permission=permission):
                transport = FakeTransport([ApiResponse(200, {}, {"permission": permission})])
                self.assertFalse(
                    GitHubClient(REPOSITORY, "token", transport=transport).actor_can_write("reviewer")
                )


if __name__ == "__main__":
    unittest.main()
