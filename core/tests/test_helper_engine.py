from __future__ import annotations

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

from lexishift_core.helper_engine import (  # noqa: E402
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
from lexishift_core.helper_paths import HelperPaths, build_helper_paths  # noqa: E402
from lexishift_core.srs_signal_queue import SrsSignalEvent, save_signal_events  # noqa: E402
from lexishift_core.srs import SrsItem, SrsSettings, SrsStore, load_srs_store, save_srs_settings, save_srs_store  # noqa: E402


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
                "lexishift_core.helper_engine.run_rulegen_for_pair",
                return_value=(SrsStore(), self._stub_output()),
            ), patch("lexishift_core.helper_engine.write_rulegen_outputs") as write_outputs, patch(
                "lexishift_core.helper_engine._update_status"
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
                "lexishift_core.helper_engine.run_rulegen_for_pair",
                return_value=(mutated_store, self._stub_output()),
            ), patch("lexishift_core.helper_engine.write_rulegen_outputs"), patch(
                "lexishift_core.helper_engine._update_status"
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
                "lexishift_core.helper_engine.run_rulegen_for_pair",
                return_value=(load_srs_store(paths.srs_store_path), self._stub_output()),
            ) as run_rulegen, patch("lexishift_core.helper_engine.write_rulegen_outputs"), patch(
                "lexishift_core.helper_engine._update_status"
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
                "lexishift_core.helper_engine.initialize_store_from_frequency_list_with_report",
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
                "lexishift_core.helper_engine.initialize_store_from_frequency_list_with_report",
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
                "lexishift_core.helper_engine.build_seed_candidates",
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
                "lexishift_core.helper_engine.build_seed_candidates",
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


if __name__ == "__main__":
    unittest.main()
