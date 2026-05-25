#!/usr/bin/env python3
"""Parse a Magnifica Humanitas Review issue body and render a score comment.

The issue template at ``.github/ISSUE_TEMPLATE/magnifica-humanitas-review.yml``
collects 30 dropdown scores (``score-1`` through ``score-30``). When GitHub
renders the submitted form into the issue body, each dropdown becomes a
``### <label>`` heading followed by the selected option text such as
``2 – Meaningful but incomplete``.

This script is the deterministic counterpart for those issues: it reads the
issue body, extracts the 30 metric scores, reuses the scoring helpers from
``magnifica-humanitas-review/scripts/finalize_score.py`` so the math matches
the agent-skill report, and prints a Markdown comment summarising the result.
A leading HTML comment marker lets the workflow upsert the same comment when
the issue is edited.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "magnifica-humanitas-review" / "scripts"))

from finalize_score import (  # noqa: E402
    METRIC_COUNT,
    ScoreError,
    orientation_band,
    summarize,
)


COMMENT_MARKER = "<!-- magnifica-humanitas-score -->"
NO_RESPONSE = "_No response_"


def parse_issue_scores(body: str) -> dict[int, int]:
    """Extract the 30 metric scores from an issue-form body.

    Each dropdown is rendered as ``### N. <label>`` followed by a blank line
    and then the selected option text (for example ``2 – Meaningful but
    incomplete``). We tolerate the en-dash, em-dash and ASCII hyphen so manual
    edits keep working.
    """

    # GitHub may use CRLF line endings on Windows-edited submissions.
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")

    scores: dict[int, int] = {}
    # Match a heading like "### 7. Truthfulness — ..." capturing the metric
    # number, then everything up to the next "### " heading (or end of body).
    pattern = re.compile(
        r"^###[ \t]+(\d{1,2})\.[ \t][^\n]*\n(.*?)(?=^###[ \t]|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    for match in pattern.finditer(normalized):
        metric_number = int(match.group(1))
        if metric_number < 1 or metric_number > METRIC_COUNT:
            continue
        if metric_number in scores:
            raise ScoreError(
                f"Metric {metric_number} appears more than once in the issue body"
            )

        # Pull the first non-empty line of the answer block.
        answer = ""
        for line in match.group(2).splitlines():
            stripped = line.strip()
            if stripped:
                answer = stripped
                break

        if not answer or answer == NO_RESPONSE:
            raise ScoreError(f"Metric {metric_number} has no selected score")

        score_match = re.match(r"([0-3])\s*[\u2014\u2013\-]", answer)
        if not score_match:
            raise ScoreError(
                f"Metric {metric_number} score is not recognisable: {answer!r}"
            )
        scores[metric_number] = int(score_match.group(1))

    missing = [str(n) for n in range(1, METRIC_COUNT + 1) if n not in scores]
    if missing:
        raise ScoreError(
            "Missing metric scores: "
            + ", ".join(missing)
            + ". Make sure every dropdown is answered."
        )
    return scores


def render_comment(summary: dict[str, object]) -> str:
    overall = float(summary["overall_score"])
    lines = [
        COMMENT_MARKER,
        "## Magnifica Humanitas score",
        "",
        f"**Overall score:** {overall:.1f}/100",
        f"**Raw score:** {summary['raw_score']}/{summary['raw_max']}",
        f"**Orientation band:** {summary['orientation_band']}",
        "",
        "| Section | Metrics | Raw score | Average /3 | Normalized /100 |",
        "|---|---:|---:|---:|---:|",
    ]
    for section in summary["sections"]:
        avg = section["average"]
        norm = section["normalized"]
        avg_str = f"{avg:.2f}" if isinstance(avg, (int, float)) else avg
        norm_str = f"{norm:.1f}" if isinstance(norm, (int, float)) else norm
        lines.append(
            f"| {section['section']} | {section['metrics']} | "
            f"{section['raw_score']}/{section['raw_max']} | {avg_str} | {norm_str} |"
        )
    lines.extend(
        [
            "",
            "_Scored automatically from the issue form. Edit the issue to update "
            "scores; this comment will refresh._",
        ]
    )
    return "\n".join(lines) + "\n"


def render_error_comment(error: Exception) -> str:
    return (
        f"{COMMENT_MARKER}\n"
        "## Magnifica Humanitas score\n\n"
        "Could not compute a deterministic score from this issue:\n\n"
        f"> {error}\n\n"
        "_This comment will refresh when the issue is edited._\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "body",
        nargs="?",
        help="Path to a file containing the issue body, or '-' for stdin.",
    )
    args = parser.parse_args()

    if not args.body or args.body == "-":
        body = sys.stdin.read()
    else:
        body = Path(args.body).read_text(encoding="utf-8")

    try:
        scores = parse_issue_scores(body)
        summary = summarize({n: scores[n] for n in range(1, METRIC_COUNT + 1)})
        # Sanity check: the orientation band derives from the overall score.
        assert summary["orientation_band"] == orientation_band(
            float(summary["overall_score"])
        )
        sys.stdout.write(render_comment(summary))
        return 0
    except ScoreError as error:
        sys.stdout.write(render_error_comment(error))
        # Exit 0 so the workflow can still post the explanatory comment.
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
