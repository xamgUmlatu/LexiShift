#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sqlite3
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path.home() / "Library" / "Application Support" / "LexiShift" / "LexiShift"
DEFAULT_RANKING_CSV = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_en_ja_latest.csv"
)
DEFAULT_BCCWJ_SQLITE = DATA_ROOT / "frequency_packs" / "freq-ja-bccwj" / "main.sqlite"
DEFAULT_AOZORA_SQLITE = DATA_ROOT / "frequency_packs" / "freq-ja-aozora-word" / "main.sqlite"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_standalone_independence_probe_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_standalone_independence_probe_en_ja_latest.md"
)

DEFAULT_TARGETS = (
    ("必用", "ひつよう"),
    ("面", "おも"),
    ("妙", "たえ"),
    ("代", "よ"),
    ("高", "こう"),
    ("主", "あるじ"),
    ("強い", "こわい"),
    ("盲", "めくら"),
    ("盲", "めしい"),
    ("故", "け"),
    ("項", "うなじ"),
    ("然り", "さり"),
    ("女", "め"),
    ("心", "しん"),
    ("林", "りん"),
    ("水道", "みずみち"),
    ("石", "せき"),
    ("骨", "こつ"),
    ("昼間", "ちゅうかん"),
    ("工場", "こうば"),
    ("国境", "くにざかい"),
    ("雷", "いかずち"),
)
INDEPENDENT_AOZORA_POS_MAJOR = {"名詞", "動詞", "形容詞", "副詞", "連体詞", "感動詞"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe whether en-ja learner-difficulty rows are independently used "
            "or mostly supported by bound/compound evidence in existing BCCWJ "
            "and Aozora sidecar data."
        )
    )
    parser.add_argument("--ranking-csv", type=Path, default=DEFAULT_RANKING_CSV)
    parser.add_argument("--bccwj-sqlite", type=Path, default=DEFAULT_BCCWJ_SQLITE)
    parser.add_argument("--aozora-sqlite", type=Path, default=DEFAULT_AOZORA_SQLITE)
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Exact target as surface/reading. May be repeated. Defaults to current concern rows.",
    )
    parser.add_argument("--compound-example-limit", type=int, default=8)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    ranking_csv = _resolve_path(args.ranking_csv)
    bccwj_sqlite = _resolve_path(args.bccwj_sqlite)
    aozora_sqlite = _resolve_path(args.aozora_sqlite)
    targets = parse_targets(args.target) or list(DEFAULT_TARGETS)
    report = build_report(
        ranking_csv=ranking_csv,
        bccwj_sqlite=bccwj_sqlite,
        aozora_sqlite=aozora_sqlite,
        targets=targets,
        compound_example_limit=max(0, int(args.compound_example_limit)),
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
    targets: Sequence[tuple[str, str]],
    compound_example_limit: int,
) -> dict[str, Any]:
    if not bccwj_sqlite.exists():
        raise SystemExit(f"Missing BCCWJ SQLite: {bccwj_sqlite}")
    if not aozora_sqlite.exists():
        raise SystemExit(f"Missing Aozora SQLite: {aozora_sqlite}")
    ranking = load_ranking(ranking_csv)
    rows: list[dict[str, Any]] = []
    with sqlite3.connect(bccwj_sqlite) as bccwj, sqlite3.connect(aozora_sqlite) as aozora:
        bccwj.row_factory = sqlite3.Row
        aozora.row_factory = sqlite3.Row
        for surface, reading in targets:
            row = build_row(
                surface=surface,
                reading=reading,
                ranking_row=ranking.get((surface, reading), {}),
                bccwj=bccwj,
                aozora=aozora,
                compound_example_limit=compound_example_limit,
            )
            rows.append(row)
    summary = summarize(rows)
    return {
        "schema_version": 1,
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "scores_changed": False,
        "purpose": (
            "Sidecar diagnostic for standalone lexical independence using existing "
            "BCCWJ and Aozora morphology aggregates."
        ),
        "inputs": {
            "ranking_csv": repo_path(ranking_csv),
            "bccwj_sqlite": str(bccwj_sqlite),
            "aozora_sqlite": str(aozora_sqlite),
            "compound_example_limit": compound_example_limit,
        },
        "summary": summary,
        "rows": rows,
    }


