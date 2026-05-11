from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (
    DEFAULT_SENTENCE_VETO_CONTEXT_VIEW,
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_EVIDENCE_VIEW,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    DEFAULT_SENTENCE_VETO_MIN_ACTIVE_SCORE,
    DEFAULT_SENTENCE_VETO_MIN_MARGIN,
    DEFAULT_SENTENCE_VETO_PHRASE_CONTROL_MODE,
    RuntimeSimilarityBackend,
    build_runtime_context_views,
    evaluate_runtime_veto_case,
    resolve_runtime_evidence_text,
)

DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE = "off"
SENTENCE_VETO_ACTIVE_RESCUE_MODES = (
    "off",
    "sense_label_near_tie_active_rescue",
)
DEFAULT_RUNTIME_SEMANTIC_FALLBACK_POLICY = "abstain_on_unavailable"
RUNTIME_SEMANTIC_FALLBACK_POLICIES = (
    "legacy_on_unavailable",
    "abstain_on_unavailable",
    "soft_affordance_on_unavailable",
)
_ACTIVE_RESCUE_PRIMARY_MARGIN_FLOOR = -0.02
_ACTIVE_RESCUE_BACKUP_MARGIN_FLOOR = 0.02
_ACTIVE_RESCUE_BACKUP_EVIDENCE_VIEW = "sense_label"


@dataclass(frozen=True)
class SemanticDecisionPolicyConfig:
    policy_id: str
    pair: str
    scorer_id: str
    model_name: str = ""
    context_view: str = DEFAULT_SENTENCE_VETO_CONTEXT_VIEW
    evidence_view: str = DEFAULT_SENTENCE_VETO_EVIDENCE_VIEW
    min_active_score: float = DEFAULT_SENTENCE_VETO_MIN_ACTIVE_SCORE
    min_margin: float = DEFAULT_SENTENCE_VETO_MIN_MARGIN
    phrase_control_mode: str = DEFAULT_SENTENCE_VETO_PHRASE_CONTROL_MODE
    active_rescue_mode: str = DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN


@dataclass(frozen=True)
class RuntimeSemanticDecisionResult:
    case_id: str
    family_id: str
    predicted_decision: str
    predicted_winner: str
    predicted_winner_type: str
    active_score: float
    strongest_shadow_score: float
    margin: float
    strongest_shadow_id: str
    context_text: str
    active_evidence_text: str
    strongest_shadow_evidence_text: str
    phrase_preemption_hit: bool
    matched_phrase_pattern: str
    phrase_reason_code: str
    reason_codes: tuple[str, ...]
    active_rescue_applied: bool
    active_rescue_reason_code: str
    active_rescue_primary_margin: float
    active_rescue_backup_margin: float | None
    active_rescue_backup_predicted_decision: str
    active_rescue_backup_predicted_winner: str
    active_rescue_backup_evidence_view: str


PRODUCTION_SEMANTIC_DECISION_POLICIES: dict[str, SemanticDecisionPolicyConfig] = {
    "en_es_sentence_veto_v1": SemanticDecisionPolicyConfig(
        policy_id="en_es_sentence_veto_v1",
        pair="en-es",
        scorer_id="sentence_transformer_cosine",
        context_view="masked_sentence",
        evidence_view="gloss_text",
        min_active_score=0.0,
        min_margin=0.0,
        phrase_control_mode="noun_family_frame_guard",
        active_rescue_mode="sense_label_near_tie_active_rescue",
        window_tokens=DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
        mask_token=DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    ),
    "en_es_sentence_veto_v2": SemanticDecisionPolicyConfig(
        policy_id="en_es_sentence_veto_v2",
        pair="en-es",
        scorer_id="tfidf_cosine",
        context_view="masked_sentence",
        evidence_view="all_evidence_text",
        min_active_score=0.015,
        min_margin=0.0,
        phrase_control_mode="noun_family_frame_guard",
        active_rescue_mode="sense_label_near_tie_active_rescue",
        window_tokens=DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
        mask_token=DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    ),
    "en_es_sentence_veto_v3": SemanticDecisionPolicyConfig(
        policy_id="en_es_sentence_veto_v3",
        pair="en-es",
        scorer_id="sentence_transformer_cosine",
        context_view="masked_sentence",
        evidence_view="all_evidence_text",
        min_active_score=0.0,
        min_margin=0.0,
        phrase_control_mode="noun_family_frame_guard",
        active_rescue_mode="sense_label_near_tie_active_rescue",
        window_tokens=DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
        mask_token=DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    ),
}
PAIR_DEFAULT_SEMANTIC_DECISION_POLICY_IDS: dict[str, str] = {
    "en-es": "en_es_sentence_veto_v3",
}


