from __future__ import annotations

import re
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "build"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from gui_app import _cleanup_windows_collect_duplicates  # noqa: E402
from gui_app import _build_command  # noqa: E402
from gui_app import _terminate_windows_dist_processes  # noqa: E402


class TestGuiAppBuild(unittest.TestCase):
    def test_pyinstaller_spec_uses_onedir_exe_payload_split(self) -> None:
        spec_text = (REPO_ROOT / "apps" / "gui" / "packaging" / "pyinstaller.spec").read_text(
            encoding="utf-8"
        )

        self.assertIn("PYINSTALLER_UPX_ENABLED", spec_text)
        self.assertEqual(spec_text.count("exclude_binaries=True"), 3)
        self.assertNotIn("upx=True", spec_text)

    def test_pyinstaller_spec_collects_core_hidden_imports(self) -> None:
        spec_text = (REPO_ROOT / "apps" / "gui" / "packaging" / "pyinstaller.spec").read_text(
            encoding="utf-8"
        )

        self.assertIn("LEXISHIFT_HELPER_USE_CASE_HIDDEN_IMPORTS", spec_text)
        self.assertIn("LEXISHIFT_CORE_HIDDEN_IMPORTS", spec_text)
        self.assertIn('"lexishift_core.helper.use_cases.rulegen_job"', spec_text)
        self.assertIn('"lexishift_core.helper.use_cases.runtime_diagnostics"', spec_text)
        self.assertIn('"lexishift_core.helper.use_cases.semantic_admission"', spec_text)
        self.assertIn('"lexishift_core.srs.seed"', spec_text)
        self.assertIn('"lexishift_core.srs.topic_overlay"', spec_text)
        self.assertNotIn('hiddenimports=["lexishift_core"]', spec_text)

    def test_pyinstaller_spec_excludes_optional_heavy_packages(self) -> None:
        spec_text = (REPO_ROOT / "apps" / "gui" / "packaging" / "pyinstaller.spec").read_text(
            encoding="utf-8"
        )
        match = re.search(
            r"PYINSTALLER_OPTIONAL_EXCLUDES = \[(?P<body>.*?)\]\n\nmain_datas",
            spec_text,
            flags=re.DOTALL,
        )

        self.assertIsNotNone(match)
        exclude_body = match.group("body") if match is not None else ""
        for package_name in (
            "accelerate",
            "cv2",
            "datasets",
            "diffusers",
            "fsrs.optimizer",
            "jieba",
            "matplotlib",
            "pandas",
            "peft",
            "scipy",
            "sentence_transformers",
            "sklearn",
            "spacy",
            "sudachidict_core",
            "sudachipy",
            "torch",
            "torchvision",
            "transformers",
            "yt_dlp",
        ):
            self.assertIn(f'"{package_name}"', exclude_body)
        self.assertNotIn('"simplemma"', exclude_body)
        self.assertEqual(spec_text.count("excludes=PYINSTALLER_OPTIONAL_EXCLUDES"), 3)
        self.assertNotIn("excludes=[]", spec_text)

    def test_build_command_keeps_pyinstaller_args_after_spec(self) -> None:
        command = _build_command(
            "/repo/apps/gui/packaging/pyinstaller.spec",
            clean=True,
            noconfirm=True,
            distpath="/tmp/dist",
            workpath="/tmp/build",
            extra=["--log-level", "WARN"],
        )

        self.assertEqual(
            command[-3:], ["/repo/apps/gui/packaging/pyinstaller.spec", "--log-level", "WARN"]
        )

    def test_cleanup_windows_collect_duplicates_removes_root_exes_when_collected_layout_exists(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dist = Path(tmpdir) / "dist"
            for dir_name, exe_name in (
                ("LexiShift", "LexiShift.exe"),
                ("LexiShiftHelper", "LexiShiftHelper.exe"),
                ("LexiShiftNativeHost", "lexishift_native_host.exe"),
            ):
                nested = dist / dir_name / exe_name
                root = dist / exe_name
                nested.parent.mkdir(parents=True, exist_ok=True)
                nested.write_bytes(b"nested")
                root.write_bytes(b"root")

            _cleanup_windows_collect_duplicates(str(dist))

            self.assertFalse((dist / "LexiShift.exe").exists())
            self.assertFalse((dist / "LexiShiftHelper.exe").exists())
            self.assertFalse((dist / "lexishift_native_host.exe").exists())
            self.assertTrue((dist / "LexiShift" / "LexiShift.exe").exists())
            self.assertTrue((dist / "LexiShiftHelper" / "LexiShiftHelper.exe").exists())
            self.assertTrue((dist / "LexiShiftNativeHost" / "lexishift_native_host.exe").exists())

    def test_terminate_windows_dist_processes_only_targets_dist_owned_processes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dist = Path(tmpdir) / "dist"
            dist.mkdir(parents=True, exist_ok=True)
            dist_owned = dist / "LexiShiftHelper.exe"
            installed = Path("C:/Program Files/LexiShift/LexiShiftHelper.exe")
            terminated: list[int] = []

            from unittest import mock

            with (
                mock.patch("gui_app.platform.system", return_value="Windows"),
                mock.patch(
                    "gui_app._list_windows_lexishift_processes",
                    return_value=[
                        (101, str(dist_owned)),
                        (202, str(installed)),
                    ],
                ),
                mock.patch(
                    "gui_app._terminate_windows_process_tree",
                    side_effect=lambda pid: terminated.append(pid),
                ),
            ):
                _terminate_windows_dist_processes(str(dist))

        self.assertEqual(terminated, [101])


if __name__ == "__main__":
    unittest.main()
