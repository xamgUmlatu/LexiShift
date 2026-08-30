#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sqlite3
import sys
import xml.etree.ElementTree as ET
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_standalone_independence_probe_en_ja import (  # noqa: E402
    DEFAULT_AOZORA_SQLITE,
    DEFAULT_BCCWJ_SQLITE,
    DEFAULT_RANKING_CSV,
    aozora_exact_stats,
    bccwj_exact_stats,
    hira_to_kata,
    repo_path,
)


DATA_ROOT = Path.home() / "Library" / "Application Support" / "LexiShift" / "LexiShift"
DEFAULT_JMDICT = DATA_ROOT / "language_packs" / "jmdict-ja-en" / "JMdict_e"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_standalone_independence_broad_audit_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_standalone_independence_broad_audit_en_ja_latest.md"
)
VOCAB_STATES = frozenset({"normal_vocab", "deprioritized_vocab"})
COMPOUNDISH_ADMISSION_WORDS = (
    "compound",
    "suffix",
    "affix",
    "morpheme",
    "on_reading",
    "on-yomi",
    "derived",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Broad sidecar audit for en-ja rows that may be over-supported by "
            "compound or bound evidence. This does not change runtime scores."
        )
    )
    parser.add_argument("--ranking-csv", type=Path, default=DEFAULT_RANKING_CSV)
    parser.add_argument("--bccwj-sqlite", type=Path, default=DEFAULT_BCCWJ_SQLITE)
    parser.add_argument("--aozora-sqlite", type=Path, default=DEFAULT_AOZORA_SQLITE)
    parser.add_argument("--jmdict", type=Path, default=DEFAULT_JMDICT)
    parser.add_argument("--rank-max", type=int, default=5000)
    parser.add_argument("--score-max", type=float, default=0.80)
    parser.add_argument("--surface-len-max", type=int, default=3)
    parser.add_argument("--review-limit", type=int, default=80)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        ranking_csv=_resolve_path(args.ranking_csv),
        bccwj_sqlite=_resolve_path(args.bccwj_sqlite),
        aozora_sqlite=_resolve_path(args.aozora_sqlite),
        jmdict_path=_resolve_path(args.jmdict),
        rank_max=max(1, int(args.rank_max)),
        score_max=float(args.score_max),
        surface_len_max=max(1, int(args.surface_len_max)),
        review_limit=max(1, int(args.review_limit)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    ranking_csv: Path,
    bccwj_sqlite: Path,
    aozora_sqlite: Path,
    jmdict_path: Path,
    rank_max: int,
    score_max: float,
    surface_len_max: int,
    review_limit: int,
) -> dict[str, Any]:
    ranking_rows = load_ranking_rows(ranking_csv)
    candidate_rows = [
        row
        for row in ranking_rows
        if is_candidate(
            row, rank_max=rank_max, score_max=score_max, surface_len_max=surface_len_max
        )
    ]
    row_lookup = {(row["lemma"], row["reading"]): row for row in ranking_rows}
    graph = build_jmdict_graph(jmdict_path, candidate_rows, row_lookup, surface_len_max)
    rows: list[dict[str, Any]] = []
    with sqlite3.connect(bccwj_sqlite) as bccwj, sqlite3.connect(aozora_sqlite) as aozora:
        bccwj.row_factory = sqlite3.Row
        aozora.row_factory = sqlite3.Row
        support_lookup = ExactSupportLookup(bccwj, aozora)
        for ranking_row in candidate_rows:
            lemma = str(ranking_row["lemma"])
            reading = str(ranking_row["reading"])
            reading_kata = hira_to_kata(reading)
            bccwj_stats = bccwj_exact_stats(bccwj, surface=lemma, reading=reading_kata)
            aozora_stats = aozora_exact_stats(aozora, surface=lemma, reading=reading_kata)
            graph_stats = graph.get((lemma, normalize_kana(reading)), empty_graph_stats())
            compound_mass = compound_frequency_mass(
                graph_stats=graph_stats,
                support_lookup=support_lookup,
                row_lookup=row_lookup,
                current_score=float(str(ranking_row.get("score") or "1.0")),
            )
            rows.append(
                score_row(
                    ranking_row=ranking_row,
                    bccwj_stats=bccwj_stats,
                    aozora_stats=aozora_stats,
                    graph_stats=graph_stats,
                    compound_mass=compound_mass,
                )
            )
    rows.sort(
        key=lambda row: (
            -float(row["risk"]["compound_component_risk"]),
            int(row["ranking"]["rank"]),
        )
    )
    summary = summarize(rows)
    return {
        "schema_version": 1,
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "scores_changed": False,
        "purpose": (
            "Broad diagnostic for standalone rows that may be over-supported by "
            "bound, compound, or vocabulary-graph evidence."
        ),
        "inputs": {
            "ranking_csv": repo_path(ranking_csv),
            "bccwj_sqlite": str(bccwj_sqlite),
            "aozora_sqlite": str(aozora_sqlite),
            "jmdict": str(jmdict_path),
            "rank_max": rank_max,
            "score_max": score_max,
            "surface_len_max": surface_len_max,
            "candidate_count": len(candidate_rows),
            "review_limit": review_limit,
        },
        "summary": summary,
        "top_candidates": [compact_output_row(row) for row in rows[:review_limit]],
        "known_manual_hits": [
            compact_output_row(row)
            for row in rows
            if row["manual"]["compoundish_manual_correction"]
        ][:review_limit],
        "high_confidence_unreviewed": [
            compact_output_row(row)
            for row in rows
            if row["risk"]["classification"] == "high_confidence_compound_component"
            and not row["manual"]["manual_correction_active"]
        ][:review_limit],
        "rows": [compact_output_row(row) for row in rows],
    }