def resolve_semantic_decision_policy(
    *,
    pair: str,
    decision_policy_id: str | None = None,
) -> SemanticDecisionPolicyConfig:
    normalized_pair = str(pair or "").strip().lower()
    requested_policy_id = str(decision_policy_id or "").strip()
    resolved_policy_id = requested_policy_id or PAIR_DEFAULT_SEMANTIC_DECISION_POLICY_IDS.get(
        normalized_pair, ""
    )
    if not resolved_policy_id:
        raise ValueError(f"No semantic decision policy configured for pair {normalized_pair!r}.")
    policy = PRODUCTION_SEMANTIC_DECISION_POLICIES.get(resolved_policy_id)
    if policy is None:
        raise ValueError(f"Unknown semantic decision policy {resolved_policy_id!r}.")
    if str(policy.pair or "").strip().lower() != normalized_pair:
        raise ValueError(
            f"Semantic decision policy {resolved_policy_id!r} does not match pair "
            f"{normalized_pair!r}."
        )
    return policy


def resolve_runtime_fallback_decision(fallback_policy: str) -> str:
    normalized = str(fallback_policy or "").strip() or DEFAULT_RUNTIME_SEMANTIC_FALLBACK_POLICY
    if normalized not in RUNTIME_SEMANTIC_FALLBACK_POLICIES:
        raise ValueError(
            f"Unsupported runtime semantic fallback policy: {normalized!r}; "
            f"expected one of {RUNTIME_SEMANTIC_FALLBACK_POLICIES!r}"
        )
    if normalized == "legacy_on_unavailable":
        return "replace"
    if normalized == "soft_affordance_on_unavailable":
        return "soft_affordance"
    return "abstain"


def _resolve_inventory_default_decision_policy_id(
    *,
    pair: str,
    inventory: Mapping[str, object] | None,
) -> str | None:
    normalized_pair = str(pair or "").strip().lower()
    capability = inventory.get("capability") if isinstance(inventory, Mapping) else None
    if not isinstance(capability, Mapping):
        return None
    competition_mode = str(capability.get("competition_mode") or "").strip()
    if normalized_pair == "en-es" and competition_mode == "active_only_anchor_cue":
        return "en_es_sentence_veto_v2"
    return None


