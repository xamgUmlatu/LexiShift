from __future__ import annotations

from pathlib import Path
import sys
import unittest

CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    RuntimeSimilarityBackend,
    build_runtime_context_views,
    decide_runtime_veto_outcome,
    evaluate_runtime_veto_case,
    extract_runtime_phrase_control_signals,
    resolve_runtime_evidence_text,
)


class SemanticRoutingRuntimeScoringTests(unittest.TestCase):
    def test_build_runtime_context_views_masks_first_matching_phrase(self) -> None:
        views = build_runtime_context_views(
            "The goalkeeper punched the ball over the bar.",
            source_phrase="ball",
            window_tokens=2,
        )
        self.assertEqual(
            views["masked_sentence"],
            "The goalkeeper punched the ___ over the bar.",
        )
        self.assertEqual(views["raw_window"], "punched the ball over the")
        self.assertEqual(views["masked_window"], "punched the ___ over the")

    def test_resolve_runtime_evidence_text_falls_back_when_requested_view_missing(self) -> None:
        sense_record = {
            "target_lemma": "pelota",
            "evidence_views": {
                "sense_label": "object used in games",
                "all_evidence_text": "object used in games | sports equipment",
            },
        }
        self.assertEqual(
            resolve_runtime_evidence_text(sense_record, evidence_view="gloss_text"),
            "object used in games | sports equipment",
        )

    def test_token_jaccard_scoring_prefers_active_literal_match(self) -> None:
        backend = RuntimeSimilarityBackend(scorer_id="token_jaccard")
        active_text = "ball sports object used in games"
        shadow_text = "formal dance gala event"
        context_text = "The goalkeeper punched the ball over the bar."
        backend.fit((active_text, shadow_text, context_text))
        self.assertGreater(
            backend.similarity(context_text, active_text),
            backend.similarity(context_text, shadow_text),
        )

    def test_tfidf_scoring_prefers_active_for_financial_bank_sentence(self) -> None:
        backend = RuntimeSimilarityBackend(scorer_id="tfidf_cosine")
        active_text = "bank account at a financial institution"
        shadow_text = "river bank edge by the water"
        context_text = "She opened a new account at the bank yesterday."
        backend.fit((active_text, shadow_text, context_text))
        self.assertGreater(
            backend.similarity(context_text, active_text),
            backend.similarity(context_text, shadow_text),
        )

    def test_decide_runtime_veto_outcome_requires_margin(self) -> None:
        self.assertEqual(
            decide_runtime_veto_outcome(
                active_score=0.8,
                strongest_shadow_score=0.7,
                min_active_score=0.5,
                min_margin=0.15,
            ),
            "abstain",
        )
        self.assertEqual(
            decide_runtime_veto_outcome(
                active_score=0.8,
                strongest_shadow_score=0.6,
                min_active_score=0.5,
                min_margin=0.15,
            ),
            "replace",
        )

    def test_evaluate_runtime_veto_case_reports_shadow_gold_case_as_abstain(self) -> None:
        backend = RuntimeSimilarityBackend(scorer_id="tfidf_cosine")
        active_sense = {
            "sense_id": "sense:pelota",
            "target_lemma": "pelota",
            "evidence_views": {"all_evidence_text": "ball used for sports and games"},
        }
        shadow_senses = (
            {
                "sense_id": "sense:baile",
                "target_lemma": "baile",
                "evidence_views": {"all_evidence_text": "royal ball formal dance gala event"},
            },
        )
        case = {
            "case_id": "case:ball:dance",
            "sentence": "They danced at the royal ball until dawn.",
            "source_phrase": "ball",
            "gold_winner": "sense:baile",
        }
        backend.fit(
            (
                active_sense["evidence_views"]["all_evidence_text"],
                shadow_senses[0]["evidence_views"]["all_evidence_text"],
                case["sentence"],
            )
        )
        result = evaluate_runtime_veto_case(
            family_id="family:ball",
            case=case,
            active_sense=active_sense,
            shadow_senses=shadow_senses,
            scorer=backend,
            context_view="raw_sentence",
            evidence_view="all_evidence_text",
            min_active_score=0.05,
            min_margin=0.05,
        )
        self.assertEqual(result.gold_winner_type, "shadow")
        self.assertEqual(result.gold_decision, "abstain")
        self.assertEqual(result.predicted_decision, "abstain")
        self.assertEqual(result.predicted_winner, "sense:baile")

    def test_extract_runtime_phrase_control_signals_detects_modal_particle_frame(self) -> None:
        signals = extract_runtime_phrase_control_signals(
            "You can bank on her support.",
            source_phrase="bank",
            family_pos_tags=("noun", "noun"),
        )
        self.assertTrue(signals.phrase_preemption_hit)
        self.assertEqual(signals.matched_phrase_pattern, "bank on")
        self.assertEqual(signals.phrase_reason_code, "trigger_particle_frame")

    def test_extract_runtime_phrase_control_signals_skips_non_control_noun_usage(self) -> None:
        signals = extract_runtime_phrase_control_signals(
            "She deposited the cash at the bank before lunch.",
            source_phrase="bank",
            family_pos_tags=("noun", "noun"),
        )
        self.assertFalse(signals.phrase_preemption_hit)
        self.assertEqual(signals.matched_phrase_pattern, "")
        self.assertEqual(signals.phrase_reason_code, "")

    def test_extract_runtime_phrase_control_signals_skips_bare_noun_preposition_frame(self) -> None:
        signals = extract_runtime_phrase_control_signals(
            "The child kicked the ball into the street.",
            source_phrase="ball",
            family_pos_tags=("noun", "noun"),
        )
        self.assertFalse(signals.phrase_preemption_hit)
        self.assertEqual(signals.matched_phrase_pattern, "")
        self.assertEqual(signals.phrase_reason_code, "")

    def test_extract_runtime_phrase_control_signals_detects_subject_object_frame(self) -> None:
        signals = extract_runtime_phrase_control_signals(
            "Those numbers match the totals on the receipt.",
            source_phrase="match",
            family_pos_tags=("noun", "noun"),
        )
        self.assertTrue(signals.phrase_preemption_hit)
        self.assertEqual(signals.matched_phrase_pattern, "numbers match the")
        self.assertEqual(signals.phrase_reason_code, "subject_trigger_object_frame")

    def test_extract_runtime_phrase_control_signals_detects_subject_particle_frame(self) -> None:
        signals = extract_runtime_phrase_control_signals(
            "Customers file past the window each morning.",
            source_phrase="file",
            family_pos_tags=("noun", "noun"),
        )
        self.assertTrue(signals.phrase_preemption_hit)
        self.assertEqual(signals.matched_phrase_pattern, "file past")
        self.assertEqual(signals.phrase_reason_code, "trigger_particle_frame")
        self.assertIn("subject_trigger_particle_frame", signals.signal_codes)

    def test_extract_runtime_phrase_control_signals_detects_ball_rolling_idiom(self) -> None:
        signals = extract_runtime_phrase_control_signals(
            "The mayor tried to keep the ball rolling after the vote.",
            source_phrase="ball",
            family_pos_tags=("noun", "noun"),
        )
        self.assertTrue(signals.phrase_preemption_hit)
        self.assertEqual(signals.matched_phrase_pattern, "keep the ball rolling")
        self.assertEqual(signals.phrase_reason_code, "idiom_progressive_object_frame")

    def test_extract_runtime_phrase_control_signals_detects_ball_court_idiom(self) -> None:
        signals = extract_runtime_phrase_control_signals(
            "The ball is in your court now.",
            source_phrase="ball",
            family_pos_tags=("noun", "noun"),
        )
        self.assertTrue(signals.phrase_preemption_hit)
        self.assertEqual(signals.matched_phrase_pattern, "ball is in your court")
        self.assertEqual(signals.phrase_reason_code, "idiom_in_determiner_noun_frame")

    def test_extract_runtime_phrase_control_signals_skips_literal_ball_rolling_frame(self) -> None:
        signals = extract_runtime_phrase_control_signals(
            "She saw the ball rolling down the hill.",
            source_phrase="ball",
            family_pos_tags=("noun", "noun"),
        )
        self.assertFalse(signals.phrase_preemption_hit)
        self.assertEqual(signals.matched_phrase_pattern, "")
        self.assertEqual(signals.phrase_reason_code, "")

    def test_extract_runtime_phrase_control_signals_detects_rest_of_frame(self) -> None:
        signals = extract_runtime_phrase_control_signals(
            "The rest of the team arrived after dinner.",
            source_phrase="rest",
            family_pos_tags=("noun",),
        )
        self.assertTrue(signals.phrase_preemption_hit)
        self.assertEqual(signals.matched_phrase_pattern, "the rest of")
        self.assertEqual(signals.phrase_reason_code, "alternate_noun_of_phrase_frame")

    def test_extract_runtime_phrase_control_signals_skips_plain_rest_noun_frame(self) -> None:
        signals = extract_runtime_phrase_control_signals(
            "The doctor recommended two days of rest.",
            source_phrase="rest",
            family_pos_tags=("noun",),
        )
        self.assertFalse(signals.phrase_preemption_hit)
        self.assertEqual(signals.matched_phrase_pattern, "")
        self.assertEqual(signals.phrase_reason_code, "")

    def test_extract_runtime_phrase_control_signals_skips_active_cell_preposition_frame(
        self,
    ) -> None:
        signals = extract_runtime_phrase_control_signals(
            "Each cell in the tissue absorbed the dye.",
            source_phrase="cell",
            family_pos_tags=("noun", "noun"),
        )
        self.assertFalse(signals.phrase_preemption_hit)
        self.assertEqual(signals.matched_phrase_pattern, "")
        self.assertEqual(signals.phrase_reason_code, "")

    def test_extract_runtime_phrase_control_signals_exposes_tokens_when_pos_guard_disabled(
        self,
    ) -> None:
        signals = extract_runtime_phrase_control_signals(
            "The dry towel hung beside the sink.",
            source_phrase="dry",
            family_pos_tags=("adjective",),
        )
        self.assertFalse(signals.phrase_preemption_hit)
        self.assertEqual(signals.preceding_token, "the")
        self.assertEqual(signals.following_token, "towel")
        self.assertEqual(signals.family_pos_tags, ("adjective",))

    def test_extract_runtime_phrase_control_signals_exposes_tokens_for_mixed_pos_family(
        self,
    ) -> None:
        signals = extract_runtime_phrase_control_signals(
            "Workers rest after lunch in the shade.",
            source_phrase="rest",
            family_pos_tags=("noun", "verb"),
        )
        self.assertFalse(signals.phrase_preemption_hit)
        self.assertEqual(signals.preceding_token, "workers")
        self.assertEqual(signals.following_token, "after")
        self.assertEqual(signals.family_pos_tags, ("noun", "verb"))

    def test_evaluate_runtime_veto_case_applies_noun_family_frame_guard(self) -> None:
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
        case = {
            "case_id": "case:bank:idiom",
            "sentence": "You can bank on her support.",
            "source_phrase": "bank",
            "gold_winner": "none",
            "gold_decision": "abstain",
        }
        backend.fit(
            (
                active_sense["evidence_views"]["all_evidence_text"],
                shadow_senses[0]["evidence_views"]["all_evidence_text"],
                case["sentence"],
            )
        )
        result = evaluate_runtime_veto_case(
            family_id="family:bank",
            case=case,
            active_sense=active_sense,
            shadow_senses=shadow_senses,
            scorer=backend,
            context_view="masked_sentence",
            evidence_view="all_evidence_text",
            min_active_score=0.0,
            min_margin=0.0,
            phrase_control_mode="noun_family_frame_guard",
            family_pos_tags=("noun", "noun"),
        )
        self.assertTrue(result.phrase_preemption_hit)
        self.assertEqual(result.predicted_decision, "abstain")
        self.assertEqual(result.phrase_reason_code, "trigger_particle_frame")


if __name__ == "__main__":
    unittest.main()
