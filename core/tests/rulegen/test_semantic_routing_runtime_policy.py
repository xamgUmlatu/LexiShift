from __future__ import annotations

from pathlib import Path
import sys
import unittest

CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.rulegen.semantic_routing_runtime_policy import (  # noqa: E402
    SemanticDecisionPolicyConfig,
    build_semantic_admit_batch_response,
    evaluate_runtime_semantic_match,
    resolve_runtime_fallback_decision,
    resolve_semantic_decision_policy,
)
from lexishift_core.rulegen.semantic_routing_runtime_scoring import RuntimeSimilarityBackend  # noqa: E402


class SemanticRoutingRuntimePolicyTests(unittest.TestCase):
    def test_resolve_semantic_decision_policy_defaults_en_es(self) -> None:
        policy = resolve_semantic_decision_policy(pair="en-es")
        self.assertEqual(policy.policy_id, "en_es_sentence_veto_v2")
        self.assertEqual(policy.pair, "en-es")
        self.assertEqual(policy.scorer_id, "tfidf_cosine")
        self.assertEqual(policy.context_view, "masked_sentence")
        self.assertEqual(policy.evidence_view, "all_evidence_text")
        self.assertEqual(policy.min_active_score, 0.015)
        self.assertEqual(policy.min_margin, 0.0)
        self.assertEqual(policy.phrase_control_mode, "noun_family_frame_guard")
        self.assertEqual(policy.active_rescue_mode, "sense_label_near_tie_active_rescue")

    def test_resolve_semantic_decision_policy_allows_explicit_lexical_v2_control(self) -> None:
        policy = resolve_semantic_decision_policy(
            pair="en-es",
            decision_policy_id="en_es_sentence_veto_v2",
        )
        self.assertEqual(policy.policy_id, "en_es_sentence_veto_v2")
        self.assertEqual(policy.scorer_id, "tfidf_cosine")
        self.assertEqual(policy.evidence_view, "all_evidence_text")
        self.assertEqual(policy.min_active_score, 0.015)

    def test_resolve_semantic_decision_policy_allows_explicit_transformer_v3(self) -> None:
        policy = resolve_semantic_decision_policy(
            pair="en-es",
            decision_policy_id="en_es_sentence_veto_v3",
        )
        self.assertEqual(policy.policy_id, "en_es_sentence_veto_v3")
        self.assertEqual(policy.scorer_id, "sentence_transformer_cosine")
        self.assertEqual(policy.evidence_view, "all_evidence_text")
        self.assertEqual(policy.min_active_score, 0.0)

    def test_resolve_semantic_decision_policy_allows_explicit_legacy_v1(self) -> None:
        policy = resolve_semantic_decision_policy(
            pair="en-es",
            decision_policy_id="en_es_sentence_veto_v1",
        )
        self.assertEqual(policy.policy_id, "en_es_sentence_veto_v1")
        self.assertEqual(policy.scorer_id, "sentence_transformer_cosine")

    def test_resolve_runtime_fallback_decision_maps_all_supported_policies(self) -> None:
        self.assertEqual(resolve_runtime_fallback_decision("legacy_on_unavailable"), "replace")
        self.assertEqual(resolve_runtime_fallback_decision("abstain_on_unavailable"), "abstain")
        self.assertEqual(
            resolve_runtime_fallback_decision("soft_affordance_on_unavailable"),
            "soft_affordance",
        )

    def test_evaluate_runtime_semantic_match_applies_phrase_guard(self) -> None:
        policy = SemanticDecisionPolicyConfig(
            policy_id="test_phrase_guard",
            pair="en-es",
            scorer_id="tfidf_cosine",
            context_view="masked_sentence",
            evidence_view="all_evidence_text",
            min_active_score=0.0,
            min_margin=0.0,
            phrase_control_mode="noun_family_frame_guard",
            active_rescue_mode="off",
        )
        backend = RuntimeSimilarityBackend(scorer_id="tfidf_cosine")
        active_sense = {
            "sense_id": "sense:banco",
            "target_lemma": "banco",
            "canonical_pos": "noun",
            "evidence_views": {"all_evidence_text": "financial bank institution accounts loans"},
        }
        shadow_senses = (
            {
                "sense_id": "sense:orilla",
                "target_lemma": "orilla",
                "canonical_pos": "noun",
                "evidence_views": {"all_evidence_text": "river bank water edge shore"},
            },
        )
        sentence = "You can bank on her support."
        backend.fit(
            (
                sentence,
                active_sense["evidence_views"]["all_evidence_text"],
                shadow_senses[0]["evidence_views"]["all_evidence_text"],
            )
        )

        result = evaluate_runtime_semantic_match(
            match_id="case:bank:idiom",
            sentence=sentence,
            source_phrase="bank",
            active_sense=active_sense,
            shadow_senses=shadow_senses,
            policy=policy,
            scorer=backend,
            family_id="family:bank",
            family_pos_tags=("noun", "noun"),
        )

        self.assertEqual(result.predicted_decision, "abstain")
        self.assertTrue(result.phrase_preemption_hit)
        self.assertIn("phrase_preemption", result.reason_codes)
        self.assertIn("trigger_particle_frame", result.reason_codes)

    def test_build_semantic_admit_batch_response_uses_policy_when_inventory_ready(self) -> None:
        class FakeBackend:
            def __init__(self, *, scorer_id: str, model_name: str = "") -> None:
                self.scorer_id = scorer_id
                self.model_name = model_name

            def fit(self, texts: object) -> None:
                return None

            def similarity(self, left_text: str, right_text: str) -> float:
                normalized_left = str(left_text or "").lower()
                normalized_right = str(right_text or "").lower()
                if "deposit" in normalized_left or "cash" in normalized_left:
                    if "financial" in normalized_right or "bank account" in normalized_right:
                        return 0.92
                    if "river" in normalized_right or "shore" in normalized_right:
                        return 0.08
                return 0.0

        inventory = {
            "schema_version": 1,
            "pair": "en-es",
            "profile_id": "default",
            "senses": {
                "sense:banco": {
                    "sense_id": "sense:banco",
                    "target_lemma": "banco",
                    "sense_label": "financial bank",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "gloss_text": "financial bank account cash deposit",
                        "sense_label": "financial bank",
                    },
                },
                "sense:orilla": {
                    "sense_id": "sense:orilla",
                    "target_lemma": "orilla",
                    "sense_label": "river bank",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "gloss_text": "river bank shore water edge",
                        "sense_label": "river bank",
                    },
                },
            },
            "competition_sets": {
                "comp:bank": {
                    "competition_set_id": "comp:bank",
                    "status": "ready",
                    "shadow_sense_ids": ["sense:orilla"],
                    "selection_policy_version": "cross_checked_v1",
                }
            },
        }
        matches = [
            {
                "match_id": "match:bank:1",
                "source_phrase": "bank",
                "context_text": "I deposited cash at the bank yesterday.",
                "semantic_admission": {
                    "schema_version": 1,
                    "status": "ready",
                    "trigger_id": "en-es:trigger:bank",
                    "sense_id": "sense:banco",
                    "competition_set_id": "comp:bank",
                    "phrase_set_id": "phrase:bank",
                },
            }
        ]

        response = build_semantic_admit_batch_response(
            pair="en-es",
            profile_id="default",
            matches=matches,
            inventory=inventory,
            backend_factory=FakeBackend,
        )

        self.assertEqual(response["decision_policy_id"], "en_es_sentence_veto_v2")
        self.assertEqual(response["fallback_policy"], "abstain_on_unavailable")
        self.assertEqual(len(response["decisions"]), 1)
        self.assertEqual(response["decisions"][0]["decision"], "replace")
        self.assertEqual(response["decisions"][0]["decision_source"], "policy")
        self.assertEqual(response["decisions"][0]["sense_id"], "sense:banco")
        self.assertEqual(response["decisions"][0]["competition_set_id"], "comp:bank")
        self.assertEqual(response["decisions"][0]["context_view_id"], "masked_sentence")

    def test_build_semantic_admit_batch_response_allows_explicit_active_only_competition(
        self,
    ) -> None:
        class FakeBackend:
            def __init__(self, *, scorer_id: str, model_name: str = "") -> None:
                self.scorer_id = scorer_id
                self.model_name = model_name

            def fit(self, texts: object) -> None:
                return None

            def similarity(self, left_text: str, right_text: str) -> float:
                if "near the station" in str(left_text or "").lower():
                    return 0.88 if "medical professional" in str(right_text or "").lower() else 0.0
                return 0.0

        inventory = {
            "schema_version": 1,
            "pair": "en-es",
            "profile_id": "default",
            "capability": {
                "competition_mode": "active_only_anchor_cue",
            },
            "senses": {
                "sense:dentista": {
                    "sense_id": "sense:dentista",
                    "target_lemma": "dentista",
                    "sense_label": "dentist",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "all_evidence_text": "medical professional dentist appointment"
                    },
                }
            },
            "competition_sets": {
                "comp:dentist": {
                    "competition_set_id": "comp:dentist",
                    "status": "ready",
                    "active_sense_id": "sense:dentista",
                    "shadow_sense_ids": [],
                    "selection_mode": "active_only",
                    "selection_policy_version": "active_only_anchor_cue_v1",
                }
            },
        }
        matches = [
            {
                "match_id": "match:dentist:1",
                "source_phrase": "dentist",
                "context_text": "She booked an appointment with a dentist near the station.",
                "semantic_admission": {
                    "schema_version": 1,
                    "status": "ready",
                    "trigger_id": "en-es:trigger:dentist",
                    "sense_id": "sense:dentista",
                    "competition_set_id": "comp:dentist",
                },
            }
        ]

        response = build_semantic_admit_batch_response(
            pair="en-es",
            profile_id="default",
            matches=matches,
            inventory=inventory,
            backend_factory=FakeBackend,
        )

        self.assertEqual(response["decision_policy_id"], "en_es_sentence_veto_v2")
        decision = response["decisions"][0]
        self.assertEqual(decision["decision"], "replace")
        self.assertEqual(decision["decision_source"], "policy")
        self.assertEqual(decision["top_shadow_score"], 0.0)
        self.assertEqual(decision["score_margin"], decision["active_score"])

    def test_per_match_fit_scope_preserves_single_match_tfidf_semantics(self) -> None:
        class FitSensitiveBackend:
            def __init__(self, *, scorer_id: str, model_name: str = "") -> None:
                self.scorer_id = scorer_id
                self.model_name = model_name
                self.fit_count = 0

            def fit(self, texts: object) -> None:
                self.fit_count = len(list(texts))

            def similarity(self, _left_text: str, _right_text: str) -> float:
                return 0.9 if self.fit_count <= 3 else 0.0

        inventory = {
            "schema_version": 1,
            "pair": "en-es",
            "profile_id": "default",
            "capability": {
                "competition_mode": "active_only_anchor_cue",
            },
            "senses": {
                "sense:dentista": {
                    "sense_id": "sense:dentista",
                    "target_lemma": "dentista",
                    "sense_label": "dentist",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "all_evidence_text": "medical professional dentist appointment"
                    },
                },
                "sense:castillo": {
                    "sense_id": "sense:castillo",
                    "target_lemma": "castillo",
                    "sense_label": "castle",
                    "canonical_pos": "noun",
                    "evidence_views": {"all_evidence_text": "fortified castle medieval residence"},
                },
            },
            "competition_sets": {
                "comp:dentist": {
                    "competition_set_id": "comp:dentist",
                    "status": "ready",
                    "active_sense_id": "sense:dentista",
                    "shadow_sense_ids": [],
                    "selection_mode": "active_only",
                },
                "comp:castle": {
                    "competition_set_id": "comp:castle",
                    "status": "ready",
                    "active_sense_id": "sense:castillo",
                    "shadow_sense_ids": [],
                    "selection_mode": "active_only",
                },
            },
        }
        matches = [
            {
                "match_id": "match:dentist",
                "source_phrase": "dentist",
                "context_text": "She booked an appointment with a dentist near the station.",
                "semantic_admission": {
                    "schema_version": 1,
                    "status": "ready",
                    "trigger_id": "en-es:trigger:dentist",
                    "sense_id": "sense:dentista",
                    "competition_set_id": "comp:dentist",
                },
            },
            {
                "match_id": "match:castle",
                "source_phrase": "castle",
                "context_text": "A castle is a type of fortified structure.",
                "semantic_admission": {
                    "schema_version": 1,
                    "status": "ready",
                    "trigger_id": "en-es:trigger:castle",
                    "sense_id": "sense:castillo",
                    "competition_set_id": "comp:castle",
                },
            },
        ]

        batched = build_semantic_admit_batch_response(
            pair="en-es",
            profile_id="default",
            matches=matches,
            inventory=inventory,
            backend_factory=FitSensitiveBackend,
        )
        per_match = build_semantic_admit_batch_response(
            pair="en-es",
            profile_id="default",
            matches=matches,
            inventory=inventory,
            fit_scope="per_match",
            backend_factory=FitSensitiveBackend,
        )

        self.assertEqual(batched["fit_scope"], "batch")
        self.assertEqual(per_match["fit_scope"], "per_match")
        self.assertEqual(
            [decision["decision"] for decision in batched["decisions"]],
            ["abstain", "abstain"],
        )
        self.assertEqual(
            [decision["decision"] for decision in per_match["decisions"]],
            ["replace", "replace"],
        )

    def test_build_semantic_admit_batch_response_falls_back_on_empty_non_active_only_shadows(
        self,
    ) -> None:
        inventory = {
            "schema_version": 1,
            "pair": "en-es",
            "profile_id": "default",
            "senses": {
                "sense:dentista": {
                    "sense_id": "sense:dentista",
                    "target_lemma": "dentista",
                    "sense_label": "dentist",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "all_evidence_text": "medical professional dentist appointment"
                    },
                }
            },
            "competition_sets": {
                "comp:dentist": {
                    "competition_set_id": "comp:dentist",
                    "status": "ready",
                    "active_sense_id": "sense:dentista",
                    "shadow_sense_ids": [],
                    "selection_mode": "automatic",
                    "selection_policy_version": "en_es_emitted_rule_siblings_v1",
                }
            },
        }
        matches = [
            {
                "match_id": "match:dentist:1",
                "source_phrase": "dentist",
                "context_text": "She booked an appointment with a dentist near the station.",
                "semantic_admission": {
                    "schema_version": 1,
                    "status": "ready",
                    "trigger_id": "en-es:trigger:dentist",
                    "sense_id": "sense:dentista",
                    "competition_set_id": "comp:dentist",
                },
            }
        ]

        response = build_semantic_admit_batch_response(
            pair="en-es",
            profile_id="default",
            matches=matches,
            inventory=inventory,
            decision_policy_id="en_es_sentence_veto_v2",
        )

        decision = response["decisions"][0]
        self.assertEqual(decision["decision"], "abstain")
        self.assertEqual(decision["decision_source"], "fallback_policy")
        self.assertIn("shadow_senses_missing", decision["reason_codes"])
