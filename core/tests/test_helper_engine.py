from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.engine import (  # noqa: E402
    apply_exposure,
    apply_feedback,
    get_srs_runtime_diagnostics,
    RulegenJobConfig,
    SrsRefreshJobConfig,
    SetInitializationJobConfig,
    SetPlanningJobConfig,
    initialize_srs_set,
    plan_srs_set,
    refresh_srs_set,
    reset_srs_data,
    run_rulegen_job,
)
from lexishift_core.helper.paths import HelperPaths, build_helper_paths  # noqa: E402
from lexishift_core.srs.signal_queue import SrsSignalEvent, load_signal_events, save_signal_events  # noqa: E402
from lexishift_core.srs import SrsHistoryEntry, SrsItem, SrsSettings, SrsStore, load_srs_store, save_srs_settings, save_srs_store  # noqa: E402
from lexishift_core.replacement.core import VocabRule  # noqa: E402


def _seed_store_and_outputs(root: Path) -> HelperPaths:
    paths = build_helper_paths(root)
    save_srs_store(
        SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                ),
                SrsItem(
                    item_id="en-en:beta",
                    lemma="beta",
                    language_pair="en-en",
                    source_type="initial_set",
                ),
            ),
            version=1,
        ),
        paths.srs_store_path,
    )
    paths.snapshot_path("en-ja").write_text("{}", encoding="utf-8")
    paths.snapshot_path("en-en").write_text("{}", encoding="utf-8")
    paths.ruleset_path("en-ja").write_text("{}", encoding="utf-8")
    paths.ruleset_path("en-en").write_text("{}", encoding="utf-8")
    return paths


class TestHelperPathsDefaults(unittest.TestCase):
    def test_build_helper_paths_creates_default_german_stopwords(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            stopwords_path = paths.srs_dir / "stopwords" / "stopwords-de.json"
            self.assertTrue(stopwords_path.exists())
            payload = json.loads(stopwords_path.read_text(encoding="utf-8"))
            self.assertIsInstance(payload, list)
            self.assertIn("der", payload)


class TestHelperEngineReset(unittest.TestCase):
    def test_reset_pair_removes_only_that_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _seed_store_and_outputs(Path(tmp))
            result = reset_srs_data(paths, pair="en-ja")

            store = load_srs_store(paths.srs_store_path)
            self.assertEqual(len(store.items), 1)
            self.assertEqual(store.items[0].item_id, "en-en:beta")

            self.assertFalse(paths.snapshot_path("en-ja").exists())
            self.assertFalse(paths.ruleset_path("en-ja").exists())
            self.assertTrue(paths.snapshot_path("en-en").exists())
            self.assertTrue(paths.ruleset_path("en-en").exists())

            self.assertEqual(result["pair"], "en-ja")
            self.assertEqual(result["removed_items"], 1)
            self.assertEqual(result["remaining_items"], 1)
            self.assertEqual(result["removed_snapshots"], 1)
            self.assertEqual(result["removed_rulesets"], 1)

    def test_reset_all_removes_all_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _seed_store_and_outputs(Path(tmp))
            result = reset_srs_data(paths)

            store = load_srs_store(paths.srs_store_path)
            self.assertEqual(len(store.items), 0)

            self.assertFalse(paths.snapshot_path("en-ja").exists())
            self.assertFalse(paths.snapshot_path("en-en").exists())
            self.assertFalse(paths.ruleset_path("en-ja").exists())
            self.assertFalse(paths.ruleset_path("en-en").exists())

            self.assertEqual(result["pair"], "all")
            self.assertEqual(result["removed_items"], 2)
            self.assertEqual(result["remaining_items"], 0)
            self.assertEqual(result["removed_snapshots"], 2)
            self.assertEqual(result["removed_rulesets"], 2)


class TestHelperEngineProfileIsolation(unittest.TestCase):
    def test_reset_pair_scopes_to_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            default_profile = "default"
            other_profile = "student-b"

            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:alpha",
                            lemma="alpha",
                            language_pair="en-ja",
                            source_type="initial_set",
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path_for(default_profile),
            )
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:beta",
                            lemma="beta",
                            language_pair="en-ja",
                            source_type="initial_set",
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path_for(other_profile),
            )

            paths.snapshot_path("en-ja", profile_id=default_profile).write_text("{}", encoding="utf-8")
            paths.ruleset_path("en-ja", profile_id=default_profile).write_text("{}", encoding="utf-8")
            paths.snapshot_path("en-ja", profile_id=other_profile).write_text("{}", encoding="utf-8")
            paths.ruleset_path("en-ja", profile_id=other_profile).write_text("{}", encoding="utf-8")

            result = reset_srs_data(paths, pair="en-ja", profile_id=other_profile)

            default_store = load_srs_store(paths.srs_store_path_for(default_profile))
            other_store = load_srs_store(paths.srs_store_path_for(other_profile))
            self.assertEqual(len(default_store.items), 1)
            self.assertEqual(len(other_store.items), 0)
            self.assertTrue(paths.snapshot_path("en-ja", profile_id=default_profile).exists())
            self.assertTrue(paths.ruleset_path("en-ja", profile_id=default_profile).exists())
            self.assertFalse(paths.snapshot_path("en-ja", profile_id=other_profile).exists())
            self.assertFalse(paths.ruleset_path("en-ja", profile_id=other_profile).exists())
            self.assertEqual(result["profile_id"], other_profile)
            self.assertEqual(result["removed_items"], 1)