def evaluate_runtime_semantic_match(
    *,
    match_id: str,
    sentence: str,
    source_phrase: str,
    active_sense: Mapping[str, object],
    shadow_senses: Sequence[Mapping[str, object]],
    policy: SemanticDecisionPolicyConfig,
    scorer: RuntimeSimilarityBackend,
    backup_scorer: RuntimeSimilarityBackend | None = None,
    family_id: str = "",
    family_pos_tags: Sequence[str] = (),
) -> RuntimeSemanticDecisionResult:
    resolved_active_rescue_mode = (
        str(policy.active_rescue_mode or "").strip() or DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE
    )
    if resolved_active_rescue_mode not in SENTENCE_VETO_ACTIVE_RESCUE_MODES:
        raise ValueError(
            f"Unsupported sentence-veto active rescue mode: {resolved_active_rescue_mode!r}; "
            f"expected one of {SENTENCE_VETO_ACTIVE_RESCUE_MODES!r}"
        )
    case = {
        "case_id": str(match_id or "").strip(),
        "sentence": str(sentence or "").strip(),
        "source_phrase": str(source_phrase or "").strip(),
        "gold_winner": "",
        "gold_decision": "",
    }
    primary = evaluate_runtime_veto_case(
        family_id=str(family_id or "").strip(),
        case=case,
        active_sense=active_sense,
        shadow_senses=shadow_senses,
        scorer=scorer,
        context_view=policy.context_view,
        evidence_view=policy.evidence_view,
        min_active_score=policy.min_active_score,
        min_margin=policy.min_margin,
        phrase_control_mode=policy.phrase_control_mode,
        family_pos_tags=family_pos_tags,
        window_tokens=policy.window_tokens,
        mask_token=policy.mask_token,
    )
    predicted_decision = primary.predicted_decision
    predicted_winner = primary.predicted_winner
    predicted_winner_type = primary.predicted_winner_type
    active_rescue_applied = False
    active_rescue_reason_code = ""
    backup_margin: float | None = None
    backup_predicted_decision = ""
    backup_predicted_winner = ""
    backup_evidence_view = ""
    if (
        backup_scorer is not None
        and resolved_active_rescue_mode != DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE
        and primary.predicted_decision != "replace"
        and not primary.phrase_preemption_hit
        and float(primary.margin) >= _ACTIVE_RESCUE_PRIMARY_MARGIN_FLOOR
    ):
        rescue_backup = evaluate_runtime_veto_case(
            family_id=str(family_id or "").strip(),
            case=case,
            active_sense=active_sense,
            shadow_senses=shadow_senses,
            scorer=backup_scorer,
            context_view=policy.context_view,
            evidence_view=_ACTIVE_RESCUE_BACKUP_EVIDENCE_VIEW,
            min_active_score=policy.min_active_score,
            min_margin=policy.min_margin,
            phrase_control_mode=policy.phrase_control_mode,
            family_pos_tags=family_pos_tags,
            window_tokens=policy.window_tokens,
            mask_token=policy.mask_token,
        )
        backup_margin = rescue_backup.margin
        backup_predicted_decision = rescue_backup.predicted_decision
        backup_predicted_winner = rescue_backup.predicted_winner
        backup_evidence_view = _ACTIVE_RESCUE_BACKUP_EVIDENCE_VIEW
        if (
            rescue_backup.predicted_decision == "replace"
            and rescue_backup.predicted_winner_type == "active"
            and float(rescue_backup.margin) >= _ACTIVE_RESCUE_BACKUP_MARGIN_FLOOR
        ):
            predicted_decision = "replace"
            predicted_winner = rescue_backup.predicted_winner
            predicted_winner_type = rescue_backup.predicted_winner_type
            active_rescue_applied = True
            active_rescue_reason_code = "sense_label_near_tie_active_rescue"

    reason_codes = _derive_policy_reason_codes(
        predicted_decision=predicted_decision,
        predicted_winner_type=predicted_winner_type,
        active_score=primary.active_score,
        margin=primary.margin,
        min_active_score=policy.min_active_score,
        min_margin=policy.min_margin,
        phrase_preemption_hit=primary.phrase_preemption_hit,
        phrase_reason_code=primary.phrase_reason_code,
        active_rescue_applied=active_rescue_applied,
        active_rescue_reason_code=active_rescue_reason_code,
    )
    return RuntimeSemanticDecisionResult(
        case_id=primary.case_id,
        family_id=primary.family_id,
        predicted_decision=predicted_decision,
        predicted_winner=predicted_winner,
        predicted_winner_type=predicted_winner_type,
        active_score=primary.active_score,
        strongest_shadow_score=primary.strongest_shadow_score,
        margin=primary.margin,
        strongest_shadow_id=primary.strongest_shadow_id,
        context_text=primary.context_text,
        active_evidence_text=primary.active_evidence_text,
        strongest_shadow_evidence_text=primary.strongest_shadow_evidence_text,
        phrase_preemption_hit=primary.phrase_preemption_hit,
        matched_phrase_pattern=primary.matched_phrase_pattern,
        phrase_reason_code=primary.phrase_reason_code,
        reason_codes=reason_codes,
        active_rescue_applied=active_rescue_applied,
        active_rescue_reason_code=active_rescue_reason_code,
        active_rescue_primary_margin=primary.margin,
        active_rescue_backup_margin=backup_margin,
        active_rescue_backup_predicted_decision=backup_predicted_decision,
        active_rescue_backup_predicted_winner=backup_predicted_winner,
        active_rescue_backup_evidence_view=backup_evidence_view,
    )


