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
BROAD_EXCLUDED_LABELS = {
    "biology",
    "hobbies",
    "lifestyle",
    "natural_sciences",
    "sciences",
}
ANIMAL_TOPIC_LABELS = {
    "animals": 0.95,
    "zoology": 0.9,
    "veterinary": 0.85,
}
PLANT_TOPIC_LABELS = {
    "botany": 0.9,
}
ANIMAL_CATEGORY_CONFIDENCE = {
    "animals": 0.84,
    "baby_animals": 0.82,
    "birds": 0.84,
    "cats": 0.84,
    "dogs": 0.84,
    "fish": 0.82,
    "horses": 0.84,
    "mammals": 0.82,
    "sheep": 0.84,
    "zoology": 0.8,
}
PLANT_CATEGORY_CONFIDENCE = {
    "botany": 0.82,
    "flowers": 0.82,
    "plants": 0.82,
    "trees": 0.82,
    "willows_and_poplars": 0.78,
}
ANIMAL_TRANSLATION_PATTERN = re.compile(
    r"^(?:a |an |the )?"
    r"(?:animal|bird|cat|cattle|cow|deer|dog|fish|foal|goat|horse|insect|mammal|"
    r"pig|rabbit|reptile|sheep|snake|spider|wolf)\b"
)
ANIMAL_GLOSS_PATTERN = re.compile(
    r"\b(?:species|breed|genus|family|type|kind) of "
    r"(?:animal|bird|cat|dog|fish|horse|insect|mammal|reptile|sheep)s?\b|"
    r"\b(?:catfish|dogfish|mammal|reptile|amphibian)\b"
)
PLANT_TRANSLATION_PATTERN = re.compile(r"^(?:a |an |the )?(?:flower|plant|shrub|tree|vine)\b")
PLANT_GLOSS_PATTERN = re.compile(
    r"\b(?:species|genus|family|type|kind) of (?:flower|plant|shrub|tree|vine)s?\b|"
    r"\b(?:flowering plant|woody plant|perennial plant)\b"
)
AMBIGUOUS_CONTEXT_LABELS = {
    "anatomy",
    "architecture",
    "astrology",
    "chess",
    "colors",
    "games",
    "genitalia",
    "heraldry",
    "medicine",
    "people",
    "tools",
}


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
    frequency_db: Path = DEFAULT_FREQUENCY_DB,
    kaikki_forward_db: Path = DEFAULT_KAIKKI_FORWARD_DB,
    top_n: int = 10000,
    generated_at: str | None = None,
) -> dict[str, object]:
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
        )
    lemmas = list(dict.fromkeys(_candidate_lemmas(frequency_path, top_n=top_n)))
    source_rows = load_kaikki_rows(kaikki_path)
    evidence_by_family_lemma: dict[tuple[str, str], list[Evidence]] = defaultdict(list)
    broad_exclusions: list[dict[str, object]] = []
    for lemma in lemmas:
        rows = source_rows.get(lemma, [])
        for evidence in evidence_from_rows(lemma, rows):
            evidence_by_family_lemma[(evidence.family, lemma)].append(evidence)
        if len(broad_exclusions) < 24:
            broad_hits = sorted(
                {
                    label
                    for row in rows
                    for label in row_labels(row)
                    if label in BROAD_EXCLUDED_LABELS
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
                "C": "allowlisted categories/tags from existing Kaikki fields",
                "D": "narrow translation/gloss patterns, review-gated",
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


def evidence_from_rows(lemma: str, rows: Sequence[Mapping[str, object]]) -> list[Evidence]:
    evidence: list[Evidence] = []
    for row in rows:
        row_context = row_labels(row)
        ambiguity_penalty = 0.7 if row_context & AMBIGUOUS_CONTEXT_LABELS else 1.0
        for topic_value in _string_list(row.get("topics")):
            topic = normalize_source_label(topic_value)
            if topic in ANIMAL_TOPIC_LABELS:
                evidence.append(
                    make_evidence(
                        family="animals",
                        lemma=lemma,
                        tier="A",
                        evidence_type="explicit_sense_topic",
                        source_channel="sense_topics",
                        source_label=topic,
                        base_confidence=ANIMAL_TOPIC_LABELS[topic],
                        specificity=1.0,
                        ambiguity_penalty=ambiguity_penalty,
                        review_required=False,
                    )
                )
            if topic in PLANT_TOPIC_LABELS:
                evidence.append(
                    make_evidence(
                        family="plants_nature",
                        lemma=lemma,
                        tier="A",
                        evidence_type="explicit_sense_topic",
                        source_channel="sense_topics",
                        source_label=topic,
                        base_confidence=PLANT_TOPIC_LABELS[topic],
                        specificity=1.0,
                        ambiguity_penalty=ambiguity_penalty,
                        review_required=False,
                    )
                )
        for channel in ("sense_categories", "entry_categories", "sense_tags", "entry_tags"):
            for label in _string_list(row.get(channel)):
                normalized_label = normalize_source_label(label)
                if normalized_label in ANIMAL_CATEGORY_CONFIDENCE:
                    evidence.append(
                        make_evidence(
                            family="animals",
                            lemma=lemma,
                            tier="C",
                            evidence_type="allowlisted_category_or_tag",
                            source_channel=channel,
                            source_label=normalized_label,
                            base_confidence=ANIMAL_CATEGORY_CONFIDENCE[normalized_label],
                            specificity=0.95,
                            ambiguity_penalty=ambiguity_penalty,
                            review_required=False,
                        )
                    )
                if normalized_label in PLANT_CATEGORY_CONFIDENCE:
                    evidence.append(
                        make_evidence(
                            family="plants_nature",
                            lemma=lemma,
                            tier="C",
                            evidence_type="allowlisted_category_or_tag",
                            source_channel=channel,
                            source_label=normalized_label,
                            base_confidence=PLANT_CATEGORY_CONFIDENCE[normalized_label],
                            specificity=0.95,
                            ambiguity_penalty=ambiguity_penalty,
                            review_required=False,
                        )
                    )
        text_fields = _sense_text(row)
        if ANIMAL_TRANSLATION_PATTERN.search(text_fields["translation"]):
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
        elif ANIMAL_GLOSS_PATTERN.search(text_fields["combined"]):
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
        if PLANT_TRANSLATION_PATTERN.search(text_fields["translation"]):
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
        elif PLANT_GLOSS_PATTERN.search(text_fields["combined"]):
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
        for row in conn.execute(
            "SELECT entry_ord, headword_lc, translation, raw_glosses_json, tags_json, "
            "topics_json, categories_json FROM sense_glosses"
        ):
            lemma = _normalize_lemma(row["headword_lc"])
            if not lemma:
                continue
            entry_meta = entry_meta_by_ord.get(int(row["entry_ord"]), {})
            rows_by_lemma[lemma].append(
                {
                    "translation": str(row["translation"] or ""),
                    "raw_glosses": _json_string_list(row["raw_glosses_json"]),
                    "topics": _json_string_list(row["topics_json"]),
                    "sense_tags": _json_string_list(row["tags_json"]),
                    "sense_categories": _json_string_list(row["categories_json"]),
                    "entry_tags": _string_list(entry_meta.get("entry_tags")),
                    "entry_categories": _string_list(entry_meta.get("entry_categories")),
                }
            )
    return rows_by_lemma


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Animals/Plants Existing Signal Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Rows measured: `{report.get('row_count', 0)}`",
        "",
        "## Findings",
        "",
    ]
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
            f"{finding.get('message', '')}"
        )
    lines.extend(["", "## Family Summary", ""])
    lines.append("| Family | Candidates | Share | Tiers | Confidence Bands | Review Required |")
    lines.append("| --- | ---: | ---: | --- | --- | ---: |")
    for family in _mapping_rows(report.get("families")):
        lines.append(
            f"| `{family.get('family', '')}` | {family.get('candidate_count', 0)} | "
            f"{_pct(family.get('candidate_share'))} | {_compact_counts(family.get('tier_counts'))} | "
            f"{_compact_counts(family.get('confidence_band_counts'))} | "
            f"{family.get('review_required_count', 0)} |"
        )
    for family in _mapping_rows(report.get("families")):
        lines.extend(["", f"## `{family.get('family', '')}` Top Candidates", ""])
        rows = _mapping_rows(family.get("top_candidates"))
        if not rows:
            lines.append("_No candidates found._")
            continue
        lines.append("| Lemma | Confidence | Band | Tier | Evidence |")
        lines.append("| --- | ---: | --- | --- | --- |")
        for row in rows[:12]:
            evidence = _mapping_rows(row.get("evidence"))
            top_evidence = evidence[0] if evidence else {}
            lines.append(
                f"| `{row.get('lemma', '')}` | {row.get('confidence', 0)} | "
                f"`{row.get('confidence_band', '')}` | `{row.get('best_tier', '')}` | "
                f"`{top_evidence.get('source_channel', '')}:{top_evidence.get('source_label', '')}` |"
            )
    lines.extend(["", "## Broad Exclusions Sample", ""])
    broad_exclusions = _mapping_rows(report.get("broad_exclusions"))
    if not broad_exclusions:
        lines.append("_No broad-only exclusions sampled._")
    else:
        lines.append("| Lemma | Excluded Labels |")
        lines.append("| --- | --- |")
        for row in broad_exclusions[:12]:
            lines.append(
                f"| `{row.get('lemma', '')}` | `{', '.join(row.get('excluded_labels', []))}` |"
            )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines) + "\n"


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