class TestHelperEngineRulegenPreview(unittest.TestCase):
    def _stub_output(self) -> SimpleNamespace:
        return SimpleNamespace(
            rules=(),
            snapshot={
                "version": 1,
                "pair": "en-ja",
                "targets": [],
                "stats": {"target_count": 0, "rule_count": 0, "source_count": 0},
            },
            target_count=0,
        )

    def test_preview_mode_does_not_persist_any_files_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)

            with patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                return_value=(SrsStore(), self._stub_output()),
            ), patch("lexishift_core.helper.engine.write_rulegen_outputs") as write_outputs, patch(
                "lexishift_core.helper.engine._update_status"
            ) as update_status:
                result = run_rulegen_job(
                    paths,
                    config=RulegenJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        initialize_if_empty=False,
                        persist_store=False,
                        persist_outputs=False,
                        update_status=False,
                    ),
                )

            self.assertFalse(paths.srs_settings_path.exists())
            self.assertFalse(paths.srs_store_path.exists())
            self.assertFalse(paths.snapshot_path("en-ja").exists())
            self.assertFalse(paths.ruleset_path("en-ja").exists())
            self.assertEqual(result["snapshot_path"], None)
            self.assertEqual(result["ruleset_path"], None)
            self.assertEqual(result["outputs_persisted"], False)
            self.assertEqual(result["store_persisted"], False)
            write_outputs.assert_not_called()
            update_status.assert_not_called()

    def test_preview_mode_keeps_existing_store_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)

            initial_store = SrsStore(
                items=(
                    SrsItem(
                        item_id="en-ja:alpha",
                        lemma="alpha",
                        language_pair="en-ja",
                        source_type="initial_set",
                    ),
                ),
                version=1,
            )
            save_srs_store(initial_store, paths.srs_store_path)
            save_srs_settings(SrsSettings(), paths.srs_settings_path)

            mutated_store = SrsStore(
                items=(
                    *initial_store.items,
                    SrsItem(
                        item_id="en-ja:beta",
                        lemma="beta",
                        language_pair="en-ja",
                        source_type="initial_set",
                    ),
                ),
                version=1,
            )

            with patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                return_value=(mutated_store, self._stub_output()),
            ), patch("lexishift_core.helper.engine.write_rulegen_outputs"), patch(
                "lexishift_core.helper.engine._update_status"
            ):
                run_rulegen_job(
                    paths,
                    config=RulegenJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        initialize_if_empty=False,
                        persist_store=False,
                        persist_outputs=False,
                        update_status=False,
                    ),
                )

            persisted = load_srs_store(paths.srs_store_path)
            self.assertEqual(len(persisted.items), 1)
            self.assertEqual(persisted.items[0].item_id, "en-ja:alpha")

    def test_preview_mode_supports_sampled_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)

            save_srs_settings(SrsSettings(), paths.srs_settings_path)
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:alpha",
                            lemma="alpha",
                            language_pair="en-ja",
                            source_type="initial_set",
                        ),
                        SrsItem(
                            item_id="en-ja:beta",
                            lemma="beta",
                            language_pair="en-ja",
                            source_type="initial_set",
                        ),
                        SrsItem(
                            item_id="en-ja:gamma",
                            lemma="gamma",
                            language_pair="en-ja",
                            source_type="initial_set",
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )

            with patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                return_value=(load_srs_store(paths.srs_store_path), self._stub_output()),
            ) as run_rulegen, patch("lexishift_core.helper.engine.write_rulegen_outputs"), patch(
                "lexishift_core.helper.engine._update_status"
            ):
                result = run_rulegen_job(
                    paths,
                    config=RulegenJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        initialize_if_empty=False,
                        persist_store=False,
                        persist_outputs=False,
                        update_status=False,
                        sample_count=2,
                        sample_strategy="weighted_priority",
                        sample_seed=42,
                    ),
                )

            called_targets = run_rulegen.call_args.kwargs.get("targets_override")
            self.assertIsInstance(called_targets, list)
            self.assertEqual(len(called_targets), 2)
            self.assertIn("sampling", result)
            sampling = result["sampling"]
            self.assertEqual(sampling["sample_count_effective"], 2)
            self.assertEqual(sampling["total_items_for_pair"], 3)


