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

First, read [the encyclical](https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20250515-magnifica-humanitas.html).

Next, choose how you'd like to use its principles to evaluate a subject.

| Path | Use when | File or workflow |
| --- | --- | --- |
| Worksheet | Write a review in a Markdown worksheet | [`magnifica-humanitas-review-worksheet.md`](magnifica-humanitas-review-worksheet.md) |
| Issue review | Write a review in a GitHub issue | [Magnifica Humanitas Review issue template](https://github.com/mrjf/encyclical/issues/new?template=magnifica-humanitas-review.yml)) |
| Agentic review | Request an agent-written report in an issue | [Request for Review issue template]((https://github.com/mrjf/encyclical/issues/new?template=request-for-review.yml)) |
| Agent skill | The Agent Skill source  | [`magnifica-humanitas-review/SKILL.md`](magnifica-humanitas-review/SKILL.md) |

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

Use the [Request for Review issue template](.github/ISSUE_TEMPLATE/request-for-review.yml) when you want a full agentic review (on my dime).

Include the review boundary, the highest-stakes questions, and relevant URLs. The requester should provide enough context for a non-interactive run, since the agent can't ask you any questions once you submit. Works best for public projects the agent can research on its own.

The [`request-for-review`](.github/workflows/request-for-review.yml) workflow runs only after admin approval, since the consumed inference is charged to the repo owner.

---

## 05. For agents

Ask your agent:

```text
Use https://github.com/mrjf/encyclical/blob/main/magnifica-humanitas-review/SKILL.md to help me review ...
```

Or take the skill and install it: [`magnifica-humanitas-review/SKILL.md`](magnifica-humanitas-review/SKILL.md)

It produces a densely linked Markdown report with per-metric scores, deal-breaker analysis, and the deterministic `0`–`100` score.

---

## 06. Reference

| File | Purpose |
| --- | --- |
| [`encyclical-summary.md`](encyclical-summary.md) | Summary of the encyclical’s core arguments |
| [`encyclical-rubric.md`](encyclical-rubric.md) | Full 30-criterion rubric, evidence guidance, and deal-breaker flags |