def load_ranking_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def is_candidate(
    row: Mapping[str, str],
    *,
    rank_max: int,
    score_max: float,
    surface_len_max: int,
) -> bool:
    lemma = str(row.get("lemma") or "")
    reading = str(row.get("reading") or "")
    if not lemma or not reading or not contains_kanji(lemma):
        return False
    if len(lemma) > surface_len_max:
        return False
    if str(row.get("candidate_state") or "") not in VOCAB_STATES:
        return False
    rank = int(float(str(row.get("rank") or "999999")))
    score = float(str(row.get("score") or "1.0"))
    return rank <= rank_max and score <= score_max


def build_jmdict_graph(
    jmdict_path: Path,
    candidate_rows: Sequence[Mapping[str, str]],
    row_lookup: Mapping[tuple[str, str], Mapping[str, str]],
    surface_len_max: int,
) -> dict[tuple[str, str], dict[str, Any]]:
    stats = {
        (str(row["lemma"]), normalize_kana(str(row["reading"]))): empty_graph_stats()
        for row in candidate_rows
    }
    surface_to_keys: dict[str, set[tuple[str, str]]] = {}
    for surface, reading in stats:
        surface_to_keys.setdefault(surface, set()).add((surface, reading))
    if not jmdict_path.exists():
        return stats

    for _event, elem in ET.iterparse(jmdict_path, events=("end",)):
        if elem.tag != "entry":
            continue
        entry = jmdict_entry_payload(elem)
        entry_id = str(entry["ent_seq"] or "")
        forms = list(entry["forms"])
        readings = list(entry["readings"])
        candidate_keys = keys_for_entry_forms(forms, surface_to_keys, surface_len_max)
        for key in candidate_keys:
            surface, target_reading = key
            target_stats = stats[key]
            update_exact_graph_stats(
                stats=target_stats,
                entry_id=entry_id,
                surface=surface,
                target_reading=target_reading,
                forms=forms,
                readings=readings,
            )
            update_compound_graph_stats(
                stats=target_stats,
                entry_id=entry_id,
                surface=surface,
                target_reading=target_reading,
                forms=forms,
                readings=readings,
                row_lookup=row_lookup,
            )
        elem.clear()
    for value in stats.values():
        value["compound_examples"].sort(
            key=lambda item: (
                not bool(item.get("priority")),
                score_sort_value(item.get("ranking_score")),
                int(item.get("form_len") or 99),
                str(item.get("surface") or ""),
            )
        )
        value["compound_examples"] = value["compound_examples"][:12]
        value["exact_priority_tags"] = sorted(value["exact_priority_tags"])
        value["compound_priority_tags"] = sorted(value["compound_priority_tags"])
    return stats


def keys_for_entry_forms(
    forms: Sequence[Mapping[str, Any]],
    surface_to_keys: Mapping[str, set[tuple[str, str]]],
    surface_len_max: int,
) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for form in forms:
        text = str(form["text"])
        max_len = min(surface_len_max, len(text))
        for start in range(len(text)):
            for end in range(start + 1, min(len(text), start + max_len) + 1):
                found.update(surface_to_keys.get(text[start:end], ()))
    return found


def update_exact_graph_stats(
    *,
    stats: dict[str, Any],
    entry_id: str,
    surface: str,
    target_reading: str,
    forms: Sequence[Mapping[str, Any]],
    readings: Sequence[Mapping[str, Any]],
) -> None:
    if entry_id in stats["_exact_entry_ids"]:
        return
    matched_priority_tags: set[str] = set()
    matched = False
    for form in forms:
        if str(form["text"]) != surface:
            continue
        for reading in readings:
            normalized = str(reading["normalized"])
            if normalized != target_reading:
                continue
            if not reading_allowed_for_form(reading, surface):
                continue
            matched = True
            matched_priority_tags.update(form["priorities"])
            matched_priority_tags.update(reading["priorities"])
    if not matched:
        return
    stats["_exact_entry_ids"].add(entry_id)
    stats["exact_entry_count"] += 1
    if matched_priority_tags:
        stats["exact_priority_entry_count"] += 1
        stats["exact_priority_tags"].update(matched_priority_tags)


