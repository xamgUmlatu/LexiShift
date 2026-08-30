from __future__ import annotations

import re
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "build"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from gui_app import _cleanup_windows_collect_duplicates  # noqa: E402
from gui_app import _build_command  # noqa: E402
from gui_app import _install_macos_app  # noqa: E402
from gui_app import _list_macos_installed_processes  # noqa: E402
from gui_app import _terminate_macos_installed_processes  # noqa: E402
from gui_app import _terminate_windows_dist_processes  # noqa: E402


class TestGuiAppBuild(unittest.TestCase):
    def test_pyinstaller_spec_uses_onedir_exe_payload_split(self) -> None:
        spec_text = (REPO_ROOT / "apps" / "gui" / "packaging" / "pyinstaller.spec").read_text(
            encoding="utf-8"
        )

        self.assertIn("PYINSTALLER_UPX_ENABLED", spec_text)
        self.assertEqual(spec_text.count("exclude_binaries=True"), 4)
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
        self.assertIn('"lexishift_core.helper.lookup_dictionary_settings"', spec_text)
        self.assertIn('"lexishift_core.helper.yomitan_lookup_dictionaries"', spec_text)
        self.assertIn('"lexishift_core.srs.seed"', spec_text)
        self.assertIn('"lexishift_core.srs.topic_overlay"', spec_text)
        self.assertIn('os.path.join(repo_root, "core", "lexishift_core", "resources")', spec_text)
        self.assertIn('os.path.join("lexishift_core", "resources")', spec_text)
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
        self.assertEqual(spec_text.count("excludes=PYINSTALLER_OPTIONAL_EXCLUDES"), 4)
        self.assertNotIn("excludes=[]", spec_text)
        self.assertIn('if sys.platform == "darwin":\n    host_a = Analysis', spec_text)
        self.assertIn("sharing unpacked bundle dependencies for fast cold startup", spec_text)

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

    def test_install_macos_app_replaces_only_the_target_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "dist" / "LexiShift.app"
            install_dir = root / "Applications"
            target = install_dir / "LexiShift.app"
            application_support = root / "Application Support" / "LexiShift"
            source.mkdir(parents=True)
            target.mkdir(parents=True)
            application_support.mkdir(parents=True)
            (source / "version.txt").write_text("new", encoding="utf-8")
            (target / "version.txt").write_text("old", encoding="utf-8")
            (application_support / "settings.json").write_text("{}", encoding="utf-8")

            installed = _install_macos_app(source, install_dir)

            self.assertEqual(installed, target)
            self.assertEqual((target / "version.txt").read_text(encoding="utf-8"), "new")
            self.assertEqual(
                (application_support / "settings.json").read_text(encoding="utf-8"), "{}"
            )
            self.assertEqual(list(install_dir.glob(".*.lexishift-*-*")), [])

    def test_list_macos_installed_processes_matches_only_installed_bundle_executables(
        self,
    ) -> None:
        output = "\n".join(
            (
                "101 /Applications/LexiShift.app/Contents/MacOS/LexiShift --open-resource-settings",
                "202 /Applications/LexiShift Helper.app/Contents/MacOS/LexiShiftHelper",
                "303 /tmp/LexiShift.app/Contents/MacOS/LexiShift",
                "404 python scripts/helper/lexishift_native_host.py",
            )
        )
        with (
            mock.patch("gui_app.platform.system", return_value="Darwin"),
            mock.patch(
                "gui_app.subprocess.run",
                return_value=mock.Mock(returncode=0, stdout=output),
            ),
        ):
            processes = _list_macos_installed_processes(Path("/Applications"))

        self.assertEqual([pid for pid, _command in processes], [101, 202])

    def test_terminate_macos_installed_processes_waits_for_clean_exit(self) -> None:
        with (
            mock.patch(
                "gui_app._list_macos_installed_processes",
                side_effect=[[(101, "/Applications/LexiShift.app/Contents/MacOS/LexiShift")], []],
            ),
            mock.patch("gui_app.os.kill") as kill,
        ):
            _terminate_macos_installed_processes(Path("/Applications"), timeout_seconds=1.0)

        kill.assert_called_once_with(101, 15)


if __name__ == "__main__":
    unittest.main()
