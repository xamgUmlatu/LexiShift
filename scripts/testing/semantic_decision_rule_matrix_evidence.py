#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: F405

from semantic_decision_rule_matrix_common import *  # noqa: F403
from semantic_decision_rule_matrix_context import *  # noqa: F403


def _score_sense(
    *,
    context_text: str,
    selector_context_text: str,
    sense: Mapping[str, object],
    winner_type: str,
    backend: RuntimeSimilarityBackend,
    config: Mapping[str, object],
    drop_source_families: Sequence[str],
) -> SenseScore:
    rows = _evidence_rows_for_sense(sense, config=config)
    dropped = {
        str(value or "").strip() for value in drop_source_families if str(value or "").strip()
    }
    if dropped:
        rows = [row for row in rows if row.source_family not in dropped]
    row_scores: list[dict[str, object]] = []
    for row in rows:
        selector_text = str(row.selector_text or row.text).strip()
        row_scores.append(
            {
                "row_id": row.row_id,
                "source_family": row.source_family,
                "text": row.text,
                "selector_text": selector_text,
                "weight": row.weight,
                "score": _round_float(backend.similarity(context_text, row.text)),
                "selection_score": _round_float(
                    backend.similarity(selector_context_text, selector_text)
                ),
            }
        )
    aggregate = _aggregate_row_scores(
        row_scores,
        aggregation_rule=str(config.get("aggregation_rule") or "single_concatenated_text"),
        top_k=int(config.get("top_k") or 2),
        selection_top_k=int(config.get("selection_top_k") or config.get("top_k") or 2),
    )
    return SenseScore(
        sense_id=str(sense.get("sense_id") or "").strip(),
        target_lemma=str(sense.get("target_lemma") or "").strip(),
        winner_type=winner_type,
        aggregate_score=aggregate,
        row_scores=tuple(row_scores),
    )


