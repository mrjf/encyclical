from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import textwrap
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_SKILL_DIR = ROOT / "magnifica-humanitas-review"
FIXTURE_FILE = ROOT / "tests" / "integration" / "fixtures" / "civic-library-kiosk.md"
ARTIFACT_ROOT = ROOT / "tests" / "integration" / ".artifacts"

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"", "0", "false", "no", "off", "replace-me", "changeme", "..."}


@dataclass(frozen=True)
class Provider:
    name: str
    run_env: str
    command_env: str
    default_command: str
    auth_any: tuple[str, ...]


PROVIDERS = (
    Provider(
        name="codex",
        run_env="RUN_CODEX_SKILL_INTEGRATION",
        command_env="CODEX_SKILL_COMMAND",
        default_command=(
            "codex exec --cd {workspace} --sandbox workspace-write "
            "--ask-for-approval never - < {prompt_file}"
        ),
        auth_any=("OPENAI_API_KEY", "CODEX_SKILL_AUTH_READY"),
    ),
    Provider(
        name="claude",
        run_env="RUN_CLAUDE_SKILL_INTEGRATION",
        command_env="CLAUDE_SKILL_COMMAND",
        default_command=(
            'claude -p "$(cat {prompt_file})" --allowedTools Read Write '
            '"Bash(python3:*)" --permission-mode acceptEdits'
        ),
        auth_any=("ANTHROPIC_API_KEY", "CLAUDE_SKILL_AUTH_READY"),
    ),
    Provider(
        name="copilot",
        run_env="RUN_COPILOT_SKILL_INTEGRATION",
        command_env="COPILOT_SKILL_COMMAND",
        default_command=(
            "gh copilot -p \"$(cat {prompt_file})\" "
            "--allow-tool='read,write,shell(python3:*)'"
        ),
        auth_any=("GH_TOKEN", "GITHUB_TOKEN", "COPILOT_SKILL_AUTH_READY"),
    ),
)


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)