def collect_runtime_policy_fit_texts(
    *,
    matches: Sequence[Mapping[str, object]],
    inventory: Mapping[str, object],
    policy: SemanticDecisionPolicyConfig,
) -> list[str]:
    senses = inventory.get("senses")
    if not isinstance(senses, Mapping):
        senses = {}
    competition_sets = inventory.get("competition_sets")
    if not isinstance(competition_sets, Mapping):
        competition_sets = {}
    texts: list[str] = []
    for raw_match in matches:
        if not isinstance(raw_match, Mapping):
            continue
        semantic_admission = raw_match.get("semantic_admission")
        if not isinstance(semantic_admission, Mapping):
            continue
        if str(semantic_admission.get("status") or "").strip() != "ready":
            continue
        sense_id = str(semantic_admission.get("sense_id") or "").strip()
        competition_set_id = str(semantic_admission.get("competition_set_id") or "").strip()
        active_sense = senses.get(sense_id)
        competition_set = competition_sets.get(competition_set_id)
        if not isinstance(active_sense, Mapping) or not isinstance(competition_set, Mapping):
            continue
        if str(competition_set.get("status") or "").strip() != "ready":
            continue
        shadow_sense_ids = competition_set.get("shadow_sense_ids")
        if not isinstance(shadow_sense_ids, Sequence) or isinstance(shadow_sense_ids, (str, bytes)):
            continue
        shadow_senses = [
            dict(sense)
            for shadow_sense_id in shadow_sense_ids
            for sense in (senses.get(str(shadow_sense_id or "").strip()),)
            if isinstance(sense, Mapping)
        ]
        selection_mode = str(competition_set.get("selection_mode") or "").strip()
        if not shadow_senses and selection_mode != "active_only":
            continue
        sentence = str(raw_match.get("context_text") or "").strip()
        source_phrase = str(raw_match.get("source_phrase") or "").strip()
        if not sentence or not source_phrase:
            continue
        context_views = build_runtime_context_views(
            sentence,
            source_phrase=source_phrase,
            mask_token=policy.mask_token,
            window_tokens=policy.window_tokens,
        )
        texts.append(str(context_views.get(policy.context_view) or "").strip())
        texts.append(
            resolve_runtime_evidence_text(active_sense, evidence_view=policy.evidence_view)
        )
        for shadow_sense in shadow_senses:
            texts.append(
                resolve_runtime_evidence_text(shadow_sense, evidence_view=policy.evidence_view)
            )
        if policy.active_rescue_mode != DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE:
            texts.append(
                resolve_runtime_evidence_text(
                    active_sense,
                    evidence_view=_ACTIVE_RESCUE_BACKUP_EVIDENCE_VIEW,
                )
            )
            for shadow_sense in shadow_senses:
                texts.append(
                    resolve_runtime_evidence_text(
                        shadow_sense,
                        evidence_view=_ACTIVE_RESCUE_BACKUP_EVIDENCE_VIEW,
                    )
                )
    return [text for text in texts if str(text or "").strip()]


