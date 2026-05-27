from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.engine import (  # noqa: E402
    SetAdmissionPreviewJobConfig,
    SetInitializationJobConfig,
    SrsRefreshJobConfig,
    apply_feedback,
    get_srs_runtime_diagnostics,
    initialize_srs_set,
    preview_srs_admission,
    refresh_srs_set,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.rulegen import annotate_rules_with_srs_serving_metadata  # noqa: E402
from lexishift_core.lexicon.word_package import build_word_package  # noqa: E402
from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402
from lexishift_core.srs import SrsSettings, load_srs_store, save_srs_settings  # noqa: E402
from lexishift_core.srs.seed import SeedWord  # noqa: E402

SRS_GATE_JS = PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_gate.js"


def _create_frequency_db(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL)")
        conn.execute(
            "INSERT INTO frequency (lemma, core_rank, pmw) VALUES (?, ?, ?)",
            ("casa", 1.0, 100.0),
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _seed(
    lemma: str,
    *,
    rank: int,
    weight: float,
    pos_bucket: str = "noun",
    topics: tuple[str, ...] = (),
) -> SeedWord:
    metadata: dict[str, object] = {
        "source": "synthetic_srs_product_loop",
        "pos_bucket": pos_bucket,
        "pos_weight": 1.0,
        "admission_weight": weight,
    }
    if topics:
        metadata["topics"] = list(topics)
    return SeedWord(
        lemma=lemma,
        language_pair="en-es",
        word_package=build_word_package(
            language_pair="en-es",
            surface=lemma,
            reading=lemma,
            source_provider="synthetic_srs_product_loop",
            pos=pos_bucket,
            pos_raw=pos_bucket,
            pos_canonical=pos_bucket,
            core_rank=float(rank),
            pmw=float(weight * 100.0),
            row_index=rank,
            row_rank=float(rank),
            source_extra={"topics": list(topics)} if topics else None,
        ),
        core_rank=float(rank),
        pos=pos_bucket,
        pos_bucket=pos_bucket,
        pos_weight=1.0,
        pmw=float(weight * 100.0),
        base_weight=weight,
        admission_weight=weight,
        metadata=metadata,
        pos_raw=pos_bucket,
        pos_canonical=pos_bucket,
        pos_source_profile="synthetic",
        pos_matched_rule="synthetic",
        pos_mapped=True,
    )


def _build_seed_candidates() -> list[SeedWord]:
    return [
        _seed("casa", rank=1, weight=0.99),
        _seed("libro", rank=2, weight=0.96),
        _seed("agua", rank=3, weight=0.94),
        _seed("perro", rank=4, weight=0.82, topics=("animals", "pets")),
        _seed("gato", rank=5, weight=0.80, topics=("animals", "pets")),
        _seed("mesa", rank=6, weight=0.78),
        _seed("ave", rank=7, weight=0.64, topics=("animals", "wildlife")),
        _seed("reptil", rank=8, weight=0.55, topics=("animals", "wildlife")),
        _seed("medicina", rank=9, weight=0.60, topics=("medicine",)),
        _seed("ballena", rank=10, weight=0.48, topics=("animals", "wildlife")),
        _seed("algoritmo", rank=11, weight=0.50, topics=("technology",)),
        _seed("jirafa", rank=12, weight=0.42, topics=("animals", "wildlife")),
    ]


def _stub_run_rulegen_for_pair(*, store, pair, **kwargs):
    active_item_ids = kwargs.get("active_item_ids")
    active_item_id_set = (
        {str(item_id).strip() for item_id in active_item_ids if str(item_id).strip()}
        if isinstance(active_item_ids, (frozenset, list, set, tuple))
        else None
    )
    pair_lemmas = sorted(
        {
            item.lemma
            for item in store.items
            if item.language_pair == pair
            and (active_item_id_set is None or item.item_id in active_item_id_set)
        }
    )
    rules = tuple(
        VocabRule(
            source_phrase=f"src_{lemma}",
            replacement=lemma,
            metadata=RuleMetadata(
                source_type="synthetic_srs_product_loop",
                language_pair=pair,
            ),
        )
        for lemma in pair_lemmas
    )
    rules = annotate_rules_with_srs_serving_metadata(
        rules,
        store=store,
        pair=pair,
        active_item_ids=active_item_ids,
    )
    snapshot = {
        "version": 1,
        "pair": pair,
        "targets": [{"lemma": lemma, "sources": [f"src_{lemma}"]} for lemma in pair_lemmas],
        "stats": {
            "target_count": len(pair_lemmas),
            "rule_count": len(rules),
            "source_count": len(rules),
        },
    }
    return store, SimpleNamespace(rules=rules, snapshot=snapshot, target_count=len(pair_lemmas))


def _ruleset_rules(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rules = payload.get("rules", [])
    return rules if isinstance(rules, list) else []


def _srs_due_metadata_count(rules: list[dict[str, object]]) -> int:
    count = 0
    for rule in rules:
        metadata = rule.get("metadata") if isinstance(rule, dict) else None
        rulegen = metadata.get("rulegen") if isinstance(metadata, dict) else None
        srs = rulegen.get("srs") if isinstance(rulegen, dict) else None
        if isinstance(srs, dict):
            count += 1
    return count


def _run_srs_gate_stats(ruleset_path: Path) -> dict[str, object]:
    script = f"""
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(SRS_GATE_JS))};
const rulesetPath = {json.dumps(str(ruleset_path))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const payload = JSON.parse(fs.readFileSync(rulesetPath, "utf8"));
const taggedRules = (payload.rules || []).map((rule) => ({{
  ...rule,
  metadata: {{
    ...(rule && rule.metadata && typeof rule.metadata === "object" ? rule.metadata : {{}}),
    lexishift_origin: "srs"
  }}
}}));

context.LexiShift.srsGate.buildSrsGate({{ srsEnabled: true }}, taggedRules, () => {{}})
  .then((gate) => {{
    console.log(JSON.stringify({{
      stats: gate.stats,
      activeLemmas: Array.from(gate.activeLemmas || []).sort()
    }}));
  }})
  .catch((error) => {{
    console.error(error);
    process.exit(1);
  }});
"""
    result = subprocess.run(
        ["node"],
        input=script,
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Node SRS gate check failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return json.loads(result.stdout)


class TestSrsPreferenceProductLoop(unittest.TestCase):
    def test_profile_preferences_survive_preview_feedback_refresh_and_runtime_serving(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            pair = "en-es"
            profile_id = "animal-profile"
            source_db = _create_frequency_db(paths.frequency_packs_dir / "freq-es-cde.sqlite")
            translation_dict = paths.language_packs_dir / "wiktionary-es-en.sqlite"
            translation_dict.parent.mkdir(parents=True, exist_ok=True)
            translation_dict.write_text("{}\n", encoding="utf-8")
            profile_context = {
                "topic_weights": {"animals": 1.0},
                "proficiency_estimate": 0.25,
                "challenge_target": 0.30,
            }
            animal_lemmas = {
                seed.lemma
                for seed in _build_seed_candidates()
                if "animals" in set(seed.metadata.get("topics", []))
            }

            save_srs_settings(
                SrsSettings(max_active_items=8, max_new_items_per_day=4),
                paths.srs_settings_path,
            )

            with (
                patch(
                    "lexishift_core.helper.rulegen.build_seed_candidates",
                    return_value=_build_seed_candidates(),
                ),
                patch(
                    "lexishift_core.helper.engine.build_seed_candidates",
                    return_value=_build_seed_candidates(),
                ),
                patch(
                    "lexishift_core.helper.engine.run_rulegen_for_pair",
                    side_effect=_stub_run_rulegen_for_pair,
                ),
            ):
                preview = preview_srs_admission(
                    paths,
                    config=SetAdmissionPreviewJobConfig(
                        pair=pair,
                        set_source_db=source_db,
                        profile_id=profile_id,
                        strategy="profile_bootstrap",
                        set_top_n=50,
                        initial_active_count=4,
                        preview_count=4,
                        profile_context=profile_context,
                    ),
                )
                preview_payload = preview["preview"]
                preview_profile = preview_payload["profile_bootstrap"]
                preview_active = set(preview_payload["initial_active_preview"])

                self.assertEqual(preview_payload["selection_strategy"], "profile_bootstrap")
                self.assertEqual(preview_payload["sampling_mode"], "reserved_topic_lane")
                self.assertEqual(preview_profile["selection_policy"], "reserved_topic_lane")
                self.assertEqual(
                    preview_profile["profile_context"]["topic_weights"]["animals"],
                    1.0,
                )
                self.assertGreaterEqual(len(preview_active & animal_lemmas), 1)
                self.assertFalse(paths.srs_store_path_for(profile_id).exists())

                initialized = initialize_srs_set(
                    paths,
                    config=SetInitializationJobConfig(
                        pair=pair,
                        set_source_db=source_db,
                        translation_dict_path=translation_dict,
                        profile_id=profile_id,
                        strategy="profile_bootstrap",
                        set_top_n=50,
                        initial_active_count=4,
                        profile_context=profile_context,
                    ),
                )
                initialized_active = set(
                    initialized["bootstrap_diagnostics"]["initial_active_preview"]
                )
                self.assertTrue(initialized["applied"])
                self.assertTrue(initialized["rulegen"]["published"])
                self.assertGreaterEqual(len(initialized_active & animal_lemmas), 1)
                self.assertEqual(
                    initialized["bootstrap_diagnostics"]["selection_policy"],
                    "reserved_topic_lane",
                )

                reviewed_lemma = sorted(initialized_active & animal_lemmas)[0]
                for rating in ("good", "easy", "good", "easy", "good", "easy", "good", "easy"):
                    apply_feedback(
                        paths,
                        pair=pair,
                        lemma=reviewed_lemma,
                        rating=rating,
                        profile_id=profile_id,
                    )

                refreshed = refresh_srs_set(
                    paths,
                    config=SrsRefreshJobConfig(
                        pair=pair,
                        set_source_db=source_db,
                        translation_dict_path=translation_dict,
                        profile_id=profile_id,
                        strategy="profile_growth",
                        set_top_n=50,
                        feedback_window_size=8,
                        max_active_items=8,
                        max_new_items=4,
                        profile_context=profile_context,
                    ),
                )

            refresh_payload = refreshed["admission_refresh"]
            selected_lemmas = set(refresh_payload["selected_lemmas"])
            selected_preferred_topic = refresh_payload["selected_preferred_topic"]
            selected_topic_share = float(selected_preferred_topic["share"])
            self.assertTrue(refreshed["applied"])
            self.assertEqual(refreshed["added_items"], 4)
            self.assertEqual(refresh_payload["reason_code"], "normal")
            self.assertEqual(refresh_payload["selection_strategy_effective"], "profile_growth")
            self.assertEqual(refresh_payload["selection_policy"], "reserved_topic_lane")
            self.assertGreaterEqual(selected_topic_share, 0.45)
            self.assertLessEqual(selected_topic_share, 0.55)
            self.assertEqual(
                selected_preferred_topic["preferred_count"],
                len(selected_lemmas & animal_lemmas),
            )
            self.assertTrue(refreshed["rulegen"]["published"])

            store = load_srs_store(paths.srs_store_path_for(profile_id))
            pair_items = [item for item in store.items if item.language_pair == pair]
            self.assertEqual(len(pair_items), 8)

            diagnostics = get_srs_runtime_diagnostics(paths, pair=pair, profile_id=profile_id)
            self.assertEqual(diagnostics["missing_inputs"], [])
            self.assertTrue(diagnostics["ruleset_exists"])
            self.assertTrue(diagnostics["snapshot_exists"])
            self.assertTrue(diagnostics["publication_manifest_exists"])
            self.assertTrue(diagnostics["publication_manifest_family_valid"])
            self.assertEqual(diagnostics["ruleset_rules_count"], 8)
            self.assertEqual(diagnostics["snapshot_target_count"], 8)
            self.assertEqual(diagnostics["inventory_active_items_for_pair"], 8)

            ruleset_path = Path(refreshed["rulegen"]["ruleset_path"])
            rules = _ruleset_rules(ruleset_path)
            self.assertEqual(_srs_due_metadata_count(rules), 8)

            gate_payload = _run_srs_gate_stats(ruleset_path)
            stats = gate_payload["stats"]
            self.assertEqual(stats["mode"], "helper_ruleset")
            self.assertEqual(stats["servingMode"], "due_metadata")
            self.assertEqual(stats["srsCount"], 8)
            self.assertGreater(stats["srsActiveCount"], 0)
            self.assertLessEqual(stats["srsActiveCount"], stats["srsCount"])
            self.assertGreaterEqual(stats["srsDueFilteredCount"], 1)
            self.assertNotIn(reviewed_lemma, set(gate_payload["activeLemmas"]))


if __name__ == "__main__":
    unittest.main()
