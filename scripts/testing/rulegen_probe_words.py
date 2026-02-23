#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Mapping, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.helper.pair_resources import resolve_pair_resources  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.lexicon.word_package import (  # noqa: E402
    build_word_package,
    normalize_word_package,
)
from lexishift_core.rulegen.generation import RuleGenerationResult  # noqa: E402
from lexishift_core.rulegen.generation import (  # noqa: E402
    PosMatchScoringConfig,
    RuleScoreWeights,
    RuleScoringConfig,
)
from lexishift_core.rulegen.pairs.en_es import (  # noqa: E402
    EnEsRulegenConfig,
    generate_en_es_results,
)
from lexishift_core.rulegen.pairs.ja_en import (  # noqa: E402
    JaEnRulegenConfig,
    generate_ja_en_results,
)
from lexishift_core.rulegen.ranking import (  # noqa: E402
    CandidateRankingContext,
    DictionaryEntryOrderRankingMechanism,
    build_ranking_sort_key,
)
from lexishift_core.srs import SrsStore, load_srs_store  # noqa: E402


def _parse_csv_words(value: str) -> list[str]:
    words = [item.strip() for item in str(value or "").split(",")]
    return [word for word in words if word]


def _parse_reading_overrides(value: str) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for chunk in str(value or "").split(","):
        part = chunk.strip()
        if not part or "=" not in part:
            continue
        lemma, reading = part.split("=", 1)
        lemma_text = lemma.strip()
        reading_text = reading.strip()
        if not lemma_text or not reading_text:
            continue
        overrides[lemma_text] = reading_text
    return overrides


def _resolve_required_file(label: str, path: Optional[Path]) -> Path:
    if path is None:
        raise FileNotFoundError(f"Could not resolve {label} path.")
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path


def _load_store(path: Path) -> SrsStore:
    if not path.exists():
        return SrsStore()
    return load_srs_store(path)


def _build_ja_word_packages(
    *,
    targets: Iterable[str],
    store: SrsStore,
    reading_overrides: Mapping[str, str],
) -> tuple[dict[str, Mapping[str, object]], list[str], list[str]]:
    target_set = {str(target).strip() for target in targets if str(target).strip()}
    by_target: dict[str, Mapping[str, object]] = {}
    notes: list[str] = []

    for item in store.items:
        if item.language_pair != "en-ja":
            continue
        lemma = str(item.lemma or "").strip()
        if lemma not in target_set:
            continue
        normalized = normalize_word_package(
            item.word_package,
            fallback_surface=lemma,
            fallback_language_tag="ja",
            fallback_provider=item.source_type or "srs",
        )
        if normalized is None:
            continue
        by_target[lemma] = normalized

    missing = [lemma for lemma in sorted(target_set) if lemma not in by_target]
    for lemma in list(missing):
        reading = str(reading_overrides.get(lemma) or "").strip()
        if not reading:
            continue
        package = build_word_package(
            language_pair="en-ja",
            surface=lemma,
            reading=reading,
            source_provider="rulegen_probe_words",
        )
        if package is None:
            continue
        by_target[lemma] = package
        missing.remove(lemma)
        notes.append(f"Using reading override for '{lemma}' -> '{reading}'.")

    return by_target, missing, notes


def _serialize_result(
    result: RuleGenerationResult,
    *,
    mechanism: DictionaryEntryOrderRankingMechanism,
) -> dict[str, object]:
    context = CandidateRankingContext(
        source_phrase=result.candidate.source_phrase,
        replacement=result.candidate.replacement,
        metadata=result.candidate.metadata,
        confidence=result.confidence,
    )
    rank_score = mechanism.score(context)
    bucket = mechanism.bucket_key(context)
    sort_key = build_ranking_sort_key(context, score=rank_score)
    morphology = result.candidate.metadata.get("morphology")
    morphology_map = morphology if isinstance(morphology, Mapping) else {}
    return {
        "target": result.rule.replacement,
        "source_phrase": result.rule.source_phrase,
        "confidence": float(result.confidence),
        "rank_score": float(rank_score),
        "bucket_key": str(bucket),
        "sort_key": sort_key,
        "gloss_index": result.candidate.metadata.get("gloss_index"),
        "gloss_total": result.candidate.metadata.get("gloss_total"),
        "variant": result.candidate.metadata.get("variant"),
        "source_form": morphology_map.get("source_form"),
        "target_surface": morphology_map.get("target_surface"),
    }


