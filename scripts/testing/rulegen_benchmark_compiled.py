#!/usr/bin/env python3
from __future__ import annotations

import itertools
from typing import Mapping, Optional, Sequence

from lexishift_core.replacement.core import VocabRule
from lexishift_core.rulegen.benchmarking import (
    RulegenBenchmarkCase,
    RulegenBenchmarkCaseResult,
    RulegenBenchmarkObjectiveWeights,
    RulegenBenchmarkSummary,
    _extract_rule_confidence,
    _is_variant_rule,
    evaluate_benchmark_case,
    normalize_benchmark_phrase,
)
from lexishift_core.rulegen.pairs.en_es import (
    EnEsCompiledBenchmarkEvaluationTables,
    EnEsCompiledSelectedRowTable,
)

from rulegen_benchmark_models import (
    CompiledBenchmarkCaseRef,
    CompiledBenchmarkCaseResultTable,
    CompiledBenchmarkCaseTable,
    CompiledBenchmarkPhraseTable,
    CompiledBenchmarkRuleTable,
    PairBenchmarkContext,
)


def _build_compiled_case_refs(
    *,
    cases: Sequence[RulegenBenchmarkCase],
    compiled_pair_context: Optional[object],
) -> tuple[CompiledBenchmarkCaseRef, ...]:
    target_ids_by_target = getattr(compiled_pair_context, "target_ids_by_target", {})
    if not isinstance(target_ids_by_target, Mapping):
        target_ids_by_target = {}
    candidate_table = getattr(compiled_pair_context, "candidate_table", None)
    candidate_row_ids_by_target_id = getattr(
        candidate_table,
        "candidate_row_ids_by_target_id",
        {},
    )
    if not isinstance(candidate_row_ids_by_target_id, Mapping):
        candidate_row_ids_by_target_id = {}
    refs: list[CompiledBenchmarkCaseRef] = []
    for index, case in enumerate(cases):
        target_id = (
            int(target_ids_by_target[case.target]) if case.target in target_ids_by_target else None
        )
        candidate_row_ids = (
            tuple(
                int(row_id)
                for row_id in candidate_row_ids_by_target_id.get(target_id, ())
                if isinstance(row_id, int)
            )
            if target_id is not None
            else ()
        )
        refs.append(
            CompiledBenchmarkCaseRef(
                case_row_id=index,
                case_id=str(case.case_id),
                target=str(case.target),
                target_id=target_id,
                candidate_row_ids=candidate_row_ids,
            )
        )
    return tuple(refs)


def _build_compiled_case_table(
    *,
    cases: Sequence[RulegenBenchmarkCase],
    compiled_case_refs: Sequence[CompiledBenchmarkCaseRef],
) -> CompiledBenchmarkCaseTable:
    refs_by_case_id = {
        str(ref.case_id): ref for ref in compiled_case_refs if str(ref.case_id).strip()
    }
    phrase_table = _build_compiled_phrase_table(cases)
    phrase_ids_by_phrase = phrase_table.phrase_ids_by_phrase

    case_row_ids: list[int] = []
    case_ids: list[str] = []
    targets: list[str] = []
    target_ids: list[int] = []
    candidate_row_id_rows: list[tuple[int, ...]] = []
    expected_any_phrase_id_rows: list[tuple[int, ...]] = []
    expected_top1_phrase_id_rows: list[tuple[int, ...]] = []
    forbidden_top1_phrase_id_rows: list[tuple[int, ...]] = []
    forbidden_any_phrase_id_rows: list[tuple[int, ...]] = []

    for index, case in enumerate(cases):
        ref = refs_by_case_id.get(str(case.case_id))
        expected_any = _normalize_case_phrase_list(case.expected_any)
        expected_top1 = (
            _normalize_case_phrase_list(case.expected_top1_any)
            if case.expected_top1_any
            else expected_any
        )
        forbidden_top1 = _normalize_case_phrase_list(case.forbidden_top1)
        forbidden_any = _normalize_case_phrase_list(case.forbidden_any)
        case_row_ids.append(int(ref.case_row_id) if ref is not None else index)
        case_ids.append(str(case.case_id))
        targets.append(str(case.target))
        target_ids.append(
            int(ref.target_id) if ref is not None and ref.target_id is not None else -1
        )
        candidate_row_id_rows.append(
            tuple(int(row_id) for row_id in (ref.candidate_row_ids if ref is not None else ()))
        )
        expected_any_phrase_id_rows.append(
            _encode_phrase_id_row(expected_any, phrase_ids_by_phrase)
        )
        expected_top1_phrase_id_rows.append(
            _encode_phrase_id_row(expected_top1, phrase_ids_by_phrase)
        )
        forbidden_top1_phrase_id_rows.append(
            _encode_phrase_id_row(forbidden_top1, phrase_ids_by_phrase)
        )
        forbidden_any_phrase_id_rows.append(
            _encode_phrase_id_row(forbidden_any, phrase_ids_by_phrase)
        )

    return CompiledBenchmarkCaseTable(
        case_row_ids=tuple(case_row_ids),
        case_ids=tuple(case_ids),
        targets=tuple(targets),
        target_ids=tuple(target_ids),
        candidate_row_id_rows=tuple(candidate_row_id_rows),
        expected_any_phrase_id_rows=tuple(expected_any_phrase_id_rows),
        expected_top1_phrase_id_rows=tuple(expected_top1_phrase_id_rows),
        forbidden_top1_phrase_id_rows=tuple(forbidden_top1_phrase_id_rows),
        forbidden_any_phrase_id_rows=tuple(forbidden_any_phrase_id_rows),
        phrase_table=phrase_table,
    )


