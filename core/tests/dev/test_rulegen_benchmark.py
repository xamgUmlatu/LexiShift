from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_benchmark import (  # noqa: E402
    BenchmarkTimingCollector,
    CompiledBenchmarkCaseRef,
    CompiledBenchmarkCaseTable,
    CompiledBenchmarkCaseResultTable,
    PairBenchmarkContext,
    SweepRunEvaluation,
    SweepConfig,
    SweepRun,
    _build_compiled_rule_table,
    _build_compiled_rule_table_from_rules,
    _build_compiled_case_result_table,
    _evaluate_benchmark_case_compiled,
    _evaluate_case_payloads_with_table,
    _evaluate_case_results,
    _evaluate_case_results_with_table,
    _build_compiled_case_table,
    _build_compiled_case_refs,
    _build_pair_resources_payload,
    _build_pair_report_payload,
    _summarize_compiled_case_results,
    _build_word_package_snapshot,
    _build_pair_compiled_rulegen_context,
    _build_reverse_preload_headwords,
    _expand_reverse_preload_headwords,
    _format_exact_hit_ambiguity_label,
    _format_exact_hit_specificity_label,
    _format_kaikki_provenance_label,
    _format_kaikki_policy_family_label,
    _load_pair_runs_from_report_payload,
    _load_render_inputs_from_report_payload,
    _load_frozen_word_package_snapshots,
    _load_html_report_renderer,
    _parse_family_set_specs,
    _preload_pair_gloss_records,
    _render_report_artifacts,
    _resolve_cli_with_preset,
    _resolve_pair_resources_for_benchmark,
    _run_pair_sweep,
    _evaluate_sweep_run,
)
from rulegen_benchmark_presets import (  # noqa: E402
    format_benchmark_presets_listing,
    load_benchmark_presets,
)
from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402
from lexishift_core.resources.dict_loaders import FreedictGlossRecord  # noqa: E402
from lexishift_core.rulegen.benchmarking import (  # noqa: E402
    RulegenBenchmarkCase,
    RulegenBenchmarkObjectiveWeights,
    RulegenBenchmarkSummary,
    evaluate_benchmark_case,
    summarize_benchmark_results,
)


class _FakePaths:
    def __init__(self, language_packs_dir: Path) -> None:
        self.language_packs_dir = language_packs_dir
        self.frequency_packs_dir = language_packs_dir


class _ImmediateFuture:
    def __init__(self, value) -> None:
        self._value = value

    def result(self):
        return self._value


class _FakeProcessPoolExecutor:
    def __init__(self, *args, initializer=None, initargs=(), **kwargs) -> None:
        self._initializer = initializer
        self._initargs = initargs
        self.futures: list[_ImmediateFuture] = []

    def __enter__(self):
        if self._initializer is not None:
            self._initializer(*self._initargs)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def submit(self, fn, *args, **kwargs):
        future = _ImmediateFuture(fn(*args, **kwargs))
        self.futures.append(future)
        return future


