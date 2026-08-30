from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
REPO_ROOT = os.path.dirname(CORE_ROOT)
GUI_SRC = os.path.join(REPO_ROOT, "apps", "gui", "src")
for candidate in (CORE_ROOT, GUI_SRC):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from helper_daemon import (  # noqa: E402
    DaemonConfig,
    _build_job_config,
    _resolve_daemon_pairs,
    _supported_pairs,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs import (  # noqa: E402
    SRS_LIFECYCLE_DISCARDED,
    SrsInventory,
    SrsItem,
    SrsPairInventory,
    SrsPairSettings,
    SrsSettings,
    SrsStore,
    save_srs_inventory,
    save_srs_store,
)


class TestHelperDaemon(unittest.TestCase):
    def test_supported_pairs_include_de_en_en_de_and_en_es(self) -> None:
        pairs = _supported_pairs()
        self.assertIn("de-en", pairs)
        self.assertIn("en-ja", pairs)
        self.assertIn("en-de", pairs)
        self.assertIn("en-es", pairs)

    def test_build_job_config_requires_jmdict_for_en_ja(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            config = DaemonConfig()
            self.assertIsNone(_build_job_config("en-ja", paths, config))

            jmdict_path = paths.language_packs_dir / "JMdict_e"
            jmdict_path.parent.mkdir(parents=True, exist_ok=True)
            jmdict_path.write_text("<JMdict/>", encoding="utf-8")

            job = _build_job_config("en-ja", paths, config)
            self.assertIsNotNone(job)
            self.assertEqual(job.pair, "en-ja")
            self.assertEqual(job.jmdict_path, jmdict_path)

    def test_build_job_config_requires_freedict_for_en_de(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            config = DaemonConfig()
            self.assertIsNone(_build_job_config("en-de", paths, config))

            freedict_path = paths.language_packs_dir / "deu-eng.tei"
            freedict_path.parent.mkdir(parents=True, exist_ok=True)
            freedict_path.write_text("<TEI/>", encoding="utf-8")

            job = _build_job_config("en-de", paths, config)
            self.assertIsNotNone(job)
            self.assertEqual(job.pair, "en-de")
            self.assertEqual(job.translation_dict_path, freedict_path)
            self.assertIsNone(job.jmdict_path)

    def test_build_job_config_uses_requested_profile_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            freedict_path = paths.language_packs_dir / "deu-eng.tei"
            freedict_path.parent.mkdir(parents=True, exist_ok=True)
            freedict_path.write_text("<TEI/>", encoding="utf-8")

            job = _build_job_config("en-de", paths, DaemonConfig(), profile_id="suisui")

            self.assertIsNotNone(job)
            self.assertEqual(job.profile_id, "suisui")

    def test_resolve_daemon_pairs_uses_configured_pair_rules_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            settings = SrsSettings(
                pair_rules={
                    "en-de": SrsPairSettings(enabled=True),
                    "en-ja": SrsPairSettings(enabled=False),
                }
            )

            pairs = _resolve_daemon_pairs(settings, paths, "suisui")

            self.assertEqual(pairs, ("en-de",))

    def test_resolve_daemon_pairs_falls_back_to_active_profile_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            save_srs_inventory(
                SrsInventory(
                    pairs={
                        "en-de": SrsPairInventory(active_item_ids=("en-de:sein",)),
                        "en-ja": SrsPairInventory(active_item_ids=()),
                    }
                ),
                paths.srs_inventory_path_for("suisui"),
            )

            pairs = _resolve_daemon_pairs(SrsSettings(), paths, "suisui")

            self.assertEqual(pairs, ("en-de",))

    def test_resolve_daemon_pairs_falls_back_to_active_profile_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-es:luz",
                            lemma="luz",
                            language_pair="en-es",
                            source_type="test",
                        ),
                        SrsItem(
                            item_id="en-de:sein",
                            lemma="sein",
                            language_pair="en-de",
                            source_type="test",
                        ),
                    )
                ),
                paths.srs_store_path_for("suisui"),
            )

            pairs = _resolve_daemon_pairs(SrsSettings(), paths, "suisui")

            self.assertEqual(pairs, ("en-de", "en-es"))

    def test_resolve_daemon_pairs_ignores_inactive_store_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-es:luz",
                            lemma="luz",
                            language_pair="en-es",
                            source_type="test",
                        ),
                        SrsItem(
                            item_id="en-ja:猫",
                            lemma="猫",
                            language_pair="en-ja",
                            source_type="test",
                            lifecycle_state=SRS_LIFECYCLE_DISCARDED,
                        ),
                    )
                ),
                paths.srs_store_path_for("suisui"),
            )

            pairs = _resolve_daemon_pairs(SrsSettings(), paths, "suisui")

            self.assertEqual(pairs, ("en-es",))

    def test_resolve_daemon_pairs_respects_disabled_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            settings = SrsSettings(enabled=False)

            pairs = _resolve_daemon_pairs(settings, paths, "suisui")

            self.assertEqual(pairs, ())

    def test_build_job_config_requires_freedict_for_en_es(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            config = DaemonConfig()
            self.assertIsNone(_build_job_config("en-es", paths, config))

            freedict_path = paths.language_packs_dir / "spa-eng.tei"
            freedict_path.parent.mkdir(parents=True, exist_ok=True)
            freedict_path.write_text("<TEI/>", encoding="utf-8")

            job = _build_job_config("en-es", paths, config)
            self.assertIsNotNone(job)
            self.assertEqual(job.pair, "en-es")
            self.assertEqual(job.translation_dict_path, freedict_path)
            self.assertIsNone(job.jmdict_path)

    def test_build_job_config_requires_freedict_for_de_en(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            config = DaemonConfig()
            self.assertIsNone(_build_job_config("de-en", paths, config))

            freedict_path = paths.language_packs_dir / "eng-deu.tei"
            freedict_path.parent.mkdir(parents=True, exist_ok=True)
            freedict_path.write_text("<TEI/>", encoding="utf-8")

            job = _build_job_config("de-en", paths, config)
            self.assertIsNotNone(job)
            self.assertEqual(job.pair, "de-en")
            self.assertEqual(job.translation_dict_path, freedict_path)
            self.assertIsNone(job.jmdict_path)


if __name__ == "__main__":
    unittest.main()