def normalize_source_label(value: object) -> str:
    text = str(value or "").strip()
    if ":" in text:
        prefix, suffix = text.split(":", 1)
        if prefix.lower() in {"es", "spanish"} and suffix.strip():
            text = suffix
    return _normalize_token(text)


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


def _resolve_column(requested: str, columns: Sequence[str]) -> str | None:
    lowered = {column.lower(): column for column in columns}
    return lowered.get(str(requested).strip().lower())


def _resolve_first_column(candidates: Sequence[str], columns: Sequence[str]) -> str | None:
    for candidate in candidates:
        resolved = _resolve_column(candidate, columns)
        if resolved:
            return resolved
    return None


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


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _counter_rows(counter: Counter[str]) -> list[dict[str, object]]:
    return [{"label": label, "count": count} for label, count in counter.most_common(20)]


def _compact_counts(value: object) -> str:
    mapping = value if isinstance(value, Mapping) else {}
    return ", ".join(f"{key}={value}" for key, value in mapping.items()) or "none"


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _quote_identifier(value: object) -> str:
    return '"' + str(value).replace('"', '""') + '"'


def _normalize_token(value: object) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    normalized = raw.replace("\\", "_").replace("/", "_").replace("-", "_").replace(" ", "_")
    normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _normalize_lemma(value: object) -> str:
    return str(value or "").strip().casefold()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