class TestHelperEnginePairGeneralization(unittest.TestCase):
    def _stub_output(self, pair: str) -> SimpleNamespace:
        return SimpleNamespace(
            rules=(),
            snapshot={
                "version": 1,
                "pair": pair,
                "targets": [],
                "stats": {"target_count": 0, "rule_count": 0, "source_count": 0},
            },
            target_count=0,
        )

    def test_run_rulegen_allows_en_de_without_jmdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            freedict_path = root / "deu-eng.tei"
            freedict_path.write_text("<TEI></TEI>", encoding="utf-8")
            with patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                return_value=(SrsStore(), self._stub_output("en-de")),
            ) as run_rulegen:
                result = run_rulegen_job(
                    paths,
                    config=RulegenJobConfig(
                        pair="en-de",
                        jmdict_path=None,
                        freedict_de_en_path=freedict_path,
                        set_source_db=None,
                        initialize_if_empty=False,
                        persist_store=False,
                        persist_outputs=False,
                        update_status=False,
                    ),
                )

            self.assertEqual(result["pair"], "en-de")
            self.assertIsNone(run_rulegen.call_args.kwargs.get("jmdict_path"))
            self.assertEqual(run_rulegen.call_args.kwargs.get("freedict_de_en_path"), freedict_path)

    def test_initialize_en_de_disables_jmdict_requirement_for_seed_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            source_db = root / "freq.sqlite"
            source_db.touch()
            freedict_path = root / "deu-eng.tei"
            freedict_path.write_text("<TEI></TEI>", encoding="utf-8")

            init_report = SimpleNamespace(
                selected_count=0,
                selected_unique_count=0,
                admitted_count=0,
                inserted_count=0,
                updated_count=0,
                selected_preview=(),
                initial_active_preview=(),
                admission_weight_profile={},
                initial_active_weight_preview=(),
            )
            with patch(
                "lexishift_core.helper.engine.initialize_store_from_frequency_list_with_report",
                return_value=(SrsStore(), init_report),
            ) as initialize_store, patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                return_value=(SrsStore(), self._stub_output("en-de")),
            ):
                result = initialize_srs_set(
                    paths,
                    config=SetInitializationJobConfig(
                        pair="en-de",
                        jmdict_path=None,
                        freedict_de_en_path=freedict_path,
                        set_source_db=source_db,
                    ),
                )

            init_config = initialize_store.call_args.kwargs["config"]
            self.assertFalse(init_config.require_jmdict)
            self.assertIsNone(init_config.jmdict_path)
            self.assertEqual(result["pair"], "en-de")
            self.assertTrue(result["applied"])

    def test_refresh_en_de_disables_jmdict_requirement_for_seed_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            source_db = root / "freq.sqlite"
            source_db.touch()
            freedict_path = root / "deu-eng.tei"
            freedict_path.write_text("<TEI></TEI>", encoding="utf-8")
            save_srs_settings(
                SrsSettings(max_active_items=10, max_new_items_per_day=2),
                paths.srs_settings_path,
            )
            save_srs_store(SrsStore(items=tuple(), version=1), paths.srs_store_path)

            with patch(
                "lexishift_core.helper.engine.build_seed_candidates",
                return_value=[],
            ) as build_seed:
                result = refresh_srs_set(
                    paths,
                    config=SrsRefreshJobConfig(
                        pair="en-de",
                        jmdict_path=None,
                        freedict_de_en_path=freedict_path,
                        set_source_db=source_db,
                        persist_store=False,
                    ),
                )

            selection_config = build_seed.call_args.kwargs["config"]
            self.assertFalse(selection_config.require_jmdict)
            self.assertIsNone(selection_config.jmdict_path)
            self.assertEqual(result["pair"], "en-de")