def build_semantic_admit_batch_response(
    *,
    pair: str,
    profile_id: str,
    matches: Sequence[Mapping[str, object]],
    inventory: Mapping[str, object] | None,
    fallback_policy: str = DEFAULT_RUNTIME_SEMANTIC_FALLBACK_POLICY,
    decision_policy_id: str | None = None,
    backend_factory: Callable[..., RuntimeSimilarityBackend] = RuntimeSimilarityBackend,
) -> dict[str, object]:
    normalized_pair = str(pair or "").strip().lower()
    normalized_profile_id = str(profile_id or "").strip() or "default"
    resolved_fallback_policy = (
        str(fallback_policy or "").strip() or DEFAULT_RUNTIME_SEMANTIC_FALLBACK_POLICY
    )
    fallback_decision = resolve_runtime_fallback_decision(resolved_fallback_policy)
    resolved_decision_policy_id = str(decision_policy_id or "").strip()
    if not resolved_decision_policy_id:
        resolved_decision_policy_id = (
            _resolve_inventory_default_decision_policy_id(
                pair=normalized_pair,
                inventory=inventory,
            )
            or ""
        )
    policy = resolve_semantic_decision_policy(
        pair=normalized_pair,
        decision_policy_id=resolved_decision_policy_id or None,
    )
    prepared_matches: list[dict[str, object]] = []
    inventory_reason_code = _validate_inventory_for_pair(
        inventory,
        pair=normalized_pair,
        profile_id=normalized_profile_id,
    )
    if inventory_reason_code:
        prepared_matches = [
            {
                "mode": "fallback",
                "decision_record": _build_fallback_decision_record(
                    match=raw_match,
                    fallback_decision=fallback_decision,
                    reason_codes=(inventory_reason_code,),
                ),
            }
            for raw_match in matches
        ]
    else:
        for raw_match in matches:
            prepared_matches.append(
                _prepare_runtime_policy_match(
                    match=raw_match,
                    inventory=inventory or {},
                    fallback_decision=fallback_decision,
                )
            )

    policy_error_reason: str | None = None
    primary_backend = None
    backup_backend = None
    policy_ready_matches = [item for item in prepared_matches if item.get("mode") == "policy"]
    if policy_ready_matches:
        try:
            primary_backend = backend_factory(
                scorer_id=policy.scorer_id,
                model_name=policy.model_name,
            )
            primary_backend.fit(
                collect_runtime_policy_fit_texts(
                    matches=[item["raw_match"] for item in policy_ready_matches],
                    inventory=inventory or {},
                    policy=policy,
                )
            )
            if policy.active_rescue_mode != DEFAULT_SENTENCE_VETO_ACTIVE_RESCUE_MODE:
                backup_backend = backend_factory(
                    scorer_id=policy.scorer_id,
                    model_name=policy.model_name,
                )
                backup_backend.fit(
                    collect_runtime_policy_fit_texts(
                        matches=[item["raw_match"] for item in policy_ready_matches],
                        inventory=inventory or {},
                        policy=SemanticDecisionPolicyConfig(
                            **{
                                **policy.__dict__,
                                "evidence_view": _ACTIVE_RESCUE_BACKUP_EVIDENCE_VIEW,
                            }
                        ),
                    )
                )
        except Exception:
            policy_error_reason = "decision_policy_error"

    decisions: list[dict[str, object]] = []
    for item in prepared_matches:
        if item.get("mode") == "fallback":
            decisions.append(dict(item["decision_record"]))
            continue
        if primary_backend is None or policy_error_reason is not None:
            decisions.append(
                _build_fallback_decision_record(
                    match=item["raw_match"],
                    fallback_decision=fallback_decision,
                    reason_codes=(str(policy_error_reason or "decision_policy_error"),),
                    selection_policy_version=str(item.get("selection_policy_version") or ""),
                    semantic_admission=item.get("semantic_admission"),
                )
            )
            continue
        result = evaluate_runtime_semantic_match(
            match_id=str(item["match_id"]),
            sentence=str(item["sentence"]),
            source_phrase=str(item["source_phrase"]),
            active_sense=item["active_sense"],
            shadow_senses=item["shadow_senses"],
            policy=policy,
            scorer=primary_backend,
            backup_scorer=backup_backend,
            family_id=str(item.get("trigger_id") or ""),
            family_pos_tags=item["family_pos_tags"],
        )
        decisions.append(
            {
                "match_id": item["match_id"],
                "decision": result.predicted_decision,
                "decision_source": "policy",
                "reason_codes": list(result.reason_codes),
                "trigger_id": str(item.get("trigger_id") or ""),
                "sense_id": str(item.get("sense_id") or ""),
                "competition_set_id": str(item.get("competition_set_id") or ""),
                "phrase_set_id": str(item.get("phrase_set_id") or ""),
                "selection_policy_version": str(item.get("selection_policy_version") or ""),
                "context_view_id": policy.context_view,
                "active_score": float(result.active_score),
                "top_shadow_score": float(result.strongest_shadow_score),
                "score_margin": float(result.margin),
                "shadow_winner_sense_id": str(result.strongest_shadow_id or ""),
                "phrase_preempted": bool(result.phrase_preemption_hit),
            }
        )
    return {
        "schema_version": 1,
        "pair": normalized_pair,
        "profile_id": normalized_profile_id,
        "decision_policy_id": policy.policy_id,
        "fallback_policy": resolved_fallback_policy,
        "decisions": decisions,
    }


