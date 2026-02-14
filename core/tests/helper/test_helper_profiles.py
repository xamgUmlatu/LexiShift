from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.profiles import get_profile_rulesets_snapshot, get_profiles_snapshot  # noqa: E402
from lexishift_core.persistence.settings import AppSettings, Profile, save_app_settings  # noqa: E402


class TestHelperProfilesSnapshot(unittest.TestCase):
    def test_snapshot_without_settings_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            payload = get_profiles_snapshot(paths)
            self.assertFalse(payload["settings_exists"])
            self.assertEqual(payload["profiles_count"], 0)
            self.assertEqual(payload["resolved_profile_id"], "default")
            self.assertEqual(payload["load_error"], None)

    def test_snapshot_with_profiles_resolves_active_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            save_app_settings(
                AppSettings(
                    profiles=(
                        Profile(profile_id="p1", name="Profile 1", dataset_path="/tmp/a.json"),
                        Profile(profile_id="p2", name="Profile 2", dataset_path="/tmp/b.json"),
                    ),
                    active_profile_id="missing-profile",
                ),
                paths.app_settings_path,
            )
            payload = get_profiles_snapshot(paths)
            self.assertTrue(payload["settings_exists"])
            self.assertEqual(payload["profiles_count"], 2)
            self.assertEqual(payload["active_profile_id"], "missing-profile")
            self.assertEqual(payload["resolved_profile_id"], "p1")

    def test_profile_rulesets_snapshot_for_requested_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            rulesets_dir = root / "rulesets"
            rulesets_dir.mkdir(parents=True, exist_ok=True)
            ruleset_one = rulesets_dir / "alpha.json"
            ruleset_two = rulesets_dir / "beta.json"
            ruleset_one.write_text(
                json.dumps(
                    {
                        "rules": [
                            {"source_phrase": "alpha", "replacement": "ALPHA", "enabled": True},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            ruleset_two.write_text(
                json.dumps(
                    {
                        "rules": [
                            {"source_phrase": "beta", "replacement": "BETA", "enabled": True},
                            {"source_phrase": "gamma", "replacement": "GAMMA", "enabled": False},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            shared_path = str(ruleset_one)
            second_path = str(ruleset_two)
            save_app_settings(
                AppSettings(
                    profiles=(
                        Profile(
                            profile_id="p1",
                            name="Profile 1",
                            dataset_path=shared_path,
                            rulesets=(shared_path, second_path),
                            active_ruleset=second_path,
                        ),
                        Profile(
                            profile_id="p2",
                            name="Profile 2",
                            dataset_path=shared_path,
                            rulesets=(shared_path,),
                            active_ruleset=shared_path,
                        ),
                    ),
                    active_profile_id="p2",
                ),
                paths.app_settings_path,
            )
            payload = get_profile_rulesets_snapshot(paths, profile_id="p1")
            self.assertEqual(payload["requested_profile_id"], "p1")
            self.assertEqual(payload["resolved_profile_id"], "p1")
            self.assertTrue(payload["profile_found"])
            self.assertEqual(payload["rulesets_count"], 2)

            ruleset_payloads = {item["path"]: item for item in payload["rulesets"]}
            self.assertIn(shared_path, ruleset_payloads)
            self.assertIn(second_path, ruleset_payloads)
            self.assertEqual(ruleset_payloads[shared_path]["rules_count"], 1)
            self.assertEqual(ruleset_payloads[second_path]["rules_count"], 2)
            self.assertEqual(ruleset_payloads[shared_path]["error"], None)
            self.assertEqual(ruleset_payloads[second_path]["error"], None)

    def test_profile_rulesets_snapshot_reports_missing_ruleset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            missing_path = str(root / "rulesets" / "missing.json")
            save_app_settings(
                AppSettings(
                    profiles=(
                        Profile(
                            profile_id="p1",
                            name="Profile 1",
                            dataset_path=missing_path,
                            rulesets=(missing_path,),
                            active_ruleset=missing_path,
                        ),
                    ),
                    active_profile_id="p1",
                ),
                paths.app_settings_path,
            )
            payload = get_profile_rulesets_snapshot(paths, profile_id="p1")
            self.assertEqual(payload["rulesets_count"], 1)
            item = payload["rulesets"][0]
            self.assertEqual(item["path"], missing_path)
            self.assertEqual(item["exists"], False)
            self.assertEqual(item["rules_count"], 0)
            self.assertEqual(item["error"], "Ruleset file not found.")
