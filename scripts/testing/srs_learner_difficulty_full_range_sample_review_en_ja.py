#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV_IN = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_en_ja_latest.csv"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_full_range_sample_review_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_full_range_sample_review_en_ja_latest.md"
)
DEFAULT_SEED = 20260630
SCORE_BANDS = tuple((index / 20.0, (index + 1) / 20.0) for index in range(20))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a deterministic full-range en-ja learner-difficulty review "
            "sample from the corrected ranking CSV."
        )
    )
    parser.add_argument("--csv-in", type=Path, default=DEFAULT_CSV_IN)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--random-per-band", type=int, default=8)
    parser.add_argument("--risk-per-band", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    csv_in = _resolve_path(args.csv_in)
    report = build_report(
        csv_in=csv_in,
        seed=int(args.seed),
        random_per_band=max(0, int(args.random_per_band)),
        risk_per_band=max(0, int(args.risk_per_band)),
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
    csv_in: Path,
    seed: int,
    random_per_band: int,
    risk_per_band: int,
) -> dict[str, Any]:
    rows = load_rows(csv_in)
    by_band: dict[str, list[dict[str, Any]]] = {band_label(*band): [] for band in SCORE_BANDS}
    for row in rows:
        by_band[score_band(float(row["score"]))].append(row)

    rng = random.Random(seed)
    bands: list[dict[str, Any]] = []
    for low, high in SCORE_BANDS:
        label = band_label(low, high)
        band_rows = by_band[label]
        random_samples = deterministic_random_rows(
            band_rows,
            rng=rng,
            sample_count=random_per_band,
        )
        risk_rows = sorted(
            band_rows,
            key=lambda row: (-risk_score(row), int(row["rank"])),
        )[:risk_per_band]
        bands.append(
            {
                "band": label,
                "count": len(band_rows),
                "random_samples": [sample_row(row) for row in random_samples],
                "risk_samples": [sample_row(row, include_risk=True) for row in risk_rows],
            }
        )

    return {
        "source": repo_path(csv_in),
        "seed": seed,
        "random_per_band": random_per_band,
        "risk_per_band": risk_per_band,
        "method": (
            "deterministic random sample per 0.05 score band plus mechanically "
            "risk-ranked rows from the corrected ranking CSV"
        ),
        "bands": bands,
    }


def load_rows(csv_in: Path) -> list[dict[str, Any]]:
    with csv_in.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["rank"] = int(row["rank"])
        row["score"] = float(row["score"])
        row["model_score"] = _float(row.get("model_score"))
        row["correction_delta"] = _float(row.get("correction_delta"))
        row["exact_commonness"] = _float(row.get("exact_commonness"))
        row["same_surface_risk"] = _float(row.get("same_surface_risk"))
        row["suspicion_full"] = _float(row.get("suspicion_full"))
        row["tail_guard"] = _float(row.get("tail_guard"))
        row["jlpt_normalized_only_known"] = _float(row.get("jlpt_normalized_only_known"))
    return rows


def deterministic_random_rows(
    rows: Sequence[dict[str, Any]],
    *,
    rng: random.Random,
    sample_count: int,
) -> list[dict[str, Any]]:
    if sample_count <= 0 or not rows:
        return []
    if len(rows) <= sample_count:
        return list(rows)
    return sorted(rng.sample(list(rows), sample_count), key=lambda row: int(row["rank"]))


def risk_score(row: Mapping[str, Any]) -> float:
    flags = split_flags(str(row.get("review_flags") or ""))
    correction_types = split_flags(str(row.get("correction_types") or ""))
    score = 0.0
    if correction_types:
        score += 0.75
    if "restricted_admission" in correction_types:
        score += 0.25
    if str(row.get("manual_review") or "").strip():
        score += 0.35
    if "early_same_surface_risk" in flags:
        score += 0.55
    if "early_kana_preferred_kanji" in flags:
        score += 0.20
    if "normalized_only_jlpt" in flags:
        score += 0.35
    if "same_surface_risk" in flags:
        score += 0.30
    score += 0.45 * float(row.get("same_surface_risk") or 0.0)
    score += 0.35 * float(row.get("suspicion_full") or 0.0)
    score += 0.20 * float(row.get("tail_guard") or 0.0)
    score += 0.30 * float(row.get("jlpt_normalized_only_known") or 0.0)
    score += min(0.35, max(0.0, float(row.get("correction_delta") or 0.0)) * 2.0)
    if float(row.get("score") or 0.0) <= 0.4 and float(row.get("exact_commonness") or 0.0) < 0.05:
        score += 0.20
    return round(score, 6)


def sample_row(row: Mapping[str, Any], *, include_risk: bool = False) -> dict[str, Any]:
    sampled = {
        "rank": int(row["rank"]),
        "score": rounded(float(row["score"])),
        "lemma": str(row.get("lemma") or ""),
        "reading": str(row.get("reading") or ""),
        "display": str(row.get("display_form") or row.get("lemma") or ""),
        "admission": str(row.get("admission_override") or row.get("candidate_state") or ""),
        "topic_stretch_allowed": str(row.get("topic_stretch_allowed") or ""),
        "flags": merged_flags(row),
        "exact_commonness": rounded(float(row.get("exact_commonness") or 0.0)),
        "suspicion": rounded(float(row.get("suspicion_full") or 0.0)),
    }
    if include_risk:
        sampled["risk_score"] = risk_score(row)
    return sampled


def merged_flags(row: Mapping[str, Any]) -> str:
    flags = []
    flags.extend(split_flags(str(row.get("correction_types") or "")))
    flags.extend(split_flags(str(row.get("review_flags") or "")))
    admission = str(row.get("admission_override") or "")
    if admission and admission != "normal_vocab":
        flags.append(admission)
    return ",".join(dict.fromkeys(flags))


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# en-ja Learner Difficulty Full-Range Sampling Review",
        "",
        f"Source: `{report['source']}`",
        f"Seed: `{report['seed']}`",
        (
            "Method: deterministic random sample of up to "
            f"{int(report.get('random_per_band') or 0)} rows per 0.05 score band, "
            "plus up to "
            f"{int(report.get('risk_per_band') or 0)} mechanically risk-ranked rows "
            "per band. Risk rows are not handpicked; they combine "
            "manual-correction presence, review flags, same-surface risk, "
            "tail/suspicion signals, and normalized-only JLPT support."
        ),
        "",
        "## Band Counts",
        "",
        "| Band | Count |",
        "| --- | ---: |",
    ]
    bands = list(report["bands"])
    for band in bands:
        lines.append(f"| `{band['band']}` | {band['count']} |")
    for band in bands:
        lines.extend(["", f"## Band {band['band']} ({band['count']} rows)", ""])
        lines.extend(["### Random Samples", ""])
        lines.extend(render_sample_table(band["random_samples"], include_risk=False))
        lines.extend(["", "### Mechanical Risk Rows", ""])
        lines.extend(render_sample_table(band["risk_samples"], include_risk=True))
    lines.append("")
    return "\n".join(lines)


