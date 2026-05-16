#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
from typing import Mapping, Sequence

from srs_animals_plants_existing_signal_rendering import render_markdown
from srs_animals_plants_signal_policy import (
    DEFAULT_SIGNAL_POLICY,
    SignalPolicy,
    load_signal_policy,
    normalize_source_label,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_FREQUENCY_DB = DEFAULT_DATA_ROOT / "frequency_packs" / "freq-es-cde.sqlite"
DEFAULT_KAIKKI_FORWARD_DB = DEFAULT_DATA_ROOT / "language_packs" / "wiktionary-es-en.sqlite"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_animals_plants_existing_signal_audit_en_es_current_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_animals_plants_existing_signal_audit_en_es_current_latest.md"
)
RANK_COLUMNS = ("core_rank", "rank", "id", "index")
FREQUENCY_VALUE_COLUMNS = (
    "pmw",
    "core_pmw",
    "frequency",
    "core_frequency",
    "freq",
    "freq_per_million",
    "count",
    "ipm",
)
FAMILIES = ("animals", "plants_nature")


@dataclass(frozen=True)
class Evidence:
    family: str
    lemma: str
    tier: str
    evidence_type: str
    source_channel: str
    source_label: str
    base_confidence: float
    specificity: float
    ambiguity_penalty: float
    score: float
    review_required: bool
    snippet: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "family": self.family,
            "lemma": self.lemma,
            "tier": self.tier,
            "evidence_type": self.evidence_type,
            "source_channel": self.source_channel,
            "source_label": self.source_label,
            "base_confidence": round(self.base_confidence, 6),
            "specificity": round(self.specificity, 6),
            "ambiguity_penalty": round(self.ambiguity_penalty, 6),
            "score": round(self.score, 6),
            "confidence_band": confidence_band(self.score),
            "review_required": self.review_required,
            "snippet": self.snippet,
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit how much animals/plants topic evidence can be extracted from existing "
            "local en-es sources. Read-only; no downloads and no pack mutation."
        )
    )
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_SIGNAL_POLICY)
    parser.add_argument("--frequency-db", type=Path, default=DEFAULT_FREQUENCY_DB)
    parser.add_argument("--kaikki-forward-db", type=Path, default=DEFAULT_KAIKKI_FORWARD_DB)
    parser.add_argument("--top-n", type=int, default=10000)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        policy_path=args.policy_json,
        frequency_db=args.frequency_db,
        kaikki_forward_db=args.kaikki_forward_db,
        top_n=max(1, int(args.top_n)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    policy_path: Path = DEFAULT_SIGNAL_POLICY,
    frequency_db: Path = DEFAULT_FREQUENCY_DB,
    kaikki_forward_db: Path = DEFAULT_KAIKKI_FORWARD_DB,
    top_n: int = 10000,
    generated_at: str | None = None,
) -> dict[str, object]:
    policy = load_signal_policy(policy_path)
    frequency_path = Path(frequency_db).expanduser().resolve(strict=False)
    kaikki_path = Path(kaikki_forward_db).expanduser().resolve(strict=False)
    if not frequency_path.exists() or not kaikki_path.exists():
        findings = []
        if not frequency_path.exists():
            findings.append(_finding("FAIL", "frequency_db_missing", "Frequency DB is missing."))
        if not kaikki_path.exists():
            findings.append(_finding("FAIL", "kaikki_db_missing", "Kaikki DB is missing."))
        return _report(
            status="review",
            generated_at=generated_at,
            frequency_db=frequency_path,
            kaikki_forward_db=kaikki_path,
            top_n=top_n,
            row_count=0,
            family_summaries=[],
            findings=findings,
            broad_exclusions=[],
            signal_policy=policy,
        )
    lemmas = list(dict.fromkeys(_candidate_lemmas(frequency_path, top_n=top_n)))
    source_rows = load_kaikki_rows(kaikki_path)
    evidence_by_family_lemma: dict[tuple[str, str], list[Evidence]] = defaultdict(list)
    broad_exclusions: list[dict[str, object]] = []
    for lemma in lemmas:
        rows = source_rows.get(lemma, [])
        for evidence in evidence_from_rows(lemma, rows, policy):
            evidence_by_family_lemma[(evidence.family, lemma)].append(evidence)
        if len(broad_exclusions) < 24:
            broad_hits = sorted(
                {
                    label
                    for row in rows
                    for label in row_labels(row)
                    if label in policy.broad_excluded_labels
                }
            )
            if broad_hits and not any(
                key[1] == lemma and values
                for key, values in evidence_by_family_lemma.items()
                if key[0] in FAMILIES
            ):
                broad_exclusions.append({"lemma": lemma, "excluded_labels": broad_hits})
    family_summaries = [
        summarize_family(family, lemmas, evidence_by_family_lemma) for family in FAMILIES
    ]
    findings = [
        _finding("PASS", "existing_sources_loaded", "Frequency and Kaikki DBs are available."),
        _finding(
            "PASS",
            "animals_plants_split_enforced",
            "Botany/plants evidence is reported separately from animal evidence.",
        ),
    ]
    animals = next(row for row in family_summaries if row["family"] == "animals")
    if int(animals["candidate_count"]) > 0:
        findings.append(
            _finding("PASS", "animal_evidence_found", "Existing sources contain animal evidence.")
        )
    else:
        findings.append(
            _finding("WARN", "animal_evidence_absent", "Existing sources found no animal evidence.")
        )
    plants = next(row for row in family_summaries if row["family"] == "plants_nature")
    if int(plants["candidate_count"]) > 0:
        findings.append(
            _finding(
                "PASS",
                "plants_nature_evidence_found",
                "Existing sources contain plants/nature evidence.",
            )
        )
    else:
        findings.append(
            _finding(
                "WARN",
                "plants_nature_evidence_absent",
                "Existing sources found no plants/nature evidence.",
            )
        )
    return _report(
        status="ok" if not any(row["level"] == "FAIL" for row in findings) else "review",
        generated_at=generated_at,
        frequency_db=frequency_path,
        kaikki_forward_db=kaikki_path,
        top_n=top_n,
        row_count=len(lemmas),
        family_summaries=family_summaries,
        findings=findings,
        broad_exclusions=broad_exclusions,
        signal_policy=policy,
    )


