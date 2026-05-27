from __future__ import annotations

from dataclasses import dataclass
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Mapping, Optional, Sequence

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.engine import apply_feedback  # noqa: E402
from lexishift_core.helper.paths import HelperPaths, build_helper_paths  # noqa: E402
from lexishift_core.helper.rulegen_outputs import RulegenOutput, write_rulegen_outputs  # noqa: E402
from lexishift_core.helper.use_cases.auto_refresh_set import (  # noqa: E402
    maybe_auto_refresh_srs_set,
)
from lexishift_core.helper.use_cases.refresh_set import refresh_srs_set  # noqa: E402
from lexishift_core.helper.use_cases.set_planning import count_items_for_pair  # noqa: E402
from lexishift_core.replacement.core import VocabRule  # noqa: E402
from lexishift_core.srs import (  # noqa: E402
    SrsSettings,
    SrsStore,
    load_srs_inventory,
    load_srs_store,
)
from lexishift_core.srs.auto_refresh import load_auto_refresh_state  # noqa: E402
from lexishift_core.srs.seed import SeedWord  # noqa: E402
from lexishift_core.srs.signal_queue import SrsSignalEvent, save_signal_events  # noqa: E402


@dataclass(frozen=True)
class _Config:
    pair: str = "en-ja"
    jmdict_path: Optional[Path] = None
    translation_dict_path: Optional[Path] = None
    set_source_db: Optional[Path] = None
    profile_id: str = "default"
    strategy: str = "profile_growth"
    set_top_n: Optional[int] = None
    feedback_window_size: Optional[int] = None
    max_active_items: Optional[int] = None
    max_new_items: Optional[int] = None
    allowed_pos: Optional[Sequence[str]] = None
    persist_store: bool = True
    profile_context: Optional[Mapping[str, object]] = None
    auto_refresh_enabled: bool = True
    auto_refresh_min_feedback_events: Optional[int] = None
    auto_refresh_min_good_easy: Optional[int] = None
    auto_refresh_repeat_min_good_easy: Optional[int] = None
    auto_refresh_cooldown_minutes: Optional[int] = None
    trigger: str = "manual"


def _resolve_profile_id(
    paths: HelperPaths,
    *,
    profile_id: str | None,
    profile_context: Optional[Mapping[str, object]] = None,
) -> str:
    del profile_context
    return paths.normalize_profile_id(profile_id)


def _event(index: int, rating: str) -> SrsSignalEvent:
    return SrsSignalEvent(
        event_type="feedback",
        pair="en-ja",
        lemma=f"lemma{index}",
        source_type="extension",
        rating=rating,
    )


