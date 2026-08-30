#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.srs.candidate_classification import (  # noqa: E402
    CANDIDATE_STATE_NORMAL_VOCAB,
    classify_srs_candidate,
)


PAIR = "en-de"
DEFAULT_ROWS_JSONL = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_palette_en_de_rows_latest.jsonl"
)
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_de.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_de.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_candidate_restriction_signal_probe_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_candidate_restriction_signal_probe_en_de_latest.md"
)
DEFAULT_SAMPLE_LIMIT = 40


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe richer en-de signal-palette evidence for candidate-state cleanup "
            "without changing production classification."
        )
    )
    parser.add_argument("--rows-jsonl", type=Path, default=DEFAULT_ROWS_JSONL)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--sample-limit", type=int, default=DEFAULT_SAMPLE_LIMIT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    rows = _load_jsonl(Path(args.rows_jsonl).expanduser())
    labels = _load_restricted_labels(
        [
            Path(args.calibration_json).expanduser(),
            Path(args.holdout_json).expanduser(),
        ]
    )
    report = build_report(
        signal_rows=rows,
        restricted_labels=labels,
        sample_limit=max(1, int(args.sample_limit)),
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
    return 0


def build_report(
    *,
    signal_rows: Sequence[Mapping[str, object]],
    restricted_labels: Mapping[str, Mapping[str, object]],
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
    generated_at: str | None = None,
) -> dict[str, object]:
    rows_by_lemma = {
        str(row.get("lemma") or "").strip(): row
        for row in signal_rows
        if str(row.get("lemma") or "").strip()
    }
    runtime_hits: list[dict[str, object]] = []
    proposal_hits: dict[str, list[dict[str, object]]] = defaultdict(list)
    proposal_counts: Counter[str] = Counter()
    runtime_state_counts: Counter[str] = Counter()

    for row in signal_rows:
        lemma = str(row.get("lemma") or "").strip()
        if not lemma:
            continue
        runtime = classify_srs_candidate(
            language_pair=PAIR,
            lemma=lemma,
            raw_pos=row.get("pos"),
        )
        if runtime.candidate_state != CANDIDATE_STATE_NORMAL_VOCAB:
            runtime_state_counts[runtime.candidate_state] += 1
            runtime_hits.append(_review_row(row, runtime=runtime, proposals=()))
        proposals = tuple(_proposal_reasons(row, rows_by_lemma=rows_by_lemma))
        for proposal in proposals:
            proposal_counts[proposal] += 1
            proposal_hits[proposal].append(_review_row(row, runtime=runtime, proposals=proposals))

    label_rows = []
    for lemma, label in sorted(restricted_labels.items()):
        row = rows_by_lemma.get(lemma, {})
        runtime = classify_srs_candidate(
            language_pair=PAIR,
            lemma=lemma,
            raw_pos=row.get("pos") if row else label.get("source_pos"),
        )
        proposals = tuple(_proposal_reasons(row, rows_by_lemma=rows_by_lemma)) if row else ()
        label_rows.append(
            {
                **_review_row(row or {"lemma": lemma}, runtime=runtime, proposals=proposals),
                "expected_candidate_state": label.get("expected_candidate_state"),
                "review_treatment": label.get("review_treatment"),
                "review_flags": list(_sequence(label.get("review_flags"))),
                "rationale": str(label.get("rationale") or ""),
                "covered_by_runtime": runtime.candidate_state != CANDIDATE_STATE_NORMAL_VOCAB,
                "covered_by_signal_probe": bool(proposals),
            }
        )

    early_rows = [
        _review_row(
            row,
            runtime=classify_srs_candidate(
                language_pair=PAIR,
                lemma=str(row.get("lemma") or "").strip(),
                raw_pos=row.get("pos"),
            ),
            proposals=tuple(_proposal_reasons(row, rows_by_lemma=rows_by_lemma)),
        )
        for row in signal_rows
        if (_float(row.get("rank_base")) or 1.0) < 0.75
        and _proposal_reasons(row, rows_by_lemma=rows_by_lemma)
    ]
    early_rows = sorted(early_rows, key=_sort_key)
    tight_recommended_reasons = {
        "de_stem_or_learner_only_no_pos_rank_lt_065",
        "de_unsupported_ausz_artifact",
    }
    tight_rows = [
        row
        for row in early_rows
        if set(_sequence(row.get("proposal_reasons"))).intersection(tight_recommended_reasons)
    ]

    proposal_samples = {
        reason: sorted(rows, key=_sort_key)[:sample_limit]
        for reason, rows in sorted(proposal_hits.items())
    }
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_de_candidate_restriction_signal_probe_ready",
        "generated_at": generated_at or _utc_now(),
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "method": {
            "policy": (
                "Diagnostic-only probe over the en-de signal palette. It compares "
                "current runtime classification with richer seed-time support-gap "
                "signals; proposal hits are not wired into production."
            ),
            "sample_limit": sample_limit,
            "proposal_actions": {
                "de_missing_pos_no_semantic_support_rank_lt_075": (
                    "review_required_or_deprioritized_vocab"
                ),
                "de_short_noun_no_semantic_support_rank_lt_075": (
                    "review_required_or_deprioritized_vocab"
                ),
                "de_stem_or_learner_only_no_pos_rank_lt_065": ("restricted_admission_review"),
                "de_unsupported_ausz_artifact": "suppress_or_redirect_review",
                "de_mixed_verb_noun_no_semantic_support_rank_lt_075": (
                    "review_required_or_restricted_admission"
                ),
            },
        },
        "summary": {
            "signal_row_count": len(signal_rows),
            "runtime_hit_count": len(runtime_hits),
            "runtime_state_counts": dict(sorted(runtime_state_counts.items())),
            "proposal_unique_hit_count": len(
                {str(row.get("lemma") or "") for rows in proposal_hits.values() for row in rows}
            ),
            "proposal_reason_counts": dict(sorted(proposal_counts.items())),
            "restricted_label_count": len(label_rows),
            "restricted_labels_covered_by_runtime": sum(
                1 for row in label_rows if row["covered_by_runtime"]
            ),
            "restricted_labels_covered_by_signal_probe": sum(
                1 for row in label_rows if row["covered_by_signal_probe"]
            ),
            "rank_base_lt_075_proposal_hit_count": len(early_rows),
            "tight_recommended_hit_count": len(tight_rows),
            "restricted_labels_covered_by_tight_recommended": sum(
                1
                for row in label_rows
                if set(_sequence(row.get("proposal_reasons"))).intersection(
                    tight_recommended_reasons
                )
            ),
        },
        "restricted_label_rows": label_rows,
        "proposal_samples": proposal_samples,
        "rank_base_lt_075_proposal_sample": early_rows[:sample_limit],
        "tight_recommended_sample": tight_rows[:sample_limit],
        "limitations": [
            "Proposal rules use signal-palette metadata that runtime classification does not receive today.",
            "Proposal hits are review candidates, not automatic production suppressions.",
            "Rank-base thresholds are used only to estimate product-visible risk in the current en-de ranking.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    lines = [
        "# en-de Candidate Restriction Signal Probe",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Summary",
        "",
        f"- Signal rows: `{summary.get('signal_row_count')}`",
        f"- Current runtime classifier hits: `{summary.get('runtime_hit_count')}`",
        f"- Proposal unique hits: `{summary.get('proposal_unique_hit_count')}`",
        f"- Proposal hits with `rank_base < 0.75`: `{summary.get('rank_base_lt_075_proposal_hit_count')}`",
        f"- Tight recommended hits: `{summary.get('tight_recommended_hit_count')}`",
        f"- Restricted labels covered by runtime: `{summary.get('restricted_labels_covered_by_runtime')}/{summary.get('restricted_label_count')}`",
        f"- Restricted labels covered by signal probe: `{summary.get('restricted_labels_covered_by_signal_probe')}/{summary.get('restricted_label_count')}`",
        f"- Restricted labels covered by tight recommendation: `{summary.get('restricted_labels_covered_by_tight_recommended')}/{summary.get('restricted_label_count')}`",
        "",
        "Proposal reason counts:",
        "",
        "| Reason | Rows |",
        "| --- | ---: |",
    ]
    for reason, count in _mapping(summary.get("proposal_reason_counts")).items():
        lines.append(f"| `{_escape(reason)}` | {count} |")
    lines.extend(
        [
            "",
            "## Restricted Label Coverage",
            "",
            _row_table(report.get("restricted_label_rows"), include_label_columns=True),
            "",
            "## Tight Recommended Subset",
            "",
            _row_table(report.get("tight_recommended_sample")),
            "",
            "## Early Proposal Sample",
            "",
            _row_table(report.get("rank_base_lt_075_proposal_sample")),
            "",
            "## Proposal Samples",
            "",
        ]
    )
    for reason, rows in _mapping(report.get("proposal_samples")).items():
        lines.extend([f"### `{_escape(reason)}`", "", _row_table(rows), ""])
    lines.extend(["## Limitations", ""])
    for limitation in _sequence(report.get("limitations")):
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


def _proposal_reasons(
    row: Mapping[str, object],
    *,
    rows_by_lemma: Mapping[str, Mapping[str, object]],
) -> list[str]:
    lemma = str(row.get("lemma") or "").strip()
    if not lemma:
        return []
    pos = str(row.get("pos") or "").strip()
    rank_base = _float(row.get("rank_base")) or 1.0
    reasons: list[str] = []
    if _has_semantic_support(row):
        return reasons

    if not pos and rank_base < 0.75:
        reasons.append("de_missing_pos_no_semantic_support_rank_lt_075")
    if (
        not pos
        and rank_base < 0.65
        and (
            (_float(row.get("learner_source_confidence")) or 0.0) > 0.0
            or (_float(row.get("goethe_stem_learner_source_known")) or 0.0) > 0.0
            or (_float(row.get("openlingo_learner_source_known")) or 0.0) > 0.0
        )
    ):
        reasons.append("de_stem_or_learner_only_no_pos_rank_lt_065")
    if 2 <= len(lemma) <= 5 and _is_alpha(lemma) and "SUB:" in pos and rank_base < 0.75:
        reasons.append("de_short_noun_no_semantic_support_rank_lt_075")
    if "VER:" in pos and "SUB:" in pos and rank_base < 0.75 and not _has_translations(row):
        reasons.append("de_mixed_verb_noun_no_semantic_support_rank_lt_075")
    if "auße" in lemma.casefold() and _looks_like_supported_ausz_counterpart(
        lemma,
        rows_by_lemma=rows_by_lemma,
    ):
        reasons.append("de_unsupported_ausz_artifact")
    return reasons


def _looks_like_supported_ausz_counterpart(
    lemma: str,
    *,
    rows_by_lemma: Mapping[str, Mapping[str, object]],
) -> bool:
    candidates = {
        lemma.casefold().replace("auße", "ausse"),
        lemma.casefold().replace("auße", "ause"),
    }
    for candidate in candidates:
        counterpart = rows_by_lemma.get(candidate)
        if counterpart and _has_semantic_support(counterpart):
            return True
    return False


def _has_semantic_support(row: Mapping[str, object]) -> bool:
    return (
        _has_translations(row)
        or any(str(item).strip() for item in _sequence(row.get("topics")))
        or (_float(row.get("reverse_support_score")) or 0.0) > 0.0
        or (_float(row.get("translation_count_score")) or 0.0) > 0.0
        or (_float(row.get("klexikon_title_known")) or 0.0) > 0.0
        or (_float(row.get("odenet_basis_learner_source_known")) or 0.0) > 0.0
    )


def _has_translations(row: Mapping[str, object]) -> bool:
    return any(str(item).strip() for item in _sequence(row.get("translations")))


def _review_row(
    row: Mapping[str, object],
    *,
    runtime: object,
    proposals: Sequence[str],
) -> dict[str, object]:
    return {
        "lemma": str(row.get("lemma") or "").strip(),
        "runtime_state": getattr(runtime, "candidate_state", ""),
        "runtime_reasons": list(getattr(runtime, "reasons", ()) or ()),
        "proposal_reasons": list(proposals),
        "rank_base": _round(row.get("rank_base")),
        "pos": str(row.get("pos") or ""),
        "pos_bucket": str(row.get("pos_bucket") or ""),
        "translations": [
            str(item).strip() for item in _sequence(row.get("translations")) if str(item).strip()
        ][:5],
        "signals": {
            key: _round(row.get(key))
            for key in (
                "learner_source_confidence",
                "goethe_official_a1_learner_source_known",
                "goethe_stem_learner_source_known",
                "openlingo_learner_source_known",
                "translation_count_score",
                "reverse_support_score",
                "klexikon_title_known",
                "odenet_basis_learner_source_known",
                "wordfreq_de_commonness_score",
                "opensubtitles_cistem_frequency_score",
            )
            if _float(row.get(key)) is not None and (_float(row.get(key)) or 0.0) > 0.0
        },
    }


def _row_table(
    value: object,
    *,
    include_label_columns: bool = False,
) -> str:
    rows = [_mapping(row) for row in _sequence(value)]
    if not rows:
        return "_No rows._"
    label_header = " | expected | runtime covered | probe covered" if include_label_columns else ""
    lines = [
        f"| Lemma | Runtime | Proposals | rank_base | POS | Translations{label_header} |",
        f"| --- | --- | --- | ---: | --- | ---{' | --- | --- | ---' if include_label_columns else ''} |",
    ]
    for row in rows:
        label_cells = ""
        if include_label_columns:
            label_cells = (
                f" | `{_escape(row.get('expected_candidate_state'))}`"
                f" | `{_escape(row.get('covered_by_runtime'))}`"
                f" | `{_escape(row.get('covered_by_signal_probe'))}`"
            )
        lines.append(
            f"| `{_escape(row.get('lemma'))}`"
            f" | `{_escape(row.get('runtime_state'))}`"
            f" | {_escape(', '.join(str(item) for item in _sequence(row.get('proposal_reasons'))) or '-')}"
            f" | {_fmt(row.get('rank_base'))}"
            f" | `{_escape(str(row.get('pos') or '')[:64])}`"
            f" | {_escape('; '.join(str(item) for item in _sequence(row.get('translations'))[:3]) or '-')}"
            f"{label_cells} |"
        )
    return "\n".join(lines)


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _load_restricted_labels(paths: Sequence[Path]) -> dict[str, Mapping[str, object]]:
    labels: dict[str, Mapping[str, object]] = {}
    for path in paths:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in _label_rows(payload):
            lemma = str(row.get("lemma") or "").strip()
            state = str(row.get("expected_candidate_state") or "").strip()
            if lemma and state and state != CANDIDATE_STATE_NORMAL_VOCAB:
                labels[lemma] = row
    return labels


def _label_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Mapping):
        rows = value.get("labels")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, Mapping)]
        rows = value.get("rows")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, Mapping)]
        items = value.get("items")
        if isinstance(items, list):
            return [row for row in items if isinstance(row, Mapping)]
    if isinstance(value, list):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _sort_key(row: Mapping[str, object]) -> tuple[float, str]:
    return (_float(row.get("rank_base")) or 1.0, str(row.get("lemma") or ""))


def _is_alpha(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]+", str(value or "")))


def _float(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _round(value: object) -> float | None:
    parsed = _float(value)
    if parsed is None:
        return None
    return round(parsed, 6)


def _fmt(value: object) -> str:
    parsed = _float(value)
    if parsed is None:
        return "-"
    return f"{parsed:.3f}"


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, (list, tuple)):
        return value
    return ()


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _escape(value: object) -> str:
    text = str(value if value is not None else "")
    return text.replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