def update_compound_graph_stats(
    *,
    stats: dict[str, Any],
    entry_id: str,
    surface: str,
    target_reading: str,
    forms: Sequence[Mapping[str, Any]],
    readings: Sequence[Mapping[str, Any]],
    row_lookup: Mapping[tuple[str, str], Mapping[str, str]],
) -> None:
    if entry_id in stats["_compound_entry_ids"]:
        return
    best_match: dict[str, Any] | None = None
    for form in forms:
        text = str(form["text"])
        if text == surface or surface not in text:
            continue
        for reading in readings:
            if not reading_allowed_for_form(reading, text):
                continue
            match = compound_reading_match(
                form=text,
                reading=str(reading["normalized"]),
                surface=surface,
                target_reading=target_reading,
            )
            if match["quality"] == "none":
                continue
            ranking_row = row_lookup.get((text, str(reading["normalized"])))
            ranking_score = optional_float(
                None if ranking_row is None else ranking_row.get("score")
            )
            priority_tags = set(form["priorities"]) | set(reading["priorities"])
            candidate = {
                "surface": text,
                "reading": str(reading["normalized"]),
                "position": match["position"],
                "quality": match["quality"],
                "priority": bool(priority_tags),
                "priority_tags": sorted(priority_tags),
                "ranking_score": ranking_score,
                "ranking_rank": optional_int(
                    None if ranking_row is None else ranking_row.get("rank")
                ),
                "form_len": len(text),
            }
            if best_match is None or compound_example_sort(candidate) < compound_example_sort(
                best_match
            ):
                best_match = candidate
    if best_match is None:
        return
    stats["_compound_entry_ids"].add(entry_id)
    stats["_compound_keys"].add((str(best_match["surface"]), str(best_match["reading"])))
    stats["compound_entry_count"] += 1
    stats["compound_position_counts"][str(best_match["position"])] = (
        stats["compound_position_counts"].get(str(best_match["position"]), 0) + 1
    )
    stats["compound_quality_counts"][str(best_match["quality"])] = (
        stats["compound_quality_counts"].get(str(best_match["quality"]), 0) + 1
    )
    if best_match["priority"]:
        stats["compound_priority_entry_count"] += 1
        stats["compound_priority_tags"].update(best_match["priority_tags"])
    if best_match["ranking_score"] is not None:
        stats["compound_ranked_entry_count"] += 1
    stats["compound_examples"].append(best_match)


class ExactSupportLookup:
    def __init__(self, bccwj: sqlite3.Connection, aozora: sqlite3.Connection) -> None:
        self.bccwj = bccwj
        self.aozora = aozora
        self.cache: dict[tuple[str, str], dict[str, Any]] = {}

    def lookup(self, surface: str, reading: str) -> dict[str, Any]:
        normalized = normalize_kana(reading)
        key = (surface, normalized)
        if key in self.cache:
            return self.cache[key]
        reading_kata = hira_to_kata(normalized)
        bccwj_stats = bccwj_exact_stats(self.bccwj, surface=surface, reading=reading_kata)
        aozora_stats = aozora_exact_stats(self.aozora, surface=surface, reading=reading_kata)
        support = {
            "surface": surface,
            "reading": normalized,
            "bccwj_total": round(float(bccwj_stats["total_frequency"]), 6),
            "bccwj_independent": round(float(bccwj_stats["independent_frequency"]), 6),
            "bccwj_bound": round(float(bccwj_stats["bound_frequency"]), 6),
            "aozora_total": int(aozora_stats["total_exact_token_count"]),
            "aozora_independent": int(aozora_stats["independent_token_count"]),
            "aozora_bound": int(aozora_stats["bound_token_count"]),
        }
        support["raw_combined_total"] = round(
            float(support["bccwj_total"]) + float(support["aozora_total"]),
            6,
        )
        support["log_combined_total"] = round(
            math.log1p(float(support["bccwj_total"])) + math.log1p(float(support["aozora_total"])),
            6,
        )
        self.cache[key] = support
        return support


