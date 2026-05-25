"""Tests for ``.github/scripts/prepare_rfr_review.py``."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".github" / "scripts"))

from prepare_rfr_review import (  # noqa: E402
    APPROVAL_LABEL,
    APPROVER,
    REQUEST_LABEL,
    render_prompt,
    should_run_review,
)


def build_event(
    *,
    action: str = "labeled",
    event_label: str = APPROVAL_LABEL,
    sender: str = APPROVER,
    issue_labels: list[str] | None = None,
) -> dict[str, object]:
    labels = issue_labels if issue_labels is not None else [REQUEST_LABEL, APPROVAL_LABEL]
    return {
        "action": action,
        "label": {"name": event_label},
        "sender": {"login": sender},
        "issue": {
            "number": 12,
            "title": "Request for Review: Example",
            "html_url": "https://github.com/mrjf/encyclical/issues/12",
            "body": (
                "### What should be reviewed?\n\nExample Tool\n\n"
                "### Relevant URLs\n\nhttps://example.com/product\n"
            ),
            "labels": [{"name": label} for label in labels],
            "user": {"login": "requester"},
        },
    }


class ShouldRunReviewTest(unittest.TestCase):
    def test_accepts_exact_approval_event(self) -> None:
        should_run, reason = should_run_review(build_event())
        self.assertTrue(should_run, reason)

    def test_rejects_approval_from_anyone_else(self) -> None:
        should_run, reason = should_run_review(build_event(sender="someone-else"))
        self.assertFalse(should_run)
        self.assertIn(APPROVER, reason)

    def test_rejects_non_approval_label_event(self) -> None:
        should_run, reason = should_run_review(build_event(event_label=REQUEST_LABEL))
        self.assertFalse(should_run)
        self.assertIn(APPROVAL_LABEL, reason)

    def test_rejects_issue_without_request_label(self) -> None:
        should_run, reason = should_run_review(build_event(issue_labels=[APPROVAL_LABEL]))
        self.assertFalse(should_run)
        self.assertIn(REQUEST_LABEL, reason)


class RenderPromptTest(unittest.TestCase):
    def test_prompt_is_non_interactive_and_mentions_skill(self) -> None:
        prompt = render_prompt(build_event(), "rfr-report.md")
        self.assertIn("non-interactive", prompt)
        self.assertIn("Do not ask", prompt)
        self.assertIn("web search", prompt)
        self.assertIn("magnifica-humanitas-review/SKILL.md", prompt)
        self.assertIn("https://example.com/product", prompt)
        self.assertIn("rfr-report.md", prompt)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    raise SystemExit(0 if result.wasSuccessful() else 1)