class TestHelperEngineRuntimeDiagnostics(unittest.TestCase):
    def test_runtime_diagnostics_with_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            payload = get_srs_runtime_diagnostics(paths, pair="en-ja")
            self.assertEqual(payload["pair"], "en-ja")
            self.assertFalse(payload["store_exists"])
            self.assertFalse(payload["ruleset_exists"])
            self.assertFalse(payload["snapshot_exists"])
            self.assertEqual(payload["store_items_for_pair"], 0)
            self.assertEqual(payload["ruleset_rules_count"], 0)
            self.assertEqual(payload["snapshot_target_count"], 0)

    def test_runtime_diagnostics_reports_missing_en_de_frequency_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            payload = get_srs_runtime_diagnostics(paths, pair="en-de")
            self.assertEqual(payload["pair"], "en-de")
            self.assertIn("pair_policy", payload)
            self.assertEqual(payload["pair_policy"]["pair"], "en-de")
            self.assertTrue(payload["set_source_db"].endswith("freq-de-default.sqlite"))
            self.assertFalse(payload["set_source_db_exists"])
            self.assertTrue(payload["freedict_de_en_path"].endswith("language_packs/deu-eng.tei"))
            self.assertFalse(payload["freedict_de_en_exists"])
            self.assertTrue(payload["stopwords_path"].endswith("stopwords/stopwords-de.json"))
            self.assertTrue(payload["stopwords_exists"])
            missing_types = [entry.get("type") for entry in payload.get("missing_inputs", [])]
            self.assertIn("set_source_db", missing_types)
            self.assertIn("freedict_de_en_path", missing_types)

    def test_runtime_diagnostics_reports_missing_en_ja_jmdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            payload = get_srs_runtime_diagnostics(paths, pair="en-ja")
            self.assertEqual(payload["pair"], "en-ja")
            self.assertTrue(payload["jmdict_path"].endswith("language_packs/JMdict_e"))
            self.assertFalse(payload["jmdict_exists"])
            missing_types = [entry.get("type") for entry in payload.get("missing_inputs", [])]
            self.assertIn("jmdict_path", missing_types)

    def test_runtime_diagnostics_with_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:alpha",
                            lemma="alpha",
                            language_pair="en-ja",
                            source_type="initial_set",
                        ),
                        SrsItem(
                            item_id="en-en:beta",
                            lemma="beta",
                            language_pair="en-en",
                            source_type="initial_set",
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )
            paths.ruleset_path("en-ja").write_text(
                '{"rules":[{"source_phrase":"one","replacement":"一"},{"source_phrase":"two","replacement":"二"}]}',
                encoding="utf-8",
            )
            paths.snapshot_path("en-ja").write_text(
                '{"stats":{"target_count":2,"rule_count":2},"targets":[{"lemma":"一"},{"lemma":"二"}]}',
                encoding="utf-8",
            )
            payload = get_srs_runtime_diagnostics(paths, pair="en-ja")
            self.assertTrue(payload["store_exists"])
            self.assertTrue(payload["ruleset_exists"])
            self.assertTrue(payload["snapshot_exists"])
            self.assertEqual(payload["store_items_total"], 2)
            self.assertEqual(payload["store_items_for_pair"], 1)
            self.assertEqual(payload["ruleset_rules_count"], 2)
            self.assertEqual(payload["snapshot_target_count"], 2)