def compound_frequency_mass(
    *,
    graph_stats: Mapping[str, Any],
    support_lookup: ExactSupportLookup,
    row_lookup: Mapping[tuple[str, str], Mapping[str, str]],
    current_score: float,
) -> dict[str, Any]:
    bccwj_total = 0.0
    bccwj_independent = 0.0
    aozora_total = 0.0
    aozora_independent = 0.0
    raw_combined_total = 0.0
    log_combined_total = 0.0
    supported_key_count = 0
    supported_ranked_key_count = 0
    easier_supported_key_count = 0
    examples: list[dict[str, Any]] = []
    for surface, reading in sorted(graph_stats.get("_compound_keys") or ()):
        support = support_lookup.lookup(str(surface), str(reading))
        ranking_row = row_lookup.get((str(surface), str(reading)))
        ranking_score = optional_float(None if ranking_row is None else ranking_row.get("score"))
        has_support = bool(float(support["raw_combined_total"]) > 0.0)
        if has_support:
            supported_key_count += 1
            bccwj_total += float(support["bccwj_total"])
            bccwj_independent += float(support["bccwj_independent"])
            aozora_total += float(support["aozora_total"])
            aozora_independent += float(support["aozora_independent"])
            raw_combined_total += float(support["raw_combined_total"])
            log_combined_total += float(support["log_combined_total"])
        if ranking_score is not None:
            supported_ranked_key_count += 1
            if ranking_score < current_score:
                easier_supported_key_count += 1
        if has_support or ranking_score is not None:
            examples.append(
                {
                    "surface": surface,
                    "reading": reading,
                    "ranking_score": ranking_score,
                    "ranking_rank": optional_int(
                        None if ranking_row is None else ranking_row.get("rank")
                    ),
                    "easier_than_current": bool(
                        ranking_score is not None and ranking_score < current_score
                    ),
                    "bccwj_total": support["bccwj_total"],
                    "aozora_total": support["aozora_total"],
                    "raw_combined_total": support["raw_combined_total"],
                    "log_combined_total": support["log_combined_total"],
                }
            )
    examples.sort(
        key=lambda item: (
            -float(item["log_combined_total"]),
            score_sort_value(item.get("ranking_score")),
            str(item["surface"]),
        )
    )
    return {
        "compound_key_count": len(graph_stats.get("_compound_keys") or ()),
        "supported_compound_key_count": supported_key_count,
        "ranked_compound_key_count": supported_ranked_key_count,
        "easier_ranked_compound_key_count": easier_supported_key_count,
        "compound_bccwj_total": round(bccwj_total, 6),
        "compound_bccwj_independent": round(bccwj_independent, 6),
        "compound_aozora_total": int(aozora_total),
        "compound_aozora_independent": int(aozora_independent),
        "compound_raw_combined_total": round(raw_combined_total, 6),
        "compound_log_combined_total": round(log_combined_total, 6),
        "compound_mass_examples": examples[:12],
    }


def compound_reading_match(
    *,
    form: str,
    reading: str,
    surface: str,
    target_reading: str,
) -> dict[str, str]:
    starts = form.startswith(surface)
    ends = form.endswith(surface)
    if starts and reading.startswith(target_reading):
        return {"quality": "anchored", "position": "prefix"}
    if ends and reading.endswith(target_reading):
        return {"quality": "anchored", "position": "suffix"}
    if len(target_reading) >= 2 and target_reading in reading:
        return {"quality": "contains", "position": "internal"}
    return {"quality": "none", "position": ""}


