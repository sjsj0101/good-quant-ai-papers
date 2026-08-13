"""Minimal GitHub REST operations for paper-suggestion Issues."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import quote, urlsplit

from .report import MACHINE_STATES, REPORT_MARKER


_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_NEXT_LINK_RE = re.compile(r'<([^>]+)>;\s*rel="next"')
_MAX_PAGES = 20


class GitHubError(ValueError):
    """A stable GitHub orchestration error."""


@dataclass(frozen=True)
class ApiResponse:
    status: int
    headers: dict[str, str]
    data: object


class ApiTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        payload: object,
        headers: dict[str, str],
    ) -> ApiResponse:
        ...


class _UrllibTransport:
    def request(
        self,
        method: str,
        url: str,
        payload: object,
        headers: dict[str, str],
    ) -> ApiResponse:
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise GitHubError("github-response-too-large")
                data = json.loads(raw.decode("utf-8")) if raw else None
                return ApiResponse(
                    status=response.status,
                    headers={key.casefold(): value for key, value in response.headers.items()},
                    data=data,
                )
        except urllib.error.HTTPError as error:
            return ApiResponse(
                status=error.code,
                headers={key.casefold(): value for key, value in error.headers.items()},
                data=None,
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            raise GitHubError("github-unavailable") from None


class GitHubClient:
    def __init__(
        self,
        repository: str,
        token: str,
        *,
        transport: ApiTransport | None = None,
    ) -> None:
        if not isinstance(repository, str) or _REPOSITORY_RE.fullmatch(repository) is None:
            raise GitHubError("invalid-repository")
        if not isinstance(token, str) or not token:
            raise GitHubError("missing-token")
        self.repository = repository
        self._root = f"https://api.github.com/repos/{repository}"
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        }
        self._transport = transport or _UrllibTransport()

    def _request(
        self,
        method: str,
        url: str,
        *,
        payload: object = None,
        expected: frozenset[int] = frozenset({200}),
    ) -> ApiResponse:
        response = self._transport.request(method, url, payload, dict(self._headers))
        if response.status not in expected:
            raise GitHubError("github-api-error")
        return response

    def _safe_next(self, value: str) -> str:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "api.github.com"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or not parsed.path.startswith(f"/repos/{self.repository}/")
        ):
            raise GitHubError("unsafe-pagination")
        return value

    def _pages(self, url: str) -> list[object]:
        items: list[object] = []
        current: str | None = url
        pages = 0
        while current is not None:
            pages += 1
            if pages > _MAX_PAGES:
                raise GitHubError("too-many-pages")
            response = self._request("GET", current)
            if not isinstance(response.data, list):
                raise GitHubError("invalid-github-response")
            items.extend(response.data)
            link = response.headers.get("link", "")
            match = _NEXT_LINK_RE.search(link)
            current = self._safe_next(match.group(1)) if match else None
        return items

    @staticmethod
    def _issue_number(value: object) -> int:
        if type(value) is not int or value <= 0:
            raise GitHubError("invalid-issue-number")
        return value

    def _upsert_marker_comment(self, issue_number: int, report: str) -> None:
        comments = self._pages(
            f"{self._root}/issues/{issue_number}/comments?per_page=100"
        )
        managed_id: int | None = None
        for comment in comments:
            if not isinstance(comment, dict):
                continue
            body = comment.get("body")
            comment_id = comment.get("id")
            if isinstance(body, str) and REPORT_MARKER in body and type(comment_id) is int:
                managed_id = comment_id
                break
        if managed_id is None:
            self._request(
                "POST",
                f"{self._root}/issues/{issue_number}/comments",
                payload={"body": report},
                expected=frozenset({201}),
            )
        else:
            self._request(
                "PATCH",
                f"{self._root}/issues/comments/{managed_id}",
                payload={"body": report},
            )

    def _issue_labels(self, issue_number: int) -> set[str]:
        labels = self._pages(f"{self._root}/issues/{issue_number}/labels?per_page=100")
        return {
            name
            for item in labels
            if isinstance(item, dict)
            if isinstance((name := item.get("name")), str)
        }

    def sync_issue(self, issue_number: int, report: str, state: str) -> None:
        issue_number = self._issue_number(issue_number)
        if not isinstance(report, str) or report.count(REPORT_MARKER) != 1:
            raise GitHubError("invalid-report")
        if state not in MACHINE_STATES:
            raise GitHubError("invalid-state")
        self._upsert_marker_comment(issue_number, report)
        current = self._issue_labels(issue_number)
        for label in sorted((current & MACHINE_STATES) - {state}):
            self._request(
                "DELETE",
                f"{self._root}/issues/{issue_number}/labels/{quote(label, safe='')}",
                expected=frozenset({200, 204, 404}),
            )
        if state not in current:
            self._request(
                "POST",
                f"{self._root}/issues/{issue_number}/labels",
                payload={"labels": [state]},
            )

    def actor_can_write(self, actor: str) -> bool:
        if not isinstance(actor, str) or not actor.strip() or len(actor) > 100:
            raise GitHubError("invalid-actor")
        response = self._request(
            "GET",
            f"{self._root}/collaborators/{quote(actor, safe='')}/permission",
        )
        if not isinstance(response.data, dict):
            raise GitHubError("invalid-github-response")
        permission = response.data.get("permission")
        return permission in {"write", "maintain", "admin"}