def _evidence_rows_for_sense(
    sense: Mapping[str, object],
    *,
    config: Mapping[str, object],
) -> list[EvidenceRow]:
    representation = str(config.get("sense_representation") or "all_evidence_text").strip()
    if str(config.get("evidence_control") or "") == "target_lemma_only":
        representation = "target_lemma_only"
    source_weights = _source_weights(config)
    evidence_views = sense.get("evidence_views")
    if not isinstance(evidence_views, Mapping):
        evidence_views = {}
    sense_id = str(sense.get("sense_id") or "sense").strip()

    def row(
        row_id: str,
        source_family: str,
        text: object,
        *,
        selector_text: object = "",
    ) -> EvidenceRow | None:
        normalized = str(text or "").strip()
        if not normalized:
            return None
        normalized_selector = str(selector_text or "").strip()
        return EvidenceRow(
            row_id=f"{sense_id}:{row_id}",
            source_family=source_family,
            text=normalized,
            weight=float(source_weights.get(source_family, 1.0)),
            selector_text=normalized_selector,
        )

    if representation in {"all_evidence_text", "current_concatenated"}:
        return _dedupe_rows(
            (row("all_evidence_text", "all_evidence", evidence_views.get("all_evidence_text")),)
        )
    if representation in {"sense_label", "gloss_text", "sense_gloss_bundle", "qualifier_text"}:
        source_family = {
            "sense_label": "sense_label",
            "gloss_text": "definition",
            "sense_gloss_bundle": "all_evidence",
            "qualifier_text": "qualifier",
        }[representation]
        return _dedupe_rows(
            (row(representation, source_family, evidence_views.get(representation)),)
        )
    if representation == "target_lemma_only":
        return _dedupe_rows((row("target_lemma", "target_lemma", sense.get("target_lemma")),))
    if representation == "definition_and_example_rows_separate":
        split_rows: list[EvidenceRow | None] = [
            row("sense_label", "sense_label", evidence_views.get("sense_label")),
            row("gloss_text", "definition", evidence_views.get("gloss_text")),
            row("qualifier_text", "qualifier", evidence_views.get("qualifier_text")),
        ]
        for index, part in enumerate(
            _split_evidence_parts(evidence_views.get("all_evidence_text"))
        ):
            split_rows.append(row(f"all_evidence_part_{index + 1}", "auxiliary", part))
        return _dedupe_rows(split_rows)
    if representation in {
        "definition_example_plus_source_rows_separate",
        "contextualized_definition_example_plus_source_rows",
    }:
        split_rows = [
            row("sense_label", "sense_label", evidence_views.get("sense_label")),
            row("gloss_text", "definition", evidence_views.get("gloss_text")),
            row("qualifier_text", "qualifier", evidence_views.get("qualifier_text")),
        ]
        for index, part in enumerate(
            _split_evidence_parts(evidence_views.get("all_evidence_text"))
        ):
            split_rows.append(row(f"all_evidence_part_{index + 1}", "auxiliary", part))
        split_rows.extend(_source_evidence_rows_for_sense(sense, config=config, row_factory=row))
        return _dedupe_rows(split_rows)
    if representation in {
        "source_rows_separate",
        "source_plus_definition_rows_separate",
        "contextualized_source_rows",
        "contextualized_source_plus_definition_rows",
    }:
        source_rows = _source_evidence_rows_for_sense(sense, config=config, row_factory=row)
        if representation in {"source_rows_separate", "contextualized_source_rows"}:
            return _dedupe_rows(source_rows)
        split_rows = [
            row("sense_label", "sense_label", evidence_views.get("sense_label")),
            row("gloss_text", "definition", evidence_views.get("gloss_text")),
            row("qualifier_text", "qualifier", evidence_views.get("qualifier_text")),
            *source_rows,
        ]
        return _dedupe_rows(split_rows)
    if representation == "ordered_evidence_phrase":
        return _dedupe_rows(
            (
                row(
                    "ordered_evidence_phrase",
                    "ordered_evidence",
                    _ordered_evidence_text(evidence_views, sense=sense),
                ),
            )
        )
    if representation == "canonical_template_evidence":
        return _dedupe_rows(
            (
                row(
                    "canonical_template_evidence",
                    "canonical_template",
                    _canonical_template_evidence_text(evidence_views, sense=sense),
                ),
            )
        )
    if representation == "paraphrase_variant_evidence":
        return _dedupe_rows(
            tuple(
                row(f"paraphrase_variant_{index + 1}", "paraphrase_variant", text)
                for index, text in enumerate(_paraphrase_variant_texts(evidence_views, sense=sense))
            )
        )
    if representation == "shuffled_evidence_tokens":
        base_text = str(evidence_views.get("all_evidence_text") or "").strip()
        return _dedupe_rows(
            (
                row(
                    "shuffled_evidence_tokens",
                    "shuffled_evidence",
                    _deterministic_shuffle_text(
                        _tokenize_experiment_text(base_text),
                        seed=sense_id,
                    ),
                ),
            )
        )
    if representation == "reversed_evidence_tokens":
        base_text = str(evidence_views.get("all_evidence_text") or "").strip()
        return _dedupe_rows(
            (
                row(
                    "reversed_evidence_tokens",
                    "reversed_evidence",
                    " ".join(reversed(_tokenize_experiment_text(base_text))),
                ),
            )
        )
    raise ValueError(f"Unsupported sense representation: {representation!r}")


def _source_evidence_rows_for_sense(
    sense: Mapping[str, object],
    *,
    config: Mapping[str, object],
    row_factory,
) -> list[EvidenceRow | None]:
    source_rows = sense.get("matrix_source_rows")
    if not isinstance(source_rows, Sequence) or isinstance(source_rows, (str, bytes)):
        return []
    source_selector_view = str(
        config.get("evidence_selector_source_view")
        or config.get("evidence_selector_context_view")
        or config.get("context_view")
        or "masked_sentence"
    ).strip()
    rows: list[EvidenceRow | None] = []
    for index, source_row in enumerate(source_rows, start=1):
        if not isinstance(source_row, Mapping):
            continue
        text = str(source_row.get("evidence_text") or source_row.get("text") or "").strip()
        if not text:
            continue
        selector_views = source_row.get("selector_views")
        selector_text = ""
        if isinstance(selector_views, Mapping):
            selector_text = str(
                selector_views.get(source_selector_view)
                or selector_views.get("masked_sentence")
                or selector_views.get("raw_sentence")
                or ""
            ).strip()
        source_family = str(source_row.get("source_family") or "source_row").strip()
        row_id = str(source_row.get("row_id") or f"source_row_{index}").strip()
        rows.append(
            row_factory(
                f"source_row_{index}:{row_id}",
                source_family,
                text,
                selector_text=selector_text,
            )
        )
    return rows


