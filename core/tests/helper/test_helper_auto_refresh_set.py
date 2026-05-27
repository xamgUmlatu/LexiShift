from __future__ import annotations

from dataclasses import dataclass
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Mapping, Optional, Sequence

from lexishift_core.helper.paths import HelperPaths, build_helper_paths
from lexishift_core.helper.use_cases.auto_refresh_set import maybe_auto_refresh_srs_set
from lexishift_core.srs.auto_refresh import load_auto_refresh_state
from lexishift_core.srs.signal_queue import SrsSignalEvent, save_signal_events


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


if __name__ == "__main__":
    unittest.main()