def render_sample_table(rows: Sequence[Mapping[str, Any]], *, include_risk: bool) -> list[str]:
    if include_risk:
        lines = [
            "| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |",
            "| ---: | ---: | ---: | --- | --- | --- | --- | --- |",
        ]
        for row in rows:
            lines.append(
                "| "
                f"{float(row['risk_score']):.3f} | "
                f"{row['rank']} | "
                f"{float(row['score']):.6f} | "
                f"`{escape(str(row['lemma']))}` | "
                f"`{escape(str(row['reading']))}` | "
                f"`{escape(str(row['display']))}` | "
                f"`{escape(str(row['admission']))}` | "
                f"{escape(str(row['flags']))} |"
            )
        return lines
    lines = [
        "| Rank | Score | Word | Reading | Display | Admission | Flags |",
        "| ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['rank']} | "
            f"{float(row['score']):.6f} | "
            f"`{escape(str(row['lemma']))}` | "
            f"`{escape(str(row['reading']))}` | "
            f"`{escape(str(row['display']))}` | "
            f"`{escape(str(row['admission']))}` | "
            f"{escape(str(row['flags']))} |"
        )
    return lines


def score_band(score: float) -> str:
    if score >= 1.0:
        index = 19
    else:
        index = min(19, max(0, int(score / 0.05)))
    return band_label(index / 20.0, (index + 1) / 20.0)


def band_label(low: float, high: float) -> str:
    return f"{low:.2f}-{high:.2f}"


def split_flags(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def rounded(value: float) -> float:
    return round(float(value), 6)


def escape(value: str) -> str:
    return value.replace("|", "\\|")


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _float(value: object) -> float:
    try:
        text = str(value if value is not None else "").strip()
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


if __name__ == "__main__":
    raise SystemExit(main())