def _aggregate_row_scores(
    row_scores: Sequence[Mapping[str, object]],
    *,
    aggregation_rule: str,
    top_k: int,
    selection_top_k: int,
) -> float:
    scores = [float(row.get("score") or 0.0) for row in row_scores]
    if not scores:
        return 0.0
    if aggregation_rule == "single_concatenated_text":
        return scores[0] if len(scores) == 1 else sum(scores) / len(scores)
    if aggregation_rule == "max_row_score":
        return max(scores)
    if aggregation_rule == "mean_row_score":
        return sum(scores) / len(scores)
    if aggregation_rule == "top_k_mean":
        selected = sorted(scores, reverse=True)[: max(1, top_k)]
        return sum(selected) / len(selected)
    if aggregation_rule == "source_weighted_top_k":
        return _source_weighted_top_k_score(row_scores, top_k=top_k)
    if aggregation_rule == "context_selected_max_row_score":
        selected_rows = _select_rows_by_context(row_scores, selection_top_k=selection_top_k)
        return max(float(row.get("score") or 0.0) for row in selected_rows)
    if aggregation_rule == "context_selected_top_k_mean":
        selected_rows = _select_rows_by_context(row_scores, selection_top_k=selection_top_k)
        selected_scores = sorted(
            (float(row.get("score") or 0.0) for row in selected_rows),
            reverse=True,
        )[: max(1, top_k)]
        return sum(selected_scores) / len(selected_scores)
    if aggregation_rule == "context_selected_source_weighted_top_k":
        selected_rows = _select_rows_by_context(row_scores, selection_top_k=selection_top_k)
        return _source_weighted_top_k_score(selected_rows, top_k=top_k)
    if aggregation_rule == "definition_example_agreement":
        by_family: dict[str, list[float]] = defaultdict(list)
        for row in row_scores:
            by_family[str(row.get("source_family") or "")].append(float(row.get("score") or 0.0))
        definition_score = max(by_family.get("definition", [0.0]))
        support_scores = [
            score
            for family, family_scores in by_family.items()
            if family != "definition"
            for score in family_scores
        ]
        support_score = max(support_scores) if support_scores else definition_score
        return min(definition_score, support_score)
    raise ValueError(f"Unsupported aggregation rule: {aggregation_rule!r}")


def _select_rows_by_context(
    row_scores: Sequence[Mapping[str, object]],
    *,
    selection_top_k: int,
) -> list[Mapping[str, object]]:
    selected = sorted(
        row_scores,
        key=lambda row: (
            float(row.get("selection_score") or 0.0),
            float(row.get("score") or 0.0),
            str(row.get("row_id") or ""),
        ),
        reverse=True,
    )[: max(1, selection_top_k)]
    return list(selected or row_scores[:1])


def _source_weighted_top_k_score(
    row_scores: Sequence[Mapping[str, object]],
    *,
    top_k: int,
) -> float:
    selected_rows = sorted(
        row_scores,
        key=lambda row: float(row.get("score") or 0.0),
        reverse=True,
    )[: max(1, top_k)]
    denominator = sum(max(0.0, float(row.get("weight") or 0.0)) for row in selected_rows)
    if denominator <= 0:
        return 0.0
    return (
        sum(
            float(row.get("score") or 0.0) * max(0.0, float(row.get("weight") or 0.0))
            for row in selected_rows
        )
        / denominator
    )


