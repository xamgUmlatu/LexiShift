from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper_paths import build_helper_paths  # noqa: E402
from lexishift_core.helper_profiles import get_profiles_snapshot  # noqa: E402
from lexishift_core.settings import AppSettings, Profile, save_app_settings  # noqa: E402


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