def _prepare_runtime_policy_match(
    *,
    match: Mapping[str, object],
    inventory: Mapping[str, object],
    fallback_decision: str,
) -> dict[str, object]:
    semantic_admission = match.get("semantic_admission")
    if not isinstance(semantic_admission, Mapping):
        return {
            "mode": "fallback",
            "decision_record": _build_fallback_decision_record(
                match=match,
                fallback_decision=fallback_decision,
                reason_codes=("semantic_admission_missing",),
            ),
        }
    status = str(semantic_admission.get("status") or "").strip()
    if status != "ready":
        fallback_reasons = [f"semantic_status_{status or 'missing'}"]
        reason_code = str(semantic_admission.get("reason_code") or "").strip()
        if reason_code:
            fallback_reasons.append(reason_code)
        return {
            "mode": "fallback",
            "decision_record": _build_fallback_decision_record(
                match=match,
                fallback_decision=fallback_decision,
                reason_codes=tuple(fallback_reasons),
                semantic_admission=semantic_admission,
            ),
        }
    senses = inventory.get("senses")
    if not isinstance(senses, Mapping):
        senses = {}
    competition_sets = inventory.get("competition_sets")
    if not isinstance(competition_sets, Mapping):
        competition_sets = {}
    sense_id = str(semantic_admission.get("sense_id") or "").strip()
    competition_set_id = str(semantic_admission.get("competition_set_id") or "").strip()
    if not sense_id or not competition_set_id:
        return {
            "mode": "fallback",
            "decision_record": _build_fallback_decision_record(
                match=match,
                fallback_decision=fallback_decision,
                reason_codes=("semantic_admission_incomplete",),
                semantic_admission=semantic_admission,
            ),
        }
    active_sense = senses.get(sense_id)
    if not isinstance(active_sense, Mapping):
        return {
            "mode": "fallback",
            "decision_record": _build_fallback_decision_record(
                match=match,
                fallback_decision=fallback_decision,
                reason_codes=("active_sense_missing",),
                semantic_admission=semantic_admission,
            ),
        }
    competition_set = competition_sets.get(competition_set_id)
    if not isinstance(competition_set, Mapping):
        return {
            "mode": "fallback",
            "decision_record": _build_fallback_decision_record(
                match=match,
                fallback_decision=fallback_decision,
                reason_codes=("competition_set_missing",),
                semantic_admission=semantic_admission,
            ),
        }
    if str(competition_set.get("status") or "").strip() != "ready":
        fallback_reasons = ["competition_set_unavailable"]
        competition_reason = str(competition_set.get("reason_code") or "").strip()
        if competition_reason:
            fallback_reasons.append(competition_reason)
        return {
            "mode": "fallback",
            "decision_record": _build_fallback_decision_record(
                match=match,
                fallback_decision=fallback_decision,
                reason_codes=tuple(fallback_reasons),
                semantic_admission=semantic_admission,
            ),
        }
    shadow_sense_ids = competition_set.get("shadow_sense_ids")
    if not isinstance(shadow_sense_ids, Sequence) or isinstance(shadow_sense_ids, (str, bytes)):
        shadow_sense_ids = ()
    shadow_senses = [
        dict(sense)
        for shadow_sense_id in shadow_sense_ids
        for sense in (senses.get(str(shadow_sense_id or "").strip()),)
        if isinstance(sense, Mapping) and str(sense.get("status") or "ready").strip() == "ready"
    ]
    selection_mode = str(competition_set.get("selection_mode") or "").strip()
    active_only_competition = selection_mode == "active_only"
    if not shadow_senses and not active_only_competition:
        return {
            "mode": "fallback",
            "decision_record": _build_fallback_decision_record(
                match=match,
                fallback_decision=fallback_decision,
                reason_codes=("shadow_senses_missing",),
                semantic_admission=semantic_admission,
                selection_policy_version=str(competition_set.get("selection_policy_version") or ""),
            ),
        }
    sentence = str(match.get("context_text") or "").strip()
    source_phrase = str(match.get("source_phrase") or "").strip()
    if not sentence or not source_phrase:
        return {
            "mode": "fallback",
            "decision_record": _build_fallback_decision_record(
                match=match,
                fallback_decision=fallback_decision,
                reason_codes=("context_or_source_phrase_missing",),
                semantic_admission=semantic_admission,
                selection_policy_version=str(competition_set.get("selection_policy_version") or ""),
            ),
        }
    family_pos_tags = tuple(
        {
            str(value or "").strip()
            for value in (
                active_sense.get("canonical_pos"),
                *(shadow.get("canonical_pos") for shadow in shadow_senses),
            )
            if str(value or "").strip()
        }
    )
    return {
        "mode": "policy",
        "raw_match": match,
        "match_id": str(match.get("match_id") or "").strip(),
        "sentence": sentence,
        "source_phrase": source_phrase,
        "semantic_admission": semantic_admission,
        "trigger_id": str(semantic_admission.get("trigger_id") or "").strip(),
        "sense_id": sense_id,
        "competition_set_id": competition_set_id,
        "phrase_set_id": str(semantic_admission.get("phrase_set_id") or "").strip(),
        "selection_policy_version": str(
            competition_set.get("selection_policy_version") or ""
        ).strip(),
        "active_sense": dict(active_sense),
        "shadow_senses": shadow_senses,
        "family_pos_tags": family_pos_tags,
    }