def _report(
    *,
    status: str,
    generated_at: str | None,
    frequency_db: Path,
    kaikki_forward_db: Path,
    top_n: int,
    row_count: int,
    family_summaries: Sequence[Mapping[str, object]],
    findings: Sequence[Mapping[str, object]],
    broad_exclusions: Sequence[Mapping[str, object]],
    signal_policy: SignalPolicy,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "animals_plants_existing_signal_audit_completed"
            if status == "ok"
            else "animals_plants_existing_signal_audit_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "inputs": {
            "signal_policy_json": str(signal_policy.path),
            "signal_policy_id": signal_policy.policy_id,
            "frequency_db": str(frequency_db),
            "kaikki_forward_db": str(kaikki_forward_db),
            "top_n": int(top_n),
        },
        "confidence_model": {
            "combiner": "max_evidence_score_v1",
            "score_formula": "base_confidence * specificity * ambiguity_penalty",
            "bands": {
                "high": ">= 0.85, eligible for strong admission lift after policy adoption",
                "medium": ">= 0.65 and < 0.85, eligible for light lift or overlay review",
                "review": ">= 0.45 and < 0.65, review-gated inventory",
                "inventory": "< 0.45, not counted as product-ready evidence",
            },
            "tier_policy": {
                "A": "explicit sense_topics, highest trust",
                "B": "primary-sense exact noun translation, high trust",
                "C": "allowlisted categories/tags from existing Kaikki fields",
                "D": "narrow translation/gloss patterns, review-gated",
            },
            "penalty_policy": {
                "secondary_sense": "0.70 multiplier for non-primary sense rows",
                "ambiguous_context": "0.70 multiplier when unrelated domain labels are present",
            },
        },
        "row_count": int(row_count),
        "families": list(family_summaries),
        "broad_exclusions": list(broad_exclusions),
        "findings": list(findings),
        "summary": {
            "finding_counts": dict(Counter(row["level"] for row in findings)),
            "issues": [row["code"] for row in findings if row["level"] == "FAIL"],
            "warnings": [row["code"] for row in findings if row["level"] == "WARN"],
        },
        "limitations": [
            "This audit uses only existing local frequency and Kaikki/Wiktionary data.",
            "It does not write overlays, mutate packs, or change admission behavior.",
            "Tier C category allowlists are intentionally narrow.",
            "Tier D gloss/translation evidence is review-gated and should be sampled before product lift.",
        ],
    }


