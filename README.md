# Magnifica Humanitas Evaluation

Evaluate a tool, policy, product, AI system, institution, or initiative against the principles of [*Magnifica Humanitas*](https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20250515-magnifica-humanitas.html).

| Field | Value |
| --- | --- |
| Method | 30 criteria scored from `0` to `3` |
| Output | A deterministic Babel-to-Jerusalem score from `0` to `100` |
| Use cases | Manual worksheets, GitHub issue reviews, agentic reports |
| Core question | Does this build Babel or help rebuild Jerusalem? |

---

## 01. Start here

Choose the path that matches the work.

| Path | Use when | File or workflow |
| --- | --- | --- |
| Worksheet | You want a manual review with no AI required | [`magnifica-humanitas-review-worksheet.md`](magnifica-humanitas-review-worksheet.md) |
| Issue review | You want to submit scored answers in GitHub | [Magnifica Humanitas Review issue template](.github/ISSUE_TEMPLATE/magnifica-humanitas-review.yml) |
| Agentic review | You want an approved non-interactive agent report | [Request for Review issue template](.github/ISSUE_TEMPLATE/request-for-review.yml) |
| Agent skill | You want to run the bundled review skill directly | [`magnifica-humanitas-review/SKILL.md`](magnifica-humanitas-review/SKILL.md) |

---

## 02. Manual review

Copy [`magnifica-humanitas-review-worksheet.md`](magnifica-humanitas-review-worksheet.md) and fill it out.

The worksheet walks through all 30 metrics, asks for score evidence, and produces section averages, deal-breaker flags, and an overall Babel-to-Jerusalem score.

---

## 03. GitHub issue review

Open **Issues → New Issue → Magnifica Humanitas Review**.

The issue template asks the same 30 questions as dropdown scores with room for evidence and summary judgment.

When a review issue is opened or edited, [`score-review-issue`](.github/workflows/score-review-issue.yml) parses the dropdown scores and posts or updates the deterministic score comment.

---

## 04. Agentic review

Use the [Request for Review issue template](.github/ISSUE_TEMPLATE/request-for-review.yml) when you want a full agentic review.

Include the review boundary, the highest-stakes questions, and relevant URLs. The requester should provide enough context for a non-interactive run.

The [`request-for-review`](.github/workflows/request-for-review.yml) workflow runs only after @mrjf applies `approved-for-review` to an issue labeled `request-for-review`.

---

## 05. For agents

The [`magnifica-humanitas-review/`](magnifica-humanitas-review/) directory contains the review skill.

It produces a densely linked Markdown report with per-metric scores, deal-breaker analysis, and the deterministic `0`–`100` score.

Read [`magnifica-humanitas-review/SKILL.md`](magnifica-humanitas-review/SKILL.md) before running or editing the skill.

---

## 06. Reference

| File | Purpose |
| --- | --- |
| [`encyclical-summary.md`](encyclical-summary.md) | Secular summary of the encyclical’s core arguments |
| [`encyclical-rubric.md`](encyclical-rubric.md) | Full 30-criterion rubric, evidence guidance, and deal-breaker flags |