def _collect_rows_for_target(
    results: Iterable[RuleGenerationResult],
    *,
    target: str,
    mechanism: DictionaryEntryOrderRankingMechanism,
) -> list[dict[str, object]]:
    rows = [
        _serialize_result(item, mechanism=mechanism)
        for item in results
        if str(item.rule.replacement) == str(target)
    ]
    rows.sort(key=lambda row: row["sort_key"])
    return rows


def _print_target_block(
    *,
    pair: str,
    target: str,
    uncapped_rows: list[dict[str, object]],
    capped_rows: list[dict[str, object]],
) -> None:
    selected_buckets = {str(row["bucket_key"]) for row in capped_rows}
    selected_definitions = len(selected_buckets)
    print(f"\n[{pair}] target='{target}'")
    print(
        f"  uncapped_rules={len(uncapped_rows)} "
        f"capped_rules={len(capped_rows)} "
        f"selected_definitions={selected_definitions}"
    )
    if not uncapped_rows:
        print("  (no rules)")
        return

    print("  uncapped:")
    for index, row in enumerate(uncapped_rows, start=1):
        bucket = str(row["bucket_key"])
        marker = "*" if bucket in selected_buckets else " "
        gloss_index = row.get("gloss_index")
        variant = str(row.get("variant") or "-")
        source_form = str(row.get("source_form") or "-")
        target_surface = str(row.get("target_surface") or "-")
        print(
            f"    {index:02d}. [{marker}] src='{row['source_phrase']}' "
            f"conf={float(row['confidence']):.4f} rank={float(row['rank_score']):.4f} "
            f"bucket={bucket} gloss_index={gloss_index} "
            f"variant={variant} source_form={source_form} target_surface={target_surface}"
        )

    print("  capped:")
    for index, row in enumerate(capped_rows, start=1):
        bucket = str(row["bucket_key"])
        gloss_index = row.get("gloss_index")
        print(
            f"    {index:02d}. src='{row['source_phrase']}' "
            f"conf={float(row['confidence']):.4f} rank={float(row['rank_score']):.4f} "
            f"bucket={bucket} gloss_index={gloss_index}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Probe rulegen outputs for fixed words and print uncapped vs capped ranking views. "
            "Useful for tracking scoring behavior changes over time."
        )
    )
    parser.add_argument(
        "--spanish-targets",
        default="hora,trabajo",
        help="Comma-separated Spanish target lemmas for en-es probe.",
    )
    parser.add_argument(
        "--japanese-targets",
        default="様,時",
        help="Comma-separated Japanese target lemmas for en-ja probe.",
    )
    parser.add_argument(
        "--ja-readings",
        default="様=よう,時=とき",
        help="Comma-separated lemma=reading overrides used when SRS store lacks word_package.",
    )
    parser.add_argument(
        "--max-definitions",
        type=int,
        default=3,
        help="Top-K definitions per target in capped run.",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.0,
        help="Minimum confidence threshold for both runs.",
    )
    parser.add_argument(
        "--max-rules-per-target",
        type=int,
        help="Optional final cap on emitted rules per target in capped run.",
    )
    parser.add_argument(
        "--no-variants",
        action="store_true",
        help="Disable variant expansion in probes.",
    )
    parser.add_argument(
        "--disable-pos-scoring",
        action="store_true",
        help="Disable POS congruence scoring in both runs.",
    )
    parser.add_argument(
        "--pos-exact-match-bonus",
        type=float,
        default=1.0,
        help="POS exact-match bonus used in both runs.",
    )
    parser.add_argument(
        "--pos-compatible-match-bonus",
        type=float,
        default=0.5,
        help="POS compatibility-class bonus used in both runs.",
    )
    parser.add_argument(
        "--score-weight-pos-match",
        type=float,
        default=0.1,
        help="Weight of POS signal in confidence scoring.",
    )
    parser.add_argument(
        "--profile-id",
        default="default",
        help="Profile ID to read SRS word packages from (for ja targets).",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        help="Override LexiShift data root (default: platform data dir or LEXISHIFT_DATA_DIR).",
    )
    parser.add_argument(
        "--freedict-es-en",
        type=Path,
        help="Override FreeDict ES->EN path for en-es probe.",
    )
    parser.add_argument(
        "--jmdict",
        type=Path,
        help="Override JMDict path for en-ja probe.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path to save full probe output as JSON.",
    )
    args = parser.parse_args()

    include_variants = not args.no_variants
    spanish_targets = _parse_csv_words(args.spanish_targets)
    japanese_targets = _parse_csv_words(args.japanese_targets)
    reading_overrides = _parse_reading_overrides(args.ja_readings)
    max_definitions = max(1, int(args.max_definitions))
    max_rules_per_target = (
        max(1, int(args.max_rules_per_target))
        if args.max_rules_per_target is not None
        else None
    )
    scoring = RuleScoringConfig(
        weights=RuleScoreWeights(pos_match=float(args.score_weight_pos_match)),
        pos_match=PosMatchScoringConfig(
            enabled=not args.disable_pos_scoring,
            exact_match_bonus=float(args.pos_exact_match_bonus),
            compatible_match_bonus=float(args.pos_compatible_match_bonus),
        ),
    )

    paths = build_helper_paths(args.data_root)
    store_path = paths.srs_store_path_for(args.profile_id)
    store = _load_store(store_path)

    _resolved_jmdict, _resolved_freedict_es_en, _ = resolve_pair_resources(
        paths,
        pair="en-es",
        jmdict_path=args.jmdict,
        freedict_de_en_path=args.freedict_es_en,
        set_source_db=None,
    )
    resolved_freedict_es_en = _resolve_required_file(
        "FreeDict ES->EN",
        _resolved_freedict_es_en,
    )

    _resolved_jmdict, _unused_freedict, _ = resolve_pair_resources(
        paths,
        pair="en-ja",
        jmdict_path=args.jmdict,
        freedict_de_en_path=args.freedict_es_en,
        set_source_db=None,
    )
    resolved_jmdict = _resolve_required_file("JMDict", _resolved_jmdict)

    ja_word_packages, missing_ja_targets, notes = _build_ja_word_packages(
        targets=japanese_targets,
        store=store,
        reading_overrides=reading_overrides,
    )
    resolved_japanese_targets = [lemma for lemma in japanese_targets if lemma in ja_word_packages]

    ranking = DictionaryEntryOrderRankingMechanism()

    # Uncapped baseline run.
    es_uncapped = generate_en_es_results(
        spanish_targets,
        config=EnEsRulegenConfig(
            freedict_es_en_path=resolved_freedict_es_en,
            include_variants=include_variants,
            confidence_threshold=args.confidence_threshold,
            max_definitions_per_target=None,
            max_rules_per_target=None,
            scoring=scoring,
        ),
    )
    ja_uncapped = generate_ja_en_results(
        resolved_japanese_targets,
        config=JaEnRulegenConfig(
            jmdict_path=resolved_jmdict,
            include_variants=include_variants,
            confidence_threshold=args.confidence_threshold,
            word_packages_by_target=ja_word_packages,
            max_definitions_per_target=None,
            max_rules_per_target=None,
            scoring=scoring,
        ),
    )

    # Capped run (top-K definitions).
    es_capped = generate_en_es_results(
        spanish_targets,
        config=EnEsRulegenConfig(
            freedict_es_en_path=resolved_freedict_es_en,
            include_variants=include_variants,
            confidence_threshold=args.confidence_threshold,
            max_definitions_per_target=max_definitions,
            max_rules_per_target=max_rules_per_target,
            scoring=scoring,
        ),
    )
    ja_capped = generate_ja_en_results(
        resolved_japanese_targets,
        config=JaEnRulegenConfig(
            jmdict_path=resolved_jmdict,
            include_variants=include_variants,
            confidence_threshold=args.confidence_threshold,
            word_packages_by_target=ja_word_packages,
            max_definitions_per_target=max_definitions,
            max_rules_per_target=max_rules_per_target,
            scoring=scoring,
        ),
    )

    print("Rulegen Probe")
    print(f"  data_root: {paths.data_root}")
    print(f"  profile_id: {args.profile_id}")
    print(f"  srs_store: {store_path}")
    print(f"  freedict_es_en: {resolved_freedict_es_en}")
    print(f"  jmdict: {resolved_jmdict}")
    print(
        f"  config: max_definitions={max_definitions}, "
        f"max_rules_per_target={max_rules_per_target}, "
        f"confidence_threshold={args.confidence_threshold}, include_variants={include_variants}, "
        f"pos_scoring_enabled={not args.disable_pos_scoring}, "
        f"pos_exact={args.pos_exact_match_bonus}, pos_compatible={args.pos_compatible_match_bonus}, "
        f"score_weight_pos_match={args.score_weight_pos_match}"
    )
    for note in notes:
        print(f"  note: {note}")
    for missing in missing_ja_targets:
        print(
            f"  warning: Missing word_package/reading for Japanese target '{missing}'. "
            "Add to SRS store or pass via --ja-readings."
        )

    output_payload: dict[str, object] = {
        "config": {
            "max_definitions": max_definitions,
            "max_rules_per_target": max_rules_per_target,
            "confidence_threshold": args.confidence_threshold,
            "include_variants": include_variants,
            "pos_scoring_enabled": (not args.disable_pos_scoring),
            "pos_exact_match_bonus": args.pos_exact_match_bonus,
            "pos_compatible_match_bonus": args.pos_compatible_match_bonus,
            "score_weight_pos_match": args.score_weight_pos_match,
        },
        "paths": {
            "data_root": str(paths.data_root),
            "profile_id": args.profile_id,
            "srs_store": str(store_path),
            "freedict_es_en": str(resolved_freedict_es_en),
            "jmdict": str(resolved_jmdict),
        },
        "notes": notes,
        "warnings": [
            (
                f"Missing word_package/reading for Japanese target '{missing}'. "
                "Add to SRS store or pass via --ja-readings."
            )
            for missing in missing_ja_targets
        ],
        "pairs": {},
    }

    es_pair_payload: dict[str, object] = {}
    for target in spanish_targets:
        uncapped_rows = _collect_rows_for_target(es_uncapped, target=target, mechanism=ranking)
        capped_rows = _collect_rows_for_target(es_capped, target=target, mechanism=ranking)
        _print_target_block(
            pair="en-es",
            target=target,
            uncapped_rows=uncapped_rows,
            capped_rows=capped_rows,
        )
        es_pair_payload[target] = {
            "uncapped": uncapped_rows,
            "capped": capped_rows,
        }
    output_payload["pairs"] = {"en-es": es_pair_payload}

    ja_pair_payload: dict[str, object] = {}
    for target in japanese_targets:
        uncapped_rows = _collect_rows_for_target(ja_uncapped, target=target, mechanism=ranking)
        capped_rows = _collect_rows_for_target(ja_capped, target=target, mechanism=ranking)
        _print_target_block(
            pair="en-ja",
            target=target,
            uncapped_rows=uncapped_rows,
            capped_rows=capped_rows,
        )
        ja_pair_payload[target] = {
            "uncapped": uncapped_rows,
            "capped": capped_rows,
        }
    output_payload["pairs"]["en-ja"] = ja_pair_payload

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(output_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nJSON output written: {args.json_output}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(
            "hint: pass explicit resource paths with --jmdict and --freedict-es-en "
            "or ensure language packs are installed in the LexiShift data directory.",
            file=sys.stderr,
        )
        raise SystemExit(2)