def evidence_from_rows(
    lemma: str, rows: Sequence[Mapping[str, object]], policy: SignalPolicy
) -> list[Evidence]:
    evidence: list[Evidence] = []
    animal_topic_labels = policy.topic_confidence.get("animals", {})
    plant_topic_labels = policy.topic_confidence.get("plants_nature", {})
    animal_category_confidence = policy.category_confidence.get("animals", {})
    plant_category_confidence = policy.category_confidence.get("plants_nature", {})
    animal_primary_translations = policy.primary_translations.get("animals", frozenset())
    plant_primary_translations = policy.primary_translations.get("plants_nature", frozenset())
    for row in rows:
        row_context = row_labels(row)
        ambiguity_penalty = _combined_penalty(row, row_context, policy)
        for topic_value in _string_list(row.get("topics")):
            topic = normalize_source_label(topic_value)
            if topic in animal_topic_labels:
                evidence.append(
                    make_evidence(
                        family="animals",
                        lemma=lemma,
                        tier="A",
                        evidence_type="explicit_sense_topic",
                        source_channel="sense_topics",
                        source_label=topic,
                        base_confidence=animal_topic_labels[topic],
                        specificity=1.0,
                        ambiguity_penalty=ambiguity_penalty,
                        review_required=False,
                    )
                )
            if topic in plant_topic_labels:
                evidence.append(
                    make_evidence(
                        family="plants_nature",
                        lemma=lemma,
                        tier="A",
                        evidence_type="explicit_sense_topic",
                        source_channel="sense_topics",
                        source_label=topic,
                        base_confidence=plant_topic_labels[topic],
                        specificity=1.0,
                        ambiguity_penalty=ambiguity_penalty,
                        review_required=False,
                    )
                )
        for channel in ("sense_categories", "entry_categories", "sense_tags", "entry_tags"):
            for label in _string_list(row.get(channel)):
                normalized_label = normalize_source_label(label)
                if normalized_label in animal_category_confidence:
                    evidence.append(
                        make_evidence(
                            family="animals",
                            lemma=lemma,
                            tier="C",
                            evidence_type="allowlisted_category_or_tag",
                            source_channel=channel,
                            source_label=normalized_label,
                            base_confidence=animal_category_confidence[normalized_label],
                            specificity=0.95,
                            ambiguity_penalty=ambiguity_penalty,
                            review_required=False,
                        )
                    )
                if normalized_label in plant_category_confidence:
                    evidence.append(
                        make_evidence(
                            family="plants_nature",
                            lemma=lemma,
                            tier="C",
                            evidence_type="allowlisted_category_or_tag",
                            source_channel=channel,
                            source_label=normalized_label,
                            base_confidence=plant_category_confidence[normalized_label],
                            specificity=0.95,
                            ambiguity_penalty=ambiguity_penalty,
                            review_required=False,
                        )
                    )
        text_fields = _sense_text(row)
        animal_primary = _primary_translation_match(
            text_fields["translation"], animal_primary_translations
        )
        plant_primary = _primary_translation_match(
            text_fields["translation"], plant_primary_translations
        )
        if animal_primary and _is_primary_noun_sense(row):
            evidence.append(
                make_evidence(
                    family="animals",
                    lemma=lemma,
                    tier="B",
                    evidence_type="primary_exact_translation",
                    source_channel="translation",
                    source_label=f"primary_translation:{animal_primary}",
                    base_confidence=0.9,
                    specificity=0.95,
                    ambiguity_penalty=ambiguity_penalty,
                    review_required=False,
                    snippet=text_fields["translation"][:160],
                )
            )
        elif policy.animal_translation_pattern.search(text_fields["translation"]):
            evidence.append(
                make_evidence(
                    family="animals",
                    lemma=lemma,
                    tier="D",
                    evidence_type="narrow_translation_pattern",
                    source_channel="translation",
                    source_label="animal_translation_pattern",
                    base_confidence=0.72,
                    specificity=0.9,
                    ambiguity_penalty=ambiguity_penalty,
                    review_required=True,
                    snippet=text_fields["translation"][:160],
                )
            )
        elif policy.animal_gloss_pattern.search(text_fields["combined"]):
            evidence.append(
                make_evidence(
                    family="animals",
                    lemma=lemma,
                    tier="D",
                    evidence_type="narrow_gloss_pattern",
                    source_channel="gloss_or_translation",
                    source_label="animal_gloss_pattern",
                    base_confidence=0.62,
                    specificity=0.85,
                    ambiguity_penalty=ambiguity_penalty,
                    review_required=True,
                    snippet=text_fields["combined"][:160],
                )
            )
        if plant_primary and _is_primary_noun_sense(row):
            evidence.append(
                make_evidence(
                    family="plants_nature",
                    lemma=lemma,
                    tier="B",
                    evidence_type="primary_exact_translation",
                    source_channel="translation",
                    source_label=f"primary_translation:{plant_primary}",
                    base_confidence=0.9,
                    specificity=0.95,
                    ambiguity_penalty=ambiguity_penalty,
                    review_required=False,
                    snippet=text_fields["translation"][:160],
                )
            )
        elif policy.plant_translation_pattern.search(text_fields["translation"]):
            evidence.append(
                make_evidence(
                    family="plants_nature",
                    lemma=lemma,
                    tier="D",
                    evidence_type="narrow_translation_pattern",
                    source_channel="translation",
                    source_label="plant_translation_pattern",
                    base_confidence=0.72,
                    specificity=0.9,
                    ambiguity_penalty=ambiguity_penalty,
                    review_required=True,
                    snippet=text_fields["translation"][:160],
                )
            )
        elif policy.plant_gloss_pattern.search(text_fields["combined"]):
            evidence.append(
                make_evidence(
                    family="plants_nature",
                    lemma=lemma,
                    tier="D",
                    evidence_type="narrow_gloss_pattern",
                    source_channel="gloss_or_translation",
                    source_label="plant_gloss_pattern",
                    base_confidence=0.62,
                    specificity=0.85,
                    ambiguity_penalty=ambiguity_penalty,
                    review_required=True,
                    snippet=text_fields["combined"][:160],
                )
            )
    return evidence