class TestHelperAutoRefreshSet(unittest.TestCase):
    def test_synced_feedback_can_trigger_refresh_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = build_helper_paths(Path(tmpdir))
            source_db = paths.srs_dir / "unit-frequency.sqlite"
            source_db.touch()
            for index, rating in enumerate(
                ("good", "easy", "good", "good", "hard", "again", "easy", "good")
            ):
                apply_feedback(
                    paths,
                    pair="en-ja",
                    lemma=f"review{index}",
                    rating=rating,
                    profile_id="default",
                    source_type="extension",
                )

            captured: dict[str, object] = {}

            def build_refresh_config(source_config, *, pair: str, profile_id: str, trigger: str):
                return _Config(
                    pair=pair,
                    profile_id=profile_id,
                    strategy=source_config.strategy,
                    set_source_db=source_db,
                    profile_context=source_config.profile_context,
                    max_active_items=20,
                    max_new_items=2,
                    feedback_window_size=100,
                    trigger=trigger,
                )

            def refresh_srs_set_fn(paths_arg, *, config):
                return refresh_srs_set(
                    paths_arg,
                    config=config,
                    resolve_pair_set_top_n_fn=lambda **_kwargs: 10,
                    resolve_pair_feedback_window_size_fn=lambda **_kwargs: 100,
                    resolve_pair_resources_fn=lambda _paths, **kwargs: (
                        kwargs.get("jmdict_path"),
                        kwargs.get("translation_dict_path"),
                        kwargs.get("set_source_db"),
                    ),
                    ensure_pair_requirements_fn=lambda **_kwargs: None,
                    resolve_profile_id_fn=_resolve_profile_id,
                    ensure_settings_fn=lambda _paths, **_kwargs: SrsSettings(
                        max_active_items=20,
                        max_new_items_per_day=2,
                    ),
                    ensure_store_fn=lambda _paths, *, profile_id, **_kwargs: (
                        load_srs_store(_paths.srs_store_path_for(profile_id))
                        if _paths.srs_store_path_for(profile_id).exists()
                        else SrsStore()
                    ),
                    count_items_for_pair_fn=count_items_for_pair,
                    resolve_stopwords_path_fn=lambda *_args, **_kwargs: None,
                    build_seed_candidates_fn=lambda **_kwargs: [
                        _seed_word(lemma, rank)
                        for rank, lemma in enumerate(
                            (
                                "alpha",
                                "beta",
                                "gamma",
                                "delta",
                                "epsilon",
                                "zeta",
                                "eta",
                                "theta",
                                "iota",
                                "kappa",
                                "lambda",
                                "mu",
                            ),
                            start=1,
                        )
                    ],
                    run_rulegen_for_pair_fn=_stub_run_rulegen_for_pair(captured),
                    write_rulegen_outputs_fn=write_rulegen_outputs,
                    update_status_fn=lambda **_kwargs: None,
                )

            result = maybe_auto_refresh_srs_set(
                paths,
                config=_Config(),
                resolve_profile_id_fn=_resolve_profile_id,
                build_refresh_config_fn=build_refresh_config,
                refresh_srs_set_fn=refresh_srs_set_fn,
            )

            self.assertTrue(result["attempted"])
            self.assertTrue(result["applied"], result)
            self.assertEqual(result["auto_refresh"]["result_reason_code"], "normal")
            refresh_payload = result["refresh"]
            self.assertIsInstance(refresh_payload, dict)
            self.assertEqual(refresh_payload["trigger"], "auto_feedback_threshold")
            self.assertEqual(refresh_payload["added_items"], 2)
            self.assertEqual(
                refresh_payload["admission_refresh"]["selected_lemmas"],
                ["alpha", "beta"],
            )
            self.assertIn("en-ja:alpha", captured["active_item_ids"])
            self.assertIn("en-ja:beta", captured["active_item_ids"])

            rulegen_payload = refresh_payload["rulegen"]
            self.assertTrue(Path(rulegen_payload["ruleset_path"]).exists())
            self.assertTrue(Path(rulegen_payload["snapshot_path"]).exists())
            self.assertTrue(Path(rulegen_payload["publication_manifest_path"]).exists())
            manifest = json.loads(
                Path(rulegen_payload["publication_manifest_path"]).read_text(encoding="utf-8")
            )
            self.assertTrue(manifest["validation"]["family_valid"])
            persisted = load_srs_store(paths.srs_store_path_for("default"))
            self.assertIn("alpha", {item.lemma for item in persisted.items})
            inventory = load_srs_inventory(paths.srs_inventory_path_for("default"))
            self.assertIn("en-ja:alpha", inventory.pairs["en-ja"].active_item_ids)

    def test_eligible_feedback_attempts_refresh_and_persists_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = build_helper_paths(Path(tmpdir))
            save_signal_events(
                paths.srs_signal_queue_path_for("default"),
                [
                    _event(index, rating)
                    for index, rating in enumerate(
                        ["good", "easy", "good", "good", "hard", "again", "easy", "good"]
                    )
                ],
            )
            captured = {}

            def build_refresh_config(source_config, *, pair: str, profile_id: str, trigger: str):
                captured["refresh_config"] = {
                    "pair": pair,
                    "profile_id": profile_id,
                    "trigger": trigger,
                    "strategy": source_config.strategy,
                }
                return SimpleNamespace(pair=pair, profile_id=profile_id, trigger=trigger)

            def refresh_srs_set_fn(paths_arg, *, config):
                captured["refresh_called"] = True
                self.assertIs(paths_arg, paths)
                self.assertEqual(config.trigger, "auto_feedback_threshold")
                return {
                    "applied": True,
                    "admission_refresh": {"reason_code": "normal"},
                }

            result = maybe_auto_refresh_srs_set(
                paths,
                config=_Config(),
                resolve_profile_id_fn=_resolve_profile_id,
                build_refresh_config_fn=build_refresh_config,
                refresh_srs_set_fn=refresh_srs_set_fn,
            )

            self.assertTrue(result["attempted"])
            self.assertTrue(result["applied"])
            self.assertTrue(captured["refresh_called"])
            self.assertEqual(captured["refresh_config"]["strategy"], "profile_growth")
            state = load_auto_refresh_state(paths.srs_auto_refresh_state_path_for("default"))
            pair_state = dict(state.pairs)["en-ja"]
            self.assertEqual(pair_state.attempt_count, 1)
            self.assertEqual(pair_state.applied_count, 1)
            self.assertEqual(pair_state.last_result_reason, "normal")

    def test_ineligible_feedback_does_not_call_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = build_helper_paths(Path(tmpdir))
            save_signal_events(
                paths.srs_signal_queue_path_for("default"),
                [_event(0, "good"), _event(1, "hard")],
            )

            def fail_refresh(*_args, **_kwargs):
                raise AssertionError("refresh should not be called")

            result = maybe_auto_refresh_srs_set(
                paths,
                config=_Config(),
                resolve_profile_id_fn=_resolve_profile_id,
                build_refresh_config_fn=lambda *_args, **_kwargs: SimpleNamespace(),
                refresh_srs_set_fn=fail_refresh,
            )

            self.assertFalse(result["attempted"])
            self.assertFalse(result["applied"])
            auto_refresh = result["auto_refresh"]
            self.assertIsInstance(auto_refresh, dict)
            self.assertEqual(auto_refresh["reason_code"], "insufficient_feedback")
            self.assertFalse(paths.srs_auto_refresh_state_path_for("default").exists())