def _build_compiled_phrase_table(
    cases: Sequence[RulegenBenchmarkCase],
) -> CompiledBenchmarkPhraseTable:
    ordered_phrases: list[str] = []
    phrase_ids_by_phrase: dict[str, int] = {}
    for case in cases:
        expected_any = _normalize_case_phrase_list(case.expected_any)
        expected_top1 = (
            _normalize_case_phrase_list(case.expected_top1_any)
            if case.expected_top1_any
            else expected_any
        )
        for phrase in itertools.chain(
            expected_any,
            expected_top1,
            _normalize_case_phrase_list(case.forbidden_top1),
            _normalize_case_phrase_list(case.forbidden_any),
        ):
            if phrase not in phrase_ids_by_phrase:
                phrase_ids_by_phrase[phrase] = len(ordered_phrases)
                ordered_phrases.append(phrase)
    return CompiledBenchmarkPhraseTable(
        normalized_phrases=tuple(ordered_phrases),
        phrase_ids_by_phrase=dict(phrase_ids_by_phrase),
    )


def _normalize_case_phrase_list(values: Sequence[object]) -> tuple[str, ...]:
    normalized = [normalize_benchmark_phrase(value) for value in values]
    return tuple(dict.fromkeys(item for item in normalized if item))


def _encode_phrase_id_row(
    phrases: Sequence[str],
    phrase_ids_by_phrase: Mapping[str, int],
) -> tuple[int, ...]:
    return tuple(
        int(phrase_ids_by_phrase[phrase]) for phrase in phrases if phrase in phrase_ids_by_phrase
    )


def _resolve_rule_candidate_row_id(
    rule: VocabRule,
    *,
    candidate_row_id_by_candidate_id: Mapping[int, int],
) -> int:
    metadata = getattr(rule, "metadata", None)
    if metadata is None:
        return -1
    rulegen = getattr(metadata, "rulegen", None)
    if not isinstance(rulegen, Mapping):
        return -1
    candidate_id = rulegen.get("compiled_candidate_id")
    if isinstance(candidate_id, bool):
        return -1
    if isinstance(candidate_id, int):
        return int(candidate_row_id_by_candidate_id.get(int(candidate_id), -1))
    if isinstance(candidate_id, str):
        text = candidate_id.strip()
        if not text:
            return -1
        try:
            parsed = int(text)
        except ValueError:
            return -1
        return int(candidate_row_id_by_candidate_id.get(parsed, -1))
    return -1


