#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

from srs_animals_plants_existing_signal_audit_en_es import _candidate_lemmas, load_kaikki_rows
from srs_food_cooking_existing_signal_audit_en_es import (
    DEFAULT_FREQUENCY_DB,
    DEFAULT_KAIKKI_FORWARD_DB,
    DEFAULT_POLICY,
    evidence_from_rows,
    load_food_policy,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_food_cooking_source_capacity_audit_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_food_cooking_source_capacity_audit_en_es_latest.md"
)
DEFAULT_TOP_N = 10000
COMMON_FOOD_PROBES = (
    "comida",
    "comer",
    "cocinar",
    "cocina",
    "restaurante",
    "agua",
    "vino",
    "pan",
    "arroz",
    "pollo",
    "carne",
    "huevo",
    "leche",
    "queso",
    "tomate",
    "patata",
    "papa",
    "azúcar",
    "sal",
    "sopa",
    "fruta",
    "verdura",
    "pescado",
    "cerveza",
    "café",
    "té",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare food/cooking signal capacity in the installed Kaikki source with "
            "the current en-es SRS frequency frontier. Read-only; no downloads or overlays."
        )
    )
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--frequency-db", type=Path, default=DEFAULT_FREQUENCY_DB)
    parser.add_argument("--kaikki-forward-db", type=Path, default=DEFAULT_KAIKKI_FORWARD_DB)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
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
    policy_path: Path = DEFAULT_POLICY,
    frequency_db: Path = DEFAULT_FREQUENCY_DB,
    kaikki_forward_db: Path = DEFAULT_KAIKKI_FORWARD_DB,
    top_n: int = DEFAULT_TOP_N,
    generated_at: str | None = None,
) -> dict[str, object]:
    policy = load_food_policy(policy_path)
    frequency_path = Path(frequency_db).expanduser().resolve(strict=False)
    kaikki_path = Path(kaikki_forward_db).expanduser().resolve(strict=False)
    if not frequency_path.exists() or not kaikki_path.exists():
        findings = []
        if not frequency_path.exists():
            findings.append(_finding("FAIL", "frequency_db_missing", "Frequency DB is missing."))
        if not kaikki_path.exists():
            findings.append(_finding("FAIL", "kaikki_db_missing", "Kaikki DB is missing."))
        return _report(
            generated_at=generated_at,
            policy_path=policy_path,
            frequency_db=frequency_path,
            kaikki_forward_db=kaikki_path,
            top_n=top_n,
            source_capacity={},
            current_frontier={},
            common_probe_rows=[],
            findings=findings,
        )

    frequency_lemmas = set(_candidate_lemmas(frequency_path, top_n=top_n))
    rows_by_lemma = load_kaikki_rows(kaikki_path)
    candidate_rows = _candidate_rows(rows_by_lemma, policy)
    current_rows = [row for row in candidate_rows if row["lemma"] in frequency_lemmas]
    outside_rows = [row for row in candidate_rows if row["lemma"] not in frequency_lemmas]
    common_probe_rows = _common_probe_rows(
        probes=COMMON_FOOD_PROBES,
        frequency_lemmas=frequency_lemmas,
        rows_by_lemma=rows_by_lemma,
        policy=policy,
    )
    findings = _findings(
        candidate_rows=candidate_rows,
        current_rows=current_rows,
        common_probe_rows=common_probe_rows,
    )
    return _report(
        generated_at=generated_at,
        policy_path=policy_path,
        frequency_db=frequency_path,
        kaikki_forward_db=kaikki_path,
        top_n=top_n,
        source_capacity=_summary(candidate_rows),
        current_frontier={
            **_summary(current_rows),
            "frequency_lemma_count": len(frequency_lemmas),
            "outside_current_candidate_count": len(outside_rows),
            "outside_current_examples": _examples(outside_rows, limit=20),
        },
        common_probe_rows=common_probe_rows,
        findings=findings,
    )


def _candidate_rows(
    rows_by_lemma: Mapping[str, Sequence[Mapping[str, object]]], policy: object
) -> list[dict[str, object]]:
    rows = []
    for lemma, source_rows in rows_by_lemma.items():
        evidence = evidence_from_rows(lemma, source_rows, policy)
        if not evidence:
            continue
        best = sorted(evidence, key=lambda item: (-item.score, item.tier, item.source_label))[0]
        rows.append(
            {
                "lemma": lemma,
                "best_tier": best.tier,
                "confidence": round(best.score, 6),
                "confidence_band": _confidence_band(best.score),
                "source_channel": best.source_channel,
                "source_label": best.source_label,
                "snippet": best.snippet,
            }
        )
    return sorted(rows, key=lambda row: (row["best_tier"], row["confidence_band"], row["lemma"]))


def _common_probe_rows(
    *,
    probes: Sequence[str],
    frequency_lemmas: set[str],
    rows_by_lemma: Mapping[str, Sequence[Mapping[str, object]]],
    policy: object,
) -> list[dict[str, object]]:
    rows = []
    for lemma in probes:
        evidence = evidence_from_rows(lemma, rows_by_lemma.get(lemma, ()), policy)
        best = (
            sorted(evidence, key=lambda item: (-item.score, item.tier, item.source_label))[0]
            if evidence
            else None
        )
        rows.append(
            {
                "lemma": lemma,
                "in_current_frequency_frontier": lemma in frequency_lemmas,
                "has_current_policy_signal": bool(best),
                "best_tier": best.tier if best else "",
                "confidence_band": _confidence_band(best.score) if best else "",
                "source_label": best.source_label if best else "",
                "snippet": best.snippet if best else "",
            }
        )
    return rows