def score_row(
    *,
    ranking_row: Mapping[str, str],
    bccwj_stats: Mapping[str, Any],
    aozora_stats: Mapping[str, Any],
    graph_stats: Mapping[str, Any],
    compound_mass: Mapping[str, Any],
) -> dict[str, Any]:
    score = float(str(ranking_row.get("score") or "1.0"))
    exact_independent = float(bccwj_stats["independent_frequency"]) + float(
        aozora_stats["independent_token_count"]
    )
    exact_bound = float(bccwj_stats["bound_frequency"]) + float(aozora_stats["bound_token_count"])
    exact_total = float(bccwj_stats["total_frequency"]) + float(
        aozora_stats["total_exact_token_count"]
    )
    graph_compounds = int(graph_stats["compound_entry_count"])
    graph_priority_compounds = int(graph_stats["compound_priority_entry_count"])
    ranked_compounds = int(graph_stats["compound_ranked_entry_count"])
    easier_compounds = [
        example
        for example in graph_stats["compound_examples"]
        if example.get("ranking_score") is not None and float(example["ranking_score"]) < score
    ]
    exact_priority = int(graph_stats["exact_priority_entry_count"])
    exact_entries = int(graph_stats["exact_entry_count"])
    graph_strength = min(1.0, math.log1p(graph_compounds) / math.log1p(30))
    if graph_priority_compounds:
        graph_strength = min(1.0, graph_strength + 0.18)
    standalone_weakness = 1.0 - min(1.0, math.log1p(exact_independent) / math.log1p(120))
    easier_strength = min(1.0, len(easier_compounds) / 4)
    bound_strength = min(1.0, exact_bound / max(1.0, exact_independent + exact_bound))
    direct_bccwj_total = float(bccwj_stats["total_frequency"])
    direct_aozora_total = float(aozora_stats["total_exact_token_count"])
    direct_raw_combined_total = direct_bccwj_total + direct_aozora_total
    direct_log_combined_total = math.log1p(direct_bccwj_total) + math.log1p(direct_aozora_total)
    compound_bccwj_total = float(compound_mass["compound_bccwj_total"])
    compound_aozora_total = float(compound_mass["compound_aozora_total"])
    compound_raw_combined_total = float(compound_mass["compound_raw_combined_total"])
    compound_log_combined_total = float(compound_mass["compound_log_combined_total"])
    mass_metrics = {
        **compound_mass,
        "direct_bccwj_total": round(direct_bccwj_total, 6),
        "direct_bccwj_independent": round(float(bccwj_stats["independent_frequency"]), 6),
        "direct_aozora_total": int(direct_aozora_total),
        "direct_aozora_independent": int(aozora_stats["independent_token_count"]),
        "direct_raw_combined_total": round(direct_raw_combined_total, 6),
        "direct_log_combined_total": round(direct_log_combined_total, 6),
        "bccwj_leak_share": safe_share(
            compound_bccwj_total, direct_bccwj_total + compound_bccwj_total
        ),
        "aozora_leak_share": safe_share(
            compound_aozora_total, direct_aozora_total + compound_aozora_total
        ),
        "raw_combined_leak_share": safe_share(
            compound_raw_combined_total,
            direct_raw_combined_total + compound_raw_combined_total,
        ),
        "combined_log_leak_share": safe_share(
            compound_log_combined_total,
            direct_log_combined_total + compound_log_combined_total,
        ),
        "combined_log_compound_to_direct_ratio": safe_ratio_float(
            compound_log_combined_total,
            direct_log_combined_total,
        ),
    }
    frequency_leak_strength = float(mass_metrics["combined_log_leak_share"])
    priority_protection = 0.18 if exact_priority else 0.0
    jlpt_protection = 0.10 if truthy(ranking_row.get("jlpt_exact_known")) else 0.0
    risk = max(
        0.0,
        min(
            1.0,
            (0.26 * graph_strength)
            + (0.24 * frequency_leak_strength)
            + (0.21 * standalone_weakness)
            + (0.15 * easier_strength)
            + (0.14 * bound_strength)
            - priority_protection
            - jlpt_protection,
        ),
    )
    classification = classify_risk(
        risk=risk,
        exact_independent=exact_independent,
        exact_bound=exact_bound,
        graph_compounds=graph_compounds,
        graph_priority_compounds=graph_priority_compounds,
        easier_compound_count=len(easier_compounds),
        exact_priority=exact_priority,
    )
    correction_types = split_correction_types(str(ranking_row.get("correction_types") or ""))
    admission_override = str(ranking_row.get("admission_override") or "")
    return {
        "lemma": str(ranking_row["lemma"]),
        "reading": str(ranking_row["reading"]),
        "ranking": compact_ranking(ranking_row),
        "manual": {
            "manual_correction_active": str(ranking_row.get("manual_correction_active") or "")
            == "yes",
            "correction_types": correction_types,
            "admission_override": admission_override,
            "compoundish_manual_correction": is_compoundish_manual_correction(
                correction_types,
                admission_override,
            ),
        },
        "corpus": {
            "bccwj_independent": round(float(bccwj_stats["independent_frequency"]), 6),
            "bccwj_bound": round(float(bccwj_stats["bound_frequency"]), 6),
            "aozora_independent": int(aozora_stats["independent_token_count"]),
            "aozora_bound": int(aozora_stats["bound_token_count"]),
            "exact_independent_support": round(exact_independent, 6),
            "exact_bound_support": round(exact_bound, 6),
            "exact_total_support": round(exact_total, 6),
        },
        "jmdict_graph": public_graph_stats(graph_stats, current_score=score),
        "frequency_mass": mass_metrics,
        "risk": {
            "compound_component_risk": round(risk, 6),
            "pressure_band": pressure_band(risk),
            "classification": classification,
            "graph_strength": round(graph_strength, 6),
            "standalone_weakness": round(standalone_weakness, 6),
            "frequency_leak_strength": round(frequency_leak_strength, 6),
            "easier_compound_count": len(easier_compounds),
            "ranked_compound_count": ranked_compounds,
            "exact_priority_entry_count": exact_priority,
            "exact_entry_count": exact_entries,
        },
    }


def pressure_band(risk: float) -> str:
    if risk >= 0.60:
        return "severe_review_pressure"
    if risk >= 0.40:
        return "strong_review_pressure"
    if risk >= 0.25:
        return "moderate_review_pressure"
    return "low_review_pressure"


def classify_risk(
    *,
    risk: float,
    exact_independent: float,
    exact_bound: float,
    graph_compounds: int,
    graph_priority_compounds: int,
    easier_compound_count: int,
    exact_priority: int,
) -> str:
    if (
        risk >= 0.68
        and graph_compounds >= 8
        and exact_independent < 120
        and (
            easier_compound_count >= 2
            or graph_priority_compounds >= 2
            or exact_bound > exact_independent
        )
    ):
        return "high_confidence_compound_component"
    if risk >= 0.55 and graph_compounds >= 5 and exact_independent < 250:
        return "medium_confidence_compound_component"
    if graph_compounds >= 8 and exact_priority and exact_independent >= 100:
        return "compound_rich_but_standalone_supported"
    if exact_independent >= 250:
        return "independent_supported"
    return "low_or_uncertain"