def _build_compiled_rule_table(
    *,
    rules_by_target: Mapping[str, Sequence[VocabRule]],
    compiled_case_table: CompiledBenchmarkCaseTable,
    compiled_pair_context: Optional[object] = None,
) -> CompiledBenchmarkRuleTable:
    phrase_ids_by_phrase = compiled_case_table.phrase_table.phrase_ids_by_phrase
    candidate_table = getattr(compiled_pair_context, "candidate_table", None)
    candidate_row_id_by_candidate_id = getattr(
        candidate_table,
        "candidate_row_id_by_candidate_id",
        {},
    )
    if not isinstance(candidate_row_id_by_candidate_id, Mapping):
        candidate_row_id_by_candidate_id = {}
    ordered_targets = tuple(
        sorted(str(target) for target in rules_by_target if str(target).strip())
    )
    all_source_rows: list[tuple[str, ...]] = []
    source_phrase_id_rows: list[tuple[int, ...]] = []
    candidate_row_id_rows: list[tuple[int, ...]] = []
    top1_confidences: list[Optional[float]] = []
    variant_rule_counts: list[int] = []
    top1_variant_flags: list[bool] = []
    row_id_by_target: dict[str, int] = {}

    for row_id, target in enumerate(ordered_targets):
        rules = tuple(rules_by_target.get(target, ()))
        normalized_sources = tuple(
            source
            for source in (normalize_benchmark_phrase(rule.source_phrase) for rule in rules)
            if source
        )
        source_phrase_ids = tuple(
            int(phrase_ids_by_phrase.get(source, -1)) for source in normalized_sources
        )
        candidate_row_ids = tuple(
            _resolve_rule_candidate_row_id(
                rule,
                candidate_row_id_by_candidate_id=candidate_row_id_by_candidate_id,
            )
            for rule in rules
        )
        all_source_rows.append(normalized_sources)
        source_phrase_id_rows.append(source_phrase_ids)
        candidate_row_id_rows.append(candidate_row_ids)
        top1_confidences.append(_extract_rule_confidence(rules[0]) if rules else None)
        variant_rule_counts.append(sum(1 for rule in rules if _is_variant_rule(rule)))
        top1_variant_flags.append(bool(rules and _is_variant_rule(rules[0])))
        row_id_by_target[target] = row_id

    return CompiledBenchmarkRuleTable(
        targets=ordered_targets,
        all_source_rows=tuple(all_source_rows),
        source_phrase_id_rows=tuple(source_phrase_id_rows),
        candidate_row_id_rows=tuple(candidate_row_id_rows),
        top1_confidences=tuple(top1_confidences),
        variant_rule_counts=tuple(variant_rule_counts),
        top1_variant_flags=tuple(top1_variant_flags),
        row_id_by_target=dict(row_id_by_target),
    )


