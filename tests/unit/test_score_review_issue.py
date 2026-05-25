"""Tests for ``.github/scripts/score_review_issue.py``."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".github" / "scripts"))
sys.path.insert(0, str(ROOT / "magnifica-humanitas-review" / "scripts"))

from finalize_score import METRIC_COUNT, ScoreError, summarize  # noqa: E402
from score_review_issue import (  # noqa: E402
    COMMENT_MARKER,
    parse_issue_scores,
    render_comment,
    render_error_comment,
)


# Mirror the dropdown options from the issue template.
DROPDOWN_OPTIONS = {
    0: "0 \u2013 Harms or ignores",
    1: "1 \u2013 Weak or symbolic",
    2: "2 \u2013 Meaningful but incomplete",
    3: "3 \u2013 Strong and accountable",
}


def build_issue_body(scores: dict[int, int]) -> str:
    """Build an issue body that mimics how GitHub renders the form."""
    parts: list[str] = [
        "### Subject reviewed\n\nAcme Example\n",
        "### Owner / sponsor\n\nAcme Corp\n",
    ]
    for number in range(1, METRIC_COUNT + 1):
        score = scores[number]
        parts.append(
            f"### {number}. Sample metric question {number} \u2014 details?\n\n"
            f"{DROPDOWN_OPTIONS[score]}\n\n"
            f"### Evidence for metric {number}\n\nSome evidence text.\n"
        )
    parts.append("### Babel or Jerusalem?\n\nMostly Jerusalem.\n")
    return "\n".join(parts)


class ParseIssueScoresTest(unittest.TestCase):
    def test_parses_all_thirty_metrics(self):
        scores = {n: (n % 4) for n in range(1, METRIC_COUNT + 1)}
        parsed = parse_issue_scores(build_issue_body(scores))
        self.assertEqual(parsed, scores)

    def test_summarize_matches_finalize_score_logic(self):
        scores = {n: 2 for n in range(1, METRIC_COUNT + 1)}
        parsed = parse_issue_scores(build_issue_body(scores))
        summary = summarize(parsed)
        # 30 metrics * 2 / 90 max = 66.7
        self.assertEqual(summary["overall_score"], 66.7)
        self.assertEqual(summary["raw_score"], 60)
        self.assertEqual(summary["raw_max"], 90)
        self.assertEqual(summary["orientation_band"], "Jerusalem-leaning")

    def test_missing_metric_raises(self):
        body = build_issue_body({n: 2 for n in range(1, METRIC_COUNT + 1)})
        # Drop the heading + answer for metric 17.
        body = body.replace(
            "### 17. Sample metric question 17 \u2014 details?\n\n"
            "2 \u2013 Meaningful but incomplete\n\n",
            "",
        )
        with self.assertRaises(ScoreError) as ctx:
            parse_issue_scores(body)
        self.assertIn("17", str(ctx.exception))

    def test_no_response_raises(self):
        scores = {n: 2 for n in range(1, METRIC_COUNT + 1)}
        body = build_issue_body(scores).replace(
            "2 \u2013 Meaningful but incomplete", "_No response_", 1
        )
        with self.assertRaises(ScoreError) as ctx:
            parse_issue_scores(body)
        self.assertIn("no selected score", str(ctx.exception))

    def test_tolerates_crlf_line_endings(self):
        scores = {n: 3 for n in range(1, METRIC_COUNT + 1)}
        body = build_issue_body(scores).replace("\n", "\r\n")
        parsed = parse_issue_scores(body)
        self.assertEqual(parsed, scores)


class RenderCommentTest(unittest.TestCase):
    def test_comment_includes_marker_and_overall(self):
        scores = {n: 3 for n in range(1, METRIC_COUNT + 1)}
        summary = summarize(scores)
        rendered = render_comment(summary)
        self.assertTrue(rendered.startswith(COMMENT_MARKER))
        self.assertIn("100.0/100", rendered)
        self.assertIn("Jerusalem", rendered)
        # Ensure every section row is present in the table.
        for section_name, _ in [
            ("Human dignity", None),
            ("Common good", None),
            ("Truth and communication", None),
            ("Freedom and responsibility", None),
            ("Work and economy", None),
            ("Participation and subsidiarity", None),
            ("AI and technology governance", None),
            ("Safety, peace, and harm prevention", None),
            ("Environment and supply chains", None),
            ("Public-interest posture", None),
        ]:
            self.assertIn(section_name, rendered)

    def test_error_comment_starts_with_marker(self):
        rendered = render_error_comment(ScoreError("boom"))
        self.assertTrue(rendered.startswith(COMMENT_MARKER))
        self.assertIn("boom", rendered)


if __name__ == "__main__":
    unittest.main()