def summarize(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, int] = {}
    by_pressure: dict[str, int] = {}
    manual_compoundish = 0
    manual_compoundish_medium = 0
    manual_compoundish_strong = 0
    manual_compoundish_severe = 0
    high_confidence = 0
    high_confidence_manual = 0
    medium_or_high = 0
    medium_or_high_manual = 0
    for row in rows:
        classification = str(row["risk"]["classification"])
        pressure = str(row["risk"]["pressure_band"])
        risk_value = float(row["risk"]["compound_component_risk"])
        by_class[classification] = by_class.get(classification, 0) + 1
        by_pressure[pressure] = by_pressure.get(pressure, 0) + 1
        is_manual = bool(row["manual"]["compoundish_manual_correction"])
        is_high = classification == "high_confidence_compound_component"
        is_medium_or_high = classification in {
            "high_confidence_compound_component",
            "medium_confidence_compound_component",
        }
        if is_manual:
            manual_compoundish += 1
            if risk_value >= 0.25:
                manual_compoundish_medium += 1
            if risk_value >= 0.40:
                manual_compoundish_strong += 1
            if risk_value >= 0.60:
                manual_compoundish_severe += 1
        if is_high:
            high_confidence += 1
        if is_high and is_manual:
            high_confidence_manual += 1
        if is_medium_or_high:
            medium_or_high += 1
        if is_medium_or_high and is_manual:
            medium_or_high_manual += 1
    moderate_pressure_count = sum(
        1 for row in rows if float(row["risk"]["compound_component_risk"]) >= 0.25
    )
    strong_pressure_count = sum(
        1 for row in rows if float(row["risk"]["compound_component_risk"]) >= 0.40
    )
    severe_pressure_count = sum(
        1 for row in rows if float(row["risk"]["compound_component_risk"]) >= 0.60
    )
    moderate_pressure_manual = sum(
        1
        for row in rows
        if float(row["risk"]["compound_component_risk"]) >= 0.25
        and row["manual"]["compoundish_manual_correction"]
    )
    strong_pressure_manual = sum(
        1
        for row in rows
        if float(row["risk"]["compound_component_risk"]) >= 0.40
        and row["manual"]["compoundish_manual_correction"]
    )
    severe_pressure_manual = sum(
        1
        for row in rows
        if float(row["risk"]["compound_component_risk"]) >= 0.60
        and row["manual"]["compoundish_manual_correction"]
    )
    return {
        "audited_row_count": len(rows),
        "classification_counts": by_class,
        "pressure_band_counts": by_pressure,
        "manual_compoundish_correction_count": manual_compoundish,
        "manual_compoundish_recalled_by_moderate_pressure": manual_compoundish_medium,
        "manual_compoundish_recalled_by_strong_pressure": manual_compoundish_strong,
        "manual_compoundish_recalled_by_severe_pressure": manual_compoundish_severe,
        "manual_compoundish_moderate_pressure_recall": safe_ratio(
            manual_compoundish_medium, manual_compoundish
        ),
        "manual_compoundish_strong_pressure_recall": safe_ratio(
            manual_compoundish_strong, manual_compoundish
        ),
        "manual_compoundish_severe_pressure_recall": safe_ratio(
            manual_compoundish_severe, manual_compoundish
        ),
        "moderate_pressure_count": moderate_pressure_count,
        "moderate_pressure_already_manual_count": moderate_pressure_manual,
        "moderate_pressure_manual_share": safe_ratio(
            moderate_pressure_manual, moderate_pressure_count
        ),
        "strong_pressure_count": strong_pressure_count,
        "strong_pressure_already_manual_count": strong_pressure_manual,
        "strong_pressure_manual_share": safe_ratio(strong_pressure_manual, strong_pressure_count),
        "severe_pressure_count": severe_pressure_count,
        "severe_pressure_already_manual_count": severe_pressure_manual,
        "severe_pressure_manual_share": safe_ratio(severe_pressure_manual, severe_pressure_count),
        "high_confidence_count": high_confidence,
        "high_confidence_already_manual_count": high_confidence_manual,
        "high_confidence_manual_share": safe_ratio(high_confidence_manual, high_confidence),
        "medium_or_high_count": medium_or_high,
        "medium_or_high_already_manual_count": medium_or_high_manual,
        "medium_or_high_manual_share": safe_ratio(medium_or_high_manual, medium_or_high),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# en-ja Standalone Independence Broad Audit",
        "",
        "This is a sidecar diagnostic only. It does not change scores, admission, or runtime behavior.",
        "",
        "## Inputs",
        "",
        f"- Ranking: `{report['inputs']['ranking_csv']}`",
        f"- BCCWJ: `{report['inputs']['bccwj_sqlite']}`",
        f"- Aozora: `{report['inputs']['aozora_sqlite']}`",
        f"- JMDict: `{report['inputs']['jmdict']}`",
        f"- Candidate filter: rank <= `{report['inputs']['rank_max']}`, score <= `{report['inputs']['score_max']}`, surface length <= `{report['inputs']['surface_len_max']}`",
        f"- Candidate count: `{report['inputs']['candidate_count']}`",
        "",
        "## Summary",
        "",
        f"- Audited rows: `{summary['audited_row_count']}`",
        f"- Classifications: `{json.dumps(summary['classification_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- Pressure bands: `{json.dumps(summary['pressure_band_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- Manual compoundish corrections in audited rows: `{summary['manual_compoundish_correction_count']}`",
        f"- Manual compoundish recall by moderate pressure: `{summary['manual_compoundish_recalled_by_moderate_pressure']}` / `{summary['manual_compoundish_correction_count']}` = `{summary['manual_compoundish_moderate_pressure_recall']}`",
        f"- Manual compoundish recall by strong pressure: `{summary['manual_compoundish_recalled_by_strong_pressure']}` / `{summary['manual_compoundish_correction_count']}` = `{summary['manual_compoundish_strong_pressure_recall']}`",
        f"- Manual compoundish recall by severe pressure: `{summary['manual_compoundish_recalled_by_severe_pressure']}` / `{summary['manual_compoundish_correction_count']}` = `{summary['manual_compoundish_severe_pressure_recall']}`",
        f"- Strong-pressure rows already manual: `{summary['strong_pressure_already_manual_count']}` / `{summary['strong_pressure_count']}` = `{summary['strong_pressure_manual_share']}`",
        f"- High-confidence rows already manual: `{summary['high_confidence_already_manual_count']}` / `{summary['high_confidence_count']}` = `{summary['high_confidence_manual_share']}`",
        "",
        "## Top Candidates",
        "",
        row_table(report["top_candidates"]),
        "",
        "## High-Confidence Unreviewed",
        "",
        row_table(report["high_confidence_unreviewed"]),
        "",
        "## Known Manual Compoundish Hits",
        "",
        row_table(report["known_manual_hits"]),
        "",
        "## Interpretation",
        "",
        "- `high_confidence_compound_component`: strongest candidates for restricted admission or a frequency-ease discount.",
        "- `medium_confidence_compound_component`: review candidates; useful for recall, not safe as an automatic correction by itself.",
        "- `compound_rich_but_standalone_supported`: many compounds exist, but exact independent support or exact priority argues against demotion.",
        "- `independent_supported`: this probe should not be used to demote the row.",
        "- JMDict vocabulary-graph evidence counts only reading-compatible compounds: prefix, suffix, or multi-mora internal reading matches.",
        "",
    ]
    return "\n".join(lines)