def _build_compiled_rule_table_from_rules(
    *,
    rules: Sequence[VocabRule],
    compiled_case_table: CompiledBenchmarkCaseTable,
    compiled_pair_context: Optional[object] = None,
) -> CompiledBenchmarkRuleTable:
    phrase_ids_by_phrase = compiled_case_table.phrase_table.phrase_ids_by_phrase
    candidate_table = getattr(compiled_pair_context, "candidate_table", None)
    candidate_row_id_by_candidate_id = getattr(
        candidate_table,
        "candidate_row_id_by_candidate_id",
        {},
    )
    if not isinstance(candidate_row_id_by_candidate_id, Mapping):
        candidate_row_id_by_candidate_id = {}

    target_rows: dict[str, dict[str, object]] = {}
    for rule in rules:
        target = str(rule.replacement or "").strip()
        if not target:
            continue
        row = target_rows.setdefault(
            target,
            {
                "all_sources": [],
                "source_phrase_ids": [],
                "candidate_row_ids": [],
                "top1_confidence": None,
                "variant_rule_count": 0,
                "top1_variant_flag": False,
            },
        )
        normalized_source = normalize_benchmark_phrase(rule.source_phrase)
        if normalized_source:
            cast_sources = row["all_sources"]
            cast_phrase_ids = row["source_phrase_ids"]
            assert isinstance(cast_sources, list)
            assert isinstance(cast_phrase_ids, list)
            cast_sources.append(normalized_source)
            cast_phrase_ids.append(int(phrase_ids_by_phrase.get(normalized_source, -1)))
        cast_candidate_row_ids = row["candidate_row_ids"]
        assert isinstance(cast_candidate_row_ids, list)
        cast_candidate_row_ids.append(
            _resolve_rule_candidate_row_id(
                rule,
                candidate_row_id_by_candidate_id=candidate_row_id_by_candidate_id,
            )
        )
        is_variant = _is_variant_rule(rule)
        row["variant_rule_count"] = int(row["variant_rule_count"]) + (1 if is_variant else 0)
        if row["top1_confidence"] is None:
            row["top1_confidence"] = _extract_rule_confidence(rule)
            row["top1_variant_flag"] = bool(is_variant)

    ordered_targets = tuple(sorted(target_rows))
    all_source_rows: list[tuple[str, ...]] = []
    source_phrase_id_rows: list[tuple[int, ...]] = []
    candidate_row_id_rows: list[tuple[int, ...]] = []
    top1_confidences: list[Optional[float]] = []
    variant_rule_counts: list[int] = []
    top1_variant_flags: list[bool] = []
    row_id_by_target: dict[str, int] = {}

    for row_id, target in enumerate(ordered_targets):
        row = target_rows[target]
        row_id_by_target[target] = row_id
        all_sources = row["all_sources"]
        source_phrase_ids = row["source_phrase_ids"]
        candidate_row_ids = row["candidate_row_ids"]
        assert isinstance(all_sources, list)
        assert isinstance(source_phrase_ids, list)
        assert isinstance(candidate_row_ids, list)
        all_source_rows.append(tuple(str(source) for source in all_sources))
        source_phrase_id_rows.append(tuple(int(value) for value in source_phrase_ids))
        candidate_row_id_rows.append(tuple(int(value) for value in candidate_row_ids))
        top1_confidences.append(
            float(row["top1_confidence"]) if row["top1_confidence"] is not None else None
        )
        variant_rule_counts.append(int(row["variant_rule_count"]))
        top1_variant_flags.append(bool(row["top1_variant_flag"]))

    return CompiledBenchmarkRuleTable(
        targets=ordered_targets,
        all_source_rows=tuple(all_source_rows),
        source_phrase_id_rows=tuple(source_phrase_id_rows),
        candidate_row_id_rows=tuple(candidate_row_id_rows),
        top1_confidences=tuple(top1_confidences),
        variant_rule_counts=tuple(variant_rule_counts),
        top1_variant_flags=tuple(top1_variant_flags),
        row_id_by_target=dict(row_id_by_target),
    )


def _build_compiled_rule_table_from_en_es_selected_rows(
    *,
    selected_row_table: EnEsCompiledSelectedRowTable,
    compiled_case_table: CompiledBenchmarkCaseTable,
    filter_table: Optional[EnEsCompiledBenchmarkEvaluationTables] = None,
    compiled_pair_context: Optional[object] = None,
) -> CompiledBenchmarkRuleTable:
    phrase_ids_by_phrase = compiled_case_table.phrase_table.phrase_ids_by_phrase
    all_source_rows: list[tuple[str, ...]] = []
    source_phrase_id_rows: list[tuple[int, ...]] = []
    candidate_row_id_rows: list[tuple[int, ...]] = []
    top1_confidences: list[Optional[float]] = []
    variant_rule_counts: list[int] = []
    top1_variant_flags: list[bool] = []
    row_id_by_target: dict[str, int] = {}

    for row_id, target in enumerate(selected_row_table.targets):
        selected_row_ids = tuple(
            int(candidate_row_id)
            for candidate_row_id in selected_row_table.candidate_row_id_rows[row_id]
        )
        if (
            row_id < len(selected_row_table.normalized_source_phrase_rows)
            and selected_row_table.normalized_source_phrase_rows[row_id]
        ):
            normalized_sources = tuple(
                str(source or "").strip()
                for source in selected_row_table.normalized_source_phrase_rows[row_id]
                if str(source or "").strip()
            )
        elif filter_table is not None:
            normalized_sources = tuple(
                str(
                    filter_table.filter_table.normalized_source_phrases[candidate_row_id] or ""
                ).strip()
                for candidate_row_id in selected_row_ids
                if str(
                    filter_table.filter_table.normalized_source_phrases[candidate_row_id] or ""
                ).strip()
            )
        else:
            normalized_sources = ()
        source_phrase_ids = tuple(
            int(phrase_ids_by_phrase.get(normalized_source, -1))
            for normalized_source in normalized_sources
        )
        all_source_rows.append(tuple(normalized_sources))
        source_phrase_id_rows.append(tuple(source_phrase_ids))
        candidate_row_id_rows.append(selected_row_ids)
        top1_confidences.append(selected_row_table.top1_confidences[row_id])
        variant_rule_counts.append(int(selected_row_table.variant_rule_counts[row_id]))
        top1_variant_flags.append(bool(selected_row_table.top1_variant_flags[row_id]))
        row_id_by_target[str(target)] = row_id

    return CompiledBenchmarkRuleTable(
        targets=tuple(str(target) for target in selected_row_table.targets),
        all_source_rows=tuple(all_source_rows),
        source_phrase_id_rows=tuple(source_phrase_id_rows),
        candidate_row_id_rows=tuple(candidate_row_id_rows),
        top1_confidences=tuple(top1_confidences),
        variant_rule_counts=tuple(variant_rule_counts),
        top1_variant_flags=tuple(top1_variant_flags),
        row_id_by_target=dict(row_id_by_target),
    )


