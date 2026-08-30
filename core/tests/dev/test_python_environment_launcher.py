from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHON_ENVIRONMENT_JS = REPO_ROOT / "scripts" / "dev" / "python_environment.js"
BOOTSTRAP_PYTHON_ENV_JS = REPO_ROOT / "scripts" / "dev" / "bootstrap_python_env.js"
RUN_PYTHON_JS = REPO_ROOT / "scripts" / "dev" / "run_python.js"


def _run_node(
    source: str, *, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", "-e", source],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


class TestPythonEnvironmentLauncher(unittest.TestCase):
    def test_repository_declares_the_ci_python_patch_version(self) -> None:
        self.assertEqual((REPO_ROOT / ".python-version").read_text(encoding="utf-8"), "3.10.16\n")

    def test_version_gate_accepts_only_python_3_10(self) -> None:
        script = f"""
const environment = require({json.dumps(str(PYTHON_ENVIRONMENT_JS))});
console.log(JSON.stringify([
  environment.isSupportedVersion({{major: 3, minor: 10, micro: 16}}),
  environment.isSupportedVersion({{major: 3, minor: 11, micro: 0}}),
  environment.isSupportedVersion({{major: 3, minor: 9, micro: 18}}),
]));
"""
        result = _run_node(script)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [True, False, False])

    def test_candidate_order_prefers_repo_venv_and_explicit_python(self) -> None:
        script = f"""
const environment = require({json.dumps(str(PYTHON_ENVIRONMENT_JS))});
const candidates = environment.resolveCandidates({{
  repoRoot: '/tmp/lexishift-test',
  includeSystem: false,
}});
console.log(JSON.stringify(candidates));
"""
        env = dict(os.environ)
        env["LEXISHIFT_PYTHON"] = "/tmp/explicit-python"
        result = _run_node(script, env=env)

        self.assertEqual(result.returncode, 0, result.stderr)
        candidates = json.loads(result.stdout)
        self.assertEqual(candidates[0]["source"], "repo .venv")
        self.assertEqual(candidates[1]["source"], "repo .venv")
        self.assertEqual(candidates[2]["command"], "/tmp/explicit-python")

    def test_launcher_honors_an_explicit_supported_interpreter(self) -> None:
        env = dict(os.environ)
        env["LEXISHIFT_PYTHON"] = sys.executable
        result = subprocess.run(
            [
                "node",
                str(RUN_PYTHON_JS),
                "-c",
                "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')",
            ],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "3.10")

    def test_package_scripts_expose_setup_and_install_workflows(self) -> None:
        package = json.loads((REPO_ROOT / "scripts" / "package.json").read_text(encoding="utf-8"))
        scripts = package["scripts"]

        self.assertEqual(scripts["setup:python"], "node dev/bootstrap_python_env.js")
        self.assertEqual(
            scripts["setup:python:build"],
            "node dev/bootstrap_python_env.js --build",
        )
        self.assertIn("--validate --install --relaunch", scripts["build:gui:install:relaunch"])

    def test_bootstrap_requires_exact_direct_dependency_pins(self) -> None:
        script = f"""
const bootstrap = require({json.dumps(str(BOOTSTRAP_PYTHON_ENV_JS))});
const pins = bootstrap.loadPinnedRequirements({json.dumps(str(REPO_ROOT / "requirements-build.txt"))});
console.log(JSON.stringify(pins));
"""
        result = _run_node(script)

        self.assertEqual(result.returncode, 0, result.stderr)
        pins = json.loads(result.stdout)
        self.assertEqual(pins["fsrs"], "6.3.1")
        self.assertEqual(pins["ruff"], "0.15.0")
        self.assertEqual(pins["simplemma"], "1.1.2")
        self.assertEqual(pins["PyInstaller"], "6.18.0")
        self.assertEqual(pins["PySide6"], "6.10.1")


if __name__ == "__main__":
    unittest.main()