def row_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_None._"
    lines = [
        "| Row | Score | Risk | Leak | Pressure | Class | Manual | Fx direct | Cx compounds | JMDict exact/compound/priority | Examples |",
        "| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        corpus = row["corpus"]
        mass = row["frequency_mass"]
        graph = row["jmdict_graph"]
        risk = row["risk"]
        ranking = row["ranking"]
        manual = row["manual"]
        examples = ", ".join(
            f"{example['surface']}/{example['reading']}"
            + f"[{float(example['log_combined_total']):.1f}]"
            + (
                f"@{example['ranking_score']:.3f}"
                if example.get("ranking_score") is not None
                else ""
            )
            for example in mass["compound_mass_examples"][:5]
        )
        manual_cell = (
            ",".join(manual["correction_types"])
            or manual["admission_override"]
            or ("yes" if manual["manual_correction_active"] else "")
        )
        lines.append(
            "| "
            f"`{escape(row['lemma'])}/{escape(row['reading'])}` | "
            f"{float(ranking['score']):.3f} | "
            f"{float(risk['compound_component_risk']):.3f} | "
            f"{float(mass['combined_log_leak_share']):.3f} | "
            f"`{escape(risk['pressure_band'])}` | "
            f"`{escape(risk['classification'])}` | "
            f"{escape(manual_cell)} | "
            f"{corpus['exact_independent_support']:.0f}/{corpus['exact_bound_support']:.0f} | "
            f"{mass['compound_bccwj_total']:.0f}+{mass['compound_aozora_total']:.0f} | "
            f"{graph['exact_entry_count']}/{graph['compound_entry_count']}/{graph['compound_priority_entry_count']} | "
            f"{escape(examples)} |"
        )
    return "\n".join(lines)


def compact_output_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "lemma": row["lemma"],
        "reading": row["reading"],
        "ranking": row["ranking"],
        "manual": row["manual"],
        "corpus": row["corpus"],
        "jmdict_graph": row["jmdict_graph"],
        "frequency_mass": row["frequency_mass"],
        "risk": row["risk"],
    }


