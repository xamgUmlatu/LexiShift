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

from lexishift_core.core import VocabRule  # noqa: E402
from lexishift_core.helper.engine import (  # noqa: E402
    SrsRefreshJobConfig,
    apply_feedback,
    refresh_srs_set,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs import (  # noqa: E402
    SrsItem,
    SrsSettings,
    SrsStore,
    load_srs_store,
    save_srs_settings,
    save_srs_store,
)


def _pair_count(paths, pair: str) -> int:
    store = load_srs_store(paths.srs_store_path)
    return len([item for item in store.items if item.language_pair == pair])


def _load_ruleset_rule_count(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rules = payload.get("rules", [])
    return len(rules) if isinstance(rules, list) else 0


def _load_snapshot_target_count(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    stats = payload.get("stats", {})
    if isinstance(stats, dict) and stats.get("target_count") is not None:
        return int(stats.get("target_count") or 0)
    targets = payload.get("targets", [])
    return len(targets) if isinstance(targets, list) else 0


def _build_seed_candidates() -> list[SimpleNamespace]:
    specs = [
        ("alpha", 0.95, "noun", 1.00),
        ("beta", 0.90, "noun", 1.00),
        ("gamma", 0.84, "adjective", 0.85),
        ("delta", 0.78, "verb", 0.70),
        ("epsilon", 0.73, "adverb", 0.55),
        ("zeta", 0.68, "other", 0.40),
    ]
    candidates: list[SimpleNamespace] = []
    for index, (lemma, base_weight, bucket, pos_weight) in enumerate(specs):
        candidates.append(
            SimpleNamespace(
                lemma=lemma,
                language_pair="en-ja",
                core_rank=float(index + 1),
                pos=f"{bucket}-tag",
                pos_bucket=bucket,
                pos_weight=pos_weight,
                pmw=100.0 - (index * 5.0),
                base_weight=base_weight,
                admission_weight=round(base_weight * pos_weight, 6),
                metadata={},
            )
        )
    return candidates


def _stub_run_rulegen_for_pair(*, store, pair, **_kwargs):
    pair_lemmas = sorted({item.lemma for item in store.items if item.language_pair == pair})
    rules = tuple(
        VocabRule(source_phrase=f"src_{lemma}", replacement=lemma)
        for lemma in pair_lemmas
    )
    snapshot_targets = [{"lemma": lemma, "sources": [f"src_{lemma}"]} for lemma in pair_lemmas]
    snapshot = {
        "version": 1,
        "pair": pair,
        "targets": snapshot_targets,
        "stats": {
            "target_count": len(pair_lemmas),
            "rule_count": len(rules),
            "source_count": len(rules),
        },
    }
    return store, SimpleNamespace(rules=rules, snapshot=snapshot, target_count=len(pair_lemmas))


class TestSrsFeedbackSimulation(unittest.TestCase):
    def test_feedback_cycles_drive_growth_and_ruleset_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            pair = "en-ja"
            profile_id = "default"
            jmdict_dir = root / "jmdict"
            jmdict_dir.mkdir(parents=True, exist_ok=True)
            source_db = root / "freq.sqlite"
            source_db.touch()

            save_srs_settings(
                SrsSettings(max_active_items=8, max_new_items_per_day=2),
                paths.srs_settings_path,
            )
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:alpha",
                            lemma="alpha",
                            language_pair=pair,
                            source_type="initial_set",
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )

            cycle_report: list[dict[str, object]] = []

            def run_refresh(label: str) -> dict[str, object]:
                result = refresh_srs_set(
                    paths,
                    config=SrsRefreshJobConfig(
                        pair=pair,
                        profile_id=profile_id,
                        jmdict_path=jmdict_dir,
                        set_source_db=source_db,
                        set_top_n=2000,
                        feedback_window_size=8,
                        persist_store=True,
                    ),
                )
                total_for_pair = _pair_count(paths, pair)
                rulegen_payload = result.get("rulegen") or {}
                ruleset_path = Path(rulegen_payload.get("ruleset_path")) if rulegen_payload else paths.ruleset_path(pair)
                snapshot_path = Path(rulegen_payload.get("snapshot_path")) if rulegen_payload else paths.snapshot_path(pair)
                ruleset_count = _load_ruleset_rule_count(ruleset_path) if ruleset_path.exists() else 0
                snapshot_targets = _load_snapshot_target_count(snapshot_path) if snapshot_path.exists() else 0
                cycle = {
                    "label": label,
                    "applied": bool(result.get("applied")),
                    "added_items": int(result.get("added_items") or 0),
                    "total_items_for_pair": total_for_pair,
                    "reason_code": str(result.get("admission_refresh", {}).get("reason_code", "")),
                    "feedback_count": int(
                        result.get("admission_refresh", {})
                        .get("feedback_window", {})
                        .get("feedback_count", 0)
                    ),
                    "retention_ratio": result.get("admission_refresh", {})
                    .get("feedback_window", {})
                    .get("retention_ratio"),
                    "ruleset_count": ruleset_count,
                    "snapshot_target_count": snapshot_targets,
                }
                cycle_report.append(cycle)
                return cycle

            with patch(
                "lexishift_core.helper.engine.build_seed_candidates",
                return_value=_build_seed_candidates(),
            ), patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                side_effect=_stub_run_rulegen_for_pair,
            ):
                for rating in ("good", "easy", "good", "easy", "good", "easy", "good", "easy"):
                    apply_feedback(paths, pair=pair, lemma="alpha", rating=rating, profile_id=profile_id)
                phase_1 = run_refresh("high_retention_1")

                for rating in ("again", "hard", "again", "hard", "again", "hard", "again", "hard"):
                    apply_feedback(paths, pair=pair, lemma="alpha", rating=rating, profile_id=profile_id)
                phase_2 = run_refresh("low_retention_pause")

                for rating in ("easy", "good", "easy", "good", "easy", "good", "easy", "good"):
                    apply_feedback(paths, pair=pair, lemma="alpha", rating=rating, profile_id=profile_id)
                phase_3 = run_refresh("high_retention_2")

            if os.environ.get("LEXISHIFT_VERBOSE_SRS_SIM", "").strip() == "1":
                print(json.dumps(cycle_report, indent=2, ensure_ascii=False))

            self.assertEqual(
                [phase_1["total_items_for_pair"], phase_2["total_items_for_pair"], phase_3["total_items_for_pair"]],
                [3, 3, 5],
                msg=json.dumps(cycle_report, indent=2, ensure_ascii=False),
            )
            self.assertTrue(bool(phase_1["applied"]), msg=json.dumps(cycle_report, indent=2, ensure_ascii=False))
            self.assertEqual(phase_1["reason_code"], "normal", msg=json.dumps(cycle_report, indent=2, ensure_ascii=False))
            self.assertEqual(phase_1["ruleset_count"], 3, msg=json.dumps(cycle_report, indent=2, ensure_ascii=False))
            self.assertEqual(
                phase_1["snapshot_target_count"],
                3,
                msg=json.dumps(cycle_report, indent=2, ensure_ascii=False),
            )

            self.assertFalse(bool(phase_2["applied"]), msg=json.dumps(cycle_report, indent=2, ensure_ascii=False))
            self.assertEqual(
                phase_2["reason_code"],
                "retention_low",
                msg=json.dumps(cycle_report, indent=2, ensure_ascii=False),
            )
            self.assertEqual(
                phase_2["ruleset_count"],
                3,
                msg=json.dumps(cycle_report, indent=2, ensure_ascii=False),
            )
            self.assertEqual(
                phase_2["snapshot_target_count"],
                3,
                msg=json.dumps(cycle_report, indent=2, ensure_ascii=False),
            )

            self.assertTrue(bool(phase_3["applied"]), msg=json.dumps(cycle_report, indent=2, ensure_ascii=False))
            self.assertEqual(phase_3["reason_code"], "normal", msg=json.dumps(cycle_report, indent=2, ensure_ascii=False))
            self.assertEqual(phase_3["ruleset_count"], 5, msg=json.dumps(cycle_report, indent=2, ensure_ascii=False))
            self.assertEqual(
                phase_3["snapshot_target_count"],
                5,
                msg=json.dumps(cycle_report, indent=2, ensure_ascii=False),
            )


if __name__ == "__main__":
    unittest.main()