def _apply_decision_rule(
    *,
    active_score: SenseScore,
    shadow_scores: Sequence[SenseScore],
    config: Mapping[str, object],
    phrase_hit: bool,
    phrase_reason_code: str,
) -> dict[str, object]:
    phrase_handling = str(config.get("phrase_handling") or "semantic_only").strip()
    shadow_candidates = list(shadow_scores)
    if phrase_handling == "phrase_as_shadow" and phrase_hit:
        phrase_score = float(config.get("phrase_shadow_score") or 1.0)
        shadow_candidates.append(
            SenseScore(
                sense_id="phrase_control",
                target_lemma="phrase_control",
                winner_type="phrase",
                aggregate_score=phrase_score,
                row_scores=(
                    {
                        "row_id": "phrase_control",
                        "source_family": "phrase_control",
                        "text": phrase_reason_code,
                        "weight": 1.0,
                        "score": _round_float(phrase_score),
                    },
                ),
            )
        )

    strongest_shadow = _strongest_shadow(shadow_candidates)
    strongest_shadow_score = strongest_shadow.aggregate_score if strongest_shadow else 0.0
    margin = float(active_score.aggregate_score) - float(strongest_shadow_score)
    ratio = _active_ratio(
        active_score.aggregate_score, strongest_shadow_score, bool(shadow_candidates)
    )
    probability = _active_softmax_probability(
        active_score.aggregate_score,
        [score.aggregate_score for score in shadow_candidates],
        temperature=float(config.get("softmax_temperature") or 8.0),
    )
    pairwise_win_rate = _pairwise_win_rate(
        active_score.aggregate_score,
        [score.aggregate_score for score in shadow_candidates],
        min_margin=float(config.get("min_margin") or 0.0),
    )

    predicted_winner = active_score.sense_id
    predicted_winner_type = "active"
    if strongest_shadow and strongest_shadow.aggregate_score > active_score.aggregate_score:
        predicted_winner = strongest_shadow.sense_id
        predicted_winner_type = strongest_shadow.winner_type

    reason_codes: list[str] = []
    if phrase_handling == "phrase_first" and phrase_hit:
        return {
            "predicted_decision": "abstain",
            "predicted_winner": "phrase_control",
            "predicted_winner_type": "phrase",
            "strongest_shadow_score": strongest_shadow_score,
            "strongest_shadow_id": strongest_shadow.sense_id if strongest_shadow else "",
            "margin": margin,
            "active_ratio": ratio,
            "active_softmax_probability": probability,
            "pairwise_win_rate": pairwise_win_rate,
            "replacement_confidence": _replacement_confidence(
                decision_rule=str(config.get("decision_rule") or "active_minus_strongest_shadow"),
                margin=margin,
                ratio=ratio,
                probability=probability,
                pairwise_win_rate=pairwise_win_rate,
                strongest_shadow_score=strongest_shadow_score,
            ),
            "reason_codes": ("phrase_first_preemption", phrase_reason_code),
        }

    predicted_decision = _semantic_decision(
        decision_rule=str(config.get("decision_rule") or "active_minus_strongest_shadow"),
        active_score=float(active_score.aggregate_score),
        strongest_shadow_score=float(strongest_shadow_score),
        shadow_scores=[score.aggregate_score for score in shadow_candidates],
        min_active_score=float(config.get("min_active_score") or 0.0),
        min_margin=float(config.get("min_margin") or 0.0),
        ratio_threshold=float(config.get("ratio_threshold") or 1.0),
        softmax_threshold=float(config.get("softmax_threshold") or 0.5),
        active_softmax_probability=probability,
        pairwise_win_rate=pairwise_win_rate,
        pairwise_min_win_rate=float(config.get("pairwise_min_win_rate") or 0.75),
        shadow_veto_threshold=float(config.get("shadow_veto_threshold") or 0.0),
    )
    reason_codes.append(str(config.get("decision_rule") or "active_minus_strongest_shadow"))
    if phrase_handling == "phrase_override" and phrase_hit:
        predicted_decision = "abstain"
        reason_codes.extend(("phrase_override", phrase_reason_code))
    if phrase_handling == "phrase_as_shadow" and phrase_hit:
        reason_codes.extend(("phrase_as_shadow", phrase_reason_code))
    if predicted_decision != "replace" and strongest_shadow:
        predicted_winner = strongest_shadow.sense_id
        predicted_winner_type = strongest_shadow.winner_type
    return {
        "predicted_decision": predicted_decision,
        "predicted_winner": predicted_winner,
        "predicted_winner_type": predicted_winner_type,
        "strongest_shadow_score": strongest_shadow_score,
        "strongest_shadow_id": strongest_shadow.sense_id if strongest_shadow else "",
        "margin": margin,
        "active_ratio": ratio,
        "active_softmax_probability": probability,
        "pairwise_win_rate": pairwise_win_rate,
        "replacement_confidence": _replacement_confidence(
            decision_rule=str(config.get("decision_rule") or "active_minus_strongest_shadow"),
            margin=margin,
            ratio=ratio,
            probability=probability,
            pairwise_win_rate=pairwise_win_rate,
            strongest_shadow_score=strongest_shadow_score,
        ),
        "reason_codes": tuple(code for code in reason_codes if code),
    }


