"""Workflow-facing CLI for paper suggestion inspection."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from scripts.catalog import load_catalog

from .check import inspect_submission
from .github import GitHubClient, GitHubError
from .http import SourceError
from .issue_form import SubmissionError, parse_issue_form
from .models import BaseMetadata, InspectionResult, ResultError
from .materialize import (
    MaterializeError,
    append_partial_record,
    branch_name,
    partial_record,
    render_pr_body,
)
from .report import render_problem_report, render_report, state_label
from .sources import Fetcher, extract_metadata


_TITLE_PREFIX = "[Paper suggestion]"


class CliError(ValueError):
    """A stable command-boundary error."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class _IssueEvent:
    number: int
    title: str
    body: str
    actor: str


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise CliError("invalid-json") from None


def _load_event(path: Path) -> _IssueEvent:
    value = _load_json(path)
    if not isinstance(value, dict):
        raise CliError("invalid-event")
    issue = value.get("issue")
    sender = value.get("sender")
    if not isinstance(issue, dict) or not isinstance(sender, dict):
        raise CliError("invalid-event")
    number = issue.get("number")
    title = issue.get("title")
    body = issue.get("body")
    actor = sender.get("login")
    if (
        type(number) is not int
        or number <= 0
        or not isinstance(title, str)
        or not title.startswith(_TITLE_PREFIX)
        or not isinstance(body, str)
        or not isinstance(actor, str)
        or not actor.strip()
    ):
        raise CliError("invalid-event")
    return _IssueEvent(number=number, title=title, body=body, actor=actor)


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _write_report_and_label(report_path: Path, label_path: Path, report: str, label: str) -> None:
    _atomic_write(report_path, report.encode("utf-8"))
    _atomic_write(label_path, f"{label}\n".encode("utf-8"))


def _write_result(path: Path, result: InspectionResult) -> None:
    data = json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _atomic_write(path, data.encode("utf-8"))


def _unresolved(url: str, code: str) -> BaseMetadata:
    return BaseMetadata(
        submitted_url=url,
        canonical_url=None,
        title=None,
        authors=(),
        venue=None,
        year=None,
        paper_url=None,
        errors=(code,),
    )


def _inspect_event(args: argparse.Namespace, *, fetcher: Fetcher | None) -> int:
    event = _load_event(args.event)
    try:
        submission = parse_issue_form(event.body)
    except SubmissionError as error:
        try:
            args.result.unlink()
        except FileNotFoundError:
            pass
        _write_report_and_label(
            args.report,
            args.labels,
            render_problem_report(error.code),
            "needs-metadata",
        )
        return 0
    try:
        metadata = extract_metadata(submission.paper_url, fetcher)
    except SourceError as error:
        metadata = _unresolved(submission.paper_url, error.code)
    result = inspect_submission(submission, metadata, load_catalog(args.catalog))
    report = render_report(result)
    label = state_label(result)
    _write_result(args.result, result)
    _write_report_and_label(args.report, args.labels, report, label)
    return 0


def _client(injected: object | None) -> object:
    if injected is not None:
        return injected
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    return GitHubClient(repository, token)


def _sync_issue(args: argparse.Namespace, *, github_client: object | None) -> int:
    event = _load_event(args.event)
    try:
        report = args.report.read_text(encoding="utf-8")
        label_text = args.labels.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        raise CliError("invalid-artifact") from None
    if label_text.count("\n") != 1 or not label_text.endswith("\n"):
        raise CliError("invalid-artifact")
    label = label_text[:-1]
    client = _client(github_client)
    client.sync_issue(event.number, report, label)  # type: ignore[attr-defined]
    return 0


def _append_output(path: Path, key: str, value: str) -> None:
    valid = False
    if key == "authorized":
        valid = value in {"true", "false"}
    elif key == "record_id":
        valid = re.fullmatch(r"[0-9]{4}-[a-z0-9]+(?:-[a-z0-9]+){2,}", value) is not None
    elif key == "branch":
        valid = re.fullmatch(r"contrib/issue-[1-9][0-9]*-[a-z0-9]+(?:-[a-z0-9]+)+", value) is not None
    if not valid:
        raise CliError("invalid-output")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(f"{key}={value}\n")
    except OSError:
        raise CliError("output-write-failed") from None


def _authorize_event(args: argparse.Namespace, *, github_client: object | None) -> int:
    event = _load_event(args.event)
    client = _client(github_client)
    allowed = client.actor_can_write(event.actor)  # type: ignore[attr-defined]
    _append_output(args.github_output, "authorized", "true" if allowed else "false")
    return 0


def _load_result(path: Path) -> InspectionResult:
    try:
        return InspectionResult.from_dict(_load_json(path))
    except ResultError:
        raise CliError("invalid-result") from None


def _materialize(args: argparse.Namespace) -> int:
    result = _load_result(args.result)
    preview = partial_record(result)
    record_id = preview["id"]
    if not isinstance(record_id, str):
        raise MaterializeError("invalid-record-id")
    branch = branch_name(args.issue_number, record_id)
    written_id = append_partial_record(args.catalog, result)
    if written_id != record_id:
        raise MaterializeError("record-id-changed")
    body = render_pr_body(args.issue_number, result)
    _atomic_write(args.pr_body, body.encode("utf-8"))
    _append_output(args.github_output, "record_id", record_id)
    _append_output(args.github_output, "branch", branch)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paper-contribution")
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect-event")
    inspect.add_argument("--event", type=Path, required=True)
    inspect.add_argument("--catalog", type=Path, required=True)
    inspect.add_argument("--result", type=Path, required=True)
    inspect.add_argument("--report", type=Path, required=True)
    inspect.add_argument("--labels", type=Path, required=True)

    sync = commands.add_parser("sync-issue")
    sync.add_argument("--event", type=Path, required=True)
    sync.add_argument("--report", type=Path, required=True)
    sync.add_argument("--labels", type=Path, required=True)

    authorize = commands.add_parser("authorize-event")
    authorize.add_argument("--event", type=Path, required=True)
    authorize.add_argument("--github-output", type=Path, required=True)

    materialize = commands.add_parser("materialize")
    materialize.add_argument("--result", type=Path, required=True)
    materialize.add_argument("--catalog", type=Path, required=True)
    materialize.add_argument("--issue-number", type=int, required=True)
    materialize.add_argument("--pr-body", type=Path, required=True)
    materialize.add_argument("--github-output", type=Path, required=True)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    fetcher: Fetcher | None = None,
    github_client: object | None = None,
) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "inspect-event":
            return _inspect_event(args, fetcher=fetcher)
        if args.command == "sync-issue":
            return _sync_issue(args, github_client=github_client)
        if args.command == "authorize-event":
            return _authorize_event(args, github_client=github_client)
        if args.command == "materialize":
            return _materialize(args)
        raise CliError("invalid-command")
    except CliError as error:
        print(f"contribution-error: {error.code}", file=sys.stderr)
        return 2
    except (GitHubError, ResultError):
        print("contribution-error: invalid-artifact", file=sys.stderr)
        return 2
    except MaterializeError:
        print("contribution-error: materialization-blocked", file=sys.stderr)
        return 2
    except Exception:
        print("contribution-error: internal-error", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
