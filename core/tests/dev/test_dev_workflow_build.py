from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from dev_workflow_build import collect_artifact_records  # noqa: E402


class TestDevWorkflowBuild(unittest.TestCase):
    def test_collect_artifact_records_for_betterdiscord_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            bundle = project_root / "apps" / "betterdiscord-plugin" / "LexiShift.plugin.js"
            bundle.parent.mkdir(parents=True, exist_ok=True)
            bundle.write_text("plugin", encoding="utf-8")

            records = collect_artifact_records(
                "betterdiscord_build",
                project_root=project_root,
                platform_name="Darwin",
            )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["label"], "betterdiscord_bundle")
        self.assertEqual(records[0]["kind"], "file")
        self.assertTrue(records[0]["exists"])
        self.assertEqual(records[0]["size_bytes"], 6)

    def test_collect_artifact_records_for_macos_gui_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            main_plist = (
                project_root / "apps" / "gui" / "dist" / "LexiShift.app" / "Contents" / "Info.plist"
            )
            helper_plist = (
                project_root
                / "apps"
                / "gui"
                / "dist"
                / "LexiShift Helper.app"
                / "Contents"
                / "Info.plist"
            )
            main_plist.parent.mkdir(parents=True, exist_ok=True)
            helper_plist.parent.mkdir(parents=True, exist_ok=True)
            main_plist.write_bytes(b"main")
            helper_plist.write_bytes(b"helper")

            records = collect_artifact_records(
                "gui_build_validate",
                project_root=project_root,
                platform_name="Darwin",
            )

        labels = {str(record["label"]): record for record in records}
        self.assertEqual(
            set(labels),
            {
                "gui_main_app_bundle",
                "gui_helper_app_bundle",
                "gui_main_info_plist",
                "gui_helper_info_plist",
            },
        )
        self.assertEqual(labels["gui_main_app_bundle"]["kind"], "directory")
        self.assertTrue(labels["gui_main_app_bundle"]["exists"])
        self.assertEqual(labels["gui_main_info_plist"]["kind"], "file")
        self.assertTrue(labels["gui_main_info_plist"]["exists"])

    def test_collect_artifact_records_for_non_macos_gui_build_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            records = collect_artifact_records(
                "gui_build_validate",
                project_root=project_root,
                platform_name="Linux",
            )

        self.assertEqual(records, [])


if __name__ == "__main__":
    unittest.main()
