from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from hashlib import sha1
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.engine import (  # noqa: E402
    apply_srs_rebalance,
    apply_exposure,
    apply_feedback,
    get_srs_runtime_diagnostics,
    load_semantic_inventory,
    plan_srs_rebalance,
    preview_srs_admission,
    RulegenJobConfig,
    SrsRebalanceJobConfig,
    SrsRefreshJobConfig,
    SetAdmissionPreviewJobConfig,
    SetInitializationJobConfig,
    SetPlanningJobConfig,
    initialize_srs_set,
    plan_srs_set,
    refresh_srs_set,
    reset_srs_data,
    run_rulegen_job,
    semantic_admit_batch,
)
from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402
from lexishift_core.helper.paths import HelperPaths, build_helper_paths  # noqa: E402
from lexishift_core.srs.signal_queue import SrsSignalEvent, load_signal_events, save_signal_events  # noqa: E402
from lexishift_core.srs import (
    SrsInventory,
    SrsHistoryEntry,
    SrsItem,
    SrsPairInventory,
    SrsSettings,
    SrsStore,
    load_srs_inventory,
    load_srs_store,
    save_srs_inventory,
    save_srs_settings,
    save_srs_store,
)  # noqa: E402
from lexishift_core.replacement.core import VocabRule  # noqa: E402
from lexishift_core.rulegen.tuning import resolve_pair_rulegen_tuning  # noqa: E402


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
    save_srs_inventory(
        SrsInventory(
            pairs={
                "en-ja": SrsPairInventory(active_item_ids=("en-ja:alpha",)),
                "en-en": SrsPairInventory(active_item_ids=("en-en:beta",)),
            }
        ),
        paths.srs_inventory_path_for("default"),
    )
    paths.snapshot_path("en-ja").write_text("{}", encoding="utf-8")
    paths.snapshot_path("en-en").write_text("{}", encoding="utf-8")
    paths.ruleset_path("en-ja").write_text("{}", encoding="utf-8")
    paths.ruleset_path("en-en").write_text("{}", encoding="utf-8")
    paths.semantic_inventory_path("en-ja").write_text("{}", encoding="utf-8")
    paths.semantic_inventory_path("en-en").write_text("{}", encoding="utf-8")
    paths.publication_manifest_path("en-ja").write_text("{}", encoding="utf-8")
    paths.publication_manifest_path("en-en").write_text("{}", encoding="utf-8")
    return paths


