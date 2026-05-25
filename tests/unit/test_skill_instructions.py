from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "magnifica-humanitas-review" / "SKILL.md"


class SkillInstructionsTest(unittest.TestCase):
    def test_collaboration_guidance_for_missing_scoring_basis(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("When running interactively", text)
        self.assertIn("ask the user for missing context or evidence", text)
        self.assertIn("lack a basis to assign a score to a category", text)
        self.assertIn("state plainly when information is insufficient", text)
        self.assertIn("choose `n/a`", text)


if __name__ == "__main__":
    unittest.main()