def _evaluate_benchmark_case_compiled(
    *,
    case: RulegenBenchmarkCase,
    case_row_id: int,
    compiled_case_table: CompiledBenchmarkCaseTable,
    compiled_rule_table: CompiledBenchmarkRuleTable,
) -> RulegenBenchmarkCaseResult:
    result, _ = _evaluate_benchmark_case_compiled_row(
        case=case,
        case_row_id=case_row_id,
        compiled_case_table=compiled_case_table,
        compiled_rule_table=compiled_rule_table,
    )
    return result


def _evaluate_benchmark_case_compiled_payload_row(
    *,
    case: RulegenBenchmarkCase,
    case_row_id: int,
    compiled_case_table: CompiledBenchmarkCaseTable,
    compiled_rule_table: CompiledBenchmarkRuleTable,
    include_payload: bool = True,
) -> tuple[
    Optional[dict[str, object]], tuple[int, Optional[float], bool, bool, bool, bool, int, bool]
]:
    rule_row_id = compiled_rule_table.row_id_by_target.get(str(case.target), -1)
    if rule_row_id >= 0:
        all_sources = compiled_rule_table.all_source_rows[rule_row_id]
        source_phrase_ids = compiled_rule_table.source_phrase_id_rows[rule_row_id]
        top1_confidence = compiled_rule_table.top1_confidences[rule_row_id]
        variant_rule_count = compiled_rule_table.variant_rule_counts[rule_row_id]
        top1_is_variant = compiled_rule_table.top1_variant_flags[rule_row_id]
    else:
        all_sources = ()
        source_phrase_ids = ()
        top1_confidence = None
        variant_rule_count = 0
        top1_is_variant = False

    top1_source = all_sources[0] if all_sources else None
    top3_phrase_ids = tuple(source_phrase_ids[:3])
    top1_phrase_id = source_phrase_ids[0] if source_phrase_ids else -1
    expected_any_ids = frozenset(compiled_case_table.expected_any_phrase_id_rows[case_row_id])
    expected_top1_ids = frozenset(compiled_case_table.expected_top1_phrase_id_rows[case_row_id])
    forbidden_top1_ids = frozenset(compiled_case_table.forbidden_top1_phrase_id_rows[case_row_id])
    forbidden_any_ids = frozenset(compiled_case_table.forbidden_any_phrase_id_rows[case_row_id])
    top1_correct = bool(top1_source and expected_top1_ids and top1_phrase_id in expected_top1_ids)
    top3_contains_expected = bool(
        expected_any_ids and any(phrase_id in expected_any_ids for phrase_id in top3_phrase_ids)
    )
    top1_forbidden = bool(
        top1_source and forbidden_top1_ids and top1_phrase_id in forbidden_top1_ids
    )
    forbidden_any_present = bool(
        any(phrase_id >= 0 and phrase_id in forbidden_any_ids for phrase_id in source_phrase_ids)
    )

    payload: Optional[dict[str, object]]
    if include_payload:
        top3_sources = tuple(all_sources[:3])
        expected_matches = tuple(
            source
            for source, phrase_id in zip(all_sources, source_phrase_ids)
            if phrase_id >= 0 and phrase_id in expected_any_ids
        )
        forbidden_matches = tuple(
            source
            for source, phrase_id in zip(all_sources, source_phrase_ids)
            if phrase_id >= 0 and phrase_id in forbidden_any_ids
        )
        payload = {
            "case_id": case.case_id,
            "pair": case.pair,
            "target": case.target,
            "rule_count": len(all_sources),
            "top1_source": top1_source,
            "top3_sources": list(top3_sources),
            "all_sources": list(all_sources),
            "top1_confidence": top1_confidence,
            "top1_correct": bool(top1_correct),
            "top3_contains_expected": bool(top3_contains_expected),
            "top1_forbidden": bool(top1_forbidden),
            "forbidden_any_present": bool(forbidden_any_present),
            "variant_rule_count": int(variant_rule_count),
            "top1_is_variant": bool(top1_is_variant),
            "expected_matches": list(expected_matches),
            "forbidden_matches": list(forbidden_matches),
        }
    else:
        payload = None

    return (
        payload,
        (
            len(all_sources),
            top1_confidence,
            top1_correct,
            top3_contains_expected,
            top1_forbidden,
            forbidden_any_present,
            variant_rule_count,
            top1_is_variant,
        ),
    )


