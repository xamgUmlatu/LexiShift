#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_formula_probe_en_es import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_FORMULA_PROBE_JSON,
    build_report as build_formula_probe_report,
)


PAIR = "en-es"
DEFAULT_TOP_N = 45000
DEFAULT_MIN_GAP = 0.35
DEFAULT_STRONG_GAP = 0.75
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_form_preference_audit_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_form_preference_audit_en_es_latest.md"
)
SPANISH_WORD_RE = re.compile(r"^[a-záéíóúüñ]+$", re.IGNORECASE)
VOWELS = set("aeiouáéíóúü")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit en-es singular/plural surface-frequency asymmetries. This is a "
            "sidecar diagnostic only; it does not change formula scores or labels."
        )
    )
    parser.add_argument("--formula-probe-json", type=Path, default=DEFAULT_FORMULA_PROBE_JSON)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--min-gap", type=float, default=DEFAULT_MIN_GAP)
    parser.add_argument("--strong-gap", type=float, default=DEFAULT_STRONG_GAP)
    parser.add_argument("--force-rebuild-probe", action="store_true")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    formula_report = load_or_build_formula_report(
        formula_probe_json=Path(args.formula_probe_json).expanduser(),
        top_n=max(1, int(args.top_n)),
        force_rebuild=bool(args.force_rebuild_probe),
    )
    report = build_report(
        formula_report=formula_report,
        min_gap=max(0.0, float(args.min_gap)),
        strong_gap=max(0.0, float(args.strong_gap)),
    )
    json_out = Path(args.json_out).expanduser().resolve(strict=False)
    markdown_out = Path(args.markdown_out).expanduser().resolve(strict=False)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def load_or_build_formula_report(
    *,
    formula_probe_json: Path,
    top_n: int,
    force_rebuild: bool = False,
) -> dict[str, object]:
    if not force_rebuild and formula_probe_json.is_file():
        payload = _load_json(formula_probe_json)
        if payload.get("rows"):
            return payload
    return build_formula_probe_report(
        top_n=top_n,
        sample_limit=8,
        include_rows=True,
    )


