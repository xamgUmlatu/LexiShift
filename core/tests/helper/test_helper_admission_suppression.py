from __future__ import annotations

from datetime import datetime, timezone
import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.engine import suppress_srs_admission  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs.admission_suppression import (  # noqa: E402
    active_suppressed_lemmas,
    load_admission_suppression_store,
)


NOW = datetime(2026, 5, 26, tzinfo=timezone.utc)


class TestHelperAdmissionSuppression(unittest.TestCase):
    def test_manual_cooldown_persists_without_mutating_srs_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))

            result = suppress_srs_admission(
                paths,
                pair="en-es",
                profile_id="alpha profile",
                lemma="perro",
                reason="manual_cooldown",
                note="feedback_popup_hide_for_now",
                now=NOW,
            )

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["profile_id"], "alpha_profile")
            self.assertEqual(result["pair"], "en-es")
            self.assertEqual(result["lemma"], "perro")
            self.assertEqual(result["reason"], "manual_cooldown")
            self.assertEqual(result["active_reason"], "manual_cooldown")
            self.assertFalse(result["runtime_srs_mutation"])
            self.assertTrue(result["suppression_store_mutation"])
            self.assertTrue(result["refresh_admission_blocked"])
            self.assertEqual(result["suppressed_until"], "2026-06-25T00:00:00Z")

            store_path = paths.srs_admission_suppression_store_path_for("alpha_profile")
            self.assertTrue(store_path.exists())
            store = load_admission_suppression_store(store_path)
            self.assertEqual(store.profile_id, "alpha_profile")
            self.assertEqual(
                active_suppressed_lemmas(store, pair="en-es", now=NOW), {"perro": "manual_cooldown"}
            )
            self.assertFalse(paths.srs_store_path_for("alpha_profile").exists())

    def test_missing_pair_or_lemma_fails_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            with self.assertRaises(ValueError):
                suppress_srs_admission(paths, pair="", profile_id="default", lemma="perro")
            with self.assertRaises(ValueError):
                suppress_srs_admission(paths, pair="en-es", profile_id="default", lemma="")

            self.assertFalse(paths.srs_admission_suppression_store_path_for("default").exists())
            self.assertFalse(paths.srs_store_path_for("default").exists())


if __name__ == "__main__":
    unittest.main()