def _evaluate_benchmark_case_compiled_row(
    *,
    case: RulegenBenchmarkCase,
    case_row_id: int,
    compiled_case_table: CompiledBenchmarkCaseTable,
    compiled_rule_table: CompiledBenchmarkRuleTable,
) -> tuple[
    RulegenBenchmarkCaseResult, tuple[int, Optional[float], bool, bool, bool, bool, int, bool]
]:
    payload, case_row = _evaluate_benchmark_case_compiled_payload_row(
        case=case,
        case_row_id=case_row_id,
        compiled_case_table=compiled_case_table,
        compiled_rule_table=compiled_rule_table,
    )
    assert payload is not None

    result = RulegenBenchmarkCaseResult(
        case_id=str(payload["case_id"]),
        pair=str(payload["pair"]),
        target=str(payload["target"]),
        rule_count=int(payload["rule_count"]),
        top1_source=payload["top1_source"]
        if payload["top1_source"] is None
        else str(payload["top1_source"]),
        top3_sources=tuple(str(source) for source in payload["top3_sources"]),
        all_sources=tuple(str(source) for source in payload["all_sources"]),
        top1_confidence=(
            float(payload["top1_confidence"]) if payload["top1_confidence"] is not None else None
        ),
        top1_correct=bool(payload["top1_correct"]),
        top3_contains_expected=bool(payload["top3_contains_expected"]),
        top1_forbidden=bool(payload["top1_forbidden"]),
        forbidden_any_present=bool(payload["forbidden_any_present"]),
        variant_rule_count=int(payload["variant_rule_count"]),
        top1_is_variant=bool(payload["top1_is_variant"]),
        expected_matches=tuple(str(source) for source in payload["expected_matches"]),
        forbidden_matches=tuple(str(source) for source in payload["forbidden_matches"]),
    )
    return (result, case_row)


def _build_compiled_case_result_table(
    *,
    case_rows: Sequence[tuple[int, Optional[float], bool, bool, bool, bool, int, bool]],
) -> CompiledBenchmarkCaseResultTable:
    rule_counts: list[int] = []
    top1_confidences: list[Optional[float]] = []
    top1_correct_flags: list[bool] = []
    top3_contains_expected_flags: list[bool] = []
    top1_forbidden_flags: list[bool] = []
    forbidden_any_present_flags: list[bool] = []
    variant_rule_counts: list[int] = []
    top1_variant_flags: list[bool] = []
    for (
        rule_count,
        top1_confidence,
        top1_correct,
        top3_contains_expected,
        top1_forbidden,
        forbidden_any_present,
        variant_rule_count,
        top1_is_variant,
    ) in case_rows:
        rule_counts.append(int(rule_count))
        top1_confidences.append(float(top1_confidence) if top1_confidence is not None else None)
        top1_correct_flags.append(bool(top1_correct))
        top3_contains_expected_flags.append(bool(top3_contains_expected))
        top1_forbidden_flags.append(bool(top1_forbidden))
        forbidden_any_present_flags.append(bool(forbidden_any_present))
        variant_rule_counts.append(int(variant_rule_count))
        top1_variant_flags.append(bool(top1_is_variant))
    return CompiledBenchmarkCaseResultTable(
        case_row_ids=tuple(range(len(case_rows))),
        rule_counts=tuple(rule_counts),
        top1_confidences=tuple(top1_confidences),
        top1_correct_flags=tuple(top1_correct_flags),
        top3_contains_expected_flags=tuple(top3_contains_expected_flags),
        top1_forbidden_flags=tuple(top1_forbidden_flags),
        forbidden_any_present_flags=tuple(forbidden_any_present_flags),
        variant_rule_counts=tuple(variant_rule_counts),
        top1_variant_flags=tuple(top1_variant_flags),
    )


