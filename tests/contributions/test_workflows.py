from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


def load_workflow(name: str) -> dict:
    value = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("workflow must be a mapping")
    return value


def steps_by_id(workflow: dict, job: str) -> dict[str, dict]:
    steps = workflow["jobs"][job]["steps"]
    return {step["id"]: step for step in steps if "id" in step}


class InspectWorkflowTests(unittest.TestCase):
    def test_has_issue_events_minimal_permissions_and_per_issue_concurrency(self) -> None:
        workflow = load_workflow("inspect-paper-suggestion.yml")

        self.assertEqual(
            set(workflow["on"]["issues"]["types"]),
            {"opened", "edited", "reopened"},
        )
        self.assertEqual(
            workflow["permissions"],
            {"contents": "read", "issues": "write"},
        )
        self.assertIn("github.event.issue.number", workflow["concurrency"]["group"])
        self.assertIs(workflow["concurrency"]["cancel-in-progress"], True)
        self.assertIn(
            "startsWith(github.event.issue.title, '[Paper suggestion]')",
            workflow["jobs"]["inspect"]["if"],
        )

    def test_runs_inspection_then_sync_without_ai_configuration(self) -> None:
        workflow = load_workflow("inspect-paper-suggestion.yml")
        steps = steps_by_id(workflow, "inspect")

        self.assertIn("inspect-event", steps["inspect"]["run"])
        self.assertIn("sync-issue", steps["sync"]["run"])
        self.assertIn("steps.inspect.outcome == 'success'", steps["sync"]["if"])
        text = (WORKFLOWS / "inspect-paper-suggestion.yml").read_text(encoding="utf-8")
        self.assertNotIn("OPENAI", text)
        self.assertNotIn("enrich", text.casefold())


class MaterializeWorkflowTests(unittest.TestCase):
    def test_is_labeled_only_and_has_explicit_write_permissions(self) -> None:
        workflow = load_workflow("materialize-paper-suggestion.yml")

        self.assertEqual(workflow["on"]["issues"]["types"], ["labeled"])
        self.assertEqual(
            workflow["permissions"],
            {"contents": "write", "issues": "write", "pull-requests": "write"},
        )
        condition = workflow["jobs"]["materialize"]["if"]
        self.assertIn("[Paper suggestion]", condition)
        self.assertIn("github.event.label.name == 'approved'", condition)
        self.assertIs(workflow["concurrency"]["cancel-in-progress"], False)

    def test_authorizes_and_reinspects_before_any_repository_write(self) -> None:
        workflow = load_workflow("materialize-paper-suggestion.yml")
        steps = workflow["jobs"]["materialize"]["steps"]
        ids = [step.get("id") for step in steps]

        self.assertLess(ids.index("auth"), ids.index("inspect"))
        self.assertLess(ids.index("inspect"), ids.index("materialize"))
        self.assertLess(ids.index("materialize"), ids.index("push"))
        for step_id in ("inspect", "materialize", "push", "pr", "mark"):
            step = next(step for step in steps if step.get("id") == step_id)
            self.assertIn("steps.auth.outputs.authorized == 'true'", step["if"])
        self.assertIn("inspect-event", next(step for step in steps if step.get("id") == "inspect")["run"])

    def test_creates_only_partial_data_commit_and_draft_pr(self) -> None:
        text = (WORKFLOWS / "materialize-paper-suggestion.yml").read_text(encoding="utf-8")

        self.assertIn("git add data/papers.yaml", text)
        self.assertNotIn("data/coverage.yaml", text)
        self.assertIn("gh pr create --draft", text)
        self.assertIn("gh pr edit", text)
        self.assertIn("--add-label pr-created", text)
        self.assertNotIn("OPENAI", text)
        self.assertNotIn("scripts/render.py", text)
        self.assertNotIn("scripts/validate.py", text)
        self.assertNotRegex(text.casefold(), r"\bgh\s+pr\s+merge\b")


if __name__ == "__main__":
    unittest.main()
