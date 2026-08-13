from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
FORM_PATH = ROOT / ".github" / "ISSUE_TEMPLATE" / "paper-suggestion.yml"


class IssueTemplateTests(unittest.TestCase):
    def test_form_has_stable_title_prefix_and_parser_headings(self) -> None:
        form = yaml.safe_load(FORM_PATH.read_text(encoding="utf-8"))

        self.assertEqual(form["title"], "[Paper suggestion] ")
        self.assertNotIn("labels", form)
        self.assertEqual(
            [item["attributes"]["label"] for item in form["body"]],
            ["Paper URL", "Scope acknowledgement"],
        )

    def test_url_and_acknowledgement_are_required(self) -> None:
        form = yaml.safe_load(FORM_PATH.read_text(encoding="utf-8"))
        url, acknowledgement = form["body"]

        self.assertEqual(url["type"], "input")
        self.assertIs(url["validations"]["required"], True)
        self.assertEqual(acknowledgement["type"], "checkboxes")
        self.assertIs(acknowledgement["validations"]["required"], True)
        self.assertEqual(len(acknowledgement["attributes"]["options"]), 1)
        self.assertIs(
            acknowledgement["attributes"]["options"][0]["required"], True
        )


if __name__ == "__main__":
    unittest.main()