class TestHelperEngineInitializeSrsSet(unittest.TestCase):
    def test_initialize_set_adds_items_for_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            source_db.touch()

            initial_store = SrsStore(
                items=(
                    SrsItem(
                        item_id="en-ja:alpha",
                        lemma="alpha",
                        language_pair="en-ja",
                        source_type="initial_set",
                    ),
                    SrsItem(
                        item_id="en-en:beta",
                        lemma="beta",
                        language_pair="en-en",
                        source_type="initial_set",
                    ),
                ),
                version=1,
            )
            save_srs_store(initial_store, paths.srs_store_path)

            updated_store = SrsStore(
                items=(
                    *initial_store.items,
                    SrsItem(
                        item_id="en-ja:gamma",
                        lemma="gamma",
                        language_pair="en-ja",
                        source_type="initial_set",
                    ),
                ),
                version=1,
            )

            with patch(
                "lexishift_core.helper.engine.initialize_store_from_frequency_list_with_report",
                return_value=(
                    updated_store,
                    SimpleNamespace(
                        selected_count=2,
                        selected_unique_count=2,
                        admitted_count=1,
                        inserted_count=1,
                        updated_count=1,
                        selected_preview=("alpha", "gamma"),
                        initial_active_preview=("alpha",),
                    ),
                ),
            ):
                result = initialize_srs_set(
                    paths,
                    config=SetInitializationJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        set_top_n=500,
                    ),
                )

            persisted = load_srs_store(paths.srs_store_path)
            self.assertEqual(len(persisted.items), 3)
            self.assertEqual(result["pair"], "en-ja")
            self.assertEqual(result["added_items"], 1)
            self.assertEqual(result["total_items_for_pair"], 2)
            self.assertEqual(result["set_top_n"], 500)

    def test_initialize_set_replace_pair_removes_existing_pair_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            source_db.touch()

            initial_store = SrsStore(
                items=(
                    SrsItem(
                        item_id="en-ja:alpha",
                        lemma="alpha",
                        language_pair="en-ja",
                        source_type="initial_set",
                    ),
                    SrsItem(
                        item_id="en-en:beta",
                        lemma="beta",
                        language_pair="en-en",
                        source_type="initial_set",
                    ),
                ),
                version=1,
            )
            save_srs_store(initial_store, paths.srs_store_path)

            replaced_store = SrsStore(
                items=(
                    SrsItem(
                        item_id="en-en:beta",
                        lemma="beta",
                        language_pair="en-en",
                        source_type="initial_set",
                    ),
                    SrsItem(
                        item_id="en-ja:gamma",
                        lemma="gamma",
                        language_pair="en-ja",
                        source_type="initial_set",
                    ),
                ),
                version=1,
            )

            with patch(
                "lexishift_core.helper.engine.initialize_store_from_frequency_list_with_report",
                return_value=(
                    replaced_store,
                    SimpleNamespace(
                        selected_count=1,
                        selected_unique_count=1,
                        admitted_count=1,
                        inserted_count=1,
                        updated_count=0,
                        selected_preview=("gamma",),
                        initial_active_preview=("gamma",),
                    ),
                ),
            ):
                result = initialize_srs_set(
                    paths,
                    config=SetInitializationJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        replace_pair=True,
                    ),
                )

            persisted = load_srs_store(paths.srs_store_path)
            self.assertEqual(len([item for item in persisted.items if item.language_pair == "en-ja"]), 1)
            self.assertEqual(result["added_items"], 1)
            self.assertEqual(result["total_items_for_pair"], 1)
            self.assertEqual(result["replace_pair"], True)

    def test_initialize_set_uses_pair_policy_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            source_db.touch()

            persisted_after_init = SrsStore(items=tuple(), version=1)
            init_report = SimpleNamespace(
                selected_count=0,
                selected_unique_count=0,
                admitted_count=0,
                inserted_count=0,
                updated_count=0,
                selected_preview=tuple(),
                initial_active_preview=tuple(),
            )
            rulegen_output = SimpleNamespace(
                rules=tuple(),
                snapshot={"stats": {"target_count": 0, "rule_count": 0}},
                target_count=0,
            )

            with patch(
                "lexishift_core.helper.engine.initialize_store_from_frequency_list_with_report",
                return_value=(persisted_after_init, init_report),
            ) as init_patch, patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                return_value=(persisted_after_init, rulegen_output),
            ):
                result = initialize_srs_set(
                    paths,
                    config=SetInitializationJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        set_top_n=None,
                        initial_active_count=None,
                    ),
                )

            set_init_config = init_patch.call_args.kwargs["config"]
            self.assertEqual(set_init_config.top_n, 800)
            self.assertEqual(set_init_config.initial_active_count, 40)
            self.assertEqual(result["set_top_n"], 800)
            self.assertEqual(result["initial_active_count"], 40)
            self.assertEqual(result["pair_policy"]["pair"], "en-ja")


class TestHelperEnginePlanSrsSet(unittest.TestCase):
    def test_plan_returns_signal_summary_and_strategy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:alpha",
                            lemma="alpha",
                            language_pair="en-ja",
                            source_type="initial_set",
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )
            plan_payload = plan_srs_set(
                paths,
                config=SetPlanningJobConfig(
                    pair="en-ja",
                    strategy="profile_bootstrap",
                    objective="bootstrap",
                    set_top_n=800,
                    profile_context={"interests": ["animals"]},
                ),
            )

            self.assertEqual(plan_payload["pair"], "en-ja")
            self.assertEqual(plan_payload["existing_items_for_pair"], 1)
            self.assertIn("plan", plan_payload)
            plan = plan_payload["plan"]
            self.assertEqual(plan["strategy_requested"], "profile_bootstrap")
            self.assertEqual(plan["strategy_effective"], "frequency_bootstrap")
            self.assertTrue(plan["can_execute"])

    def test_plan_resolves_stopwords_path_from_srs_subdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            stopwords_dir = paths.srs_dir / "stopwords"
            stopwords_dir.mkdir(parents=True, exist_ok=True)
            stopwords_path = stopwords_dir / "stopwords-ja.json"
            stopwords_path.write_text('["の","に"]', encoding="utf-8")
            plan_payload = plan_srs_set(
                paths,
                config=SetPlanningJobConfig(
                    pair="en-ja",
                    strategy="frequency_bootstrap",
                    objective="bootstrap",
                ),
            )

            self.assertEqual(plan_payload["stopwords_path"], str(stopwords_path))

    def test_plan_uses_pair_policy_defaults_when_values_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            plan_payload = plan_srs_set(
                paths,
                config=SetPlanningJobConfig(
                    pair="en-de",
                    strategy="frequency_bootstrap",
                    objective="bootstrap",
                    set_top_n=None,
                    initial_active_count=None,
                ),
            )

            self.assertEqual(plan_payload["set_top_n"], 800)
            self.assertEqual(plan_payload["initial_active_count"], 40)
            self.assertEqual(plan_payload["pair_policy"]["pair"], "en-de")