def load_ranking(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {(str(row["lemma"]), str(row["reading"])): row for row in csv.DictReader(handle)}


def build_row(
    *,
    surface: str,
    reading: str,
    ranking_row: Mapping[str, str],
    bccwj: sqlite3.Connection,
    aozora: sqlite3.Connection,
    compound_example_limit: int,
) -> dict[str, Any]:
    reading_kata = hira_to_kata(reading)
    bccwj_stats = bccwj_exact_stats(bccwj, surface=surface, reading=reading_kata)
    aozora_stats = aozora_exact_stats(aozora, surface=surface, reading=reading_kata)
    compounds = aozora_compound_stats(
        aozora,
        surface=surface,
        reading=reading_kata,
        limit=compound_example_limit,
    )
    evidence = classify_evidence(
        bccwj_stats=bccwj_stats,
        aozora_stats=aozora_stats,
        compound_count=int(compounds["trusted_token_count"]),
    )
    return {
        "surface": surface,
        "reading": reading,
        "reading_katakana": reading_kata,
        "ranking": compact_ranking(ranking_row),
        "bccwj": bccwj_stats,
        "aozora": {
            **aozora_stats,
            "compound_match_reliable": bool(compounds["match_reliable"]),
            "compound_trusted_token_count": int(compounds["trusted_token_count"]),
            "compound_trusted_work_count": int(compounds["trusted_work_count"]),
            "compound_raw_token_count": int(compounds["raw_token_count"]),
            "compound_raw_work_count": int(compounds["raw_work_count"]),
            "compound_proper_token_count": int(compounds["proper_token_count"]),
            "compound_examples": compounds["examples"],
        },
        "metrics": evidence["metrics"],
        "classification": evidence["classification"],
        "suggested_action": evidence["suggested_action"],
        "explanation": evidence["explanation"],
    }


def bccwj_exact_stats(
    conn: sqlite3.Connection,
    *,
    surface: str,
    reading: str,
) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT pos, SUM(COALESCE(frequency, 0.0)) AS frequency,
               SUM(COALESCE(core_frequency, 0.0)) AS core_frequency
        FROM frequency
        WHERE lemma = ? AND lform = ?
        GROUP BY pos
        ORDER BY frequency DESC
        """,
        (surface, reading),
    ).fetchall()
    independent = 0.0
    bound = 0.0
    proper = 0.0
    other = 0.0
    pos_breakdown: list[dict[str, Any]] = []
    for row in rows:
        pos = str(row["pos"] or "")
        frequency = float(row["frequency"] or 0.0)
        core_frequency = float(row["core_frequency"] or 0.0)
        bucket = bccwj_pos_bucket(pos)
        if bucket == "independent":
            independent += frequency
        elif bucket == "bound":
            bound += frequency
        elif bucket == "proper":
            proper += frequency
        else:
            other += frequency
        pos_breakdown.append(
            {
                "pos": pos,
                "bucket": bucket,
                "frequency": rounded(frequency),
                "core_frequency": rounded(core_frequency),
            }
        )
    total = independent + bound + proper + other
    return {
        "independent_frequency": rounded(independent),
        "bound_frequency": rounded(bound),
        "proper_frequency": rounded(proper),
        "other_frequency": rounded(other),
        "total_frequency": rounded(total),
        "independence_share": share(independent, total),
        "bound_share": share(bound, total),
        "pos_breakdown": pos_breakdown,
    }


def aozora_exact_stats(
    conn: sqlite3.Connection,
    *,
    surface: str,
    reading: str,
) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT pos_major, pos_sub1, SUM(token_count) AS token_count,
               SUM(work_count) AS work_count,
               SUM(modern_token_count) AS modern_token_count,
               SUM(accessible_token_count) AS accessible_token_count,
               SUM(hard_token_count) AS hard_token_count
        FROM token_context_profile
        WHERE (surface = ? OR base_form = ?) AND reading = ?
        GROUP BY pos_major, pos_sub1
        ORDER BY token_count DESC
        """,
        (surface, surface, reading),
    ).fetchall()
    independent = 0
    bound = 0
    proper = 0
    other = 0
    work_count = 0
    pos_breakdown: list[dict[str, Any]] = []
    for row in rows:
        pos_major = str(row["pos_major"] or "")
        pos_sub1 = str(row["pos_sub1"] or "")
        token_count = int(row["token_count"] or 0)
        bucket = aozora_pos_bucket(pos_major, pos_sub1)
        if bucket == "independent":
            independent += token_count
        elif bucket == "bound":
            bound += token_count
        elif bucket == "proper":
            proper += token_count
        else:
            other += token_count
        work_count += int(row["work_count"] or 0)
        pos_breakdown.append(
            {
                "pos_major": pos_major,
                "pos_sub1": pos_sub1,
                "bucket": bucket,
                "token_count": token_count,
                "work_count": int(row["work_count"] or 0),
                "modern_token_count": int(row["modern_token_count"] or 0),
                "accessible_token_count": int(row["accessible_token_count"] or 0),
                "hard_token_count": int(row["hard_token_count"] or 0),
            }
        )
    total = independent + bound + proper + other
    return {
        "independent_token_count": independent,
        "bound_token_count": bound,
        "proper_token_count": proper,
        "other_token_count": other,
        "total_exact_token_count": total,
        "exact_work_count_sum": work_count,
        "independence_share": share(independent, total),
        "bound_share": share(bound, total),
        "pos_breakdown": pos_breakdown,
    }