def env_truthy(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in TRUE_VALUES


def env_has_value(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() not in FALSE_VALUES


def first_command_word(command: str) -> str:
    try:
        return shlex.split(command, posix=True)[0]
    except (IndexError, ValueError):
        return ""


def shell_quote(path_or_text: Path | str) -> str:
    return shlex.quote(str(path_or_text))


def render_command(template: str, prompt: str, paths: dict[str, Path]) -> str:
    values = {
        "workspace": shell_quote(paths["workspace"]),
        "skill_dir": shell_quote(paths["skill_dir"]),
        "subject_file": shell_quote(paths["subject_file"]),
        "report_path": shell_quote(paths["report_path"]),
        "prompt_file": shell_quote(paths["prompt_file"]),
        "scorer": shell_quote(paths["scorer"]),
        "prompt": shlex.quote(prompt),
    }
    return template.format(**values)


def build_prompt(paths: dict[str, Path]) -> str:
    return textwrap.dedent(
        f"""
        You are running a full integration test for an Agent Skills-compatible skill.

        Use only these local files and paths:
        - Skill root: {paths["skill_dir"]}
        - Skill instructions: {paths["skill_dir"] / "SKILL.md"}
        - Subject evidence: {paths["subject_file"]}
        - Output report path: {paths["report_path"]}
        - Deterministic scorer: {paths["scorer"]}

        Task:
        1. Read the skill instructions and follow them.
        2. Use the report template bundled in the skill.
        3. Evaluate the subject evidence file as the thing reviewed.
        4. Write the completed Markdown report to the output report path.
        5. Run: python3 {paths["scorer"]} {paths["report_path"]} --write --check

        Hard requirements:
        - Do not use the network.
        - Do not modify files outside the test workspace.
        - Preserve template text outside sparkle pills and deterministic score marker ranges.
        - Replace every sparkle pill with final content.
        - Every scorecard score cell must be a bare integer 0, 1, 2, or 3, or n/a when the category does not apply.
        - Link report claims to the local subject evidence file where possible.
        - Finish only after the deterministic scorer command succeeds.
        """
    ).strip()


PROVIDERS_BY_NAME = {provider.name: provider for provider in PROVIDERS}


class AgentSkillCliIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        load_dotenv(ROOT / ".env")

    def require_integration_enabled(self) -> None:
        if not env_truthy("RUN_AGENT_SKILL_INTEGRATION_TESTS"):
            self.skipTest("Set RUN_AGENT_SKILL_INTEGRATION_TESTS=1 in .env to run real CLI tests")

    def test_codex_cli_can_generate_scored_report_with_skill(self) -> None:
        self.require_integration_enabled()
        self.run_provider(PROVIDERS_BY_NAME["codex"])

    def test_claude_cli_can_generate_scored_report_with_skill(self) -> None:
        self.require_integration_enabled()
        self.run_provider(PROVIDERS_BY_NAME["claude"])

    def test_copilot_cli_can_generate_scored_report_with_skill(self) -> None:
        self.require_integration_enabled()
        self.run_provider(PROVIDERS_BY_NAME["copilot"])

    def run_provider(self, provider: Provider) -> None:
        if not env_truthy(provider.run_env, "1"):
            self.skipTest(f"{provider.run_env}=0")

        if not any(env_has_value(name) for name in provider.auth_any):
            names = ", ".join(provider.auth_any)
            self.skipTest(f"Missing auth marker/key; set one of: {names}")

        command_template = os.environ.get(provider.command_env, provider.default_command)
        executable = first_command_word(command_template)
        if not executable or shutil.which(executable) is None:
            self.skipTest(f"Command executable not found for {provider.name}: {executable}")

        paths = self.prepare_workspace(provider)
        prompt = build_prompt(paths)
        paths["prompt_file"].write_text(prompt + "\n", encoding="utf-8")

        command = render_command(command_template, prompt, paths)
        result = subprocess.run(
            command,
            cwd=paths["workspace"],
            env=os.environ.copy(),
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=int(os.environ.get("AGENT_SKILL_CLI_TIMEOUT", "900")),
        )
        paths["log_file"].write_text(result.stdout, encoding="utf-8")

        self.assertEqual(
            result.returncode,
            0,
            f"{provider.name} CLI failed; see {paths['log_file']}\n{result.stdout[-4000:]}",
        )
        self.assert_report_is_valid(provider, paths)

    def prepare_workspace(self, provider: Provider) -> dict[str, Path]:
        workspace = ARTIFACT_ROOT / provider.name / "workspace"
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)

        skill_dir = workspace / SOURCE_SKILL_DIR.name
        shutil.copytree(SOURCE_SKILL_DIR, skill_dir)

        subject_file = workspace / "subject.md"
        shutil.copy2(FIXTURE_FILE, subject_file)

        return {
            "workspace": workspace,
            "skill_dir": skill_dir,
            "subject_file": subject_file,
            "report_path": workspace / "report.md",
            "prompt_file": workspace / "prompt.md",
            "scorer": skill_dir / "scripts" / "finalize_score.py",
            "log_file": workspace / f"{provider.name}.log",
        }

    def assert_report_is_valid(self, provider: Provider, paths: dict[str, Path]) -> None:
        report_path = paths["report_path"]
        self.assertTrue(report_path.exists(), f"{provider.name} did not create {report_path}")

        report = report_path.read_text(encoding="utf-8")
        self.assertNotIn("*(", report, "Report still contains unresolved sparkle pills")
        self.assertIn("# Magnifica Humanitas Review:", report)
        self.assertIn("Civic Library Kiosk", report)
        self.assertIn("subject.md", report, "Report should cite the local subject fixture")
        self.assertIn("<!-- METRIC-SCORECARD:START -->", report)
        self.assertRegex(
            report,
            r"<!-- OVERALL-SCORE:START -->\d+(?:\.\d)?/100<!-- OVERALL-SCORE:END -->",
        )
        self.assertGreaterEqual(
            len(re.findall(r"\[[^\]]+\]\([^)]+\)", report)),
            30,
            "Report should preserve dense source/principle links",
        )

        check = subprocess.run(
            [
                "python3",
                str(paths["scorer"]),
                str(report_path),
                "--check",
                "--json",
            ],
            cwd=paths["workspace"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.assertEqual(
            check.returncode,
            0,
            f"{provider.name} report failed deterministic score check:\n{check.stdout}",
        )

        summary = json.loads(check.stdout)
        self.assertEqual(summary["metric_count"], 30)
        self.assertEqual(len(summary["scores"]), 30)
        self.assertGreaterEqual(summary["overall_score"], 0)
        self.assertLessEqual(summary["overall_score"], 100)


if __name__ == "__main__":
    unittest.main()