def _create_frequency_db(
    path: Path,
    *,
    rows: tuple[tuple[object, ...], ...] | None = None,
) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT,
                core_rank REAL,
                pmw REAL,
                pos TEXT,
                lform TEXT,
                wtype TEXT,
                sublemma TEXT,
                sense_topics TEXT,
                topics TEXT,
                topic TEXT,
                profile_topics TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO frequency (
                lemma,
                core_rank,
                pmw,
                pos,
                lform,
                wtype,
                sublemma,
                sense_topics,
                topics,
                topic,
                profile_topics
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows or (("alpha", 1.0, 100.0, "n", None, None, None, None, None, None, None),),
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _artifact_manifest_entry(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {
        "path": str(path),
        "exists": True,
        "sha1": sha1(payload).hexdigest(),
        "bytes": len(payload),
    }


def _write_publication_manifest_fixture(
    paths: HelperPaths,
    *,
    pair: str,
    generation_id: str,
    generated_at: str,
    profile_id: str = "default",
    semantic_inventory_included: bool = True,
) -> None:
    manifest_payload = {
        "schema_version": 1,
        "pair": pair,
        "profile_id": profile_id,
        "generated_at": generated_at,
        "published_at": generated_at,
        "generation_id": generation_id,
        "artifacts": {
            "ruleset": _artifact_manifest_entry(paths.ruleset_path(pair, profile_id=profile_id)),
            "snapshot": _artifact_manifest_entry(paths.snapshot_path(pair, profile_id=profile_id)),
            "semantic_inventory": _artifact_manifest_entry(
                paths.semantic_inventory_path(pair, profile_id=profile_id)
            )
            if semantic_inventory_included
            else {
                "path": str(paths.semantic_inventory_path(pair, profile_id=profile_id)),
                "exists": False,
                "sha1": None,
                "bytes": 0,
            },
        },
        "validation": {
            "family_valid": True,
            "semantic_inventory_included": semantic_inventory_included,
            "errors": [],
        },
    }
    paths.publication_manifest_path(pair, profile_id=profile_id).write_text(
        json.dumps(manifest_payload),
        encoding="utf-8",
    )


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
            self.assertFalse(paths.semantic_inventory_path("en-ja").exists())
            self.assertFalse(paths.publication_manifest_path("en-ja").exists())
            self.assertTrue(paths.snapshot_path("en-en").exists())
            self.assertTrue(paths.ruleset_path("en-en").exists())
            self.assertTrue(paths.semantic_inventory_path("en-en").exists())
            self.assertTrue(paths.publication_manifest_path("en-en").exists())
            inventory = load_srs_inventory(paths.srs_inventory_path_for("default"))
            self.assertEqual(tuple(inventory.pairs.keys()), ("en-en",))
            self.assertEqual(
                tuple(inventory.pairs["en-en"].active_item_ids),
                ("en-en:beta",),
            )

            self.assertEqual(result["pair"], "en-ja")
            self.assertEqual(result["removed_items"], 1)
            self.assertEqual(result["remaining_items"], 1)
            self.assertEqual(result["removed_snapshots"], 1)
            self.assertEqual(result["removed_rulesets"], 1)
            self.assertEqual(result["removed_inventory_files"], 0)
            self.assertEqual(result["removed_inventory_pairs"], 1)
            self.assertEqual(result["removed_semantic_inventories"], 1)
            self.assertEqual(result["removed_publication_manifests"], 1)

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
            self.assertFalse(paths.semantic_inventory_path("en-ja").exists())
            self.assertFalse(paths.semantic_inventory_path("en-en").exists())
            self.assertFalse(paths.publication_manifest_path("en-ja").exists())
            self.assertFalse(paths.publication_manifest_path("en-en").exists())
            self.assertFalse(paths.srs_inventory_path_for("default").exists())

            self.assertEqual(result["pair"], "all")
            self.assertEqual(result["removed_items"], 2)
            self.assertEqual(result["remaining_items"], 0)
            self.assertEqual(result["removed_snapshots"], 2)
            self.assertEqual(result["removed_rulesets"], 2)
            self.assertEqual(result["removed_inventory_files"], 1)
            self.assertEqual(result["removed_inventory_pairs"], 2)
            self.assertEqual(result["removed_semantic_inventories"], 2)
            self.assertEqual(result["removed_publication_manifests"], 2)


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
            save_srs_inventory(
                SrsInventory(
                    pairs={
                        "en-ja": SrsPairInventory(active_item_ids=("en-ja:alpha",)),
                    }
                ),
                paths.srs_inventory_path_for(default_profile),
            )
            save_srs_inventory(
                SrsInventory(
                    pairs={
                        "en-ja": SrsPairInventory(active_item_ids=("en-ja:beta",)),
                    }
                ),
                paths.srs_inventory_path_for(other_profile),
            )

            paths.snapshot_path("en-ja", profile_id=default_profile).write_text(
                "{}", encoding="utf-8"
            )
            paths.ruleset_path("en-ja", profile_id=default_profile).write_text(
                "{}", encoding="utf-8"
            )
            paths.semantic_inventory_path("en-ja", profile_id=default_profile).write_text(
                "{}", encoding="utf-8"
            )
            paths.publication_manifest_path("en-ja", profile_id=default_profile).write_text(
                "{}", encoding="utf-8"
            )
            paths.snapshot_path("en-ja", profile_id=other_profile).write_text(
                "{}", encoding="utf-8"
            )
            paths.ruleset_path("en-ja", profile_id=other_profile).write_text("{}", encoding="utf-8")
            paths.semantic_inventory_path("en-ja", profile_id=other_profile).write_text(
                "{}", encoding="utf-8"
            )
            paths.publication_manifest_path("en-ja", profile_id=other_profile).write_text(
                "{}", encoding="utf-8"
            )

            result = reset_srs_data(paths, pair="en-ja", profile_id=other_profile)

            default_store = load_srs_store(paths.srs_store_path_for(default_profile))
            other_store = load_srs_store(paths.srs_store_path_for(other_profile))
            self.assertEqual(len(default_store.items), 1)
            self.assertEqual(len(other_store.items), 0)
            self.assertTrue(paths.snapshot_path("en-ja", profile_id=default_profile).exists())
            self.assertTrue(paths.ruleset_path("en-ja", profile_id=default_profile).exists())
            self.assertTrue(
                paths.semantic_inventory_path("en-ja", profile_id=default_profile).exists()
            )
            self.assertTrue(
                paths.publication_manifest_path("en-ja", profile_id=default_profile).exists()
            )
            self.assertTrue(paths.srs_inventory_path_for(default_profile).exists())
            self.assertFalse(paths.snapshot_path("en-ja", profile_id=other_profile).exists())
            self.assertFalse(paths.ruleset_path("en-ja", profile_id=other_profile).exists())
            self.assertFalse(
                paths.semantic_inventory_path("en-ja", profile_id=other_profile).exists()
            )
            self.assertFalse(
                paths.publication_manifest_path("en-ja", profile_id=other_profile).exists()
            )
            self.assertFalse(paths.srs_inventory_path_for(other_profile).exists())
            self.assertEqual(result["profile_id"], other_profile)
            self.assertEqual(result["removed_items"], 1)
            self.assertEqual(result["removed_inventory_files"], 1)
            self.assertEqual(result["removed_inventory_pairs"], 1)
            self.assertEqual(result["removed_publication_manifests"], 1)


class TestHelperEngineSemanticInventoryLoad(unittest.TestCase):
    def test_load_semantic_inventory_reads_profile_scoped_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            payload = {
                "schema_version": 1,
                "pair": "en-es",
                "profile_id": "default",
                "generated_at": "2026-04-13T00:00:00Z",
                "triggers": {},
                "senses": {},
                "competition_sets": {},
                "phrase_sets": {},
            }
            paths.semantic_inventory_path("en-es").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            loaded = load_semantic_inventory(paths, pair="en-es")

            self.assertEqual(loaded["pair"], "en-es")
            self.assertEqual(loaded["schema_version"], 1)

    def test_semantic_admit_batch_falls_back_when_inventory_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))

            response = semantic_admit_batch(
                paths,
                payload={
                    "pair": "en-es",
                    "profile_id": "default",
                    "fallback_policy": "abstain_on_unavailable",
                    "matches": [
                        {
                            "match_id": "m1",
                            "source_phrase": "bank",
                            "context_text": "You can bank on her support.",
                            "match_start": 8,
                            "match_end": 12,
                            "semantic_admission": {
                                "schema_version": 1,
                                "status": "ready",
                                "trigger_id": "en-es:trigger:bank",
                                "sense_id": "sense:banco",
                                "competition_set_id": "comp:bank",
                            },
                        }
                    ],
                },
            )

            self.assertEqual(response["decision_policy_id"], "en_es_sentence_veto_v1")
            self.assertEqual(response["decisions"][0]["decision"], "abstain")
            self.assertEqual(response["decisions"][0]["decision_source"], "fallback_policy")
            self.assertIn("semantic_inventory_missing", response["decisions"][0]["reason_codes"])

    def test_semantic_admit_batch_rejects_non_object_match_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))

            with self.assertRaisesRegex(
                ValueError,
                "semantic_admit_batch requires object-valued `matches` items.",
            ):
                semantic_admit_batch(
                    paths,
                    payload={
                        "pair": "en-es",
                        "profile_id": "default",
                        "matches": [{}, None],
                    },
                )


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

            with (
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    return_value=(SrsStore(), self._stub_output()),
                ),
                patch("lexishift_core.helper.engine.write_rulegen_outputs") as write_outputs,
                patch("lexishift_core.helper.engine._update_status") as update_status,
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
                    ),
                )

            self.assertFalse(paths.srs_settings_path.exists())
            self.assertFalse(paths.srs_store_path.exists())
            self.assertFalse(paths.snapshot_path("en-ja").exists())
            self.assertFalse(paths.ruleset_path("en-ja").exists())
            self.assertFalse(paths.semantic_inventory_path("en-ja").exists())
            self.assertEqual(result["snapshot_path"], None)
            self.assertEqual(result["ruleset_path"], None)
            self.assertEqual(result["semantic_inventory_path"], None)
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

            with (
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    return_value=(mutated_store, self._stub_output()),
                ),
                patch("lexishift_core.helper.engine.write_rulegen_outputs"),
                patch("lexishift_core.helper.engine._update_status"),
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

            with (
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    return_value=(load_srs_store(paths.srs_store_path), self._stub_output()),
                ) as run_rulegen,
                patch("lexishift_core.helper.engine.write_rulegen_outputs"),
                patch("lexishift_core.helper.engine._update_status"),
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

    def test_rulegen_uses_inventory_active_ids_when_present(self) -> None:
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
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )
            save_srs_inventory(
                SrsInventory(
                    pairs={
                        "en-ja": SrsPairInventory(active_item_ids=("en-ja:beta",)),
                    }
                ),
                paths.srs_inventory_path_for("default"),
            )

            with (
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    return_value=(load_srs_store(paths.srs_store_path), self._stub_output()),
                ) as run_rulegen,
                patch("lexishift_core.helper.engine.write_rulegen_outputs"),
                patch("lexishift_core.helper.engine._update_status"),
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
                    ),
                )

            self.assertEqual(
                tuple(run_rulegen.call_args.kwargs["active_item_ids"]),
                ("en-ja:beta",),
            )
            self.assertEqual(result["inventory"]["source"], "inventory")
            self.assertEqual(result["inventory"]["active_items_for_pair"], 1)

    def test_rulegen_backfills_inventory_after_bootstrap_publish(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            _create_frequency_db(source_db)

            seeded_store = SrsStore(
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
                ),
                version=1,
            )

            with (
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    return_value=(seeded_store, self._stub_output()),
                ) as run_rulegen,
                patch("lexishift_core.helper.engine.write_rulegen_outputs"),
                patch("lexishift_core.helper.engine._update_status"),
            ):
                result = run_rulegen_job(
                    paths,
                    config=RulegenJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        initialize_if_empty=True,
                        persist_store=False,
                        persist_outputs=True,
                        update_status=False,
                    ),
                )

            self.assertIsNone(run_rulegen.call_args.kwargs["active_item_ids"])
            inventory = load_srs_inventory(paths.srs_inventory_path_for("default"))
            self.assertEqual(
                tuple(inventory.pairs["en-ja"].active_item_ids),
                ("en-ja:alpha", "en-ja:beta"),
            )
            self.assertEqual(result["inventory"]["source"], "inventory_backfilled")
            self.assertTrue(result["inventory"]["backfilled_from_store"])

    def test_rulegen_uses_pair_tuning_defaults_when_overrides_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            freedict_path = root / "spa-eng.tei"
            freedict_path.write_text("<TEI></TEI>", encoding="utf-8")

            with (
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    return_value=(SrsStore(), self._stub_output()),
                ) as run_rulegen,
                patch("lexishift_core.helper.engine.write_rulegen_outputs"),
                patch("lexishift_core.helper.engine._update_status"),
            ):
                run_rulegen_job(
                    paths,
                    config=RulegenJobConfig(
                        pair="en-es",
                        jmdict_path=None,
                        translation_dict_path=freedict_path,
                        set_source_db=None,
                        initialize_if_empty=False,
                        persist_store=False,
                        persist_outputs=False,
                        update_status=False,
                    ),
                )

            rulegen_config = run_rulegen.call_args.kwargs["rulegen_config"]
            defaults = resolve_pair_rulegen_tuning("en-es")
            self.assertAlmostEqual(
                rulegen_config.confidence_threshold,
                defaults.confidence_threshold,
                places=6,
            )
            self.assertEqual(
                rulegen_config.max_definitions_per_target,
                defaults.max_definitions_per_target,
            )
            self.assertEqual(
                rulegen_config.max_rules_per_target,
                defaults.max_rules_per_target,
            )
            self.assertAlmostEqual(
                rulegen_config.semantic_demotion_scale,
                defaults.semantic_demotion_scale,
                places=6,
            )
            self.assertEqual(
                rulegen_config.include_variants,
                defaults.include_variants,
            )
            self.assertEqual(
                rulegen_config.allow_multiword_glosses,
                defaults.allow_multiword_glosses,
            )
            self.assertAlmostEqual(
                rulegen_config.scoring.weights.pos_match,
                defaults.scoring.weights.pos_match,
                places=6,
            )
            self.assertEqual(
                rulegen_config.scoring.pos_match.enabled,
                defaults.scoring.pos_match.enabled,
            )
            self.assertEqual(
                rulegen_config.reverse_check.enabled,
                defaults.reverse_check.enabled,
            )
            self.assertAlmostEqual(
                rulegen_config.reverse_check.match_bonus,
                defaults.reverse_check.match_bonus,
                places=6,
            )

    def test_rulegen_overrides_take_precedence_over_pair_tuning_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            freedict_path = root / "spa-eng.tei"
            freedict_path.write_text("<TEI></TEI>", encoding="utf-8")

            with (
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    return_value=(SrsStore(), self._stub_output()),
                ) as run_rulegen,
                patch("lexishift_core.helper.engine.write_rulegen_outputs"),
                patch("lexishift_core.helper.engine._update_status"),
            ):
                run_rulegen_job(
                    paths,
                    config=RulegenJobConfig(
                        pair="en-es",
                        jmdict_path=None,
                        translation_dict_path=freedict_path,
                        set_source_db=None,
                        initialize_if_empty=False,
                        persist_store=False,
                        persist_outputs=False,
                        update_status=False,
                        confidence_threshold=0.25,
                        max_definitions_per_target=2,
                        max_rules_per_target=4,
                        semantic_demotion_scale=0.65,
                        include_variants=True,
                        allow_multiword_glosses=True,
                        pos_scoring_enabled=False,
                        score_weight_pos_match=0.35,
                        reverse_check_enabled=True,
                        reverse_check_match_bonus=0.24,
                        reverse_check_near_bonus=0.09,
                        reverse_check_near_rank_max=1,
                        reverse_check_miss_penalty=0.19,
                        reverse_check_exact_hit_ambiguity_threshold=12,
                        reverse_check_exact_hit_ambiguity_penalty=0.33,
                        reverse_check_exact_hit_specificity_bonus=0.14,
                    ),
                )

            rulegen_config = run_rulegen.call_args.kwargs["rulegen_config"]
            self.assertAlmostEqual(rulegen_config.confidence_threshold, 0.25, places=6)
            self.assertEqual(rulegen_config.max_definitions_per_target, 2)
            self.assertEqual(rulegen_config.max_rules_per_target, 4)
            self.assertAlmostEqual(rulegen_config.semantic_demotion_scale, 0.65, places=6)
            self.assertTrue(rulegen_config.include_variants)
            self.assertTrue(rulegen_config.allow_multiword_glosses)
            self.assertFalse(rulegen_config.scoring.pos_match.enabled)
            self.assertAlmostEqual(rulegen_config.scoring.weights.pos_match, 0.35, places=6)
            self.assertTrue(rulegen_config.reverse_check.enabled)
            self.assertAlmostEqual(rulegen_config.reverse_check.match_bonus, 0.24, places=6)
            self.assertAlmostEqual(rulegen_config.reverse_check.near_bonus, 0.09, places=6)
            self.assertEqual(rulegen_config.reverse_check.near_rank_max, 1)
            self.assertAlmostEqual(rulegen_config.reverse_check.miss_penalty, 0.19, places=6)
            self.assertEqual(rulegen_config.reverse_check.exact_hit_ambiguity_threshold, 12)
            self.assertAlmostEqual(
                rulegen_config.reverse_check.exact_hit_ambiguity_penalty,
                0.33,
                places=6,
            )
            self.assertAlmostEqual(
                rulegen_config.reverse_check.exact_hit_specificity_bonus,
                0.14,
                places=6,
            )


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
                        translation_dict_path=freedict_path,
                        set_source_db=None,
                        initialize_if_empty=False,
                        persist_store=False,
                        persist_outputs=False,
                        update_status=False,
                    ),
                )

            self.assertEqual(result["pair"], "en-de")
            self.assertIsNone(run_rulegen.call_args.kwargs.get("jmdict_path"))
            self.assertEqual(
                run_rulegen.call_args.kwargs.get("translation_dict_path"),
                freedict_path,
            )

    def test_run_rulegen_allows_de_en_without_jmdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            translation_dict_path = root / "eng-deu.tei"
            translation_dict_path.write_text("<TEI></TEI>", encoding="utf-8")
            with patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                return_value=(SrsStore(), self._stub_output("de-en")),
            ) as run_rulegen:
                result = run_rulegen_job(
                    paths,
                    config=RulegenJobConfig(
                        pair="de-en",
                        jmdict_path=None,
                        translation_dict_path=translation_dict_path,
                        set_source_db=None,
                        initialize_if_empty=False,
                        persist_store=False,
                        persist_outputs=False,
                        update_status=False,
                    ),
                )

            self.assertEqual(result["pair"], "de-en")
            self.assertIsNone(run_rulegen.call_args.kwargs.get("jmdict_path"))
            self.assertEqual(
                run_rulegen.call_args.kwargs.get("translation_dict_path"),
                translation_dict_path,
            )
            self.assertEqual(
                run_rulegen.call_args.kwargs.get("translation_dict_path"),
                translation_dict_path,
            )

    def test_run_rulegen_accepts_generic_translation_dictionary_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            translation_dict_path = root / "deu-eng.tei"
            translation_dict_path.write_text("<TEI></TEI>", encoding="utf-8")
            with patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                return_value=(SrsStore(), self._stub_output("en-de")),
            ) as run_rulegen:
                result = run_rulegen_job(
                    paths,
                    config=RulegenJobConfig(
                        pair="en-de",
                        jmdict_path=None,
                        translation_dict_path=translation_dict_path,
                        set_source_db=None,
                        initialize_if_empty=False,
                        persist_store=False,
                        persist_outputs=False,
                        update_status=False,
                    ),
                )

            self.assertEqual(result["pair"], "en-de")
            self.assertIsNone(run_rulegen.call_args.kwargs.get("jmdict_path"))
            self.assertEqual(
                run_rulegen.call_args.kwargs.get("translation_dict_path"),
                translation_dict_path,
            )
            self.assertEqual(
                run_rulegen.call_args.kwargs.get("translation_dict_path"),
                translation_dict_path,
            )

    def test_run_rulegen_debug_reports_manifest_backed_translation_pack_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            forward_root = paths.language_packs_dir / "wiktionary-es-en"
            forward_root.mkdir(parents=True, exist_ok=True)
            forward_artifact = forward_root / "main.sqlite"
            forward_artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                paths.language_packs_dir,
                pack_id="wiktionary-es-en",
                pack_kind="language",
                provider="wiktionary",
                local_kind="file",
                build_mode="kaikki_jsonl_to_sqlite",
                artifact_path=forward_artifact,
                sqlite_filename="main.sqlite",
            )
            reverse_root = paths.language_packs_dir / "wiktionary-en-es"
            reverse_root.mkdir(parents=True, exist_ok=True)
            reverse_artifact = reverse_root / "main.sqlite"
            reverse_artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                paths.language_packs_dir,
                pack_id="wiktionary-en-es",
                pack_kind="language",
                provider="wiktionary",
                local_kind="file",
                build_mode="kaikki_jsonl_to_sqlite",
                artifact_path=reverse_artifact,
                sqlite_filename="main.sqlite",
            )
            with patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                return_value=(SrsStore(), self._stub_output("en-es")),
            ):
                result = run_rulegen_job(
                    paths,
                    config=RulegenJobConfig(
                        pair="en-es",
                        jmdict_path=None,
                        translation_dict_path=forward_artifact,
                        set_source_db=None,
                        initialize_if_empty=False,
                        persist_store=False,
                        persist_outputs=False,
                        update_status=False,
                        debug=True,
                    ),
                )

            payload = result["diagnostics"]
            self.assertEqual(payload["translation_dict_provider"], "wiktionary")
            self.assertEqual(payload["translation_pack_id"], "wiktionary_es_en")
            self.assertEqual(payload["translation_pos_source_profile"], "wiktionary")
            self.assertTrue(
                payload["translation_pack_path"].endswith("/wiktionary-es-en/main.sqlite")
            )
            self.assertTrue(payload["set_source_db"].endswith("freq-es-cde.sqlite"))
            self.assertEqual(payload["frequency_pack_id"], "freq-es-cde")
            self.assertEqual(payload["frequency_pack_provider"], "freq-es-cde")
            self.assertEqual(payload["frequency_pos_source_profile"], "freq-es-cde")
            self.assertEqual(payload["reverse_translation_dict_provider"], "wiktionary")
            self.assertEqual(payload["reverse_translation_pack_id"], "wiktionary_en_es")
            self.assertEqual(payload["reverse_translation_pos_source_profile"], "wiktionary")
            self.assertTrue(
                payload["reverse_translation_pack_path"].endswith("/wiktionary-en-es/main.sqlite")
            )

    def test_initialize_en_de_disables_jmdict_requirement_for_seed_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            source_db = root / "freq.sqlite"
            _create_frequency_db(source_db)
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
            with (
                patch(
                    "lexishift_core.helper.engine.initialize_store_from_frequency_list_with_report",
                    return_value=(SrsStore(), init_report),
                ) as initialize_store,
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    return_value=(SrsStore(), self._stub_output("en-de")),
                ),
            ):
                result = initialize_srs_set(
                    paths,
                    config=SetInitializationJobConfig(
                        pair="en-de",
                        jmdict_path=None,
                        translation_dict_path=freedict_path,
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
            _create_frequency_db(source_db)
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
                        translation_dict_path=freedict_path,
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
            self.assertFalse(payload["inventory_exists"])
            self.assertFalse(payload["ruleset_exists"])
            self.assertFalse(payload["snapshot_exists"])
            self.assertFalse(payload["semantic_inventory_exists"])
            self.assertEqual(payload["store_items_for_pair"], 0)
            self.assertEqual(payload["ruleset_rules_count"], 0)
            self.assertEqual(payload["ruleset_rules_with_semantic_admission"], 0)
            self.assertEqual(payload["snapshot_target_count"], 0)
            self.assertEqual(payload["semantic_inventory_trigger_count"], 0)

    def test_runtime_diagnostics_reports_missing_en_de_frequency_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            payload = get_srs_runtime_diagnostics(paths, pair="en-de")
            self.assertEqual(payload["pair"], "en-de")
            self.assertIn("pair_policy", payload)
            self.assertEqual(payload["pair_policy"]["pair"], "en-de")
            self.assertTrue(payload["set_source_db"].endswith("freq-de-default.sqlite"))
            self.assertFalse(payload["set_source_db_exists"])
            self.assertTrue(payload["frequency_pack_path"].endswith("freq-de-default.sqlite"))
            self.assertFalse(payload["frequency_pack_exists"])
            self.assertEqual(payload["frequency_pack_id"], "freq-de-default")
            self.assertEqual(payload["frequency_pack_provider"], "freq-de-default")
            self.assertEqual(payload["frequency_pos_source_profile"], "freq-de-default")
            self.assertTrue(
                payload["translation_dict_path"].endswith("language_packs/freedict-de-en.sqlite")
            )
            self.assertFalse(payload["translation_dict_exists"])
            self.assertEqual(payload["translation_dict_provider"], "freedict")
            self.assertEqual(payload["translation_pack_id"], "freedict_de_en")
            self.assertEqual(payload["translation_pos_source_profile"], "freedict")
            self.assertTrue(
                payload["translation_pack_path"].endswith("language_packs/freedict-de-en.sqlite")
            )
            self.assertFalse(payload["translation_pack_exists"])
            self.assertTrue(
                payload["reverse_translation_pack_path"].endswith(
                    "language_packs/freedict-en-de.sqlite"
                )
            )
            self.assertEqual(payload["reverse_translation_pack_id"], "freedict_en_de")
            self.assertEqual(payload["reverse_translation_dict_provider"], "freedict")
            self.assertTrue(payload["stopwords_path"].endswith("stopwords/stopwords-de.json"))
            self.assertTrue(payload["stopwords_exists"])
            missing_types = [entry.get("type") for entry in payload.get("missing_inputs", [])]
            self.assertIn("set_source_db", missing_types)
            self.assertIn("translation_dict_path", missing_types)
            self.assertIn("translation_pack_path", missing_types)
            self.assertTrue(payload["requirements"]["requires_translation_dictionary_for_rulegen"])

    def test_runtime_diagnostics_reports_missing_en_es_frequency_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            payload = get_srs_runtime_diagnostics(paths, pair="en-es")
            self.assertEqual(payload["pair"], "en-es")
            self.assertIn("pair_policy", payload)
            self.assertEqual(payload["pair_policy"]["pair"], "en-es")
            self.assertTrue(payload["set_source_db"].endswith("freq-es-cde.sqlite"))
            self.assertFalse(payload["set_source_db_exists"])
            self.assertTrue(payload["frequency_pack_path"].endswith("freq-es-cde.sqlite"))
            self.assertFalse(payload["frequency_pack_exists"])
            self.assertEqual(payload["frequency_pack_id"], "freq-es-cde")
            self.assertEqual(payload["frequency_pack_provider"], "freq-es-cde")
            self.assertEqual(payload["frequency_pos_source_profile"], "freq-es-cde")
            self.assertTrue(
                payload["translation_dict_path"].endswith("language_packs/wiktionary-es-en.sqlite")
            )
            self.assertFalse(payload["translation_dict_exists"])
            self.assertEqual(payload["translation_dict_provider"], "wiktionary")
            self.assertEqual(payload["translation_pack_id"], "wiktionary_es_en")
            self.assertEqual(payload["translation_pos_source_profile"], "wiktionary")
            self.assertTrue(
                payload["translation_pack_path"].endswith("language_packs/wiktionary-es-en.sqlite")
            )
            self.assertFalse(payload["translation_pack_exists"])
            self.assertTrue(
                payload["reverse_translation_pack_path"].endswith(
                    "language_packs/wiktionary-en-es.sqlite"
                )
            )
            self.assertEqual(payload["reverse_translation_pack_id"], "wiktionary_en_es")
            self.assertEqual(payload["reverse_translation_dict_provider"], "wiktionary")
            missing_types = [entry.get("type") for entry in payload.get("missing_inputs", [])]
            self.assertIn("set_source_db", missing_types)
            self.assertIn("translation_dict_path", missing_types)
            self.assertIn("translation_pack_path", missing_types)
            self.assertTrue(payload["requirements"]["requires_translation_dictionary_for_rulegen"])

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
                            word_package={
                                "version": 1,
                                "language_tag": "ja",
                                "surface": "alpha",
                                "reading": "alpha",
                                "script_forms": {"surface": "alpha"},
                                "source": {"provider": "seed"},
                            },
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
            save_srs_inventory(
                SrsInventory(
                    pairs={
                        "en-ja": SrsPairInventory(
                            active_item_ids=("en-ja:alpha", "en-ja:missing"),
                            last_initialized_at="2026-04-09T00:00:00Z",
                            last_refreshed_at="2026-04-10T00:00:00Z",
                        )
                    }
                ),
                paths.srs_inventory_path_for("default"),
            )
            paths.ruleset_path("en-ja").write_text(
                (
                    '{"rules":['
                    '{"source_phrase":"one","replacement":"一","metadata":{"script_forms":{"kanji":"一"},"semantic_admission":{"schema_version":1,"status":"unavailable","reason_code":"missing_jmdict_entry_locator"}}},'
                    '{"source_phrase":"two","replacement":"二","metadata":{"word_package":'
                    '{"version":1,"language_tag":"ja","surface":"二","reading":"に",'
                    '"script_forms":{"kanji":"二","kana":"に","romaji":"ni"},'
                    '"source":{"provider":"jmdict"}},"semantic_admission":{"schema_version":1,"status":"ready","trigger_id":"en-ja:trigger:two","sense_id":"en-ja:jmdict:二:1","competition_set_id":"en-ja:two:二:v1"}}}]}'
                ),
                encoding="utf-8",
            )
            paths.snapshot_path("en-ja").write_text(
                '{"stats":{"target_count":2,"rule_count":2},"targets":[{"lemma":"一"},{"lemma":"二"}],"generation_id":"en-ja:default:test-generation"}',
                encoding="utf-8",
            )
            paths.semantic_inventory_path("en-ja").write_text(
                (
                    '{"schema_version":1,"pair":"en-ja","profile_id":"default","generated_at":"2026-04-10T00:00:00Z","generation_id":"en-ja:default:test-generation",'
                    '"capability":{"pointer_modes":["jmdict_entry"],"default_unavailable_reason_code":"missing_jmdict_entry_locator","competition_mode":"not_published","competition_reason_code":"missing_shadow_selection","phrase_mode":"not_published","phrase_reason_code":"missing_phrase_inventory"},'
                    '"triggers":{"en-ja:trigger:two":{"trigger_id":"en-ja:trigger:two","source_phrase":"two","normalized_source_phrase":"two","token_count":1}},'
                    '"senses":{"en-ja:jmdict:二:1":{"sense_id":"en-ja:jmdict:二:1","trigger_id":"en-ja:trigger:two","status":"ready","target_lemma":"二","provider":"jmdict","locator":{"provider":"jmdict","locator_kind":"jmdict_entry","kana_forms":["に"]}}},'
                    '"competition_sets":{"en-ja:two:二:v1":{"competition_set_id":"en-ja:two:二:v1","trigger_id":"en-ja:trigger:two","status":"ready","active_sense_id":"en-ja:jmdict:二:1","shadow_sense_ids":["en-ja:jmdict:2:shadow"],"selection_mode":"manual","selection_policy_version":"v1"}},'
                    '"phrase_sets":{}}'
                ),
                encoding="utf-8",
            )
            _write_publication_manifest_fixture(
                paths,
                pair="en-ja",
                generation_id="en-ja:default:test-generation",
                generated_at="2026-04-10T00:00:00Z",
            )
            payload = get_srs_runtime_diagnostics(paths, pair="en-ja")
            self.assertTrue(payload["store_exists"])
            self.assertTrue(payload["ruleset_exists"])
            self.assertTrue(payload["snapshot_exists"])
            self.assertEqual(payload["store_items_total"], 2)
            self.assertEqual(payload["store_items_for_pair"], 1)
            self.assertEqual(payload["store_items_with_word_package_total"], 1)
            self.assertEqual(payload["store_items_with_word_package_for_pair"], 1)
            self.assertTrue(payload["inventory_exists"])
            self.assertEqual(payload["inventory_active_items_for_pair"], 1)
            self.assertEqual(payload["inventory_source"], "inventory")
            self.assertEqual(payload["inventory_last_initialized_at"], "2026-04-09T00:00:00Z")
            self.assertEqual(payload["inventory_last_refreshed_at"], "2026-04-10T00:00:00Z")
            self.assertEqual(payload["inventory_store_missing_item_ids_count"], 1)
            self.assertEqual(payload["ruleset_rules_count"], 2)
            self.assertEqual(payload["ruleset_rules_with_script_forms"], 1)
            self.assertEqual(payload["ruleset_rules_with_word_package"], 1)
            self.assertEqual(payload["ruleset_rules_with_semantic_admission"], 2)
            self.assertEqual(payload["ruleset_rules_semantic_ready"], 1)
            self.assertEqual(payload["ruleset_rules_semantic_unavailable"], 1)
            self.assertEqual(payload["ruleset_rules_semantic_not_applicable"], 0)
            self.assertEqual(payload["snapshot_target_count"], 2)
            self.assertEqual(payload["snapshot_generation_id"], "en-ja:default:test-generation")
            self.assertTrue(payload["semantic_inventory_exists"])
            self.assertEqual(payload["semantic_inventory_schema_version"], 1)
            self.assertEqual(
                payload["semantic_inventory_generation_id"], "en-ja:default:test-generation"
            )
            self.assertEqual(payload["semantic_inventory_pointer_modes"], ["jmdict_entry"])
            self.assertEqual(
                payload["semantic_inventory_default_unavailable_reason_code"],
                "missing_jmdict_entry_locator",
            )
            self.assertEqual(payload["semantic_inventory_trigger_count"], 1)
            self.assertEqual(payload["semantic_inventory_sense_count"], 1)
            self.assertEqual(payload["semantic_inventory_competition_set_count"], 1)
            self.assertEqual(payload["semantic_inventory_phrase_set_count"], 0)
            self.assertTrue(payload["publication_manifest_exists"])
            self.assertEqual(
                payload["publication_manifest_generation_id"], "en-ja:default:test-generation"
            )
            self.assertTrue(payload["publication_manifest_family_valid"])
            self.assertEqual(payload["publication_manifest_error_count"], 0)

    def test_runtime_diagnostics_recomputes_publication_family_validity_for_generation_drift(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            paths.ruleset_path("en-ja").write_text(
                '{"rules":[{"source_phrase":"one","replacement":"一","metadata":{}}]}',
                encoding="utf-8",
            )
            paths.snapshot_path("en-ja").write_text(
                '{"stats":{"target_count":1,"rule_count":1},"targets":[{"lemma":"一"}],"generation_id":"en-ja:default:gen-a"}',
                encoding="utf-8",
            )
            paths.semantic_inventory_path("en-ja").write_text(
                (
                    '{"schema_version":1,"pair":"en-ja","profile_id":"default","generated_at":"2026-04-11T00:00:00Z",'
                    '"generation_id":"en-ja:default:gen-b",'
                    '"capability":{"pointer_modes":["jmdict_entry"],"default_unavailable_reason_code":"missing_jmdict_entry_locator"},'
                    '"triggers":{},"senses":{},"competition_sets":{},"phrase_sets":{}}'
                ),
                encoding="utf-8",
            )
            _write_publication_manifest_fixture(
                paths,
                pair="en-ja",
                generation_id="en-ja:default:gen-a",
                generated_at="2026-04-11T00:00:00Z",
            )

            payload = get_srs_runtime_diagnostics(paths, pair="en-ja")

            self.assertTrue(payload["publication_manifest_exists"])
            self.assertFalse(payload["publication_manifest_family_valid"])
            self.assertGreaterEqual(payload["publication_manifest_error_count"], 1)
            self.assertIn(
                "semantic_inventory.generation_id 'en-ja:default:gen-b' does not match publication_manifest generation 'en-ja:default:gen-a'",
                payload["publication_manifest_errors"],
            )

    def test_runtime_diagnostics_reports_store_fallback_inventory_with_publication_state(
        self,
    ) -> None:
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
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )
            paths.ruleset_path("en-ja").write_text(
                '{"rules":[{"source_phrase":"one","replacement":"一","metadata":{}}]}',
                encoding="utf-8",
            )
            paths.snapshot_path("en-ja").write_text(
                '{"stats":{"target_count":1,"rule_count":1},"targets":[{"lemma":"一"}],"generation_id":"en-ja:default:fallback-generation"}',
                encoding="utf-8",
            )
            paths.semantic_inventory_path("en-ja").write_text(
                (
                    '{"schema_version":1,"pair":"en-ja","profile_id":"default","generated_at":"2026-04-11T00:00:00Z",'
                    '"generation_id":"en-ja:default:fallback-generation",'
                    '"capability":{"pointer_modes":["jmdict_entry"],"default_unavailable_reason_code":"missing_jmdict_entry_locator"},'
                    '"triggers":{},"senses":{},"competition_sets":{},"phrase_sets":{}}'
                ),
                encoding="utf-8",
            )
            _write_publication_manifest_fixture(
                paths,
                pair="en-ja",
                generation_id="en-ja:default:fallback-generation",
                generated_at="2026-04-11T00:00:00Z",
            )

            payload = get_srs_runtime_diagnostics(paths, pair="en-ja")

            self.assertFalse(payload["inventory_exists"])
            self.assertEqual(payload["inventory_active_items_for_pair"], 1)
            self.assertEqual(payload["inventory_source"], "store_fallback")
            self.assertEqual(payload["inventory_store_missing_item_ids_count"], 0)
            self.assertIsNone(payload["inventory_last_initialized_at"])
            self.assertTrue(payload["semantic_inventory_exists"])
            self.assertEqual(
                payload["semantic_inventory_generation_id"],
                "en-ja:default:fallback-generation",
            )
            self.assertTrue(payload["publication_manifest_exists"])
            self.assertEqual(
                payload["publication_manifest_generation_id"],
                "en-ja:default:fallback-generation",
            )
            self.assertTrue(payload["publication_manifest_family_valid"])
            self.assertEqual(payload["publication_manifest_error_count"], 0)


class TestHelperEngineInitializeSrsSet(unittest.TestCase):
    def test_initialize_set_adds_items_for_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            _create_frequency_db(source_db)

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
            inventory = load_srs_inventory(paths.srs_inventory_path_for("default"))
            self.assertEqual(len(persisted.items), 3)
            self.assertEqual(
                tuple(inventory.pairs["en-ja"].active_item_ids),
                ("en-ja:alpha",),
            )
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
            _create_frequency_db(source_db)

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
            inventory = load_srs_inventory(paths.srs_inventory_path_for("default"))
            self.assertEqual(
                len([item for item in persisted.items if item.language_pair == "en-ja"]), 1
            )
            self.assertEqual(
                tuple(inventory.pairs["en-ja"].active_item_ids),
                ("en-ja:gamma",),
            )
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
            _create_frequency_db(source_db)

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

            with (
                patch(
                    "lexishift_core.helper.engine.initialize_store_from_frequency_list_with_report",
                    return_value=(persisted_after_init, init_report),
                ) as init_patch,
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    return_value=(persisted_after_init, rulegen_output),
                ) as run_rulegen_patch,
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
            rulegen_config = run_rulegen_patch.call_args.kwargs["rulegen_config"]
            rulegen_defaults = resolve_pair_rulegen_tuning("en-ja")
            self.assertEqual(
                rulegen_config.max_definitions_per_target,
                rulegen_defaults.max_definitions_per_target,
            )
            self.assertEqual(
                rulegen_config.max_rules_per_target,
                rulegen_defaults.max_rules_per_target,
            )
            self.assertEqual(
                rulegen_config.include_variants,
                rulegen_defaults.include_variants,
            )
            self.assertEqual(
                rulegen_config.reverse_check.enabled,
                rulegen_defaults.reverse_check.enabled,
            )
            self.assertEqual(result["set_top_n"], 800)
            self.assertEqual(result["initial_active_count"], 40)
            self.assertEqual(result["pair_policy"]["pair"], "en-ja")

    def test_initialize_set_runs_rulegen_against_active_inventory_and_forwards_semantic_inventory(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            _create_frequency_db(source_db)

            updated_store = SrsStore(
                items=(
                    SrsItem(
                        item_id="en-ja:alpha",
                        lemma="alpha",
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
            )
            semantic_inventory = {
                "schema_version": 1,
                "pair": "en-ja",
                "profile_id": "default",
                "generated_at": "2026-04-10T00:00:00Z",
                "triggers": {},
                "senses": {},
                "competition_sets": {},
                "phrase_sets": {},
            }
            rulegen_output = SimpleNamespace(
                rules=tuple(),
                snapshot={"stats": {"target_count": 2, "rule_count": 0}},
                target_count=2,
                semantic_inventory=semantic_inventory,
            )

            with (
                patch(
                    "lexishift_core.helper.engine.initialize_store_from_frequency_list_with_report",
                    return_value=(
                        updated_store,
                        SimpleNamespace(
                            selected_count=2,
                            selected_unique_count=2,
                            admitted_count=2,
                            inserted_count=2,
                            updated_count=0,
                            selected_preview=("alpha", "gamma"),
                            initial_active_preview=("alpha", "gamma"),
                        ),
                    ),
                ),
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    return_value=(updated_store, rulegen_output),
                ) as run_rulegen_patch,
                patch("lexishift_core.helper.engine.write_rulegen_outputs") as write_outputs_patch,
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

            self.assertEqual(
                tuple(run_rulegen_patch.call_args.kwargs["active_item_ids"]),
                ("en-ja:alpha", "en-ja:gamma"),
            )
            self.assertEqual(
                write_outputs_patch.call_args.kwargs["semantic_inventory"],
                semantic_inventory,
            )
            inventory = load_srs_inventory(paths.srs_inventory_path_for("default"))
            self.assertEqual(
                tuple(inventory.pairs["en-ja"].active_item_ids),
                ("en-ja:alpha", "en-ja:gamma"),
            )
            self.assertEqual(result["inventory"]["source"], "initialized")
            self.assertEqual(result["inventory"]["active_items_for_pair"], 2)
            self.assertTrue(result["rulegen"]["published"])
            self.assertTrue(result["rulegen"]["semantic_inventory_path"].endswith("en-ja.json"))


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
            _create_frequency_db(source_db)

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
            inventory = load_srs_inventory(paths.srs_inventory_path_for("default"))
            by_pair = [item for item in persisted.items if item.language_pair == "en-ja"]
            self.assertEqual(len(by_pair), 4)
            self.assertEqual(
                tuple(inventory.pairs["en-ja"].active_item_ids),
                ("en-ja:alpha", "en-ja:beta", "en-ja:gamma", "en-ja:delta"),
            )
            self.assertTrue(result["applied"])
            self.assertEqual(result["added_items"], 3)
            self.assertEqual(result["admission_refresh"]["reason_code"], "normal")
            self.assertIn("admission_weight", result["admission_refresh"]["weight_terms"])
            self.assertIn("serving_priority", result["admission_refresh"]["weight_terms"])

    def test_refresh_respects_allowed_pos_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            _create_frequency_db(source_db)

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
                    pos="動詞-一般",
                    pos_bucket="verb",
                    pos_weight=0.7,
                    pmw=90.0,
                    base_weight=0.8,
                    admission_weight=0.56,
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
                        allowed_pos=["noun"],
                        persist_store=True,
                    ),
                )

            persisted = load_srs_store(paths.srs_store_path)
            inventory = load_srs_inventory(paths.srs_inventory_path_for("default"))
            lemmas = {item.lemma for item in persisted.items if item.language_pair == "en-ja"}
            self.assertEqual(lemmas, {"alpha", "beta"})
            self.assertEqual(
                tuple(inventory.pairs["en-ja"].active_item_ids),
                ("en-ja:alpha", "en-ja:beta"),
            )
            self.assertTrue(result["applied"])
            self.assertEqual(result["added_items"], 1)
            self.assertEqual(result["allowed_pos"], ["noun"])
            diagnostics = result["admission_refresh"]["diagnostics"]
            self.assertEqual(diagnostics["filtered_by_pos"], 1)
            self.assertEqual(diagnostics["admitted_by_pos_bucket"].get("noun"), 1)

    def test_refresh_pauses_admission_for_low_retention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            _create_frequency_db(source_db)

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
            _create_frequency_db(source_db)
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
            _create_frequency_db(source_db)

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
            feedback_events = [
                event
                for event in events
                if event.event_type == "feedback" and event.pair == "en-ja"
            ]
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
            inventory = load_srs_inventory(paths.srs_inventory_path_for("default"))
            by_pair = [item for item in stored_after.items if item.language_pair == "en-ja"]
            self.assertEqual(len(by_pair), 1)
            self.assertEqual(
                tuple(inventory.pairs["en-ja"].active_item_ids),
                ("en-ja:alpha",),
            )
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
            _create_frequency_db(source_db)

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
                semantic_inventory = {
                    "schema_version": 1,
                    "pair": pair,
                    "profile_id": "default",
                    "generated_at": "2026-04-10T00:00:00Z",
                    "triggers": {},
                    "senses": {},
                    "competition_sets": {},
                    "phrase_sets": {},
                }
                return store, SimpleNamespace(
                    rules=rules,
                    snapshot=snapshot,
                    target_count=2,
                    semantic_inventory=semantic_inventory,
                )

            with (
                patch(
                    "lexishift_core.helper.engine.build_seed_candidates",
                    return_value=selected,
                ),
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    side_effect=_stub_run_rulegen_for_pair,
                ) as run_rulegen_patch,
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
            inventory = load_srs_inventory(paths.srs_inventory_path_for("default"))
            by_pair = [item for item in persisted.items if item.language_pair == "en-ja"]
            self.assertEqual(len(by_pair), 3)
            self.assertEqual(
                tuple(inventory.pairs["en-ja"].active_item_ids),
                ("en-ja:alpha", "en-ja:beta", "en-ja:gamma"),
            )
            self.assertTrue(result["applied"])
            self.assertEqual(result["added_items"], 2)
            self.assertEqual(result["admission_refresh"]["reason_code"], "normal")
            self.assertEqual(result["admission_refresh"]["feedback_window"]["feedback_count"], 8)
            rulegen_config = run_rulegen_patch.call_args.kwargs["rulegen_config"]
            rulegen_defaults = resolve_pair_rulegen_tuning("en-ja")
            self.assertEqual(
                rulegen_config.max_definitions_per_target,
                rulegen_defaults.max_definitions_per_target,
            )
            self.assertEqual(
                rulegen_config.max_rules_per_target,
                rulegen_defaults.max_rules_per_target,
            )
            self.assertEqual(
                rulegen_config.include_variants,
                rulegen_defaults.include_variants,
            )
            self.assertEqual(
                rulegen_config.reverse_check.enabled,
                rulegen_defaults.reverse_check.enabled,
            )
            self.assertEqual(
                tuple(run_rulegen_patch.call_args.kwargs["active_item_ids"]),
                ("en-ja:alpha", "en-ja:beta", "en-ja:gamma"),
            )

            rulegen_payload = result.get("rulegen")
            self.assertIsNotNone(rulegen_payload)
            self.assertTrue(rulegen_payload.get("published"))
            self.assertEqual(rulegen_payload.get("targets"), 2)
            self.assertEqual(rulegen_payload.get("rules"), 2)
            snapshot_path = Path(rulegen_payload.get("snapshot_path"))
            ruleset_path = Path(rulegen_payload.get("ruleset_path"))
            semantic_inventory_path = Path(rulegen_payload.get("semantic_inventory_path"))
            publication_manifest_path = Path(rulegen_payload.get("publication_manifest_path"))
            self.assertTrue(snapshot_path.exists())
            self.assertTrue(ruleset_path.exists())
            self.assertTrue(semantic_inventory_path.exists())
            self.assertTrue(publication_manifest_path.exists())
            snapshot_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            semantic_inventory_payload = json.loads(
                semantic_inventory_path.read_text(encoding="utf-8")
            )
            manifest_payload = json.loads(publication_manifest_path.read_text(encoding="utf-8"))
            generation_id = manifest_payload["generation_id"]
            self.assertEqual(snapshot_payload["generation_id"], generation_id)
            self.assertEqual(semantic_inventory_payload["generation_id"], generation_id)
            self.assertTrue(manifest_payload["validation"]["family_valid"])
            self.assertTrue(manifest_payload["artifacts"]["semantic_inventory"]["exists"])


class TestHelperEnginePreviewSrsAdmission(unittest.TestCase):
    def test_preview_returns_profile_bootstrap_payload_without_mutating_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            _create_frequency_db(source_db)

            preview_report = SimpleNamespace(
                selected_count=3,
                selected_unique_count=3,
                admitted_count=2,
                inserted_count=2,
                updated_count=0,
                selected_preview=("alpha", "beta", "gamma"),
                initial_active_preview=("beta", "alpha"),
                admission_weight_profile={"noun": 1.0},
                initial_active_weight_preview=(
                    {"lemma": "beta", "admission_weight": 0.82, "pos_bucket": "noun"},
                    {"lemma": "alpha", "admission_weight": 0.75, "pos_bucket": "noun"},
                ),
                selection_strategy="profile_bootstrap",
                selection_policy="top_n",
                selector_version="profile_bootstrap_v3",
                profile_bootstrap_diagnostics={
                    "profile_context": {
                        "active_signals": ["proficiency", "challenge_preference"],
                    },
                    "ranking_preview": [
                        {
                            "lemma": "beta",
                            "reranked_rank": 1,
                            "base_rank": 2,
                            "rank_delta": 1,
                            "profile_score": 0.82,
                            "explanation": "Boosted by challenge_fit.",
                        },
                        {
                            "lemma": "alpha",
                            "reranked_rank": 2,
                            "base_rank": 1,
                            "rank_delta": -1,
                            "profile_score": 0.75,
                            "explanation": (
                                "Demoted relative to the neutral frequency order because "
                                "competing items matched the profile better."
                            ),
                        },
                    ],
                },
            )

            with patch(
                "lexishift_core.helper.engine.initialize_store_from_frequency_list_with_report",
                return_value=(SrsStore(items=tuple(), version=1), preview_report),
            ):
                payload = preview_srs_admission(
                    paths,
                    config=SetAdmissionPreviewJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        strategy="profile_bootstrap",
                        preview_count=2,
                        profile_context={
                            "proficiency": {"self_reported_level": 0.35},
                            "difficulty_preferences": {"target_challenge_center": 0.58},
                        },
                    ),
                )

            self.assertEqual(payload["pair"], "en-ja")
            self.assertEqual(payload["plan"]["strategy_effective"], "frequency_bootstrap")
            preview = payload["preview"]
            self.assertEqual(preview["selection_strategy"], "profile_bootstrap")
            self.assertEqual(preview["selector_version"], "profile_bootstrap_v3")
            self.assertEqual(preview["sample_count_requested"], 2)
            self.assertEqual(preview["sample_count_effective"], 2)
            self.assertEqual(preview["initial_active_preview"], ["beta", "alpha"])
            self.assertEqual(preview["admitted_words"][0]["lemma"], "beta")
            self.assertNotIn("ranking_preview", preview["profile_bootstrap"])
            self.assertEqual(
                preview["admitted_words"][0]["explanation"],
                "Boosted by challenge_fit.",
            )
            self.assertEqual(
                preview["profile_bootstrap"]["profile_context"]["active_signals"],
                ["proficiency", "challenge_preference"],
            )

    def test_preview_can_return_weighted_sample_from_planned_active_pool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            _create_frequency_db(source_db)

            preview_report = SimpleNamespace(
                selected_count=3,
                selected_unique_count=3,
                admitted_count=3,
                inserted_count=3,
                updated_count=0,
                selected_preview=("alpha", "beta", "gamma"),
                initial_active_preview=("alpha", "gamma", "beta"),
                admission_weight_profile={"noun": 1.0},
                initial_active_weight_preview=(
                    {"lemma": "alpha", "admission_weight": 0.8, "pos_bucket": "noun"},
                    {"lemma": "beta", "admission_weight": 0.6, "pos_bucket": "noun"},
                    {"lemma": "gamma", "admission_weight": 0.2, "pos_bucket": "noun"},
                ),
                selection_strategy="profile_bootstrap",
                selection_policy="weighted_without_replacement",
                selector_version="profile_bootstrap_v3",
                profile_bootstrap_diagnostics={
                    "profile_context": {"active_signals": ["interests"]},
                    "ranking_preview": [
                        {
                            "lemma": "alpha",
                            "reranked_rank": 1,
                            "base_rank": 1,
                            "rank_delta": 0,
                            "profile_score": 0.9,
                            "explanation": (
                                "Kept near frequency order; strongest profile signal was "
                                "topic_affinity."
                            ),
                        },
                        {
                            "lemma": "beta",
                            "reranked_rank": 2,
                            "base_rank": 2,
                            "rank_delta": 0,
                            "profile_score": 0.5,
                            "explanation": (
                                "Kept near frequency order; strongest profile signal was "
                                "topic_affinity."
                            ),
                        },
                        {
                            "lemma": "gamma",
                            "reranked_rank": 3,
                            "base_rank": 3,
                            "rank_delta": 0,
                            "profile_score": 0.1,
                            "explanation": (
                                "Kept near frequency order; strongest profile signal was "
                                "topic_affinity."
                            ),
                        },
                    ],
                },
            )

            with patch(
                "lexishift_core.helper.engine.initialize_store_from_frequency_list_with_report",
                return_value=(SrsStore(items=tuple(), version=1), preview_report),
            ):
                payload = preview_srs_admission(
                    paths,
                    config=SetAdmissionPreviewJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        strategy="profile_bootstrap",
                        preview_count=2,
                        preview_sampling_mode="weighted_without_replacement",
                        preview_seed=1,
                        profile_context={"interests": ["animals"]},
                    ),
                )

            preview = payload["preview"]
            self.assertEqual(preview["sampling_mode"], "weighted_without_replacement")
            self.assertEqual(preview["sampling_pool_count"], 3)
            self.assertEqual(preview["sample_count_effective"], 2)
            self.assertEqual(
                [entry["lemma"] for entry in preview["admitted_words"]],
                ["alpha", "gamma"],
            )

    def test_preview_returns_plan_only_for_non_executable_strategy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            source_db = root / "freq.sqlite"
            _create_frequency_db(source_db)

            payload = preview_srs_admission(
                paths,
                config=SetAdmissionPreviewJobConfig(
                    pair="en-de",
                    set_source_db=source_db,
                    strategy="profile_growth",
                    preview_count=3,
                    profile_context={"interests": ["animals"]},
                ),
            )

            self.assertEqual(payload["pair"], "en-de")
            self.assertFalse(payload["plan"]["can_execute"])
            self.assertEqual(payload["plan"]["execution_mode"], "planner_only")
            self.assertEqual(payload["preview"]["sample_count_requested"], 3)
            self.assertEqual(payload["preview"]["sample_count_effective"], 0)
            self.assertEqual(payload["preview"]["admitted_words"], [])

    def test_preview_executes_real_profile_bootstrap_with_seed_topic_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            source_db = root / "freq.sqlite"
            _create_frequency_db(
                source_db,
                rows=(
                    ("alpha", 1.0, 100.0, "n", None, None, None, None, None, None, None),
                    ("beta", 2.0, 98.0, "n", None, None, None, None, "animals", None, None),
                    ("gamma", 3.0, 50.0, "n", None, None, None, None, None, None, None),
                ),
            )

            payload = preview_srs_admission(
                paths,
                config=SetAdmissionPreviewJobConfig(
                    pair="en-en",
                    set_source_db=source_db,
                    strategy="profile_bootstrap",
                    preview_count=2,
                    initial_active_count=2,
                    profile_context={"interests": ["animals"]},
                ),
            )

            self.assertEqual(payload["pair"], "en-en")
            self.assertTrue(payload["plan"]["can_execute"])
            self.assertEqual(payload["plan"]["strategy_effective"], "frequency_bootstrap")
            preview = payload["preview"]
            self.assertEqual(preview["selection_strategy"], "profile_bootstrap")
            self.assertEqual(preview["sample_count_effective"], 2)
            self.assertEqual(preview["admitted_words"][0]["lemma"], "beta")
            self.assertEqual(preview["admitted_words"][0]["rank_delta"], 1)
            self.assertEqual(
                preview["admitted_words"][0]["signals"]["topic_affinity_source"],
                "topic_hint:animals",
            )
            self.assertEqual(
                preview["admitted_words"][0]["explanation"],
                "Boosted by topic_affinity, while remaining supported by coverage_gain.",
            )
            self.assertEqual(
                preview["profile_bootstrap"]["profile_context"]["active_signals"],
                ["interests"],
            )
            self.assertEqual(
                preview["profile_bootstrap"]["profile_context"]["explicit_topic_weights"],
                {"animals": 1.0},
            )
            self.assertEqual(
                preview["profile_bootstrap"]["active_topic_support"]["topics"][0]["topic"],
                "animals",
            )
            self.assertEqual(
                preview["profile_bootstrap"]["active_topic_support"]["topics"][0][
                    "candidate_count"
                ],
                1,
            )
            self.assertFalse(
                preview["profile_bootstrap"]["active_topic_support"]["topics"][0][
                    "eligible_for_scarcity_calibration"
                ]
            )

    def test_preview_omits_large_ranking_preview_from_helper_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            _create_frequency_db(source_db)

            ranking_preview = [
                {
                    "lemma": f"lemma_{index}",
                    "reranked_rank": index + 1,
                    "base_rank": index + 1,
                    "rank_delta": 0,
                    "profile_score": 0.5,
                    "explanation": (
                        "Verbose bootstrap explanation kept intentionally large to exercise "
                        "native messaging reply trimming."
                    ),
                }
                for index in range(800)
            ]
            preview_report = SimpleNamespace(
                selected_count=800,
                selected_unique_count=800,
                admitted_count=5,
                inserted_count=5,
                updated_count=0,
                selected_preview=tuple(entry["lemma"] for entry in ranking_preview[:10]),
                initial_active_preview=tuple(entry["lemma"] for entry in ranking_preview[:5]),
                admission_weight_profile={"noun": 1.0},
                initial_active_weight_preview=tuple(
                    {
                        "lemma": entry["lemma"],
                        "admission_weight": 0.5,
                        "pos_bucket": "noun",
                    }
                    for entry in ranking_preview[:5]
                ),
                selection_strategy="profile_bootstrap",
                selection_policy="top_n",
                selector_version="profile_bootstrap_v3",
                profile_bootstrap_diagnostics={
                    "profile_context": {"active_signals": ["interests"]},
                    "ranking_preview": ranking_preview,
                },
            )

            with patch(
                "lexishift_core.helper.engine.initialize_store_from_frequency_list_with_report",
                return_value=(SrsStore(items=tuple(), version=1), preview_report),
            ):
                payload = preview_srs_admission(
                    paths,
                    config=SetAdmissionPreviewJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        strategy="profile_bootstrap",
                        preview_count=5,
                        profile_context={"interests": ["animals"]},
                    ),
                )

            preview = payload["preview"]
            self.assertNotIn("ranking_preview", preview["profile_bootstrap"])
            self.assertLess(len(json.dumps(payload).encode("utf-8")), 50_000)