def _combined_penalty(
    row: Mapping[str, object], row_context: set[str], policy: SignalPolicy
) -> float:
    penalty = 1.0
    if row_context & policy.ambiguous_context_labels:
        penalty *= 0.7
    if _sense_index(row) > 0:
        penalty *= 0.7
    return penalty


def _is_primary_noun_sense(row: Mapping[str, object]) -> bool:
    return _sense_index(row) == 0 and _is_noun_pos(row.get("pos"))


def _sense_index(row: Mapping[str, object]) -> int:
    value = row.get("sense_index")
    return value if isinstance(value, int) else 0


def _is_noun_pos(value: object) -> bool:
    return str(value or "").strip().casefold() in {"noun", "n", "sustantivo"}


def _primary_translation_match(translation: str, allowlist: set[str] | frozenset[str]) -> str:
    item = _first_translation_item(translation)
    return item if item in allowlist else ""


def _first_translation_item(translation: str) -> str:
    text = str(translation or "").strip().casefold()
    if not text:
        return ""
    text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"^\([^)]*\)\s*", "", text)
    first = re.split(r"[,;]", text, maxsplit=1)[0]
    first = re.sub(r"\([^)]*\)", "", first).strip()
    first = re.sub(r"^(?:a|an|the)\s+", "", first).strip()
    first = re.sub(r"\s+", " ", first)
    return first


def make_evidence(
    *,
    family: str,
    lemma: str,
    tier: str,
    evidence_type: str,
    source_channel: str,
    source_label: str,
    base_confidence: float,
    specificity: float,
    ambiguity_penalty: float,
    review_required: bool,
    snippet: str = "",
) -> Evidence:
    score = max(0.0, min(1.0, base_confidence * specificity * ambiguity_penalty))
    return Evidence(
        family=family,
        lemma=lemma,
        tier=tier,
        evidence_type=evidence_type,
        source_channel=source_channel,
        source_label=source_label,
        base_confidence=base_confidence,
        specificity=specificity,
        ambiguity_penalty=ambiguity_penalty,
        score=score,
        review_required=review_required,
        snippet=snippet,
    )


