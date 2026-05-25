#!/usr/bin/env python3
"""Deterministically calculate Magnifica Humanitas report scores."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


METRIC_COUNT = 30
MAX_PER_METRIC = 3
MAX_TOTAL = METRIC_COUNT * MAX_PER_METRIC

SCORECARD_START = "<!-- METRIC-SCORECARD:START -->"
SCORECARD_END = "<!-- METRIC-SCORECARD:END -->"
OVERALL_START = "<!-- OVERALL-SCORE:START -->"
OVERALL_END = "<!-- OVERALL-SCORE:END -->"
BLOCK_START = "<!-- DETERMINISTIC-SCORE:START -->"
BLOCK_END = "<!-- DETERMINISTIC-SCORE:END -->"

SECTION_RANGES = [
    ("Human dignity", range(1, 4)),
    ("Common good", range(4, 7)),
    ("Truth and communication", range(7, 10)),
    ("Freedom and responsibility", range(10, 13)),
    ("Work and economy", range(13, 16)),
    ("Participation and subsidiarity", range(16, 19)),
    ("AI and technology governance", range(19, 22)),
    ("Safety, peace, and harm prevention", range(22, 25)),
    ("Environment and supply chains", range(25, 28)),
    ("Public-interest posture", range(28, 31)),
]


class ScoreError(ValueError):
    """Raised when a report cannot be scored deterministically."""


def extract_between(text: str, start: str, end: str) -> str:
    start_index = text.find(start)
    if start_index == -1:
        raise ScoreError(f"Missing marker: {start}")
    content_start = start_index + len(start)
    end_index = text.find(end, content_start)
    if end_index == -1:
        raise ScoreError(f"Missing marker: {end}")
    return text[content_start:end_index]


def replace_between(text: str, start: str, end: str, replacement: str) -> str:
    start_index = text.find(start)
    if start_index == -1:
        raise ScoreError(f"Missing marker: {start}")
    content_start = start_index + len(start)
    end_index = text.find(end, content_start)
    if end_index == -1:
        raise ScoreError(f"Missing marker: {end}")
    return text[:content_start] + replacement + text[end_index:]


def split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def parse_score_cell(cell: str, metric_number: int) -> int:
    normalized = cell.replace("`", "").strip()
    if "*(" in normalized:
        raise ScoreError(
            f"Metric {metric_number} still has an unresolved score placeholder: {cell}"
        )
    match = re.fullmatch(r"(?:score\s*[:=]\s*)?([0-3])(?:\s*/\s*3)?", normalized, re.I)
    if not match:
        raise ScoreError(
            f"Metric {metric_number} score must be a bare integer 0, 1, 2, or 3; got: {cell}"
        )
    return int(match.group(1))


def parse_scores(markdown: str) -> dict[int, int]:
    scorecard = extract_between(markdown, SCORECARD_START, SCORECARD_END)
    scores: dict[int, int] = {}

    for line in scorecard.splitlines():
        cells = split_markdown_row(line)
        if len(cells) < 4:
            continue
        if not re.fullmatch(r"\d{1,2}", cells[0]):
            continue
        metric_number = int(cells[0])
        if metric_number < 1 or metric_number > METRIC_COUNT:
            raise ScoreError(f"Unexpected metric number in scorecard: {metric_number}")
        if metric_number in scores:
            raise ScoreError(f"Duplicate metric number in scorecard: {metric_number}")
        scores[metric_number] = parse_score_cell(cells[2], metric_number)

    missing = [str(number) for number in range(1, METRIC_COUNT + 1) if number not in scores]
    if missing:
        raise ScoreError(f"Missing metric scores: {', '.join(missing)}")

    return scores


def orientation_band(overall_score: float) -> str:
    if overall_score <= 20:
        return "Babel"
    if overall_score < 40:
        return "Babel-leaning"
    if overall_score < 60:
        return "Mixed"
    if overall_score < 80:
        return "Jerusalem-leaning"
    return "Jerusalem"


def summarize(scores: dict[int, int]) -> dict[str, object]:
    total = sum(scores.values())
    overall = round(total / MAX_TOTAL * 100, 1)

    sections = []
    for section_name, metric_range in SECTION_RANGES:
        metric_numbers = list(metric_range)
        section_total = sum(scores[number] for number in metric_numbers)
        section_max = len(metric_numbers) * MAX_PER_METRIC
        sections.append(
            {
                "section": section_name,
                "metrics": f"{metric_numbers[0]}-{metric_numbers[-1]}",
                "raw_score": section_total,
                "raw_max": section_max,
                "average": round(section_total / len(metric_numbers), 2),
                "normalized": round(section_total / section_max * 100, 1),
            }
        )

    return {
        "overall_score": overall,
        "orientation_band": orientation_band(overall),
        "raw_score": total,
        "raw_max": MAX_TOTAL,
        "metric_count": METRIC_COUNT,
        "sections": sections,
        "scores": {str(number): scores[number] for number in range(1, METRIC_COUNT + 1)},
    }


def render_score_block(summary: dict[str, object]) -> str:
    lines = [
        f"**Overall score:** {summary['overall_score']:.1f}/100",
        f"**Raw score:** {summary['raw_score']}/{summary['raw_max']}",
        f"**Orientation band:** {summary['orientation_band']}",
        "",
        "| Section | Metrics | Raw score | Average /3 | Normalized /100 |",
        "|---|---:|---:|---:|---:|",
    ]
    for section in summary["sections"]:
        lines.append(
            "| {section} | {metrics} | {raw_score}/{raw_max} | {average:.2f} | {normalized:.1f} |".format(
                **section
            )
        )
    return "\n".join(lines)


def update_report(markdown: str, summary: dict[str, object]) -> str:
    updated = replace_between(
        markdown, OVERALL_START, OVERALL_END, f"{summary['overall_score']:.1f}/100"
    )
    updated = replace_between(
        updated, BLOCK_START, BLOCK_END, "\n" + render_score_block(summary) + "\n"
    )
    return updated


def check_report(markdown: str, summary: dict[str, object]) -> None:
    expected_overall = f"{summary['overall_score']:.1f}/100"
    actual_overall = extract_between(markdown, OVERALL_START, OVERALL_END).strip()
    if actual_overall != expected_overall:
        raise ScoreError(
            f"Overall score marker is {actual_overall!r}; expected {expected_overall!r}"
        )

    expected_block = render_score_block(summary).strip()
    actual_block = extract_between(markdown, BLOCK_START, BLOCK_END).strip()
    if actual_block != expected_block:
        raise ScoreError("Deterministic score block does not match metric scores")


def load_report(path_arg: str) -> tuple[str, Path | None]:
    if path_arg == "-":
        return sys.stdin.read(), None
    path = Path(path_arg)
    return path.read_text(encoding="utf-8"), path


def run_self_test() -> None:
    rows = [
        SCORECARD_START,
        "| # | Metric | Score | Assessment and evidence | Principle links |",
        "|---:|---|---:|---|---|",
    ]
    rows.extend(
        f"| {number} | Metric {number} | `2` | Evidence | Links |"
        for number in range(1, METRIC_COUNT + 1)
    )
    rows.append(SCORECARD_END)
    fixture = "\n".join(
        [
            "- **Overall score:** "
            + OVERALL_START
            + "*( deterministic overall score )"
            + OVERALL_END,
            BLOCK_START,
            "*( deterministic score block )",
            BLOCK_END,
            *rows,
        ]
    )
    summary = summarize(parse_scores(fixture))
    if summary["overall_score"] != 66.7:
        raise AssertionError(f"Expected 66.7, got {summary['overall_score']}")
    updated = update_report(fixture, summary)
    check_report(updated, summary)
    print("self-test passed")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Calculate and optionally write the deterministic 0-100 Magnifica Humanitas score."
    )
    parser.add_argument("report", nargs="?", help="Markdown report path, or '-' for stdin")
    parser.add_argument("--write", action="store_true", help="Update deterministic score markers")
    parser.add_argument("--check", action="store_true", help="Verify deterministic score markers")
    parser.add_argument("--json", action="store_true", help="Print machine-readable score summary")
    parser.add_argument("--self-test", action="store_true", help="Run built-in parser tests")
    args = parser.parse_args()

    try:
        if args.self_test:
            run_self_test()
            return 0

        if not args.report:
            raise ScoreError("A report path is required unless --self-test is used")

        markdown, path = load_report(args.report)
        summary = summarize(parse_scores(markdown))

        if args.write:
            if path is None:
                raise ScoreError("--write requires a file path, not stdin")
            markdown = update_report(markdown, summary)
            path.write_text(markdown, encoding="utf-8")

        if args.check:
            check_report(markdown, summary)

        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            if args.write:
                print(f"updated {path}")
            print(render_score_block(summary))

        return 0
    except ScoreError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