class TestHelperEngineRefreshSrsSet(unittest.TestCase):
    def test_refresh_adds_new_items_when_feedback_and_capacity_allow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            source_db.touch()

            save_srs_settings(
                SrsSettings(max_active_items=10, max_new_items_per_day=4),
                paths.srs_settings_path,
            )
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:alpha",
                            lemma="alpha",
                            language_pair="en-ja",
                            source_type="initial_set",
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )
            save_signal_events(
                paths.srs_signal_queue_path,
                [
                    SrsSignalEvent(
                        event_type="feedback",
                        pair="en-ja",
                        lemma=f"lemma{i}",
                        source_type="extension",
                        rating="good",
                    )
                    for i in range(12)
                ],
            )

            selected = [
                SimpleNamespace(
                    lemma="alpha",
                    language_pair="en-ja",
                    core_rank=1.0,
                    pos="名詞-普通名詞-一般",
                    pos_bucket="noun",
                    pos_weight=1.0,
                    pmw=100.0,
                    base_weight=0.9,
                    admission_weight=0.9,
                    metadata={},
                ),
                SimpleNamespace(
                    lemma="beta",
                    language_pair="en-ja",
                    core_rank=2.0,
                    pos="名詞-普通名詞-一般",
                    pos_bucket="noun",
                    pos_weight=1.0,
                    pmw=95.0,
                    base_weight=0.85,
                    admission_weight=0.85,
                    metadata={},
                ),
                SimpleNamespace(
                    lemma="gamma",
                    language_pair="en-ja",
                    core_rank=3.0,
                    pos="形容詞-一般",
                    pos_bucket="adjective",
                    pos_weight=0.85,
                    pmw=90.0,
                    base_weight=0.8,
                    admission_weight=0.68,
                    metadata={},
                ),
                SimpleNamespace(
                    lemma="delta",
                    language_pair="en-ja",
                    core_rank=4.0,
                    pos="動詞-一般",
                    pos_bucket="verb",
                    pos_weight=0.70,
                    pmw=85.0,
                    base_weight=0.75,
                    admission_weight=0.525,
                    metadata={},
                ),
            ]
            with patch(
                "lexishift_core.helper.engine.build_seed_candidates",
                return_value=selected,
            ):
                result = refresh_srs_set(
                    paths,
                    config=SrsRefreshJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        set_top_n=2000,
                        feedback_window_size=100,
                        persist_store=True,
                    ),
                )

            persisted = load_srs_store(paths.srs_store_path)
            by_pair = [item for item in persisted.items if item.language_pair == "en-ja"]
            self.assertEqual(len(by_pair), 4)
            self.assertTrue(result["applied"])
            self.assertEqual(result["added_items"], 3)
            self.assertEqual(result["admission_refresh"]["reason_code"], "normal")
            self.assertIn("admission_weight", result["admission_refresh"]["weight_terms"])
            self.assertIn("serving_priority", result["admission_refresh"]["weight_terms"])

    def test_refresh_pauses_admission_for_low_retention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            source_db.touch()

            save_srs_settings(
                SrsSettings(max_active_items=10, max_new_items_per_day=4),
                paths.srs_settings_path,
            )
            save_srs_store(SrsStore(items=tuple(), version=1), paths.srs_store_path)
            save_signal_events(
                paths.srs_signal_queue_path,
                [
                    SrsSignalEvent(
                        event_type="feedback",
                        pair="en-ja",
                        lemma=f"lemma{i}",
                        source_type="extension",
                        rating=("again" if i % 2 == 0 else "hard"),
                    )
                    for i in range(12)
                ],
            )

            selected = [
                SimpleNamespace(
                    lemma="beta",
                    language_pair="en-ja",
                    core_rank=2.0,
                    pos="名詞-普通名詞-一般",
                    pos_bucket="noun",
                    pos_weight=1.0,
                    pmw=95.0,
                    base_weight=0.85,
                    admission_weight=0.85,
                    metadata={},
                ),
            ]
            with patch(
                "lexishift_core.helper.engine.build_seed_candidates",
                return_value=selected,
            ):
                result = refresh_srs_set(
                    paths,
                    config=SrsRefreshJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        feedback_window_size=100,
                        persist_store=True,
                    ),
                )

            persisted = load_srs_store(paths.srs_store_path)
            self.assertEqual(len(persisted.items), 0)
            self.assertFalse(result["applied"])
            self.assertEqual(result["added_items"], 0)
            self.assertEqual(result["admission_refresh"]["reason_code"], "retention_low")

    def test_refresh_uses_pair_policy_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            source_db.touch()
            save_srs_store(SrsStore(items=tuple(), version=1), paths.srs_store_path)

            with patch(
                "lexishift_core.helper.engine.build_seed_candidates",
                return_value=[],
            ) as build_seed:
                result = refresh_srs_set(
                    paths,
                    config=SrsRefreshJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        set_top_n=None,
                        feedback_window_size=None,
                        persist_store=False,
                    ),
                )

            selection_config = build_seed.call_args.kwargs["config"]
            self.assertEqual(selection_config.top_n, 2000)
            self.assertEqual(result["set_top_n"], 2000)
            self.assertEqual(result["feedback_window_size"], 100)
            self.assertEqual(result["pair_policy"]["pair"], "en-ja")