def summarize_family(
    family: str,
    lemmas: Sequence[str],
    evidence_by_family_lemma: Mapping[tuple[str, str], Sequence[Evidence]],
) -> dict[str, object]:
    best_rows: list[dict[str, object]] = []
    tier_counter: Counter[str] = Counter()
    band_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter()
    review_required_count = 0
    for lemma in lemmas:
        rows = list(evidence_by_family_lemma.get((family, lemma), ()))
        if not rows:
            continue
        rows.sort(key=lambda row: (-row.score, row.tier, row.source_label))
        best = rows[0]
        best_band = confidence_band(best.score)
        requires_review = best.review_required or best_band == "review"
        best_rows.append(
            {
                "lemma": lemma,
                "confidence": round(best.score, 6),
                "confidence_band": best_band,
                "best_tier": best.tier,
                "review_required": requires_review,
                "evidence": [row.to_dict() for row in rows[:6]],
            }
        )
        tier_counter[best.tier] += 1
        band_counter[best_band] += 1
        source_counter[best.source_label] += 1
        if requires_review:
            review_required_count += 1
    best_rows.sort(key=lambda row: (-float(row["confidence"]), str(row["lemma"])))
    return {
        "family": family,
        "candidate_count": len(best_rows),
        "candidate_share": _ratio(len(best_rows), len(lemmas)),
        "review_required_count": review_required_count,
        "tier_counts": dict(sorted(tier_counter.items())),
        "confidence_band_counts": {
            band: band_counter.get(band, 0) for band in ("high", "medium", "review", "inventory")
        },
        "top_source_labels": _counter_rows(source_counter),
        "candidate_inventory": best_rows,
        "top_candidates": best_rows[:20],
        "review_candidates": [row for row in best_rows if row["review_required"]][:20],
    }


def load_kaikki_rows(path: Path) -> dict[str, list[dict[str, object]]]:
    rows_by_lemma: dict[str, list[dict[str, object]]] = defaultdict(list)
    entry_meta_by_ord: dict[int, dict[str, object]] = {}
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute(
            "SELECT entry_ord, headword_lc, tags_json, categories_json FROM entry_meta"
        ):
            entry_meta_by_ord[int(row["entry_ord"])] = {
                "entry_tags": _json_string_list(row["tags_json"]),
                "entry_categories": _json_string_list(row["categories_json"]),
            }
        sense_columns = _column_names(conn, "sense_glosses")
        entry_ord_select = _optional_select_expr(sense_columns, "entry_ord", "rowid", "entry_ord")
        sense_ord_select = _optional_select_expr(sense_columns, "sense_ord", "rowid", "sense_ord")
        gloss_ord_select = _optional_select_expr(sense_columns, "gloss_ord", "rowid", "gloss_ord")
        pos_select = _optional_select_expr(sense_columns, "pos", "''", "pos")
        for row in conn.execute(
            f"SELECT {entry_ord_select}, headword_lc, translation, raw_glosses_json, tags_json, "
            f"topics_json, categories_json, {pos_select}, {sense_ord_select}, {gloss_ord_select}, "
            "rowid AS rowid FROM sense_glosses "
            "ORDER BY headword_lc, entry_ord, sense_ord, gloss_ord, rowid"
        ):
            lemma = _normalize_lemma(row["headword_lc"])
            if not lemma:
                continue
            entry_meta = entry_meta_by_ord.get(int(row["entry_ord"]), {})
            rows_by_lemma[lemma].append(
                {
                    "sort_key": (
                        _safe_int(row["entry_ord"]),
                        _safe_int(row["sense_ord"]),
                        _safe_int(row["gloss_ord"]),
                        _safe_int(row["rowid"]),
                    ),
                    "pos": str(row["pos"] or ""),
                    "translation": str(row["translation"] or ""),
                    "raw_glosses": _json_string_list(row["raw_glosses_json"]),
                    "topics": _json_string_list(row["topics_json"]),
                    "sense_tags": _json_string_list(row["tags_json"]),
                    "sense_categories": _json_string_list(row["categories_json"]),
                    "entry_tags": _string_list(entry_meta.get("entry_tags")),
                    "entry_categories": _string_list(entry_meta.get("entry_categories")),
                }
            )
    for lemma, rows in rows_by_lemma.items():
        rows.sort(key=lambda row: row.get("sort_key", (0, 0, 0, 0)))
        for index, row in enumerate(rows):
            row["sense_index"] = index
    return rows_by_lemma