def aozora_compound_stats(
    conn: sqlite3.Connection,
    *,
    surface: str,
    reading: str,
    limit: int,
) -> dict[str, Any]:
    match_reliable = len(reading) >= 2
    aggregate_rows = conn.execute(
        """
        SELECT pos_major, pos_sub1, COALESCE(SUM(token_count), 0) AS token_count,
               COALESCE(SUM(work_count), 0) AS work_count
        FROM token_context_profile
        WHERE (surface LIKE ? OR base_form LIKE ?)
          AND NOT (surface = ? OR base_form = ?)
          AND reading LIKE ?
        GROUP BY pos_major, pos_sub1
        """,
        (f"%{surface}%", f"%{surface}%", surface, surface, f"%{reading}%"),
    ).fetchall()
    raw_token_count = 0
    raw_work_count = 0
    proper_token_count = 0
    proper_work_count = 0
    trusted_token_count = 0
    trusted_work_count = 0
    for row in aggregate_rows:
        pos_sub1 = str(row["pos_sub1"] or "")
        token_count = int(row["token_count"] or 0)
        work_count = int(row["work_count"] or 0)
        raw_token_count += token_count
        raw_work_count += work_count
        if "固有名詞" in pos_sub1:
            proper_token_count += token_count
            proper_work_count += work_count
        elif match_reliable:
            trusted_token_count += token_count
            trusted_work_count += work_count
    examples: list[dict[str, Any]] = []
    if limit > 0:
        rows = conn.execute(
            """
            SELECT surface, base_form, reading, pos_major, pos_sub1, token_count, work_count
            FROM token_context_profile
            WHERE (surface LIKE ? OR base_form LIKE ?)
              AND NOT (surface = ? OR base_form = ?)
              AND reading LIKE ?
            ORDER BY token_count DESC
            LIMIT ?
            """,
            (f"%{surface}%", f"%{surface}%", surface, surface, f"%{reading}%", limit),
        ).fetchall()
        examples = [
            {
                "surface": str(row["surface"] or ""),
                "base_form": str(row["base_form"] or ""),
                "reading": str(row["reading"] or ""),
                "pos_major": str(row["pos_major"] or ""),
                "pos_sub1": str(row["pos_sub1"] or ""),
                "token_count": int(row["token_count"] or 0),
                "work_count": int(row["work_count"] or 0),
                "trusted_for_classification": bool(
                    match_reliable and "固有名詞" not in str(row["pos_sub1"] or "")
                ),
            }
            for row in rows
        ]
    return {
        "match_reliable": match_reliable,
        "trusted_token_count": trusted_token_count,
        "trusted_work_count": trusted_work_count,
        "raw_token_count": raw_token_count,
        "raw_work_count": raw_work_count,
        "proper_token_count": proper_token_count,
        "proper_work_count": proper_work_count,
        "examples": examples,
    }