class TestHelperEngineFeedbackCycle(unittest.TestCase):
    def test_feedback_updates_schedule_and_blocks_low_retention_admission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            source_db.touch()

            save_srs_settings(
                SrsSettings(max_active_items=20, max_new_items_per_day=4),
                paths.srs_settings_path,
            )
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:alpha",
                            lemma="alpha",
                            language_pair="en-ja",
                            source_type="initial_set",
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )

            for _ in range(8):
                apply_feedback(
                    paths,
                    pair="en-ja",
                    lemma="alpha",
                    rating="again",
                    source_type="extension",
                )

            stored = load_srs_store(paths.srs_store_path)
            alpha = next(item for item in stored.items if item.item_id == "en-ja:alpha")
            self.assertEqual(alpha.exposures, 8)
            self.assertEqual(len(alpha.history), 8)
            self.assertEqual(alpha.history[-1].rating, "again")
            self.assertIsNotNone(alpha.last_seen)
            self.assertIsNotNone(alpha.next_due)
            self.assertIsNotNone(alpha.stability)
            self.assertIsNotNone(alpha.difficulty)

            events = load_signal_events(paths.srs_signal_queue_path)
            feedback_events = [event for event in events if event.event_type == "feedback" and event.pair == "en-ja"]
            self.assertEqual(len(feedback_events), 8)
            self.assertTrue(all(event.rating == "again" for event in feedback_events))

            selected = [
                SimpleNamespace(
                    lemma="beta",
                    language_pair="en-ja",
                    core_rank=2.0,
                    pos="名詞-普通名詞-一般",
                    pos_bucket="noun",
                    pos_weight=1.0,
                    pmw=95.0,
                    base_weight=0.85,
                    admission_weight=0.85,
                    metadata={},
                ),
            ]
            with patch(
                "lexishift_core.helper.engine.build_seed_candidates",
                return_value=selected,
            ):
                result = refresh_srs_set(
                    paths,
                    config=SrsRefreshJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        feedback_window_size=100,
                        persist_store=True,
                    ),
                )

            stored_after = load_srs_store(paths.srs_store_path)
            by_pair = [item for item in stored_after.items if item.language_pair == "en-ja"]
            self.assertEqual(len(by_pair), 1)
            self.assertFalse(result["applied"])
            self.assertEqual(result["added_items"], 0)
            self.assertEqual(result["admission_refresh"]["reason_code"], "retention_low")
            self.assertEqual(result["admission_refresh"]["feedback_window"]["feedback_count"], 8)

    def test_good_feedback_allows_admission_and_publishes_rulegen_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            source_db.touch()

            save_srs_settings(
                SrsSettings(max_active_items=20, max_new_items_per_day=2),
                paths.srs_settings_path,
            )
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:alpha",
                            lemma="alpha",
                            language_pair="en-ja",
                            source_type="initial_set",
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )

            for rating in ("good", "easy", "good", "easy", "good", "easy", "good", "easy"):
                apply_feedback(
                    paths,
                    pair="en-ja",
                    lemma="alpha",
                    rating=rating,
                    source_type="extension",
                )

            selected = [
                SimpleNamespace(
                    lemma="alpha",
                    language_pair="en-ja",
                    core_rank=1.0,
                    pos="名詞-普通名詞-一般",
                    pos_bucket="noun",
                    pos_weight=1.0,
                    pmw=100.0,
                    base_weight=0.9,
                    admission_weight=0.9,
                    metadata={},
                ),
                SimpleNamespace(
                    lemma="beta",
                    language_pair="en-ja",
                    core_rank=2.0,
                    pos="名詞-普通名詞-一般",
                    pos_bucket="noun",
                    pos_weight=1.0,
                    pmw=95.0,
                    base_weight=0.85,
                    admission_weight=0.85,
                    metadata={},
                ),
                SimpleNamespace(
                    lemma="gamma",
                    language_pair="en-ja",
                    core_rank=3.0,
                    pos="形容詞-一般",
                    pos_bucket="adjective",
                    pos_weight=0.85,
                    pmw=90.0,
                    base_weight=0.8,
                    admission_weight=0.68,
                    metadata={},
                ),
            ]

            def _stub_run_rulegen_for_pair(*, store, pair, **_kwargs):
                rules = (
                    VocabRule(source_phrase="matter", replacement="事"),
                    VocabRule(source_phrase="thing", replacement="物"),
                )
                snapshot = {
                    "version": 1,
                    "pair": pair,
                    "targets": [
                        {"lemma": "事", "sources": ["matter"]},
                        {"lemma": "物", "sources": ["thing"]},
                    ],
                    "stats": {"target_count": 2, "rule_count": 2, "source_count": 2},
                }
                return store, SimpleNamespace(rules=rules, snapshot=snapshot, target_count=2)

            with patch(
                "lexishift_core.helper.engine.build_seed_candidates",
                return_value=selected,
            ), patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                side_effect=_stub_run_rulegen_for_pair,
            ):
                result = refresh_srs_set(
                    paths,
                    config=SrsRefreshJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        feedback_window_size=100,
                        persist_store=True,
                    ),
                )

            persisted = load_srs_store(paths.srs_store_path)
            by_pair = [item for item in persisted.items if item.language_pair == "en-ja"]
            self.assertEqual(len(by_pair), 3)
            self.assertTrue(result["applied"])
            self.assertEqual(result["added_items"], 2)
            self.assertEqual(result["admission_refresh"]["reason_code"], "normal")
            self.assertEqual(result["admission_refresh"]["feedback_window"]["feedback_count"], 8)

            rulegen_payload = result.get("rulegen")
            self.assertIsNotNone(rulegen_payload)
            self.assertTrue(rulegen_payload.get("published"))
            self.assertEqual(rulegen_payload.get("targets"), 2)
            self.assertEqual(rulegen_payload.get("rules"), 2)
            self.assertTrue(Path(rulegen_payload.get("snapshot_path")).exists())
            self.assertTrue(Path(rulegen_payload.get("ruleset_path")).exists())


