# Magnifica Humanitas Evaluation

Evaluate any tool, project, policy, company, product, AI system, institution, or initiative against the principles of [*Magnifica Humanitas*](https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20250515-magnifica-humanitas.html). Score 30 criteria on a 0–3 scale and produce a Babel-to-Jerusalem overall score from 0 to 100.

## For People

No AI required. Two ways to conduct a review yourself:

### Worksheet

[**magnifica-humanitas-review-worksheet.md**](magnifica-humanitas-review-worksheet.md) — Copy this markdown file and fill it out. It walks you through every evaluation question, asks for a score and evidence for each of the 30 metrics, and produces a summary with section averages, deal-breaker flags, and an overall Babel-to-Jerusalem score.

### Issue Template

Use the [**Magnifica Humanitas Review** issue template](.github/ISSUE_TEMPLATE/magnifica-humanitas-review.yml) to submit a review as a GitHub issue. The template asks the same 30 questions as dropdown scores with space for evidence, and collects your summary judgment.

To use it: go to **Issues → New Issue → Magnifica Humanitas Review** in this repository.

## For AI Agents

The [`magnifica-humanitas-review/`](magnifica-humanitas-review/) directory contains an agent skill that automates the same evaluation. It produces a densely linked Markdown report with per-metric 0–3 scores, deal-breaker analysis, and a deterministic 0–100 overall score.

See [`magnifica-humanitas-review/SKILL.md`](magnifica-humanitas-review/SKILL.md) for the full skill specification.

## Background

- [**encyclical-summary.md**](encyclical-summary.md) — A secular summary of the encyclical's core arguments.
- [**encyclical-rubric.md**](encyclical-rubric.md) — The full 30-criterion evaluation rubric with evaluation questions, evidence guidance, and deal-breaker flags.