def _validate_inventory_for_pair(
    inventory: Mapping[str, object] | None,
    *,
    pair: str,
    profile_id: str,
) -> str:
    if not isinstance(inventory, Mapping):
        return "semantic_inventory_missing"
    inventory_pair = str(inventory.get("pair") or "").strip().lower()
    if inventory_pair and inventory_pair != pair:
        return "semantic_inventory_pair_mismatch"
    inventory_profile_id = str(inventory.get("profile_id") or "").strip()
    if inventory_profile_id and inventory_profile_id != profile_id:
        return "semantic_inventory_profile_mismatch"
    return ""


def _build_fallback_decision_record(
    *,
    match: Mapping[str, object],
    fallback_decision: str,
    reason_codes: Sequence[str],
    semantic_admission: Mapping[str, object] | None = None,
    selection_policy_version: str = "",
) -> dict[str, object]:
    admission = (
        semantic_admission
        if isinstance(semantic_admission, Mapping)
        else (
            match.get("semantic_admission")
            if isinstance(match.get("semantic_admission"), Mapping)
            else {}
        )
    )
    normalized_reason_codes = [
        code for code in (str(code or "").strip() for code in reason_codes) if code
    ]
    if not normalized_reason_codes:
        normalized_reason_codes = ["fallback_policy"]
    return {
        "match_id": str(match.get("match_id") or "").strip(),
        "decision": fallback_decision,
        "decision_source": "fallback_policy",
        "reason_codes": normalized_reason_codes,
        "trigger_id": str(admission.get("trigger_id") or "").strip(),
        "sense_id": str(admission.get("sense_id") or "").strip(),
        "competition_set_id": str(admission.get("competition_set_id") or "").strip(),
        "phrase_set_id": str(admission.get("phrase_set_id") or "").strip(),
        "selection_policy_version": str(selection_policy_version or "").strip(),
    }


def _derive_policy_reason_codes(
    *,
    predicted_decision: str,
    predicted_winner_type: str,
    active_score: float,
    margin: float,
    min_active_score: float,
    min_margin: float,
    phrase_preemption_hit: bool,
    phrase_reason_code: str,
    active_rescue_applied: bool,
    active_rescue_reason_code: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if phrase_preemption_hit:
        reason_codes.append("phrase_preemption")
        if str(phrase_reason_code or "").strip():
            reason_codes.append(str(phrase_reason_code).strip())
        return tuple(reason_codes)
    if active_rescue_applied:
        reason_codes.append("active_rescue_applied")
        if str(active_rescue_reason_code or "").strip():
            reason_codes.append(str(active_rescue_reason_code).strip())
        return tuple(reason_codes)
    if predicted_decision == "replace":
        reason_codes.append("active_margin_clear")
        return tuple(reason_codes)
    if float(active_score) < float(min_active_score):
        reason_codes.append("active_score_below_floor")
    if float(margin) < float(min_margin):
        reason_codes.append("active_margin_below_floor")
    if predicted_winner_type == "shadow":
        reason_codes.append("shadow_winner")
    if not reason_codes:
        reason_codes.append("policy_abstain")
    return tuple(reason_codes)