class TestHelperEngineExposureOnly(unittest.TestCase):
    def test_exposure_only_does_not_mutate_schedule_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            initial_last_seen = "2026-02-01T00:00:00+00:00"
            initial_next_due = "2026-02-20T00:00:00+00:00"
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:alpha",
                            lemma="alpha",
                            language_pair="en-ja",
                            source_type="initial_set",
                            stability=2.5,
                            difficulty=0.4,
                            last_seen=initial_last_seen,
                            next_due=initial_next_due,
                            exposures=3,
                            history=(
                                SrsHistoryEntry(ts="2026-01-31T00:00:00+00:00", rating="good"),
                            ),
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )

            apply_exposure(paths, pair="en-ja", lemma="alpha", source_type="extension")
            apply_exposure(paths, pair="en-ja", lemma="alpha", source_type="extension")

            stored = load_srs_store(paths.srs_store_path)
            alpha = next(item for item in stored.items if item.item_id == "en-ja:alpha")
            self.assertEqual(alpha.exposures, 5)
            self.assertEqual(len(alpha.history), 1)
            self.assertEqual(alpha.stability, 2.5)
            self.assertEqual(alpha.difficulty, 0.4)
            self.assertEqual(alpha.next_due, initial_next_due)
            self.assertNotEqual(alpha.last_seen, initial_last_seen)

            events = load_signal_events(paths.srs_signal_queue_path)
            exposure_events = [event for event in events if event.event_type == "exposure" and event.pair == "en-ja"]
            feedback_events = [event for event in events if event.event_type == "feedback" and event.pair == "en-ja"]
            self.assertEqual(len(exposure_events), 2)
            self.assertEqual(len(feedback_events), 0)
            self.assertTrue(all(event.rating is None for event in exposure_events))


if __name__ == "__main__":
    unittest.main()