class TestHelperEngineRebalanceSrsSet(unittest.TestCase):
    def _stub_rulegen_output(self) -> SimpleNamespace:
        return SimpleNamespace(
            rules=(),
            snapshot={
                "version": 1,
                "pair": "en-ja",
                "targets": [],
                "stats": {"target_count": 0, "rule_count": 0, "source_count": 0},
            },
            target_count=0,
            semantic_inventory={
                "schema_version": 1,
                "pair": "en-ja",
                "profile_id": "default",
                "generated_at": "2026-04-10T00:00:00Z",
                "triggers": {},
                "senses": {},
                "competition_sets": {},
                "phrase_sets": {},
            },
        )

    def _rebalance_candidates(self) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(
                lemma="beta",
                language_pair="en-ja",
                pos_bucket="noun",
                base_weight=0.55,
                admission_weight=0.55,
                metadata={},
            ),
            SimpleNamespace(
                lemma="gamma",
                language_pair="en-ja",
                pos_bucket="noun",
                base_weight=0.52,
                admission_weight=0.52,
                metadata={},
            ),
            SimpleNamespace(
                lemma="delta",
                language_pair="en-ja",
                pos_bucket="noun",
                base_weight=0.5,
                admission_weight=0.5,
                metadata={"topics": ["animals"]},
            ),
            SimpleNamespace(
                lemma="epsilon",
                language_pair="en-ja",
                pos_bucket="noun",
                base_weight=0.49,
                admission_weight=0.49,
                metadata={"topics": ["animals"]},
            ),
        ]

    def test_rebalance_plan_and_apply_are_inventory_aware(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            _create_frequency_db(source_db)

            save_srs_settings(SrsSettings(max_active_items=10), paths.srs_settings_path)
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:alpha",
                            lemma="alpha",
                            language_pair="en-ja",
                            source_type="initial_set",
                            history=(
                                SrsHistoryEntry(ts="2026-04-01T00:00:00Z", rating="good"),
                                SrsHistoryEntry(ts="2026-04-02T00:00:00Z", rating="good"),
                                SrsHistoryEntry(ts="2026-04-03T00:00:00Z", rating="good"),
                                SrsHistoryEntry(ts="2026-04-04T00:00:00Z", rating="good"),
                            ),
                        ),
                        SrsItem(
                            item_id="en-ja:beta",
                            lemma="beta",
                            language_pair="en-ja",
                            source_type="initial_set",
                            confidence=0.55,
                            history=(SrsHistoryEntry(ts="2026-04-05T00:00:00Z", rating="good"),),
                        ),
                        SrsItem(
                            item_id="en-ja:gamma",
                            lemma="gamma",
                            language_pair="en-ja",
                            source_type="initial_set",
                            confidence=0.52,
                        ),
                        SrsItem(
                            item_id="en-ja:delta",
                            lemma="delta",
                            language_pair="en-ja",
                            source_type="frequency_list",
                            confidence=0.5,
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )
            save_srs_inventory(
                SrsInventory(
                    pairs={
                        "en-ja": SrsPairInventory(
                            active_item_ids=("en-ja:alpha", "en-ja:beta", "en-ja:gamma")
                        )
                    }
                ),
                paths.srs_inventory_path_for("default"),
            )

            with patch(
                "lexishift_core.helper.engine.build_seed_candidates",
                return_value=self._rebalance_candidates(),
            ):
                preview = plan_srs_rebalance(
                    paths,
                    config=SrsRebalanceJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        max_active_items=10,
                        profile_context={"interests": ["animals"]},
                    ),
                )

            self.assertTrue(preview["plan"]["can_execute"])
            self.assertNotIn("_rebalance_plan", preview)
            self.assertEqual(preview["summary"]["protected_count"], 1)
            self.assertEqual(preview["summary"]["proposed_park_count"], 2)
            self.assertEqual(preview["summary"]["proposed_activate_count"], 2)
            self.assertEqual(
                [entry["lemma"] for entry in preview["proposed_activations"]],
                ["delta", "epsilon"],
            )

            with (
                patch(
                    "lexishift_core.helper.engine.build_seed_candidates",
                    return_value=self._rebalance_candidates(),
                ),
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    return_value=(
                        load_srs_store(paths.srs_store_path),
                        self._stub_rulegen_output(),
                    ),
                ) as run_rulegen_patch,
            ):
                result = apply_srs_rebalance(
                    paths,
                    config=SrsRebalanceJobConfig(
                        pair="en-ja",
                        jmdict_path=jmdict_dir,
                        translation_dict_path=jmdict_dir,
                        set_source_db=source_db,
                        max_active_items=10,
                        profile_context={"interests": ["animals"]},
                    ),
                )

            self.assertTrue(result["applied"])
            self.assertEqual(result["inserted_items"], 1)
            persisted = load_srs_store(paths.srs_store_path)
            inventory = load_srs_inventory(paths.srs_inventory_path_for("default"))
            by_pair = {
                item.lemma: item for item in persisted.items if item.language_pair == "en-ja"
            }
            self.assertEqual(set(by_pair.keys()), {"alpha", "beta", "gamma", "delta", "epsilon"})
            self.assertEqual(len(by_pair["beta"].history), 1)
            self.assertEqual(
                tuple(inventory.pairs["en-ja"].active_item_ids),
                ("en-ja:alpha", "en-ja:delta", "en-ja:epsilon"),
            )
            self.assertIsNotNone(inventory.pairs["en-ja"].last_rebalanced_at)
            self.assertEqual(
                tuple(run_rulegen_patch.call_args.kwargs["active_item_ids"]),
                ("en-ja:alpha", "en-ja:delta", "en-ja:epsilon"),
            )
            rulegen_payload = result.get("rulegen")
            self.assertIsNotNone(rulegen_payload)
            self.assertTrue(rulegen_payload.get("published"))
            self.assertTrue(Path(rulegen_payload.get("snapshot_path")).exists())
            self.assertTrue(Path(rulegen_payload.get("ruleset_path")).exists())
            self.assertTrue(Path(rulegen_payload.get("publication_manifest_path")).exists())
            self.assertTrue(Path(rulegen_payload.get("semantic_inventory_path")).exists())


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
            exposure_events = [
                event
                for event in events
                if event.event_type == "exposure" and event.pair == "en-ja"
            ]
            feedback_events = [
                event
                for event in events
                if event.event_type == "feedback" and event.pair == "en-ja"
            ]
            self.assertEqual(len(exposure_events), 2)
            self.assertEqual(len(feedback_events), 0)
            self.assertTrue(all(event.rating is None for event in exposure_events))


if __name__ == "__main__":
    unittest.main()