def classify_evidence(
    *,
    bccwj_stats: Mapping[str, Any],
    aozora_stats: Mapping[str, Any],
    compound_count: int,
) -> dict[str, Any]:
    b_ind = float(bccwj_stats["independent_frequency"])
    b_bound = float(bccwj_stats["bound_frequency"])
    b_total = float(bccwj_stats["total_frequency"])
    a_ind = int(aozora_stats["independent_token_count"])
    a_bound = int(aozora_stats["bound_token_count"])
    a_total = int(aozora_stats["total_exact_token_count"])
    independent = b_ind + a_ind
    bound = b_bound + a_bound
    exact_total = b_total + a_total
    context_total = exact_total + compound_count
    independence = share(independent, context_total)
    exact_independence = share(independent, exact_total)
    bound_context_share = share(bound + compound_count, context_total)
    compound_ratio = round(compound_count / max(1.0, independent), 6)

    if exact_total <= 75 and compound_count <= 25:
        classification = "weak_exact_or_orthographic_variant"
        suggested_action = "raise_or_variant_review"
        explanation = "Exact support is tiny and does not appear to be rescued by compound context."
    elif bound >= max(20.0, independent * 2.0) or (
        compound_count >= 500 and compound_ratio >= 3.0 and independence < 0.2
    ):
        classification = "bound_or_compound_heavy"
        suggested_action = "restricted_admission_or_frequency_discount"
        explanation = (
            "Most evidence is bound usage or longer compound usage, so frequency should not "
            "fully make the standalone row easy."
        )
    elif independent >= 100 and exact_independence >= 0.6:
        classification = "independent_supported"
        suggested_action = "leave_or_light_review"
        explanation = "Exact independent usage is substantial enough that this is not mainly a compound-only row."
    else:
        classification = "mixed_or_uncertain"
        suggested_action = "manual_review"
        explanation = "Evidence is not clean enough for a broad automatic decision."

    return {
        "metrics": {
            "combined_independent_support": rounded(independent),
            "combined_bound_support": rounded(bound),
            "combined_exact_support": rounded(exact_total),
            "compound_containing_support": compound_count,
            "standalone_independence_with_compounds": independence,
            "standalone_independence_exact_only": exact_independence,
            "bound_or_compound_context_share": bound_context_share,
            "compound_to_independent_ratio": compound_ratio,
        },
        "classification": classification,
        "suggested_action": suggested_action,
        "explanation": explanation,
    }


def summarize(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, int] = {}
    by_action: dict[str, int] = {}
    for row in rows:
        classification = str(row["classification"])
        action = str(row["suggested_action"])
        by_class[classification] = by_class.get(classification, 0) + 1
        by_action[action] = by_action.get(action, 0) + 1
    return {
        "target_count": len(rows),
        "classification_counts": by_class,
        "suggested_action_counts": by_action,
    }