def _group_rules_by_target(rules: Sequence[VocabRule]) -> dict[str, list[VocabRule]]:
    by_target: dict[str, list[VocabRule]] = {}
    for rule in rules:
        target = str(rule.replacement or "").strip()
        if not target:
            continue
        by_target.setdefault(target, []).append(rule)
    return by_target


def _evaluate_case_results_with_table(
    *,
    context: PairBenchmarkContext,
    rules_by_target: Optional[Mapping[str, Sequence[VocabRule]]] = None,
    rules: Optional[Sequence[VocabRule]] = None,
    compiled_rule_table: Optional[CompiledBenchmarkRuleTable] = None,
) -> tuple[tuple[RulegenBenchmarkCaseResult, ...], Optional[CompiledBenchmarkCaseResultTable]]:
    compiled_case_table = context.compiled_case_table
    if compiled_case_table is None:
        resolved_rules_by_target = (
            rules_by_target if rules_by_target is not None else _group_rules_by_target(rules or ())
        )
        return (
            tuple(
                evaluate_benchmark_case(case, tuple(resolved_rules_by_target.get(case.target, ())))
                for case in context.cases
            ),
            None,
        )
    if compiled_rule_table is None and rules is not None:
        compiled_rule_table = _build_compiled_rule_table_from_rules(
            rules=rules,
            compiled_case_table=compiled_case_table,
            compiled_pair_context=context.compiled_pair_context,
        )
    elif compiled_rule_table is None:
        compiled_rule_table = _build_compiled_rule_table(
            rules_by_target=rules_by_target or {},
            compiled_case_table=compiled_case_table,
            compiled_pair_context=context.compiled_pair_context,
        )
    case_results: list[RulegenBenchmarkCaseResult] = []
    case_rows: list[tuple[int, Optional[float], bool, bool, bool, bool, int, bool]] = []
    for index, case in enumerate(context.cases):
        case_result, case_row = _evaluate_benchmark_case_compiled_row(
            case=case,
            case_row_id=index,
            compiled_case_table=compiled_case_table,
            compiled_rule_table=compiled_rule_table,
        )
        case_results.append(case_result)
        case_rows.append(case_row)
    return (
        tuple(case_results),
        _build_compiled_case_result_table(case_rows=case_rows),
    )


def _evaluate_case_payloads_with_table(
    *,
    context: PairBenchmarkContext,
    rules_by_target: Optional[Mapping[str, Sequence[VocabRule]]] = None,
    rules: Optional[Sequence[VocabRule]] = None,
    compiled_rule_table: Optional[CompiledBenchmarkRuleTable] = None,
    include_payloads: bool = True,
) -> tuple[tuple[dict[str, object], ...], Optional[CompiledBenchmarkCaseResultTable]]:
    compiled_case_table = context.compiled_case_table
    if compiled_case_table is None:
        case_results, case_result_table = _evaluate_case_results_with_table(
            context=context,
            rules_by_target=rules_by_target,
            rules=rules,
            compiled_rule_table=compiled_rule_table,
        )
        return (
            tuple(result.to_dict() for result in case_results) if include_payloads else (),
            case_result_table,
        )
    if compiled_rule_table is None and rules is not None:
        compiled_rule_table = _build_compiled_rule_table_from_rules(
            rules=rules,
            compiled_case_table=compiled_case_table,
            compiled_pair_context=context.compiled_pair_context,
        )
    elif compiled_rule_table is None:
        compiled_rule_table = _build_compiled_rule_table(
            rules_by_target=rules_by_target or {},
            compiled_case_table=compiled_case_table,
            compiled_pair_context=context.compiled_pair_context,
        )
    case_payloads: list[dict[str, object]] = []
    case_rows: list[tuple[int, Optional[float], bool, bool, bool, bool, int, bool]] = []
    for index, case in enumerate(context.cases):
        case_payload, case_row = _evaluate_benchmark_case_compiled_payload_row(
            case=case,
            case_row_id=index,
            compiled_case_table=compiled_case_table,
            compiled_rule_table=compiled_rule_table,
            include_payload=include_payloads,
        )
        if case_payload is not None:
            case_payloads.append(case_payload)
        case_rows.append(case_row)
    return (
        tuple(case_payloads),
        _build_compiled_case_result_table(case_rows=case_rows),
    )