def _seed_word(lemma: str, rank: float) -> SeedWord:
    base_weight = max(0.1, 1.0 - (rank * 0.05))
    return SeedWord(
        lemma=lemma,
        language_pair="en-ja",
        word_package=None,
        core_rank=rank,
        pos="名詞-普通名詞-一般",
        pos_bucket="noun",
        pos_weight=1.0,
        pmw=100.0 - rank,
        base_weight=base_weight,
        admission_weight=base_weight,
        metadata={},
    )


def _stub_run_rulegen_for_pair(captured: dict[str, object]):
    def _run_rulegen_for_pair(*, store, pair, active_item_ids, **_kwargs):
        captured["active_item_ids"] = tuple(active_item_ids)
        rules = (
            VocabRule(source_phrase="alpha source", replacement="alpha"),
            VocabRule(source_phrase="beta source", replacement="beta"),
        )
        return store, RulegenOutput(
            rules=rules,
            snapshot={
                "version": 1,
                "pair": pair,
                "targets": [
                    {"lemma": "alpha", "sources": ["alpha source"]},
                    {"lemma": "beta", "sources": ["beta source"]},
                ],
                "stats": {"target_count": 2, "rule_count": 2, "source_count": 2},
            },
            target_count=2,
            semantic_inventory={
                "schema_version": 1,
                "pair": pair,
                "profile_id": "default",
                "generated_at": "2026-05-27T00:00:00Z",
                "triggers": {},
                "senses": {},
                "competition_sets": {},
                "phrase_sets": {},
            },
        )

    return _run_rulegen_for_pair


if __name__ == "__main__":
    unittest.main()