def compact_ranking(row: Mapping[str, str]) -> dict[str, Any]:
    return {
        "rank": int(float(str(row.get("rank") or "0"))),
        "score": float(str(row.get("score") or "0")),
        "candidate_state": str(row.get("candidate_state") or ""),
        "correction_types": str(row.get("correction_types") or ""),
        "admission_override": str(row.get("admission_override") or ""),
        "jlpt_exact_known": truthy(row.get("jlpt_exact_known")),
        "exact_commonness": optional_float(row.get("exact_commonness")),
        "suspicion_full": optional_float(row.get("suspicion_full")),
    }


def public_graph_stats(stats: Mapping[str, Any], *, current_score: float) -> dict[str, Any]:
    examples = []
    for example in stats["compound_examples"][:12]:
        item = dict(example)
        item["easier_than_current"] = (
            item.get("ranking_score") is not None and float(item["ranking_score"]) < current_score
        )
        examples.append(item)
    return {
        "exact_entry_count": int(stats["exact_entry_count"]),
        "exact_priority_entry_count": int(stats["exact_priority_entry_count"]),
        "exact_priority_tags": list(stats["exact_priority_tags"]),
        "compound_entry_count": int(stats["compound_entry_count"]),
        "compound_priority_entry_count": int(stats["compound_priority_entry_count"]),
        "compound_ranked_entry_count": int(stats["compound_ranked_entry_count"]),
        "compound_priority_tags": list(stats["compound_priority_tags"]),
        "compound_position_counts": dict(stats["compound_position_counts"]),
        "compound_quality_counts": dict(stats["compound_quality_counts"]),
        "compound_examples": examples,
    }


def empty_graph_stats() -> dict[str, Any]:
    return {
        "_exact_entry_ids": set(),
        "_compound_entry_ids": set(),
        "exact_entry_count": 0,
        "exact_priority_entry_count": 0,
        "exact_priority_tags": set(),
        "compound_entry_count": 0,
        "compound_priority_entry_count": 0,
        "compound_ranked_entry_count": 0,
        "compound_priority_tags": set(),
        "_compound_keys": set(),
        "compound_position_counts": {},
        "compound_quality_counts": {},
        "compound_examples": [],
    }


def jmdict_entry_payload(elem: ET.Element) -> dict[str, Any]:
    ent_seq = elem.findtext("ent_seq") or ""
    forms = [
        {
            "text": child.findtext("keb") or "",
            "priorities": [node.text or "" for node in child.findall("ke_pri") if node.text],
        }
        for child in elem.findall("k_ele")
        if child.findtext("keb")
    ]
    readings = []
    for child in elem.findall("r_ele"):
        text = child.findtext("reb") or ""
        if not text:
            continue
        readings.append(
            {
                "text": text,
                "normalized": normalize_kana(text),
                "priorities": [node.text or "" for node in child.findall("re_pri") if node.text],
                "restrictions": [
                    node.text or "" for node in child.findall("re_restr") if node.text
                ],
            }
        )
    return {"ent_seq": ent_seq, "forms": forms, "readings": readings}


def reading_allowed_for_form(reading: Mapping[str, Any], form: str) -> bool:
    restrictions = {str(value) for value in reading.get("restrictions") or ()}
    return not restrictions or form in restrictions


def normalize_kana(value: str) -> str:
    chars = []
    for char in value:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6:
            chars.append(chr(code - 0x60))
        else:
            chars.append(char)
    return "".join(chars)


def contains_kanji(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def split_correction_types(value: str) -> list[str]:
    return [item.strip() for item in value.replace("|", ",").split(",") if item.strip()]


def is_compoundish_manual_correction(
    correction_types: Sequence[str],
    admission_override: str,
) -> bool:
    text = ",".join([*correction_types, admission_override]).lower()
    return "restricted_admission" in correction_types and any(
        word in text for word in COMPOUNDISH_ADMISSION_WORDS
    )


def truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def optional_float(value: object) -> float | None:
    try:
        text = str(value if value is not None else "").strip()
        return round(float(text), 6) if text else None
    except ValueError:
        return None


def optional_int(value: object) -> int | None:
    try:
        text = str(value if value is not None else "").strip()
        return int(float(text)) if text else None
    except ValueError:
        return None


def safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 6)


def safe_ratio_float(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 6)


def safe_share(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 6)


def score_sort_value(value: object) -> float:
    maybe = optional_float(value)
    return 2.0 if maybe is None else maybe


def compound_example_sort(example: Mapping[str, Any]) -> tuple[bool, float, int, str]:
    return (
        not bool(example.get("priority")),
        score_sort_value(example.get("ranking_score")),
        int(example.get("form_len") or 99),
        str(example.get("surface") or ""),
    )


def escape(value: object) -> str:
    return str(value).replace("|", "\\|")


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