def _evaluate_case_results(
    *,
    context: PairBenchmarkContext,
    rules_by_target: Mapping[str, Sequence[VocabRule]],
) -> tuple[RulegenBenchmarkCaseResult, ...]:
    case_results, _ = _evaluate_case_results_with_table(
        context=context,
        rules_by_target=rules_by_target,
    )
    return case_results


def _summarize_compiled_case_results(
    *,
    pair: str,
    case_result_table: CompiledBenchmarkCaseResultTable,
    objective_weights: Optional[RulegenBenchmarkObjectiveWeights] = None,
) -> RulegenBenchmarkSummary:
    weights = objective_weights or RulegenBenchmarkObjectiveWeights()
    case_count = len(case_result_table.case_row_ids)
    top1_correct_count = sum(1 for flag in case_result_table.top1_correct_flags if flag)
    top3_contains_expected_count = sum(
        1 for flag in case_result_table.top3_contains_expected_flags if flag
    )
    forbidden_top1_count = sum(1 for flag in case_result_table.top1_forbidden_flags if flag)
    forbidden_any_count = sum(1 for flag in case_result_table.forbidden_any_present_flags if flag)
    variant_top1_count = sum(1 for flag in case_result_table.top1_variant_flags if flag)

    total_rule_count = sum(case_result_table.rule_counts)
    variant_rule_count = sum(case_result_table.variant_rule_counts)
    avg_rules_per_target = (total_rule_count / case_count) if case_count else 0.0
    top1_confidences = [
        confidence for confidence in case_result_table.top1_confidences if confidence is not None
    ]
    avg_top1_confidence = (
        float(sum(top1_confidences) / len(top1_confidences)) if top1_confidences else None
    )

    top1_accuracy = (top1_correct_count / case_count) if case_count else 0.0
    top3_recall = (top3_contains_expected_count / case_count) if case_count else 0.0
    forbidden_top1_rate = (forbidden_top1_count / case_count) if case_count else 0.0
    forbidden_any_rate = (forbidden_any_count / case_count) if case_count else 0.0
    variant_rule_rate = (variant_rule_count / total_rule_count) if total_rule_count else 0.0
    variant_top1_rate = (variant_top1_count / case_count) if case_count else 0.0
    objective_score = (
        (top1_accuracy * weights.top1_accuracy)
        + (top3_recall * weights.top3_recall)
        - (forbidden_top1_rate * weights.forbidden_top1_rate)
        - (forbidden_any_rate * weights.forbidden_any_rate)
        - (avg_rules_per_target * weights.avg_rules_per_target)
        - (variant_top1_rate * weights.variant_top1_rate)
    )

    return RulegenBenchmarkSummary(
        pair=pair,
        case_count=case_count,
        top1_correct_count=top1_correct_count,
        top3_contains_expected_count=top3_contains_expected_count,
        forbidden_top1_count=forbidden_top1_count,
        forbidden_any_count=forbidden_any_count,
        avg_rules_per_target=avg_rules_per_target,
        avg_top1_confidence=avg_top1_confidence,
        variant_rule_count=variant_rule_count,
        total_rule_count=total_rule_count,
        variant_top1_count=variant_top1_count,
        top1_accuracy=top1_accuracy,
        top3_recall=top3_recall,
        forbidden_top1_rate=forbidden_top1_rate,
        forbidden_any_rate=forbidden_any_rate,
        variant_rule_rate=variant_rule_rate,
        variant_top1_rate=variant_top1_rate,
        objective_score=objective_score,
    )