def confidence_band(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.65:
        return "medium"
    if score >= 0.45:
        return "review"
    return "inventory"


def row_labels(row: Mapping[str, object]) -> set[str]:
    labels: set[str] = set()
    for key in (
        "topics",
        "sense_tags",
        "sense_categories",
        "entry_tags",
        "entry_categories",
    ):
        labels.update(normalize_source_label(value) for value in _string_list(row.get(key)))
    return {label for label in labels if label}


def _sense_text(row: Mapping[str, object]) -> dict[str, str]:
    translation = str(row.get("translation") or "").strip().casefold()
    glosses = " ".join(_string_list(row.get("raw_glosses"))).casefold()
    combined = " ".join(part for part in (translation, glosses) if part)
    return {"translation": translation, "combined": combined}


def _candidate_lemmas(path: Path, *, top_n: int) -> list[str]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        columns = _column_names(conn, "frequency")
        lemma_column = _resolve_column("lemma", columns)
        if not lemma_column:
            return []
        rank_column = _resolve_first_column(RANK_COLUMNS, columns)
        frequency_column = _resolve_first_column(FREQUENCY_VALUE_COLUMNS, columns)
        order_terms: list[str] = []
        if rank_column:
            order_terms.append(f"{_quote_identifier(rank_column)} IS NULL ASC")
            order_terms.append(f"{_quote_identifier(rank_column)} ASC")
        if frequency_column:
            order_terms.append(f"{_quote_identifier(frequency_column)} DESC")
        order_sql = f" ORDER BY {', '.join(order_terms)}" if order_terms else ""
        sql = f"SELECT {_quote_identifier(lemma_column)} FROM frequency{order_sql} LIMIT ?"
        return [
            _normalize_lemma(row[lemma_column])
            for row in conn.execute(sql, (max(1, int(top_n)),))
            if _normalize_lemma(row[lemma_column])
        ]
    finally:
        conn.close()


def _column_names(conn: sqlite3.Connection, table_name: str) -> list[str]:
    return [str(row[1]) for row in conn.execute(f"PRAGMA table_info({table_name})")]


def _optional_select_expr(
    columns: Sequence[str], column_name: str, fallback_sql: str, alias: str
) -> str:
    if column_name in columns:
        return f"{_quote_identifier(column_name)} AS {_quote_identifier(alias)}"
    return f"{fallback_sql} AS {_quote_identifier(alias)}"


def _resolve_column(requested: str, columns: Sequence[str]) -> str | None:
    lowered = {column.lower(): column for column in columns}
    return lowered.get(str(requested).strip().lower())


def _resolve_first_column(candidates: Sequence[str], columns: Sequence[str]) -> str | None:
    for candidate in candidates:
        resolved = _resolve_column(candidate, columns)
        if resolved:
            return resolved
    return None


def _safe_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _json_string_list(value: object) -> list[str]:
    if value is None:
        return []
    text = str(value or "").strip()
    if not text or text == "[]":
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return [text]
    if not isinstance(payload, list):
        return []
    return [str(item) for item in payload if str(item).strip()]


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, set):
        return sorted(str(item) for item in value if str(item).strip())
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return []


def _counter_rows(counter: Counter[str]) -> list[dict[str, object]]:
    return [{"label": label, "count": count} for label, count in counter.most_common(20)]


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _quote_identifier(value: object) -> str:
    return '"' + str(value).replace('"', '""') + '"'


def _normalize_lemma(value: object) -> str:
    return str(value or "").strip().casefold()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