def compact_ranking(row: Mapping[str, str]) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "rank": safe_int(row.get("rank")),
        "score": safe_float(row.get("score")),
        "model_score": safe_float(row.get("model_score")),
        "correction_delta": safe_float(row.get("correction_delta")),
        "band": str(row.get("band") or ""),
        "correction_types": str(row.get("correction_types") or ""),
        "admission_override": str(row.get("admission_override") or ""),
        "topic_stretch_allowed": str(row.get("topic_stretch_allowed") or ""),
        "review_flags": str(row.get("review_flags") or ""),
        "exact_commonness": safe_float(row.get("exact_commonness")),
        "same_surface_risk": safe_float(row.get("same_surface_risk")),
        "suspicion_full": safe_float(row.get("suspicion_full")),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# en-ja Standalone Independence Probe",
        "",
        f"Ranking: `{report['inputs']['ranking_csv']}`",
        f"BCCWJ: `{report['inputs']['bccwj_sqlite']}`",
        f"Aozora: `{report['inputs']['aozora_sqlite']}`",
        "",
        "Purpose: separate exact independent usage from bound, suffix/prefix, and longer-compound evidence before changing the learner-difficulty ranking.",
        "",
        "## Summary",
        "",
        f"- Targets: `{report['summary']['target_count']}`",
        f"- Classifications: `{json.dumps(report['summary']['classification_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- Suggested actions: `{json.dumps(report['summary']['suggested_action_counts'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "## Rows",
        "",
        "| Row | Score | Class | Suggested action | Indep. w/ compounds | Exact-only indep. | BCCWJ independent/bound | Aozora independent/bound | Trusted Aozora compound tokens | Top raw compound examples |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in report["rows"]:
        ranking = row["ranking"]
        bccwj = row["bccwj"]
        aozora = row["aozora"]
        metrics = row["metrics"]
        examples = ", ".join(
            f"{example['surface']}/{example['reading']}({example['token_count']})"
            for example in aozora["compound_examples"][:5]
        )
        lines.append(
            "| "
            f"`{escape(row['surface'])}/{escape(row['reading'])}` | "
            f"{format_score(ranking.get('score'))} | "
            f"`{escape(row['classification'])}` | "
            f"`{escape(row['suggested_action'])}` | "
            f"{metrics['standalone_independence_with_compounds']:.3f} | "
            f"{metrics['standalone_independence_exact_only']:.3f} | "
            f"{bccwj['independent_frequency']:.0f}/{bccwj['bound_frequency']:.0f} | "
            f"{aozora['independent_token_count']}/{aozora['bound_token_count']} | "
            f"{aozora['compound_trusted_token_count']} | "
            f"{escape(examples)} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Notes",
            "",
            "- `bound_or_compound_heavy`: strongest evidence for restricted admission or frequency-ease discount.",
            "- `weak_exact_or_orthographic_variant`: exact row is barely attested; this is usually a spelling/variant problem rather than compound support.",
            "- `independent_supported`: this row should not be aggressively demoted just because it has an easier same-surface family member.",
            "- `mixed_or_uncertain`: keep manual review unless a broader pattern emerges.",
            "- Trusted Aozora compound evidence excludes proper-name compounds and ignores one-mora reading substring matches because those are too noisy for automatic classification.",
            "",
        ]
    )
    return "\n".join(lines)


def bccwj_pos_bucket(pos: str) -> str:
    if "接尾" in pos or "接頭" in pos:
        return "bound"
    if "固有名詞" in pos:
        return "proper"
    if pos:
        return "independent"
    return "other"


def aozora_pos_bucket(pos_major: str, pos_sub1: str) -> str:
    if pos_major == "接頭詞" or "接尾" in pos_sub1 or "接頭" in pos_sub1:
        return "bound"
    if "固有名詞" in pos_sub1:
        return "proper"
    if pos_major in INDEPENDENT_AOZORA_POS_MAJOR:
        return "independent"
    return "other"


def parse_targets(values: Sequence[str]) -> list[tuple[str, str]]:
    parsed = []
    for value in values:
        if "/" not in value:
            raise SystemExit(f"--target must be surface/reading: {value}")
        surface, reading = value.split("/", 1)
        parsed.append((surface.strip(), reading.strip()))
    return [item for item in parsed if item[0] and item[1]]


def hira_to_kata(value: str) -> str:
    chars = []
    for char in value:
        code = ord(char)
        if 0x3041 <= code <= 0x3096:
            chars.append(chr(code + 0x60))
        else:
            chars.append(char)
    return "".join(chars)


def share(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return rounded(float(numerator) / float(denominator))


def safe_float(value: object) -> float | None:
    try:
        text = str(value if value is not None else "").strip()
        return rounded(float(text)) if text else None
    except ValueError:
        return None


def safe_int(value: object) -> int | None:
    try:
        text = str(value if value is not None else "").strip()
        return int(float(text)) if text else None
    except ValueError:
        return None


def rounded(value: float) -> float:
    return round(float(value), 6)


def format_score(value: object) -> str:
    if value is None:
        return ""
    return f"{float(value):.3f}"


def escape(value: object) -> str:
    return str(value).replace("|", "\\|")


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