def build_report(
    *,
    formula_report: Mapping[str, object],
    min_gap: float = DEFAULT_MIN_GAP,
    strong_gap: float = DEFAULT_STRONG_GAP,
    generated_at: str | None = None,
    wordfreq_zipf_by_term: Mapping[str, float] | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    rows = [_as_mapping(row) for row in _as_sequence(formula_report.get("rows"))]
    if not rows:
        raise ValueError("formula report must contain rows; rebuild with include_rows=True")
    lemma_set = {
        str(row.get("lemma") or "").strip().lower()
        for row in rows
        if _is_simple_spanish_word(str(row.get("lemma") or "").strip().lower())
    }
    zipf_lookup = _zipf_lookup(wordfreq_zipf_by_term)
    audit_rows = [
        audit
        for row in rows
        if (
            audit := _audit_row(
                row,
                lemma_set=lemma_set,
                zipf_lookup=zipf_lookup,
                min_gap=min_gap,
                strong_gap=strong_gap,
            )
        )
    ]
    audit_rows = sorted(
        audit_rows,
        key=lambda row: (
            _severity_sort(str(row.get("severity") or "")),
            _safe_float(row.get("mate_gap")) or 0.0,
            _safe_float(row.get("current_score")) or 0.0,
        ),
        reverse=True,
    )
    status = "ok" if zipf_lookup["available"] else "review"
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "status": status,
        "decision": (
            "en_es_form_preference_audit_ready"
            if status == "ok"
            else "en_es_form_preference_audit_needs_wordfreq"
        ),
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "manual_labels_added": False,
        "method": {
            "purpose": (
                "Cheap diagnostic for singular/plural preferred-form risk. It finds "
                "candidate rows whose generated singular/plural mate has materially "
                "higher wordfreq Spanish surface frequency."
            ),
            "formula_probe_decision": formula_report.get("decision"),
            "formula_probe_generated_at": formula_report.get("generated_at"),
            "formula_probe_top_n": _as_mapping(formula_report.get("inputs")).get("top_n"),
            "wordfreq_language": "es",
            "min_gap": _round_float(min_gap),
            "strong_gap": _round_float(strong_gap),
        },
        "summary": _summary(audit_rows, rows=rows, zipf_available=bool(zipf_lookup["available"])),
        "audit_rows": audit_rows,
        "limitations": [
            "Plural/singular generation is heuristic and intended only to find review candidates.",
            "A higher-frequency mate does not prove the candidate is bad; it can reflect normal number semantics.",
            "This audit intentionally does not merge family frequency into the model or change difficulty scores.",
            "Rows with POS or dictionary gaps are more suspicious, but still require review before becoming a rule.",
            "If the preferred mate is absent from candidate rows, treat the finding as a candidate inventory/canonical form question before treating it as a difficulty formula question.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    method = _as_mapping(report.get("method"))
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Form Preference Audit",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        f"- Formula probe: `{method.get('formula_probe_decision')}`",
        f"- Minimum mate gap: `{method.get('min_gap')}` Zipf",
        f"- Strong gap: `{method.get('strong_gap')}` Zipf",
        "",
        "## Summary",
        "",
        f"- Candidate rows scanned: `{summary.get('candidate_rows_scanned')}`",
        f"- Audit rows: `{summary.get('audit_row_count')}`",
        f"- Strong rows: `{summary.get('strong_row_count')}`",
        f"- Moderate rows: `{summary.get('moderate_row_count')}`",
        f"- Suspicious support rows: `{summary.get('suspicious_support_count')}`",
        f"- Preferred mate present in candidate rows: `{summary.get('preferred_mate_present_count')}`",
        f"- Preferred mate missing from candidate rows: `{summary.get('preferred_mate_missing_count')}`",
        "",
        "| Direction | Rows |",
        "| --- | ---: |",
    ]
    for direction, count in _as_mapping(summary.get("direction_counts")).items():
        lines.append(f"| `{_escape(direction)}` | {count} |")
    lines.extend(
        [
            "",
            "## Audit Rows",
            "",
            "| # | Lemma | Mate | Mate In Rows | Direction | Gap | Score | Severity | Support | Translations |",
            "| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    for index, raw in enumerate(_as_sequence(report.get("audit_rows")), start=1):
        row = _as_mapping(raw)
        support = _as_mapping(row.get("support"))
        support_bits = []
        for key in ("pos_bucket", "dict_entry_count", "learner_source_known"):
            support_bits.append(f"{key}={support.get(key)}")
        lines.append(
            f"| {index} | `{_escape(row.get('lemma'))}` "
            f"({_fmt(row.get('candidate_zipf'))}) | "
            f"`{_escape(row.get('preferred_mate'))}` ({_fmt(row.get('preferred_mate_zipf'))}) | "
            f"`{row.get('preferred_mate_in_candidate_rows')}` | "
            f"`{_escape(row.get('direction'))}` | {_fmt(row.get('mate_gap'))} | "
            f"{_fmt(row.get('current_score'))} | `{_escape(row.get('severity'))}` | "
            f"{_escape(', '.join(support_bits))} | "
            f"{_escape('; '.join(str(item) for item in _as_sequence(row.get('translations'))[:3])) or '-'} |"
        )
    limitations = _as_sequence(report.get("limitations"))
    if limitations:
        lines.extend(["", "## Limitations", ""])
        for item in limitations:
            lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def _audit_row(
    row: Mapping[str, object],
    *,
    lemma_set: set[str],
    zipf_lookup: Mapping[str, object],
    min_gap: float,
    strong_gap: float,
) -> dict[str, object] | None:
    lemma = str(row.get("lemma") or "").strip().lower()
    if not _is_simple_spanish_word(lemma):
        return None
    candidate_zipf = _zipf(lemma, zipf_lookup)
    if candidate_zipf <= 0.0:
        return None
    mate_candidates = _mate_candidates(lemma)
    if not mate_candidates:
        return None
    mate_scores = [
        (mate, _zipf(mate, zipf_lookup), direction) for mate, direction in mate_candidates
    ]
    mate_scores = [item for item in mate_scores if item[1] > 0.0]
    if not mate_scores:
        return None
    preferred_mate, preferred_zipf, direction = max(mate_scores, key=lambda item: item[1])
    gap = preferred_zipf - candidate_zipf
    if gap < min_gap:
        return None
    components = _as_mapping(row.get("components"))
    dictionary = _as_mapping(row.get("dictionary"))
    support = {
        "pos": row.get("pos"),
        "pos_bucket": row.get("pos_bucket"),
        "pos_other_risk": _round_float(components.get("pos_other_risk")),
        "dict_entry_count": _safe_int(dictionary.get("entry_count")),
        "dict_sense_count": _safe_int(dictionary.get("sense_count")),
        "dict_marked_usage_risk": _round_float(components.get("dict_marked_usage_risk")),
        "learner_source_known": _round_float(components.get("learner_source_known")),
        "learner_source_count": _round_float(components.get("learner_source_count")),
    }
    suspicious = _support_is_suspicious(support)
    severity = _severity(gap, suspicious=suspicious, strong_gap=strong_gap)
    return {
        "lemma": lemma,
        "preferred_mate": preferred_mate,
        "preferred_mate_in_candidate_rows": preferred_mate in lemma_set,
        "direction": direction,
        "candidate_zipf": _round_float(candidate_zipf),
        "preferred_mate_zipf": _round_float(preferred_zipf),
        "mate_gap": _round_float(gap),
        "current_score": _round_float(
            _as_mapping(row.get("variant_scores")).get("spalex_blend_frequency")
        ),
        "candidate_state": row.get("candidate_state"),
        "spalex_rank": row.get("spalex_rank"),
        "translations": list(_as_sequence(row.get("translations")))[:6],
        "support": support,
        "suspicious_support": suspicious,
        "severity": severity,
        "all_mates": [
            {
                "term": mate,
                "direction": mate_direction,
                "in_candidate_rows": mate in lemma_set,
                "zipf": _round_float(score),
                "gap": _round_float(score - candidate_zipf),
            }
            for mate, score, mate_direction in sorted(
                mate_scores,
                key=lambda item: item[1],
                reverse=True,
            )
        ],
    }


def _mate_candidates(lemma: str) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    for plural in _plural_candidates(lemma):
        if plural != lemma:
            candidates.append((plural, "candidate_singular_mate_plural"))
    for singular in _singular_candidates(lemma):
        if singular != lemma:
            candidates.append((singular, "candidate_plural_mate_singular"))
    return sorted(dict.fromkeys(candidates))


def _plural_candidates(lemma: str) -> list[str]:
    if len(lemma) < 3:
        return []
    if lemma.endswith("z"):
        return [lemma[:-1] + "ces"]
    if lemma[-1] in VOWELS:
        return [lemma + "s"]
    return [lemma + "es"]


def _singular_candidates(lemma: str) -> list[str]:
    if len(lemma) < 4 or not lemma.endswith("s"):
        return []
    candidates: list[str] = []
    if lemma.endswith("ces") and len(lemma) > 4:
        candidates.append(lemma[:-3] + "z")
    if lemma.endswith("es") and len(lemma) > 4:
        candidates.append(lemma[:-2])
    candidates.append(lemma[:-1])
    return [item for item in dict.fromkeys(candidates) if len(item) >= 3]


def _summary(
    audit_rows: Sequence[Mapping[str, object]],
    *,
    rows: Sequence[Mapping[str, object]],
    zipf_available: bool,
) -> dict[str, object]:
    severity_counts = Counter(str(row.get("severity") or "") for row in audit_rows)
    direction_counts = Counter(str(row.get("direction") or "") for row in audit_rows)
    return {
        "wordfreq_available": zipf_available,
        "candidate_rows_scanned": len(rows),
        "audit_row_count": len(audit_rows),
        "strong_row_count": severity_counts.get("strong", 0),
        "moderate_row_count": severity_counts.get("moderate", 0),
        "suspicious_support_count": sum(
            1 for row in audit_rows if bool(row.get("suspicious_support"))
        ),
        "preferred_mate_present_count": sum(
            1 for row in audit_rows if bool(row.get("preferred_mate_in_candidate_rows"))
        ),
        "preferred_mate_missing_count": sum(
            1 for row in audit_rows if not bool(row.get("preferred_mate_in_candidate_rows"))
        ),
        "severity_counts": dict(sorted(severity_counts.items())),
        "direction_counts": dict(sorted(direction_counts.items())),
        "top_gaps": [
            {
                "lemma": row.get("lemma"),
                "preferred_mate": row.get("preferred_mate"),
                "preferred_mate_in_candidate_rows": row.get("preferred_mate_in_candidate_rows"),
                "mate_gap": row.get("mate_gap"),
                "severity": row.get("severity"),
                "current_score": row.get("current_score"),
            }
            for row in audit_rows[:20]
        ],
    }


def _zipf_lookup(
    wordfreq_zipf_by_term: Mapping[str, float] | None,
) -> dict[str, object]:
    if wordfreq_zipf_by_term is not None:
        return {
            "available": True,
            "manual": True,
            "values": {
                str(key).strip().lower(): _round_float(value)
                for key, value in wordfreq_zipf_by_term.items()
            },
        }
    try:
        from wordfreq import zipf_frequency  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency path.
        return {"available": False, "manual": False, "error": str(exc), "values": {}}
    return {"available": True, "manual": False, "zipf_frequency": zipf_frequency, "values": {}}


def _zipf(term: str, lookup: Mapping[str, object]) -> float:
    values = _as_mapping(lookup.get("values"))
    if values:
        return _round_float(values.get(term))
    func = lookup.get("zipf_frequency")
    if not callable(func):
        return 0.0
    try:
        return _round_float(func(term, "es"))
    except Exception:
        return 0.0


def _support_is_suspicious(support: Mapping[str, object]) -> bool:
    return (
        str(support.get("pos_bucket") or "") == "other"
        or _safe_int(support.get("dict_entry_count")) == 0
        or (_safe_float(support.get("dict_marked_usage_risk")) or 0.0) >= 0.5
    )


def _severity(gap: float, *, suspicious: bool, strong_gap: float) -> str:
    if gap >= strong_gap or (gap >= 0.55 and suspicious):
        return "strong"
    return "moderate"


def _severity_sort(severity: str) -> int:
    return {"strong": 2, "moderate": 1}.get(severity, 0)


def _is_simple_spanish_word(value: str) -> bool:
    return bool(SPANISH_WORD_RE.match(value))


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: object) -> int:
    numeric = _safe_float(value)
    return int(numeric) if numeric is not None else 0


def _round_float(value: object, digits: int = 6) -> float:
    numeric = _safe_float(value)
    if numeric is None:
        return 0.0
    return round(numeric, digits)


def _fmt(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "-"
    return f"{numeric:.3f}"


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
