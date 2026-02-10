from __future__ import annotations

import ast
import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

PACKAGE_ROOT = Path(PROJECT_ROOT) / "lexishift_core"


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def _collect_import_modules(file_path: Path) -> set[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
    return modules


class TestArchitectureBoundaries(unittest.TestCase):
    def test_core_top_level_is_package_only(self) -> None:
        top_level_python = sorted(
            path.name
            for path in PACKAGE_ROOT.glob("*.py")
            if path.is_file()
        )
        self.assertEqual(top_level_python, ["__init__.py"])

    def test_core_does_not_import_apps_or_scripts(self) -> None:
        violations: list[str] = []
        for file_path in _iter_python_files(PACKAGE_ROOT):
            for module in _collect_import_modules(file_path):
                if module.startswith("apps") or module.startswith("scripts"):
                    rel = file_path.relative_to(PACKAGE_ROOT.parent)
                    violations.append(f"{rel}: {module}")
        self.assertEqual(violations, [])

    def test_srs_does_not_import_helper_layer(self) -> None:
        srs_root = PACKAGE_ROOT / "srs"
        violations: list[str] = []
        for file_path in _iter_python_files(srs_root):
            for module in _collect_import_modules(file_path):
                if module.startswith("lexishift_core.helper"):
                    rel = file_path.relative_to(PACKAGE_ROOT.parent)
                    violations.append(f"{rel}: {module}")
        self.assertEqual(violations, [])

    def test_frequency_pair_specific_modules_live_under_pair_namespace(self) -> None:
        frequency_root = PACKAGE_ROOT / "frequency"
        forbidden = sorted(path.name for path in frequency_root.glob("de_*.py"))
        self.assertEqual(forbidden, [])
        self.assertTrue((frequency_root / "de" / "build.py").exists())
        self.assertTrue((frequency_root / "de" / "pipeline.py").exists())
        self.assertTrue((frequency_root / "de" / "pos_compile.py").exists())

    def test_rulegen_pair_specific_modules_live_under_pairs_namespace(self) -> None:
        rulegen_root = PACKAGE_ROOT / "rulegen"
        self.assertFalse((rulegen_root / "ja_en.py").exists())
        self.assertFalse((rulegen_root / "en_de.py").exists())
        self.assertTrue((rulegen_root / "pairs" / "ja_en.py").exists())
        self.assertTrue((rulegen_root / "pairs" / "en_de.py").exists())


if __name__ == "__main__":
    unittest.main()
