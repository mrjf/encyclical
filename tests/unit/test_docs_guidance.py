from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"


class DocsGuidanceTest(unittest.TestCase):
    def test_readme_uses_structured_markdown_overview(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn("| Field | Value |", text)
        self.assertIn("## 01. Start here", text)
        self.assertIn("## 05. For agents", text)
        self.assertIn("Does this build Babel or help rebuild Jerusalem?", text)

    def test_agents_records_swiss_markdown_style(self) -> None:
        text = AGENTS.read_text(encoding="utf-8")
        self.assertIn("mrjf/swiss-design-skill-md", text)
        self.assertIn("Structure is the grid", text)
        self.assertIn("native Markdown only", text)
        self.assertIn("Avoid CSS, scripts, custom fonts", text)


if __name__ == "__main__":
    unittest.main()