def render_markdown(report: Mapping[str, object]) -> str:
    source = _as_mapping(report.get("source_capacity"))
    current = _as_mapping(report.get("current_frontier"))
    lines = [
        "# en-es Food/Cooking Source Capacity Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Full local Kaikki food-signal lemmas: `{source.get('candidate_count', 0)}`",
        f"- Current frequency frontier food-signal lemmas: `{current.get('candidate_count', 0)}`",
        f"- Outside current frontier: `{current.get('outside_current_candidate_count', 0)}`",
        "",
        "## Findings",
        "",
    ]
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
            f"{finding.get('message', '')}"
        )
    lines.extend(["", "## Source Capacity", ""])
    lines.append(f"- Tier counts: `{source.get('tier_counts', {})}`")
    lines.append(f"- Confidence bands: `{source.get('confidence_band_counts', {})}`")
    lines.append("")
    lines.append("### Top Source Labels")
    lines.append("")
    for row in _mapping_rows(source.get("top_source_labels")):
        lines.append(f"- `{row.get('label', '')}`: {row.get('count', 0)}")
    lines.extend(["", "## Common Food Probe Coverage", ""])
    lines.append("| Lemma | In Current Frontier | Policy Signal | Best Signal |")
    lines.append("| --- | --- | --- | --- |")
    for row in _mapping_rows(report.get("common_food_probe_rows")):
        signal = ":".join(
            part
            for part in (
                str(row.get("best_tier") or ""),
                str(row.get("confidence_band") or ""),
                str(row.get("source_label") or ""),
            )
            if part
        )
        lines.append(
            f"| `{row.get('lemma', '')}` | `{row.get('in_current_frequency_frontier', False)}` | "
            f"`{row.get('has_current_policy_signal', False)}` | `{signal}` |"
        )
    lines.extend(["", "## Outside-Frontier Examples", ""])
    for row in _mapping_rows(current.get("outside_current_examples")):
        lines.append(
            f"- `{row.get('lemma', '')}`: `{row.get('best_tier', '')}` "
            f"`{row.get('confidence_band', '')}` via `{row.get('source_label', '')}`"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines) + "\n"


def _report(
    *,
    generated_at: str | None,
    policy_path: Path,
    frequency_db: Path,
    kaikki_forward_db: Path,
    top_n: int,
    source_capacity: Mapping[str, object],
    current_frontier: Mapping[str, object],
    common_probe_rows: Sequence[Mapping[str, object]],
    findings: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "food_cooking_source_capacity_audit_completed"
            if status == "ok"
            else "food_cooking_source_capacity_audit_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "inputs": {
            "signal_policy_json": str(Path(policy_path).expanduser().resolve(strict=False)),
            "frequency_db": str(frequency_db),
            "kaikki_forward_db": str(kaikki_forward_db),
            "top_n": int(top_n),
        },
        "source_capacity": dict(source_capacity),
        "current_frontier": dict(current_frontier),
        "common_food_probe_rows": list(common_probe_rows),
        "findings": list(findings),
        "summary": {
            "finding_counts": dict(Counter(row["level"] for row in findings)),
            "issues": [row["code"] for row in findings if row["level"] == "FAIL"],
            "warnings": [row["code"] for row in findings if row["level"] == "WARN"],
        },
        "limitations": [
            "This audit uses installed local Kaikki/Wiktionary rows and the current food/cooking policy only.",
            "It does not download sources, mutate packs, write overlays, or change admission behavior.",
            "Source-capacity totals are not precision-reviewed; use the full-source review packet for sampled precision.",
            "The common probe list is diagnostic and intentionally small.",
        ],
    }


def _summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "candidate_count": len(rows),
        "tier_counts": _counts(rows, "best_tier"),
        "confidence_band_counts": _counts(rows, "confidence_band"),
        "top_source_labels": _counter_rows(
            Counter(str(row.get("source_label") or "") for row in rows)
        ),
        "examples": _examples(rows, limit=20),
    }


def _findings(
    *,
    candidate_rows: Sequence[Mapping[str, object]],
    current_rows: Sequence[Mapping[str, object]],
    common_probe_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    findings = []
    if candidate_rows:
        findings.append(
            _finding(
                "PASS",
                "full_source_food_signals_present",
                "Local Kaikki has food/cooking signal supply.",
            )
        )
    else:
        findings.append(
            _finding("FAIL", "full_source_food_signals_absent", "No food/cooking signals found.")
        )
    if len(candidate_rows) >= max(1, len(current_rows) * 10):
        findings.append(
            _finding(
                "PASS",
                "frontier_is_primary_recall_bottleneck",
                "Full local source has far more food/cooking candidates than the current SRS frontier.",
            )
        )
    missing_common = [
        row["lemma"]
        for row in common_probe_rows
        if row.get("has_current_policy_signal") and not row.get("in_current_frequency_frontier")
    ]
    if missing_common:
        findings.append(
            _finding(
                "WARN",
                "common_food_terms_missing_from_current_frontier",
                f"Common food probes missing from the current frontier: {', '.join(missing_common[:12])}.",
            )
        )
    return findings


def _examples(rows: Sequence[Mapping[str, object]], *, limit: int) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in sorted(rows, key=lambda row: -float(row.get("confidence") or 0))[:limit]
    ]


def _counter_rows(counter: Counter[str], *, limit: int = 20) -> list[dict[str, object]]:
    return [{"label": label, "count": count} for label, count in counter.most_common(limit)]


def _counts(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "") for row in rows).items()))


def _confidence_band(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.65:
        return "medium"
    if score >= 0.45:
        return "review"
    return "inventory"


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