class TestRulegenBenchmark(unittest.TestCase):
    def test_load_html_report_renderer_returns_callable(self) -> None:
        renderer = _load_html_report_renderer()
        self.assertTrue(callable(renderer))

    def test_resolve_pair_resources_includes_reverse_freedict_for_en_es(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            forward = language_packs_dir / "spa-eng.tei"
            reverse = language_packs_dir / "eng-spa.tei"
            forward.write_text("forward", encoding="utf-8")
            reverse.write_text("reverse", encoding="utf-8")

            jmdict_path, freedict_path, reverse_path = _resolve_pair_resources_for_benchmark(
                paths=_FakePaths(language_packs_dir),
                pair="en-es",
                jmdict_override=None,
                freedict_override=forward,
                freedict_reverse_override=None,
            )

            self.assertIsNone(jmdict_path)
            self.assertEqual(freedict_path, forward)
            self.assertEqual(reverse_path, reverse)

    def test_parse_family_set_specs_supports_multiple_sets(self) -> None:
        parsed = _parse_family_set_specs(
            "math_geometry+government_law;none;register_region,hunting_fishing_tools",
            name="kaikki-policy-risk-family-sets",
        )

        self.assertEqual(
            parsed,
            [
                ("math_geometry", "government_law"),
                (),
                ("register_region", "hunting_fishing_tools"),
            ],
        )

    def test_format_kaikki_policy_family_label_uses_short_codes(self) -> None:
        label = _format_kaikki_policy_family_label(
            ("math_geometry", "government_law", "register_region")
        )

        self.assertEqual(label, "mg+gl+rr")

    def test_format_exact_hit_ambiguity_label_uses_threshold_and_penalty(self) -> None:
        config = SweepConfig(
            max_definitions_per_target=3,
            max_rules_per_target=None,
            confidence_threshold=0.0,
            semantic_demotion_scale=1.0,
            include_variants=False,
            pos_scoring_enabled=True,
            pos_exact_match_bonus=1.0,
            pos_compatible_match_bonus=0.5,
            score_weight_dict_priority=0.6,
            score_weight_frequency_weight=0.2,
            score_weight_pos_match=0.1,
            score_weight_variant_penalty=0.1,
            score_weight_phrase_penalty=0.1,
            score_weight_embedding=0.2,
            reverse_check_enabled=True,
            reverse_check_match_bonus=0.2,
            reverse_check_near_bonus=0.1,
            reverse_check_near_rank_max=2,
            reverse_check_far_hit_penalty=0.0,
            reverse_check_miss_penalty=0.2,
            reverse_check_exact_hit_ambiguity_threshold=12,
            reverse_check_exact_hit_ambiguity_penalty=0.4,
            kaikki_policy_live_demotion=False,
            kaikki_policy_risk_families=(),
        )

        self.assertEqual(_format_exact_hit_ambiguity_label(config), "12:0.40")

    def test_format_exact_hit_specificity_label_uses_bonus(self) -> None:
        config = SweepConfig(
            max_definitions_per_target=3,
            max_rules_per_target=None,
            confidence_threshold=0.0,
            semantic_demotion_scale=1.0,
            include_variants=False,
            pos_scoring_enabled=True,
            pos_exact_match_bonus=1.0,
            pos_compatible_match_bonus=0.5,
            score_weight_dict_priority=0.6,
            score_weight_frequency_weight=0.2,
            score_weight_pos_match=0.1,
            score_weight_variant_penalty=0.1,
            score_weight_phrase_penalty=0.1,
            score_weight_embedding=0.2,
            reverse_check_enabled=True,
            reverse_check_match_bonus=0.2,
            reverse_check_near_bonus=0.1,
            reverse_check_near_rank_max=2,
            reverse_check_far_hit_penalty=0.0,
            reverse_check_miss_penalty=0.2,
            reverse_check_exact_hit_ambiguity_threshold=0,
            reverse_check_exact_hit_ambiguity_penalty=0.0,
            kaikki_policy_live_demotion=False,
            kaikki_policy_risk_families=(),
            reverse_check_exact_hit_specificity_bonus=0.15,
        )

        self.assertEqual(_format_exact_hit_specificity_label(config), "0.15")

    def test_format_kaikki_provenance_label_uses_penalty(self) -> None:
        config = SweepConfig(
            max_definitions_per_target=3,
            max_rules_per_target=None,
            confidence_threshold=0.0,
            semantic_demotion_scale=1.0,
            include_variants=False,
            pos_scoring_enabled=True,
            pos_exact_match_bonus=1.0,
            pos_compatible_match_bonus=0.5,
            score_weight_dict_priority=0.6,
            score_weight_frequency_weight=0.2,
            score_weight_pos_match=0.1,
            score_weight_variant_penalty=0.1,
            score_weight_phrase_penalty=0.1,
            score_weight_embedding=0.2,
            reverse_check_enabled=True,
            reverse_check_match_bonus=0.2,
            reverse_check_near_bonus=0.1,
            reverse_check_near_rank_max=2,
            reverse_check_far_hit_penalty=0.0,
            reverse_check_miss_penalty=0.2,
            reverse_check_exact_hit_ambiguity_threshold=0,
            reverse_check_exact_hit_ambiguity_penalty=0.0,
            kaikki_policy_live_demotion=False,
            kaikki_policy_risk_families=(),
            reverse_check_exact_hit_specificity_bonus=0.0,
            kaikki_policy_late_sense_penalty=0.12,
        )

        self.assertEqual(_format_kaikki_provenance_label(config), "0.12")

    def test_build_pair_report_payload_mirrors_pair_resources(self) -> None:
        run = SweepRun(
            pair="en-es",
            run_index=1,
            config=SweepConfig(
                max_definitions_per_target=3,
                max_rules_per_target=None,
                confidence_threshold=0.0,
                semantic_demotion_scale=1.0,
                include_variants=False,
                pos_scoring_enabled=True,
                pos_exact_match_bonus=1.0,
                pos_compatible_match_bonus=0.5,
                score_weight_dict_priority=0.6,
                score_weight_frequency_weight=0.2,
                score_weight_pos_match=0.1,
                score_weight_variant_penalty=0.1,
                score_weight_phrase_penalty=0.1,
                score_weight_embedding=0.2,
                reverse_check_enabled=True,
                reverse_check_match_bonus=0.2,
                reverse_check_near_bonus=0.1,
                reverse_check_near_rank_max=2,
                reverse_check_far_hit_penalty=0.0,
                reverse_check_miss_penalty=0.2,
                reverse_check_exact_hit_ambiguity_threshold=0,
                reverse_check_exact_hit_ambiguity_penalty=0.0,
                kaikki_policy_live_demotion=False,
                kaikki_policy_risk_families=(),
            ),
            summary=RulegenBenchmarkSummary(
                pair="en-es",
                case_count=1,
                top1_correct_count=1,
                top3_contains_expected_count=1,
                forbidden_top1_count=0,
                forbidden_any_count=0,
                avg_rules_per_target=1.0,
                avg_top1_confidence=0.5,
                variant_rule_count=0,
                total_rule_count=1,
                variant_top1_count=0,
                top1_accuracy=1.0,
                top3_recall=1.0,
                forbidden_top1_rate=0.0,
                forbidden_any_rate=0.0,
                variant_rule_rate=0.0,
                variant_top1_rate=0.0,
                objective_score=100.0,
            ),
            case_results=(
                {
                    "case_id": "en-es:test",
                    "pair": "en-es",
                    "target": "casa",
                    "rule_count": 1,
                    "top1_source": "house",
                    "top3_sources": ["house"],
                    "all_sources": ["house"],
                    "top1_confidence": 0.5,
                    "top1_correct": True,
                    "top3_contains_expected": True,
                    "top1_forbidden": False,
                    "forbidden_any_present": False,
                    "variant_rule_count": 0,
                    "top1_is_variant": False,
                    "expected_matches": ["house"],
                    "forbidden_matches": [],
                },
            ),
        )

        payload = _build_pair_report_payload(
            case_count=1,
            runs=[run],
            resources={
                "translation_dict_path": "/tmp/wiktionary-es-en.sqlite",
                "reverse_translation_dict_path": "/tmp/wiktionary-en-es.sqlite",
            },
            word_package_snapshot={"casa": None},
            include_case_results=False,
        )

        self.assertEqual(
            payload["resources"]["translation_dict_path"],
            "/tmp/wiktionary-es-en.sqlite",
        )
        self.assertEqual(
            payload["resources"]["reverse_translation_dict_path"],
            "/tmp/wiktionary-en-es.sqlite",
        )
        self.assertIn("best_run", payload)
        self.assertEqual(payload["run_count"], 1)
        self.assertEqual(payload["word_package_snapshot"]["casa"], None)

    def test_build_pair_resources_payload_includes_sha256_checksums(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forward = root / "forward.sqlite"
            reverse = root / "reverse.sqlite"
            forward.write_text("forward", encoding="utf-8")
            reverse.write_text("reverse", encoding="utf-8")

            payload = _build_pair_resources_payload(
                jmdict_path=None,
                translation_dict_path=forward,
                reverse_translation_dict_path=reverse,
            )

            self.assertEqual(payload["translation_dict_path"], str(forward))
            self.assertEqual(payload["reverse_translation_dict_path"], str(reverse))
            checksums = payload["checksums"]
            self.assertTrue(str(checksums["translation_dict_sha256"]).startswith("sha256:"))
            self.assertTrue(str(checksums["reverse_translation_dict_sha256"]).startswith("sha256:"))
            self.assertIsNone(checksums["jmdict_sha256"])

    def test_build_word_package_snapshot_preserves_missing_targets_as_null(self) -> None:
        snapshot = _build_word_package_snapshot(
            targets=["casa", "madre"],
            word_packages_by_target={
                "casa": {
                    "version": 1,
                    "language_tag": "es",
                    "surface": "casa",
                    "reading": "casa",
                    "script_forms": {"default": "casa"},
                    "source": {"provider": "test"},
                }
            },
        )

        self.assertIsInstance(snapshot["casa"], dict)
        self.assertEqual(snapshot["casa"]["surface"], "casa")
        self.assertIsNone(snapshot["madre"])

    def test_preload_pair_gloss_records_loads_en_es_forward_and_reverse(self) -> None:
        forward_tei = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>casa</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">house</quote></cit>
        </sense>
      </entry>
      <entry>
        <form><orth>madre</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">mother</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        reverse_tei = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>house</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="es">casa</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forward = root / "spa-eng.tei"
            reverse = root / "eng-spa.tei"
            forward.write_text(forward_tei, encoding="utf-8")
            reverse.write_text(reverse_tei, encoding="utf-8")

            records_by_target, reverse_records_by_source = _preload_pair_gloss_records(
                pair="en-es",
                translation_dict_path=forward,
                reverse_translation_dict_path=reverse,
                targets=("casa",),
            )

        assert records_by_target is not None
        assert reverse_records_by_source is not None
        self.assertIn("casa", records_by_target)
        self.assertNotIn("madre", records_by_target)
        self.assertEqual(records_by_target["casa"][0].translation, "house")
        self.assertIn("house", reverse_records_by_source)
        self.assertEqual(reverse_records_by_source["house"][0].translation, "casa")

    def test_build_reverse_preload_headwords_for_en_es_covers_normalized_and_variant_forms(
        self,
    ) -> None:
        headwords = _build_reverse_preload_headwords(
            pair="en-es",
            forward_records_by_target={
                "casa": [FreedictGlossRecord(translation="house", pos_raw="noun")],
                "correr": [FreedictGlossRecord(translation="To Run!", pos_raw="verb")],
                "quitar": [
                    FreedictGlossRecord(
                        translation="to remove, to disrobe",
                        pos_raw="verb",
                    )
                ],
            },
        )

        assert headwords is not None
        self.assertIn("house", headwords)
        self.assertIn("houses", headwords)
        self.assertIn("run", headwords)
        self.assertIn("remove", headwords)
        self.assertIn("disrobe", headwords)
        self.assertNotIn("to run!", headwords)

    def test_preload_pair_gloss_records_scopes_en_es_reverse_load_to_candidate_headwords(
        self,
    ) -> None:
        forward_tei = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>casa</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">house</quote></cit>
        </sense>
      </entry>
      <entry>
        <form><orth>correr</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">To Run!</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        reverse_tei = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>house</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="es">casa</quote></cit>
        </sense>
      </entry>
      <entry>
        <form><orth>houses</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="es">casas</quote></cit>
        </sense>
      </entry>
      <entry>
        <form><orth>run</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="es">correr</quote></cit>
        </sense>
      </entry>
      <entry>
        <form><orth>tree</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="es">árbol</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forward = root / "spa-eng.tei"
            reverse = root / "eng-spa.tei"
            forward.write_text(forward_tei, encoding="utf-8")
            reverse.write_text(reverse_tei, encoding="utf-8")

            records_by_target, reverse_records_by_source = _preload_pair_gloss_records(
                pair="en-es",
                translation_dict_path=forward,
                reverse_translation_dict_path=reverse,
                targets=("casa", "correr"),
            )

        assert records_by_target is not None
        assert reverse_records_by_source is not None
        self.assertIn("house", reverse_records_by_source)
        self.assertIn("houses", reverse_records_by_source)
        self.assertIn("run", reverse_records_by_source)
        self.assertNotIn("tree", reverse_records_by_source)

    def test_expand_reverse_preload_headwords_adds_raw_infinitive_aliases(self) -> None:
        reverse_tei = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>to remove</orth></form>
        <gramGrp><pos>verb</pos></gramGrp>
        <sense>
          <cit type="trans"><quote xml:lang="es">quitar</quote></cit>
        </sense>
      </entry>
      <entry>
        <form><orth>house</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="es">casa</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            reverse = Path(tmp) / "eng-spa.tei"
            reverse.write_text(reverse_tei, encoding="utf-8")
            expanded = _expand_reverse_preload_headwords(
                pair="en-es",
                reverse_translation_dict_path=reverse,
                reverse_headwords=("remove", "house"),
            )

        assert expanded is not None
        self.assertIn("remove", expanded)
        self.assertIn("house", expanded)
        self.assertIn("to remove", expanded)

    def test_preload_pair_gloss_records_keeps_reverse_infinitive_hits_for_en_es(
        self,
    ) -> None:
        forward_tei = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>quitar</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">remove</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        reverse_tei = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>to remove</orth></form>
        <gramGrp><pos>verb</pos></gramGrp>
        <sense>
          <cit type="trans"><quote xml:lang="es">quitar</quote></cit>
        </sense>
      </entry>
      <entry>
        <form><orth>tree</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="es">arbol</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forward = root / "spa-eng.tei"
            reverse = root / "eng-spa.tei"
            forward.write_text(forward_tei, encoding="utf-8")
            reverse.write_text(reverse_tei, encoding="utf-8")

            records_by_target, reverse_records_by_source = _preload_pair_gloss_records(
                pair="en-es",
                translation_dict_path=forward,
                reverse_translation_dict_path=reverse,
                targets=("quitar",),
            )

        assert records_by_target is not None
        assert reverse_records_by_source is not None
        self.assertIn("to remove", reverse_records_by_source)
        self.assertNotIn("tree", reverse_records_by_source)

        compiled = _build_pair_compiled_rulegen_context(
            pair="en-es",
            targets=("quitar",),
            translation_dict_path=Path("/tmp/wiktionary-es-en.sqlite"),
            reverse_translation_dict_path=Path("/tmp/wiktionary-en-es.sqlite"),
            gloss_records_by_target=records_by_target,
            reverse_gloss_records_by_source=reverse_records_by_source,
            word_packages_by_target={},
            gloss_base_forms=("remove",),
        )

        assert compiled is not None
        candidate = compiled.compiled_targets_by_target["quitar"].base_candidates[0]
        self.assertTrue(candidate.metadata["reverse_check_supported"])
        self.assertTrue(candidate.metadata["reverse_check_hit"])
        self.assertEqual(candidate.metadata["reverse_check_rank"], 0)

    def test_build_pair_compiled_rulegen_context_builds_en_es_compiled_resources(self) -> None:
        gloss_records_by_target = {
            "casa": [FreedictGlossRecord(translation="house", pos_raw="noun")]
        }
        reverse_gloss_records_by_source = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")]
        }
        compiled = _build_pair_compiled_rulegen_context(
            pair="en-es",
            targets=("casa",),
            translation_dict_path=Path("/tmp/wiktionary-es-en.sqlite"),
            reverse_translation_dict_path=Path("/tmp/wiktionary-en-es.sqlite"),
            gloss_records_by_target=gloss_records_by_target,
            reverse_gloss_records_by_source=reverse_gloss_records_by_source,
            word_packages_by_target={},
            gloss_base_forms=("house", "home"),
        )

        self.assertIsNotNone(compiled)
        assert compiled is not None
        self.assertIn("casa", compiled.compiled_targets_by_target)
        target_context = compiled.compiled_targets_by_target["casa"]
        self.assertEqual(target_context.entries[0].translation, "house")
        self.assertEqual(target_context.base_candidates[0].source_phrase, "house")
        self.assertEqual(
            target_context.base_candidates[0].metadata.get("definition_bucket_key"),
            "gloss:0",
        )
        self.assertEqual(target_context.target_id, 0)
        self.assertEqual(target_context.base_candidates[0].metadata.get("compiled_target_id"), 0)
        self.assertEqual(
            target_context.base_candidates[0].metadata.get("compiled_candidate_id"),
            0,
        )
        self.assertIsNotNone(compiled.candidate_table)
        assert compiled.candidate_table is not None
        self.assertEqual(compiled.candidate_table.candidate_ids, (0,))
        self.assertEqual(compiled.candidate_table.candidate_row_ids_by_target_id, {0: (0,)})
        self.assertEqual(compiled.gloss_base_forms, frozenset({"house", "home"}))

    def test_build_compiled_case_refs_assigns_stable_case_rows(self) -> None:
        candidate_table = type(
            "CandidateTable",
            (),
            {"candidate_row_ids_by_target_id": {4: (2, 5), 7: (1,)}},
        )()
        compiled_pair_context = type(
            "CompiledContext",
            (),
            {
                "target_ids_by_target": {"casa": 4, "red": 7},
                "candidate_table": candidate_table,
            },
        )()

        refs = _build_compiled_case_refs(
            cases=(
                RulegenBenchmarkCase(case_id="en-es:casa:0", pair="en-es", target="casa"),
                RulegenBenchmarkCase(case_id="en-es:red:1", pair="en-es", target="red"),
            ),
            compiled_pair_context=compiled_pair_context,
        )

        self.assertEqual(
            refs,
            (
                CompiledBenchmarkCaseRef(
                    case_row_id=0,
                    case_id="en-es:casa:0",
                    target="casa",
                    target_id=4,
                    candidate_row_ids=(2, 5),
                ),
                CompiledBenchmarkCaseRef(
                    case_row_id=1,
                    case_id="en-es:red:1",
                    target="red",
                    target_id=7,
                    candidate_row_ids=(1,),
                ),
            ),
        )

    def test_build_compiled_case_table_normalizes_phrase_sets_and_links_candidate_rows(
        self,
    ) -> None:
        refs = (
            CompiledBenchmarkCaseRef(
                case_row_id=0,
                case_id="en-es:casa:0",
                target="casa",
                target_id=4,
                candidate_row_ids=(2, 5),
            ),
            CompiledBenchmarkCaseRef(
                case_row_id=1,
                case_id="en-es:red:1",
                target="red",
                target_id=7,
                candidate_row_ids=(1,),
            ),
        )

        table = _build_compiled_case_table(
            cases=(
                RulegenBenchmarkCase(
                    case_id="en-es:casa:0",
                    pair="en-es",
                    target="casa",
                    expected_any=(" House ", "home", "house"),
                    forbidden_top1=("HOME",),
                    forbidden_any=(" shack ", "home"),
                ),
                RulegenBenchmarkCase(
                    case_id="en-es:red:1",
                    pair="en-es",
                    target="red",
                    expected_any=("network",),
                    expected_top1_any=(" web ",),
                ),
            ),
            compiled_case_refs=refs,
        )

        self.assertIsInstance(table, CompiledBenchmarkCaseTable)
        self.assertEqual(table.case_row_ids, (0, 1))
        self.assertEqual(table.target_ids, (4, 7))
        self.assertEqual(table.candidate_row_id_rows, ((2, 5), (1,)))
        self.assertEqual(
            table.phrase_table.phrase_ids_by_phrase,
            {
                "house": 0,
                "home": 1,
                "shack": 2,
                "network": 3,
                "web": 4,
            },
        )
        self.assertEqual(table.expected_any_phrase_id_rows, ((0, 1), (3,)))
        self.assertEqual(table.expected_top1_phrase_id_rows, ((0, 1), (4,)))
        self.assertEqual(table.forbidden_top1_phrase_id_rows, ((1,), ()))
        self.assertEqual(table.forbidden_any_phrase_id_rows, ((2, 1), ()))

    def test_build_compiled_rule_table_links_selected_rules_back_to_candidate_rows(self) -> None:
        case = RulegenBenchmarkCase(
            case_id="en-es:casa:0",
            pair="en-es",
            target="casa",
            expected_any=("house",),
        )
        case_table = _build_compiled_case_table(
            cases=(case,),
            compiled_case_refs=(
                CompiledBenchmarkCaseRef(
                    case_row_id=0,
                    case_id=case.case_id,
                    target=case.target,
                    target_id=0,
                    candidate_row_ids=(0, 1),
                ),
            ),
        )
        compiled_pair_context = type(
            "CompiledPairContext",
            (),
            {
                "candidate_table": type(
                    "CandidateTable",
                    (),
                    {"candidate_row_id_by_candidate_id": {12: 3, 19: 5}},
                )(),
            },
        )()

        rule_table = _build_compiled_rule_table(
            rules_by_target={
                "casa": (
                    VocabRule(
                        source_phrase="house",
                        replacement="casa",
                        metadata=RuleMetadata(
                            confidence=0.7,
                            rulegen={"compiled_candidate_id": 12},
                        ),
                    ),
                    VocabRule(
                        source_phrase="home",
                        replacement="casa",
                        metadata=RuleMetadata(
                            confidence=0.6,
                            rulegen={"compiled_candidate_id": 19},
                        ),
                    ),
                )
            },
            compiled_case_table=case_table,
            compiled_pair_context=compiled_pair_context,
        )

        self.assertEqual(rule_table.candidate_row_id_rows, ((3, 5),))

    def test_build_compiled_rule_table_from_rules_matches_mapping_builder(self) -> None:
        case = RulegenBenchmarkCase(
            case_id="en-es:casa:0",
            pair="en-es",
            target="casa",
            expected_any=("house",),
        )
        case_table = _build_compiled_case_table(
            cases=(case,),
            compiled_case_refs=(
                CompiledBenchmarkCaseRef(
                    case_row_id=0,
                    case_id=case.case_id,
                    target=case.target,
                    target_id=0,
                    candidate_row_ids=(0, 1),
                ),
            ),
        )
        compiled_pair_context = type(
            "CompiledPairContext",
            (),
            {
                "candidate_table": type(
                    "CandidateTable",
                    (),
                    {"candidate_row_id_by_candidate_id": {12: 3, 19: 5}},
                )(),
            },
        )()
        rules = (
            VocabRule(
                source_phrase="house",
                replacement="casa",
                metadata=RuleMetadata(
                    confidence=0.7,
                    rulegen={"compiled_candidate_id": 12},
                ),
            ),
            VocabRule(
                source_phrase="home",
                replacement="casa",
                metadata=RuleMetadata(
                    confidence=0.6,
                    rulegen={"compiled_candidate_id": 19},
                ),
            ),
        )

        from_mapping = _build_compiled_rule_table(
            rules_by_target={"casa": rules},
            compiled_case_table=case_table,
            compiled_pair_context=compiled_pair_context,
        )
        from_rules = _build_compiled_rule_table_from_rules(
            rules=rules,
            compiled_case_table=case_table,
            compiled_pair_context=compiled_pair_context,
        )

        self.assertEqual(from_rules.targets, from_mapping.targets)
        self.assertEqual(from_rules.all_source_rows, from_mapping.all_source_rows)
        self.assertEqual(from_rules.source_phrase_id_rows, from_mapping.source_phrase_id_rows)
        self.assertEqual(from_rules.candidate_row_id_rows, from_mapping.candidate_row_id_rows)
        self.assertEqual(from_rules.top1_confidences, from_mapping.top1_confidences)
        self.assertEqual(from_rules.variant_rule_counts, from_mapping.variant_rule_counts)
        self.assertEqual(from_rules.top1_variant_flags, from_mapping.top1_variant_flags)
        self.assertEqual(from_rules.row_id_by_target, from_mapping.row_id_by_target)

    def test_compiled_case_evaluator_matches_legacy_evaluator(self) -> None:
        case = RulegenBenchmarkCase(
            case_id="en-es:casa:0",
            pair="en-es",
            target="casa",
            expected_any=("house", "home"),
            forbidden_top1=("home",),
            forbidden_any=("shack",),
        )
        refs = (
            CompiledBenchmarkCaseRef(
                case_row_id=0,
                case_id=case.case_id,
                target=case.target,
                target_id=4,
                candidate_row_ids=(2, 5),
            ),
        )
        case_table = _build_compiled_case_table(cases=(case,), compiled_case_refs=refs)
        rules = (
            VocabRule(
                source_phrase="home",
                replacement="casa",
                metadata=RuleMetadata(confidence=0.91),
            ),
            VocabRule(
                source_phrase="house",
                replacement="casa",
                metadata=RuleMetadata(
                    confidence=0.77,
                    morphology={"source_form": "houses"},
                ),
            ),
            VocabRule(
                source_phrase="shack",
                replacement="casa",
                metadata=RuleMetadata(confidence=0.2),
            ),
        )
        compiled_rule_table = _build_compiled_rule_table(
            rules_by_target={"casa": rules},
            compiled_case_table=case_table,
        )

        compiled_result = _evaluate_benchmark_case_compiled(
            case=case,
            case_row_id=0,
            compiled_case_table=case_table,
            compiled_rule_table=compiled_rule_table,
        )
        legacy_result = evaluate_benchmark_case(case, rules)

        self.assertEqual(compiled_result.to_dict(), legacy_result.to_dict())

    def test_evaluate_case_results_uses_compiled_case_table_without_changing_outputs(self) -> None:
        case = RulegenBenchmarkCase(
            case_id="en-es:casa:0",
            pair="en-es",
            target="casa",
            expected_any=("house",),
            forbidden_any=("shack",),
        )
        context = PairBenchmarkContext(
            pair="en-es",
            cases=(case,),
            targets=("casa",),
            jmdict_path=None,
            translation_dict_path=None,
            reverse_translation_dict_path=None,
            resources={},
            word_package_snapshot={},
            word_packages_by_target={},
            compiled_case_refs=(
                CompiledBenchmarkCaseRef(
                    case_row_id=0,
                    case_id=case.case_id,
                    target=case.target,
                    target_id=0,
                    candidate_row_ids=(0,),
                ),
            ),
            compiled_case_table=_build_compiled_case_table(
                cases=(case,),
                compiled_case_refs=(
                    CompiledBenchmarkCaseRef(
                        case_row_id=0,
                        case_id=case.case_id,
                        target=case.target,
                        target_id=0,
                        candidate_row_ids=(0,),
                    ),
                ),
            ),
        )
        rules_by_target = {
            "casa": (
                VocabRule(
                    source_phrase="house",
                    replacement="casa",
                    metadata=RuleMetadata(confidence=0.5),
                ),
                VocabRule(
                    source_phrase="shack",
                    replacement="casa",
                    metadata=RuleMetadata(confidence=0.2),
                ),
            )
        }

        compiled_results = _evaluate_case_results(
            context=context,
            rules_by_target=rules_by_target,
        )
        legacy_results = (evaluate_benchmark_case(case, rules_by_target["casa"]),)

        self.assertEqual(
            [result.to_dict() for result in compiled_results],
            [result.to_dict() for result in legacy_results],
        )

    def test_evaluate_case_results_with_table_builds_compiled_case_result_table(self) -> None:
        case = RulegenBenchmarkCase(
            case_id="en-es:casa:0",
            pair="en-es",
            target="casa",
            expected_any=("house",),
            forbidden_any=("shack",),
        )
        case_ref = CompiledBenchmarkCaseRef(
            case_row_id=0,
            case_id=case.case_id,
            target=case.target,
            target_id=0,
            candidate_row_ids=(0, 1),
        )
        context = PairBenchmarkContext(
            pair="en-es",
            cases=(case,),
            targets=("casa",),
            jmdict_path=None,
            translation_dict_path=None,
            reverse_translation_dict_path=None,
            resources={},
            word_package_snapshot={},
            word_packages_by_target={},
            compiled_case_refs=(case_ref,),
            compiled_case_table=_build_compiled_case_table(
                cases=(case,),
                compiled_case_refs=(case_ref,),
            ),
        )
        rules_by_target = {
            "casa": (
                VocabRule(
                    source_phrase="house",
                    replacement="casa",
                    metadata=RuleMetadata(confidence=0.5),
                ),
                VocabRule(
                    source_phrase="shack",
                    replacement="casa",
                    metadata=RuleMetadata(
                        confidence=0.2,
                        morphology={"source_form": "shacks"},
                    ),
                ),
            )
        }

        case_results, case_result_table = _evaluate_case_results_with_table(
            context=context,
            rules_by_target=rules_by_target,
        )

        self.assertEqual(len(case_results), 1)
        self.assertIsInstance(case_result_table, CompiledBenchmarkCaseResultTable)
        assert case_result_table is not None
        self.assertEqual(case_result_table.case_row_ids, (0,))
        self.assertEqual(case_result_table.rule_counts, (2,))
        self.assertEqual(case_result_table.top1_confidences, (0.5,))
        self.assertEqual(case_result_table.top1_correct_flags, (True,))
        self.assertEqual(case_result_table.forbidden_any_present_flags, (True,))
        self.assertEqual(case_result_table.variant_rule_counts, (1,))
        self.assertEqual(case_result_table.top1_variant_flags, (False,))

    def test_evaluate_case_results_with_table_accepts_flat_rules_for_compiled_context(self) -> None:
        case = RulegenBenchmarkCase(
            case_id="en-es:casa:0",
            pair="en-es",
            target="casa",
            expected_any=("house",),
            forbidden_any=("shack",),
        )
        case_ref = CompiledBenchmarkCaseRef(
            case_row_id=0,
            case_id=case.case_id,
            target=case.target,
            target_id=0,
            candidate_row_ids=(0, 1),
        )
        context = PairBenchmarkContext(
            pair="en-es",
            cases=(case,),
            targets=("casa",),
            jmdict_path=None,
            translation_dict_path=None,
            reverse_translation_dict_path=None,
            resources={},
            word_package_snapshot={},
            word_packages_by_target={},
            compiled_case_refs=(case_ref,),
            compiled_case_table=_build_compiled_case_table(
                cases=(case,),
                compiled_case_refs=(case_ref,),
            ),
        )
        rules = (
            VocabRule(
                source_phrase="house",
                replacement="casa",
                metadata=RuleMetadata(confidence=0.5),
            ),
            VocabRule(
                source_phrase="shack",
                replacement="casa",
                metadata=RuleMetadata(
                    confidence=0.2,
                    morphology={"source_form": "shacks"},
                ),
            ),
        )

        from_mapping, mapping_table = _evaluate_case_results_with_table(
            context=context,
            rules_by_target={"casa": rules},
        )
        from_rules, flat_table = _evaluate_case_results_with_table(
            context=context,
            rules=rules,
        )

        self.assertEqual(
            [result.to_dict() for result in from_rules],
            [result.to_dict() for result in from_mapping],
        )
        self.assertEqual(flat_table, mapping_table)

    def test_evaluate_case_payloads_with_table_matches_case_result_dicts(self) -> None:
        case = RulegenBenchmarkCase(
            case_id="en-es:casa:0",
            pair="en-es",
            target="casa",
            expected_any=("house",),
            forbidden_any=("shack",),
        )
        case_ref = CompiledBenchmarkCaseRef(
            case_row_id=0,
            case_id=case.case_id,
            target=case.target,
            target_id=0,
            candidate_row_ids=(0, 1),
        )
        context = PairBenchmarkContext(
            pair="en-es",
            cases=(case,),
            targets=("casa",),
            jmdict_path=None,
            translation_dict_path=None,
            reverse_translation_dict_path=None,
            resources={},
            word_package_snapshot={},
            word_packages_by_target={},
            compiled_case_refs=(case_ref,),
            compiled_case_table=_build_compiled_case_table(
                cases=(case,),
                compiled_case_refs=(case_ref,),
            ),
        )
        rules = (
            VocabRule(
                source_phrase="house",
                replacement="casa",
                metadata=RuleMetadata(confidence=0.5),
            ),
            VocabRule(
                source_phrase="shack",
                replacement="casa",
                metadata=RuleMetadata(
                    confidence=0.2,
                    morphology={"source_form": "shacks"},
                ),
            ),
        )

        case_results, result_table = _evaluate_case_results_with_table(
            context=context,
            rules=rules,
        )
        case_payloads, payload_table = _evaluate_case_payloads_with_table(
            context=context,
            rules=rules,
        )

        self.assertEqual(case_payloads, tuple(result.to_dict() for result in case_results))
        self.assertEqual(payload_table, result_table)

    def test_evaluate_sweep_run_compiled_path_skips_case_result_to_dict(self) -> None:
        case = RulegenBenchmarkCase(
            case_id="en-es:casa:0",
            pair="en-es",
            target="casa",
            expected_any=("house",),
            forbidden_any=("shack",),
        )
        case_ref = CompiledBenchmarkCaseRef(
            case_row_id=0,
            case_id=case.case_id,
            target=case.target,
            target_id=0,
            candidate_row_ids=(0, 1),
        )
        context = PairBenchmarkContext(
            pair="en-es",
            cases=(case,),
            targets=("casa",),
            jmdict_path=None,
            translation_dict_path=None,
            reverse_translation_dict_path=None,
            resources={},
            word_package_snapshot={},
            word_packages_by_target={},
            compiled_case_refs=(case_ref,),
            compiled_case_table=_build_compiled_case_table(
                cases=(case,),
                compiled_case_refs=(case_ref,),
            ),
        )
        config = SweepConfig(
            max_definitions_per_target=3,
            max_rules_per_target=None,
            confidence_threshold=0.0,
            semantic_demotion_scale=1.0,
            include_variants=False,
            pos_scoring_enabled=True,
            pos_exact_match_bonus=1.0,
            pos_compatible_match_bonus=0.5,
            score_weight_dict_priority=0.6,
            score_weight_frequency_weight=0.2,
            score_weight_pos_match=0.1,
            score_weight_variant_penalty=0.1,
            score_weight_phrase_penalty=0.1,
            score_weight_embedding=0.2,
            reverse_check_enabled=True,
            reverse_check_match_bonus=0.2,
            reverse_check_near_bonus=0.1,
            reverse_check_near_rank_max=2,
            reverse_check_far_hit_penalty=0.0,
            reverse_check_miss_penalty=0.2,
            reverse_check_exact_hit_ambiguity_threshold=0,
            reverse_check_exact_hit_ambiguity_penalty=0.0,
            kaikki_policy_live_demotion=False,
            kaikki_policy_risk_families=(),
        )
        rules = (
            VocabRule(
                source_phrase="house",
                replacement="casa",
                metadata=RuleMetadata(confidence=0.5),
            ),
            VocabRule(
                source_phrase="shack",
                replacement="casa",
                metadata=RuleMetadata(confidence=0.2),
            ),
        )

        with (
            patch("rulegen_benchmark.run_rules_with_adapter", return_value=rules),
            patch(
                "rulegen_benchmark.RulegenBenchmarkCaseResult.to_dict",
                side_effect=AssertionError("compiled sweep path should not serialize case results"),
            ),
        ):
            evaluation = _evaluate_sweep_run(
                context=context,
                config=config,
                run_index=0,
                objective_weights=RulegenBenchmarkObjectiveWeights(),
            )

        self.assertEqual(len(evaluation.run.case_results), 1)
        self.assertEqual(evaluation.run.case_results[0]["top1_source"], "house")
        self.assertTrue(evaluation.run.case_results[0]["top1_correct"])

    def test_summarize_compiled_case_results_matches_legacy_summary(self) -> None:
        case_results = (
            evaluate_benchmark_case(
                RulegenBenchmarkCase(
                    case_id="en-es:casa:0",
                    pair="en-es",
                    target="casa",
                    expected_any=("house",),
                    forbidden_any=("shack",),
                ),
                (
                    VocabRule(
                        source_phrase="house",
                        replacement="casa",
                        metadata=RuleMetadata(confidence=0.8),
                    ),
                    VocabRule(
                        source_phrase="shack",
                        replacement="casa",
                        metadata=RuleMetadata(
                            confidence=0.2,
                            morphology={"source_form": "shacks"},
                        ),
                    ),
                ),
            ),
            evaluate_benchmark_case(
                RulegenBenchmarkCase(
                    case_id="en-es:red:1",
                    pair="en-es",
                    target="red",
                    expected_any=("network",),
                    expected_top1_any=("web",),
                    forbidden_top1=("network",),
                ),
                (
                    VocabRule(
                        source_phrase="network",
                        replacement="red",
                        metadata=RuleMetadata(confidence=0.4),
                    ),
                ),
            ),
        )
        compiled_table = _build_compiled_case_result_table(
            case_rows=(
                (
                    case_results[0].rule_count,
                    case_results[0].top1_confidence,
                    case_results[0].top1_correct,
                    case_results[0].top3_contains_expected,
                    case_results[0].top1_forbidden,
                    case_results[0].forbidden_any_present,
                    case_results[0].variant_rule_count,
                    case_results[0].top1_is_variant,
                ),
                (
                    case_results[1].rule_count,
                    case_results[1].top1_confidence,
                    case_results[1].top1_correct,
                    case_results[1].top3_contains_expected,
                    case_results[1].top1_forbidden,
                    case_results[1].forbidden_any_present,
                    case_results[1].variant_rule_count,
                    case_results[1].top1_is_variant,
                ),
            )
        )
        weights = RulegenBenchmarkObjectiveWeights()

        compiled_summary = _summarize_compiled_case_results(
            pair="en-es",
            case_result_table=compiled_table,
            objective_weights=weights,
        )
        legacy_summary = summarize_benchmark_results(
            pair="en-es",
            case_results=case_results,
            objective_weights=weights,
        )

        self.assertEqual(compiled_summary.to_dict(), legacy_summary.to_dict())

    def test_benchmark_timing_collector_tracks_overall_and_pair_stats(self) -> None:
        collector = BenchmarkTimingCollector()

        collector.add("run_config", 0.5, pair="en-es")
        collector.add("run_config", 0.25, pair="en-es")
        collector.add("load_dataset", 0.1)

        payload = collector.to_dict(wall_clock_seconds=1.5)

        self.assertAlmostEqual(payload["wall_clock_seconds"], 1.5, places=6)
        self.assertAlmostEqual(payload["total_recorded_seconds"], 0.85, places=6)
        self.assertEqual(payload["phases"]["run_config"]["count"], 2)
        self.assertAlmostEqual(payload["phases"]["run_config"]["avg_seconds"], 0.375, places=6)
        self.assertEqual(payload["pairs"]["en-es"]["run_config"]["count"], 2)
        self.assertAlmostEqual(
            payload["pairs"]["en-es"]["run_config"]["total_seconds"],
            0.75,
            places=6,
        )

    def test_run_pair_sweep_parallel_aggregates_worker_timings(self) -> None:
        context = PairBenchmarkContext(
            pair="en-es",
            cases=(RulegenBenchmarkCase(case_id="en-es:casa:0", pair="en-es", target="casa"),),
            targets=("casa",),
            jmdict_path=None,
            translation_dict_path=None,
            reverse_translation_dict_path=None,
            resources={},
            word_package_snapshot={},
            word_packages_by_target={},
        )
        config_a = SweepConfig(
            max_definitions_per_target=3,
            max_rules_per_target=None,
            confidence_threshold=0.0,
            semantic_demotion_scale=1.0,
            include_variants=False,
            pos_scoring_enabled=True,
            pos_exact_match_bonus=1.0,
            pos_compatible_match_bonus=0.5,
            score_weight_dict_priority=0.6,
            score_weight_frequency_weight=0.2,
            score_weight_pos_match=0.1,
            score_weight_variant_penalty=0.1,
            score_weight_phrase_penalty=0.1,
            score_weight_embedding=0.2,
            reverse_check_enabled=True,
            reverse_check_match_bonus=0.2,
            reverse_check_near_bonus=0.1,
            reverse_check_near_rank_max=2,
            reverse_check_far_hit_penalty=0.0,
            reverse_check_miss_penalty=0.2,
            reverse_check_exact_hit_ambiguity_threshold=0,
            reverse_check_exact_hit_ambiguity_penalty=0.0,
            kaikki_policy_live_demotion=False,
            kaikki_policy_risk_families=(),
        )
        config_b = SweepConfig(
            max_definitions_per_target=3,
            max_rules_per_target=None,
            confidence_threshold=0.0,
            semantic_demotion_scale=1.0,
            include_variants=False,
            pos_scoring_enabled=True,
            pos_exact_match_bonus=1.0,
            pos_compatible_match_bonus=0.5,
            score_weight_dict_priority=0.6,
            score_weight_frequency_weight=0.2,
            score_weight_pos_match=0.1,
            score_weight_variant_penalty=0.1,
            score_weight_phrase_penalty=0.1,
            score_weight_embedding=0.2,
            reverse_check_enabled=False,
            reverse_check_match_bonus=0.2,
            reverse_check_near_bonus=0.1,
            reverse_check_near_rank_max=2,
            reverse_check_far_hit_penalty=0.0,
            reverse_check_miss_penalty=0.2,
            reverse_check_exact_hit_ambiguity_threshold=0,
            reverse_check_exact_hit_ambiguity_penalty=0.0,
            kaikki_policy_live_demotion=False,
            kaikki_policy_risk_families=(),
        )
        objective_weights = RulegenBenchmarkObjectiveWeights()
        timing = BenchmarkTimingCollector()

        def _fake_eval(run_index: int, config: SweepConfig) -> SweepRunEvaluation:
            objective = 110.0 if run_index == 2 else 100.0
            return SweepRunEvaluation(
                run=SweepRun(
                    pair="en-es",
                    run_index=run_index,
                    config=config,
                    summary=RulegenBenchmarkSummary(
                        pair="en-es",
                        case_count=1,
                        top1_correct_count=1,
                        top3_contains_expected_count=1,
                        forbidden_top1_count=0,
                        forbidden_any_count=0,
                        avg_rules_per_target=1.0,
                        avg_top1_confidence=0.5,
                        variant_rule_count=0,
                        total_rule_count=1,
                        variant_top1_count=0,
                        top1_accuracy=1.0,
                        top3_recall=1.0,
                        forbidden_top1_rate=0.0,
                        forbidden_any_rate=0.0,
                        variant_rule_rate=0.0,
                        variant_top1_rate=0.0,
                        objective_score=objective,
                    ),
                    case_results=(),
                ),
                phase_timings={"run_config": 0.25, "summarize_run": 0.05},
            )

        with (
            patch("rulegen_benchmark.ProcessPoolExecutor", _FakeProcessPoolExecutor),
            patch(
                "rulegen_benchmark.as_completed",
                side_effect=lambda futures: list(reversed(list(futures))),
            ),
            patch(
                "rulegen_benchmark._evaluate_sweep_run_from_worker_state",
                side_effect=_fake_eval,
            ),
        ):
            runs = _run_pair_sweep(
                context=context,
                sweep_configs=(config_a, config_b),
                objective_weights=objective_weights,
                jobs=2,
                timing=timing,
            )

        self.assertEqual([run.run_index for run in runs], [2, 1])
        timing_payload = timing.to_dict()
        self.assertEqual(timing_payload["pairs"]["en-es"]["run_config"]["count"], 2)
        self.assertAlmostEqual(
            timing_payload["pairs"]["en-es"]["run_config"]["total_seconds"],
            0.5,
            places=6,
        )

    def test_load_benchmark_presets_includes_canonical_en_es_matrix(self) -> None:
        presets = load_benchmark_presets(
            REPO_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_presets.json"
        )

        self.assertIn("en_es_canonical_matrix", presets)
        listing = format_benchmark_presets_listing(presets)
        self.assertIn("en_es_canonical_matrix", listing)

    def test_resolve_cli_with_preset_allows_explicit_cli_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            preset_file = Path(tmp) / "presets.json"
            preset_file.write_text(
                (
                    "{"
                    '"presets":{"tiny":{"description":"tiny preset","args":["--pairs","en-es","--max-configurations","8"]}}'
                    "}"
                ),
                encoding="utf-8",
            )

            args, preset = _resolve_cli_with_preset(
                argv=(
                    "--preset-file",
                    str(preset_file),
                    "--preset",
                    "tiny",
                    "--pairs",
                    "es-en",
                )
            )

            self.assertEqual(args.pairs, "es-en")
            self.assertEqual(args.max_configurations, 8)
            self.assertIsNotNone(preset)
            assert preset is not None
            self.assertEqual(preset.name, "tiny")

    def test_load_frozen_word_package_snapshots_supports_bundle_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload_path = Path(tmp) / "snapshot.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "pairs": {
                            "en-es": {
                                "casa": {
                                    "version": 1,
                                    "language_tag": "es",
                                    "surface": "casa",
                                    "reading": "casa",
                                    "script_forms": {"default": "casa"},
                                    "source": {"provider": "bundle"},
                                },
                                "agua": None,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            snapshots = _load_frozen_word_package_snapshots(payload_path)

            self.assertIn("en-es", snapshots)
            self.assertEqual(snapshots["en-es"]["casa"]["surface"], "casa")
            self.assertIsNone(snapshots["en-es"]["agua"])

    def test_load_frozen_word_package_snapshots_supports_benchmark_report_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload_path = Path(tmp) / "report.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "pairs": {
                            "en-es": {
                                "word_package_snapshot": {
                                    "madre": {
                                        "version": 1,
                                        "language_tag": "es",
                                        "surface": "madre",
                                        "reading": "madre",
                                        "script_forms": {"default": "madre"},
                                        "source": {"provider": "report"},
                                    }
                                }
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            snapshots = _load_frozen_word_package_snapshots(payload_path)

            self.assertEqual(snapshots["en-es"]["madre"]["surface"], "madre")

    def test_load_pair_runs_from_report_payload_rehydrates_best_case_results(self) -> None:
        payload = {
            "pairs": {
                "en-es": {
                    "best_run": {
                        "pair": "en-es",
                        "run_index": 2,
                        "config": {
                            "max_definitions_per_target": 3,
                            "max_rules_per_target": None,
                            "confidence_threshold": 0.0,
                            "semantic_demotion_scale": 1.0,
                            "include_variants": False,
                            "pos_scoring_enabled": True,
                            "pos_exact_match_bonus": 1.0,
                            "pos_compatible_match_bonus": 0.5,
                            "score_weight_dict_priority": 0.6,
                            "score_weight_frequency_weight": 0.2,
                            "score_weight_pos_match": 0.1,
                            "score_weight_variant_penalty": 0.1,
                            "score_weight_phrase_penalty": 0.1,
                            "score_weight_embedding": 0.2,
                            "reverse_check_enabled": True,
                            "reverse_check_match_bonus": 0.2,
                            "reverse_check_near_bonus": 0.1,
                            "reverse_check_near_rank_max": 2,
                            "reverse_check_far_hit_penalty": 0.0,
                            "reverse_check_miss_penalty": 0.2,
                            "reverse_check_exact_hit_ambiguity_threshold": 0,
                            "reverse_check_exact_hit_ambiguity_penalty": 0.0,
                            "reverse_check_exact_hit_specificity_bonus": 0.0,
                            "kaikki_policy_live_demotion": True,
                            "kaikki_policy_risk_families": ["math_geometry"],
                            "kaikki_policy_late_sense_penalty": 0.1,
                        },
                        "summary": {
                            "pair": "en-es",
                            "case_count": 1,
                            "top1_correct_count": 1,
                            "top3_contains_expected_count": 1,
                            "forbidden_top1_count": 0,
                            "forbidden_any_count": 0,
                            "avg_rules_per_target": 1.0,
                            "avg_top1_confidence": 0.75,
                            "variant_rule_count": 0,
                            "total_rule_count": 1,
                            "variant_top1_count": 0,
                            "top1_accuracy": 1.0,
                            "top3_recall": 1.0,
                            "forbidden_top1_rate": 0.0,
                            "forbidden_any_rate": 0.0,
                            "variant_rule_rate": 0.0,
                            "variant_top1_rate": 0.0,
                            "objective_score": 129.474,
                        },
                        "case_results": [
                            {
                                "case_id": "en-es:casa:0",
                                "pair": "en-es",
                                "target": "casa",
                                "rule_count": 1,
                                "top1_source": "house",
                                "top3_sources": ["house"],
                                "all_sources": ["house"],
                                "top1_confidence": 0.75,
                                "top1_correct": True,
                                "top3_contains_expected": True,
                                "top1_forbidden": False,
                                "forbidden_any_present": False,
                                "variant_rule_count": 0,
                                "top1_is_variant": False,
                                "expected_matches": ["house"],
                                "forbidden_matches": [],
                            }
                        ],
                    },
                    "runs": [
                        {
                            "pair": "en-es",
                            "run_index": 2,
                            "config": {
                                "max_definitions_per_target": 3,
                                "max_rules_per_target": None,
                                "confidence_threshold": 0.0,
                                "semantic_demotion_scale": 1.0,
                                "include_variants": False,
                                "pos_scoring_enabled": True,
                                "pos_exact_match_bonus": 1.0,
                                "pos_compatible_match_bonus": 0.5,
                                "score_weight_dict_priority": 0.6,
                                "score_weight_frequency_weight": 0.2,
                                "score_weight_pos_match": 0.1,
                                "score_weight_variant_penalty": 0.1,
                                "score_weight_phrase_penalty": 0.1,
                                "score_weight_embedding": 0.2,
                                "reverse_check_enabled": True,
                                "reverse_check_match_bonus": 0.2,
                                "reverse_check_near_bonus": 0.1,
                                "reverse_check_near_rank_max": 2,
                                "reverse_check_far_hit_penalty": 0.0,
                                "reverse_check_miss_penalty": 0.2,
                                "reverse_check_exact_hit_ambiguity_threshold": 0,
                                "reverse_check_exact_hit_ambiguity_penalty": 0.0,
                                "reverse_check_exact_hit_specificity_bonus": 0.0,
                                "kaikki_policy_live_demotion": True,
                                "kaikki_policy_risk_families": ["math_geometry"],
                                "kaikki_policy_late_sense_penalty": 0.1,
                            },
                            "summary": {
                                "pair": "en-es",
                                "case_count": 1,
                                "top1_correct_count": 1,
                                "top3_contains_expected_count": 1,
                                "forbidden_top1_count": 0,
                                "forbidden_any_count": 0,
                                "avg_rules_per_target": 1.0,
                                "avg_top1_confidence": 0.75,
                                "variant_rule_count": 0,
                                "total_rule_count": 1,
                                "variant_top1_count": 0,
                                "top1_accuracy": 1.0,
                                "top3_recall": 1.0,
                                "forbidden_top1_rate": 0.0,
                                "forbidden_any_rate": 0.0,
                                "variant_rule_rate": 0.0,
                                "variant_top1_rate": 0.0,
                                "objective_score": 129.474,
                            },
                        }
                    ],
                }
            }
        }

        pair_runs = _load_pair_runs_from_report_payload(payload)

        self.assertEqual(len(pair_runs["en-es"]), 1)
        self.assertEqual(pair_runs["en-es"][0].case_results[0]["target"], "casa")
        self.assertEqual(
            pair_runs["en-es"][0].config.kaikki_policy_risk_families, ("math_geometry",)
        )

    def test_load_render_inputs_from_report_payload_loads_dataset_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset_path = root / "cases.json"
            dataset_path.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "case_id": "en-es:casa:0",
                                "pair": "en-es",
                                "target": "casa",
                                "expected_any": ["house"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            report_payload = {
                "dataset_path": str(dataset_path),
                "pairs": {
                    "en-es": {
                        "best_run": {
                            "pair": "en-es",
                            "run_index": 1,
                            "config": {
                                "max_definitions_per_target": 3,
                                "max_rules_per_target": None,
                                "confidence_threshold": 0.0,
                                "semantic_demotion_scale": 1.0,
                                "include_variants": False,
                                "pos_scoring_enabled": True,
                                "pos_exact_match_bonus": 1.0,
                                "pos_compatible_match_bonus": 0.5,
                                "score_weight_dict_priority": 0.6,
                                "score_weight_frequency_weight": 0.2,
                                "score_weight_pos_match": 0.1,
                                "score_weight_variant_penalty": 0.1,
                                "score_weight_phrase_penalty": 0.1,
                                "score_weight_embedding": 0.2,
                                "reverse_check_enabled": True,
                                "reverse_check_match_bonus": 0.2,
                                "reverse_check_near_bonus": 0.1,
                                "reverse_check_near_rank_max": 2,
                                "reverse_check_far_hit_penalty": 0.0,
                                "reverse_check_miss_penalty": 0.2,
                                "reverse_check_exact_hit_ambiguity_threshold": 0,
                                "reverse_check_exact_hit_ambiguity_penalty": 0.0,
                                "reverse_check_exact_hit_specificity_bonus": 0.0,
                                "kaikki_policy_live_demotion": False,
                                "kaikki_policy_risk_families": [],
                                "kaikki_policy_late_sense_penalty": 0.0,
                            },
                            "summary": {
                                "pair": "en-es",
                                "case_count": 1,
                                "top1_correct_count": 1,
                                "top3_contains_expected_count": 1,
                                "forbidden_top1_count": 0,
                                "forbidden_any_count": 0,
                                "avg_rules_per_target": 1.0,
                                "avg_top1_confidence": 0.5,
                                "variant_rule_count": 0,
                                "total_rule_count": 1,
                                "variant_top1_count": 0,
                                "top1_accuracy": 1.0,
                                "top3_recall": 1.0,
                                "forbidden_top1_rate": 0.0,
                                "forbidden_any_rate": 0.0,
                                "variant_rule_rate": 0.0,
                                "variant_top1_rate": 0.0,
                                "objective_score": 100.0,
                            },
                            "case_results": [
                                {
                                    "case_id": "en-es:casa:0",
                                    "pair": "en-es",
                                    "target": "casa",
                                    "rule_count": 1,
                                    "top1_source": "house",
                                    "top3_sources": ["house"],
                                    "all_sources": ["house"],
                                    "top1_confidence": 0.5,
                                    "top1_correct": True,
                                    "top3_contains_expected": True,
                                    "top1_forbidden": False,
                                    "forbidden_any_present": False,
                                    "variant_rule_count": 0,
                                    "top1_is_variant": False,
                                    "expected_matches": ["house"],
                                    "forbidden_matches": [],
                                }
                            ],
                        },
                        "runs": [],
                    }
                },
            }

            pair_runs, cases_by_pair = _load_render_inputs_from_report_payload(report_payload)

            self.assertEqual(pair_runs["en-es"][0].summary.objective_score, 100.0)
            self.assertEqual(cases_by_pair["en-es"][0].expected_any, ("house",))

    def test_render_report_artifacts_updates_timing_before_html_snapshot(self) -> None:
        timing = BenchmarkTimingCollector()
        report_payload = {
            "generated_at": "2026-03-27T00:00:00+00:00",
            "profile_id": "default",
            "data_root": "D:/data",
            "dataset_path": "D:/cases.json",
            "sweep": {"configuration_count": 1},
        }
        run = SweepRun(
            pair="en-es",
            run_index=1,
            config=SweepConfig(
                max_definitions_per_target=3,
                max_rules_per_target=None,
                confidence_threshold=0.0,
                semantic_demotion_scale=1.0,
                include_variants=False,
                pos_scoring_enabled=True,
                pos_exact_match_bonus=1.0,
                pos_compatible_match_bonus=0.5,
                score_weight_dict_priority=0.6,
                score_weight_frequency_weight=0.2,
                score_weight_pos_match=0.1,
                score_weight_variant_penalty=0.1,
                score_weight_phrase_penalty=0.1,
                score_weight_embedding=0.2,
                reverse_check_enabled=True,
                reverse_check_match_bonus=0.2,
                reverse_check_near_bonus=0.1,
                reverse_check_near_rank_max=2,
                reverse_check_far_hit_penalty=0.0,
                reverse_check_miss_penalty=0.2,
                reverse_check_exact_hit_ambiguity_threshold=0,
                reverse_check_exact_hit_ambiguity_penalty=0.0,
                kaikki_policy_live_demotion=False,
                kaikki_policy_risk_families=(),
            ),
            summary=RulegenBenchmarkSummary(
                pair="en-es",
                case_count=1,
                top1_correct_count=1,
                top3_contains_expected_count=1,
                forbidden_top1_count=0,
                forbidden_any_count=0,
                avg_rules_per_target=1.0,
                avg_top1_confidence=0.5,
                variant_rule_count=0,
                total_rule_count=1,
                variant_top1_count=0,
                top1_accuracy=1.0,
                top3_recall=1.0,
                forbidden_top1_rate=0.0,
                forbidden_any_rate=0.0,
                variant_rule_rate=0.0,
                variant_top1_rate=0.0,
                objective_score=100.0,
            ),
            case_results=(
                {
                    "case_id": "en-es:casa:0",
                    "pair": "en-es",
                    "target": "casa",
                    "rule_count": 1,
                    "top1_source": "house",
                    "top3_sources": ["house"],
                    "all_sources": ["house"],
                    "top1_confidence": 0.5,
                    "top1_correct": True,
                    "top3_contains_expected": True,
                    "top1_forbidden": False,
                    "forbidden_any_present": False,
                    "variant_rule_count": 0,
                    "top1_is_variant": False,
                    "expected_matches": ["house"],
                    "forbidden_matches": [],
                },
            ),
        )
        cases_by_pair = {
            "en-es": [
                RulegenBenchmarkCase(
                    case_id="en-es:casa:0",
                    pair="en-es",
                    target="casa",
                    expected_any=("house",),
                )
            ]
        }
        captured_timings: list[dict[str, object]] = []

        def _fake_renderer(**kwargs):
            raw_timing = kwargs["report_payload"].get("timing")
            if isinstance(raw_timing, dict):
                captured_timings.append(dict(raw_timing))
            return "<html>ok</html>"

        with patch("rulegen_benchmark._load_html_report_renderer", return_value=_fake_renderer):
            _, _, timing_payload = _render_report_artifacts(
                report_payload=report_payload,
                pair_runs={"en-es": [run]},
                cases_by_pair=cases_by_pair,
                top_n=1,
                timing=timing,
                wall_clock_started=0.0,
            )

        self.assertTrue(captured_timings)
        self.assertIn("render_markdown", captured_timings[0]["phases"])
        self.assertIn("render_html", timing_payload["phases"])


if __name__ == "__main__":
    unittest.main()
