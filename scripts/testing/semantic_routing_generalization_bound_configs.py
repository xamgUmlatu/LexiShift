#!/usr/bin/env python3
from __future__ import annotations

FIXED_SHADOW_CONTROL_CONFIG = {
    "label": "Fixed-shadow runtime control",
    "scorer_id": "tfidf_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.05,
    "min_margin": 0.0,
    "phrase_control_mode": "noun_family_frame_guard",
    "active_rescue_mode": "sense_label_near_tie_active_rescue",
}

FIXED_SHADOW_REFERENCE_CONFIG = {
    "label": "Sentence-transformer phrase-guard candidate",
    "scorer_id": "sentence_transformer_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.0,
    "min_margin": 0.0,
    "phrase_control_mode": "noun_family_frame_guard",
    "active_rescue_mode": "sense_label_near_tie_active_rescue",
}

FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG = {
    "label": "Sentence-transformer active-sense phrase-guard experiment",
    "scorer_id": "sentence_transformer_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.0,
    "min_margin": 0.0,
    "phrase_control_mode": "noun_family_frame_guard",
    "phrase_guard_pos_scope": "active_only",
    "active_rescue_mode": "sense_label_near_tie_active_rescue",
    "experimental": True,
}

FIXED_SHADOW_LADDER_CONFIG = {
    "label": "Sentence-transformer zero-noise soft ladder",
    "scorer_id": "sentence_transformer_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.0,
    "min_margin": 0.0,
    "phrase_control_mode": "noun_family_frame_guard",
    "active_rescue_mode": "sense_label_near_tie_active_rescue",
    "soft_min_active_score": 0.55,
    "soft_min_margin": -0.03,
    "apply_over_current_abstains_only": True,
}

FIXED_SHADOW_RESCUE_OVERLAY_CONFIG = {
    "label": "Sentence-transformer widened-rescue candidate (simulated)",
    "scorer_id": "sentence_transformer_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.0,
    "min_margin": 0.0,
    "phrase_control_mode": "noun_family_frame_guard",
    "active_rescue_mode": "sense_label_near_tie_active_rescue",
    "backup_evidence_view": "sense_label",
    "primary_margin_floor": -0.05,
    "backup_margin_floor": 0.02,
    "simulated": True,
}

FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG = {
    "label": "Sentence-transformer active-sense phrase-guard overlay (simulated)",
    "scorer_id": "sentence_transformer_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.0,
    "min_margin": 0.0,
    "phrase_control_mode": "noun_family_frame_guard",
    "phrase_guard_pos_scope": "active_only",
    "active_rescue_mode": "sense_label_near_tie_active_rescue",
    "backup_evidence_view": "sense_label",
    "primary_margin_floor": -0.05,
    "backup_margin_floor": 0.02,
    "simulated": True,
    "experimental": True,
}

FIXED_SHADOW_METRIC_DIRECTIONS = {
    "decision_accuracy": "higher",
    "replace_precision": "higher",
    "replace_recall": "higher",
    "harmful_replace_rate": "lower",
    "false_abstain_rate": "lower",
    "winner_accuracy": "higher",
    "shadow_winner_accuracy": "higher",
}

FIXED_SHADOW_LADDER_METRIC_DIRECTIONS = {
    "hard_replace_recall": "higher",
    "hard_harmful_replace_rate": "lower",
    "replace_or_soft_recall": "higher",
    "soft_noise_rate": "lower",
    "surfaced_precision": "higher",
    "remaining_missed_replace_rate": "lower",
}

VETO_PROXY_METRIC_DIRECTIONS = {
    "overall_accuracy": "higher",
    "abstain_recall": "higher",
    "harmful_allow_rate": "lower",
    "allow_precision": "higher",
    "overblocking_rate": "lower",
}