def _semantic_decision(
    *,
    decision_rule: str,
    active_score: float,
    strongest_shadow_score: float,
    shadow_scores: Sequence[float],
    min_active_score: float,
    min_margin: float,
    ratio_threshold: float,
    softmax_threshold: float,
    active_softmax_probability: float,
    pairwise_win_rate: float,
    pairwise_min_win_rate: float,
    shadow_veto_threshold: float,
) -> str:
    if decision_rule == "shadow_veto_only":
        return "abstain" if strongest_shadow_score >= shadow_veto_threshold else "replace"
    if active_score < min_active_score:
        return "abstain"
    if decision_rule == "active_minus_strongest_shadow":
        return "replace" if active_score - strongest_shadow_score >= min_margin else "abstain"
    if decision_rule == "active_ratio_strongest_shadow":
        ratio = _active_ratio(active_score, strongest_shadow_score, bool(shadow_scores))
        return "replace" if ratio >= ratio_threshold else "abstain"
    if decision_rule == "softmax_probability":
        return "replace" if active_softmax_probability >= softmax_threshold else "abstain"
    if decision_rule == "pairwise_active_beats_all_shadows":
        return (
            "replace"
            if all(active_score - score >= min_margin for score in shadow_scores)
            else "abstain"
        )
    if decision_rule == "pairwise_active_beats_most_shadows":
        return "replace" if pairwise_win_rate >= pairwise_min_win_rate else "abstain"
    raise ValueError(f"Unsupported decision rule: {decision_rule!r}")


def _apply_evidence_control(
    *,
    active_sense: Mapping[str, object],
    shadow_senses: Sequence[Mapping[str, object]],
    evidence_control: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    active = dict(active_sense)
    shadows = [dict(shadow) for shadow in shadow_senses]
    if evidence_control in {"normal", "target_lemma_only"}:
        return active, shadows
    if evidence_control in {"active_only_source", "no_shadow_competition"}:
        return active, []
    if evidence_control == "shadow_only_source":
        empty_active = dict(active)
        empty_active["evidence_views"] = {}
        empty_active["target_lemma"] = ""
        return empty_active, shadows
    if evidence_control == "shuffled_labels" and shadows:
        shuffled_active = dict(shadows[0])
        shuffled_shadows = [active, *shadows[1:]]
        return shuffled_active, shuffled_shadows
    return active, shadows


def _source_weights(config: Mapping[str, object]) -> dict[str, float]:
    raw = config.get("source_weights")
    weights = dict(DEFAULT_SOURCE_WEIGHTS)
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            try:
                weights[str(key)] = float(value)
            except (TypeError, ValueError):
                continue
    return weights


def _dedupe_rows(rows: Sequence[EvidenceRow | None]) -> list[EvidenceRow]:
    seen: set[str] = set()
    deduped: list[EvidenceRow] = []
    for row in rows:
        if row is None:
            continue
        key = row.text.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _split_evidence_parts(value: object) -> list[str]:
    return [part.strip() for part in str(value or "").split("|") if part.strip()]


def _ordered_evidence_text(
    evidence_views: Mapping[str, object],
    *,
    sense: Mapping[str, object],
) -> str:
    parts = _split_evidence_parts(evidence_views.get("all_evidence_text"))
    if not parts:
        parts = [
            str(evidence_views.get("sense_label") or "").strip(),
            str(evidence_views.get("gloss_text") or "").strip(),
        ]
    ordered_parts: list[str] = []
    target = str(sense.get("target_lemma") or "").strip()
    if target:
        ordered_parts.append(f"target={target}")
    for index, part in enumerate(parts, start=1):
        tokens = _tokenize_experiment_text(part)
        ordered_parts.append(f"part{index}=" + " ".join(tokens))
        ngrams = _ordered_ngram_text(tokens)
        if ngrams:
            ordered_parts.append(f"part{index}_order={ngrams}")
    return " | ".join(part for part in ordered_parts if part.strip())


def _canonical_template_evidence_text(
    evidence_views: Mapping[str, object],
    *,
    sense: Mapping[str, object],
) -> str:
    target = str(sense.get("target_lemma") or "").strip()
    label = str(evidence_views.get("sense_label") or "").strip()
    gloss = str(evidence_views.get("gloss_text") or "").strip()
    bundle = str(evidence_views.get("sense_gloss_bundle") or "").strip()
    parts = []
    if target and gloss:
        parts.append(f"{target} means {gloss}")
        parts.append(f"use {target} when the context means {gloss}")
    if target and label:
        parts.append(f"{target} is the {label} sense")
    if bundle:
        parts.append(f"sense evidence says {bundle}")
    return " | ".join(parts)


def _paraphrase_variant_texts(
    evidence_views: Mapping[str, object],
    *,
    sense: Mapping[str, object],
) -> list[str]:
    target = str(sense.get("target_lemma") or "").strip()
    label = str(evidence_views.get("sense_label") or "").strip()
    gloss = str(evidence_views.get("gloss_text") or "").strip()
    variants = []
    if gloss:
        variants.append(gloss)
        variants.append(f"this context is about {gloss}")
    if label:
        variants.append(label)
        variants.append(f"this is the {label} meaning")
    if target and gloss:
        variants.append(f"{target}: {gloss}")
    return [variant for variant in variants if variant.strip()]


def _strongest_shadow(shadow_scores: Sequence[SenseScore]) -> SenseScore | None:
    if not shadow_scores:
        return None
    return sorted(
        shadow_scores,
        key=lambda score: (-float(score.aggregate_score), score.sense_id),
    )[0]


def _active_ratio(active_score: float, strongest_shadow_score: float, has_shadow: bool) -> float:
    if not has_shadow:
        return math.inf if active_score > 0 else 0.0
    if strongest_shadow_score <= 0:
        return math.inf if active_score > 0 else 0.0
    return active_score / strongest_shadow_score


def _active_softmax_probability(
    active_score: float,
    shadow_scores: Sequence[float],
    *,
    temperature: float,
) -> float:
    values = [float(active_score), *(float(score) for score in shadow_scores)]
    if not values:
        return 0.0
    scaled = [value * max(0.01, temperature) for value in values]
    max_value = max(scaled)
    exp_values = [math.exp(value - max_value) for value in scaled]
    denominator = sum(exp_values)
    return exp_values[0] / denominator if denominator > 0 else 0.0


def _pairwise_win_rate(
    active_score: float,
    shadow_scores: Sequence[float],
    *,
    min_margin: float,
) -> float:
    if not shadow_scores:
        return 1.0
    wins = sum(1 for score in shadow_scores if active_score - float(score) >= min_margin)
    return wins / len(shadow_scores)


def _replacement_confidence(
    *,
    decision_rule: str,
    margin: float,
    ratio: float,
    probability: float,
    pairwise_win_rate: float,
    strongest_shadow_score: float,
) -> float:
    if decision_rule == "active_ratio_strongest_shadow":
        return ratio
    if decision_rule == "softmax_probability":
        return probability
    if decision_rule in {"pairwise_active_beats_all_shadows", "pairwise_active_beats_most_shadows"}:
        return pairwise_win_rate
    if decision_rule == "shadow_veto_only":
        return -float(strongest_shadow_score)
    return margin


__all__ = [name for name in globals() if not name.startswith("__")]
