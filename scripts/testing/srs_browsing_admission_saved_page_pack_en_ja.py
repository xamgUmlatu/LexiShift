#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (CORE_ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.use_cases.browsing_admission import (  # noqa: E402
    ingest_browsing_admission_signals,
)
from lexishift_core.srs.browsing_admission import (  # noqa: E402
    BROWSING_SIGNAL_SOURCE,
    BROWSING_SIGNAL_TARGET,
    BrowsingSignalIngestPolicy,
)
from lexishift_core.srs.browsing_identity import (  # noqa: E402
    BROWSING_OBSERVATION_SOURCE_MAPPING,
    BROWSING_OBSERVATION_TARGET_SURFACE,
    build_browsing_target_key,
)
from srs_browsing_admission_saved_page_support import (  # noqa: E402
    JmdictCandidate,
    SavedDocument,
    SavedPagePolicy,
    ambiguity_confidence,
    build_jmdict_indexes,
    collect_exact_ruby_counts,
    collect_source_counts,
    collect_target_surface_counts,
    counter_preview,
    document_summary,
    load_json_mapping,
    load_saved_documents,
    repo_path,
    resolve_pair_data_paths,
    ruby_preview,
)


REPORT_SCHEMA_VERSION = 1
DEFAULT_PAIR = "en-ja"
DEFAULT_MANIFEST_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_browsing_admission_saved_pages_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_browsing_admission_saved_page_pack_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_browsing_admission_saved_page_pack_en_ja_latest.md"
)


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    args = parse_args()
    report = build_report(
        manifest_json=args.manifest_json,
        jmdict_path=args.jmdict_path,
        frequency_db=args.frequency_db,
        json_out=args.json_out,
        policy=SavedPagePolicy(),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"json_out: {args.json_out}")
    print(f"markdown_out: {args.markdown_out}")
    print(
        "summary: "
        f"status={report['status']} "
        f"pass={report['summary']['pass']} "
        f"warn={report['summary']['warn']} "
        f"fail={report['summary']['fail']}"
    )
    if args.fail_on_review and report["status"] != "pass":
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert saved en-ja browsing page fixtures into aggregate browsing signals."
    )
    parser.add_argument("--manifest-json", type=Path, default=DEFAULT_MANIFEST_JSON)
    parser.add_argument("--jmdict-path", type=Path)
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def build_report(
    *,
    manifest_json: Path,
    jmdict_path: Path | None,
    frequency_db: Path | None = None,
    json_out: Path | None = None,
    policy: SavedPagePolicy = SavedPagePolicy(),
    generated_at: str | None = None,
) -> dict[str, Any]:
    manifest = load_json_mapping(manifest_json)
    pair = str(manifest.get("pair") or DEFAULT_PAIR)
    resolved_jmdict, resolved_frequency_db = resolve_pair_data_paths(
        pair=pair,
        jmdict_path=jmdict_path,
        frequency_db=frequency_db,
    )
    documents = load_saved_documents(manifest)
    source_counts = collect_source_counts(documents)
    target_text = "\n".join(document.text for document in documents if document.side == "target")
    source_index, target_index, exact_pairs, jmdict_summary = build_jmdict_indexes(
        resolved_jmdict,
        source_terms=set(source_counts),
        target_text=target_text,
        frequency_db=resolved_frequency_db,
        policy=policy,
    )
    signals, signal_debug = build_signal_entries(
        documents=documents,
        source_counts=source_counts,
        source_index=source_index,
        target_index=target_index,
        exact_pairs=exact_pairs,
        policy=policy,
    )
    ingest_result = ingest_signals(pair=pair, signals=signals)
    findings = build_findings(
        manifest=manifest,
        signals=signals,
        ingest_result=ingest_result,
        documents=documents,
    )
    summary = summarize_findings(findings)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": generated_at or now_iso_utc(),
        "status": "fail" if summary["fail"] else "pass" if not summary["warn"] else "warn",
        "pair": pair,
        "runtime_scope": "saved_page_to_browsing_aggregate",
        "policy": policy.to_dict(),
        "inputs": {
            "manifest_json": repo_path(manifest_json),
            "jmdict_path": str(resolved_jmdict),
            "frequency_db": str(resolved_frequency_db) if resolved_frequency_db else None,
            "output_json": repo_path(json_out),
            "documents": [document_summary(document) for document in documents],
        },
        "privacy": {
            "saved_fixture_files_contain_page_content": True,
            "aggregate_report_stores_raw_text": False,
            "helper_store_stores_raw_text": False,
            "runtime_browser_capture": False,
            "runtime_srs_mutation": False,
        },
        "jmdict": jmdict_summary,
        "extraction": {
            "source_terms": counter_preview(source_counts),
            "ruby_pair_count": sum(sum(document.ruby_pairs.values()) for document in documents),
            "top_ruby_pairs": ruby_preview(documents),
        },
        "signals": {
            "count": len(signals),
            "source_mapping_count": sum(
                1
                for signal in signals
                if signal.get("observation_source") == BROWSING_OBSERVATION_SOURCE_MAPPING
            ),
            "target_surface_count": sum(
                1
                for signal in signals
                if signal.get("observation_source") == BROWSING_OBSERVATION_TARGET_SURFACE
            ),
            "top": signal_debug[:30],
        },
        "helper_ingest": ingest_result,
        "findings": findings,
        "summary": summary,
        "limitations": [
            "Saved-page extraction is deterministic and local; browser DOM timing is not tested.",
            "English source mapping uses exact JMDict gloss matches only, so it favors precision over recall.",
            "Japanese non-ruby surface fallback uses simple string counts and JMDict ambiguity damping.",
            "The helper aggregate store is temporary in this harness; no live SRS state is mutated.",
        ],
    }


def build_signal_entries(
    *,
    documents: Sequence[SavedDocument],
    source_counts: Counter[str],
    source_index: Mapping[str, Sequence[JmdictCandidate]],
    target_index: Mapping[str, Sequence[JmdictCandidate]],
    exact_pairs: set[tuple[str, str]],
    policy: SavedPagePolicy,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: dict[tuple[str, str], dict[str, object]] = {}
    debug_rows: list[dict[str, object]] = []
    for term, count in source_counts.most_common():
        candidates = tuple(source_index.get(term) or ())
        if not candidates:
            continue
        if len(candidates) > policy.max_source_ambiguity_candidates:
            continue
        confidence = ambiguity_confidence(len(candidates))
        for candidate in candidates[: policy.max_source_candidates_per_term]:
            add_signal(
                rows,
                target_lemma=candidate.target_lemma,
                target_reading=candidate.target_reading,
                side=BROWSING_SIGNAL_SOURCE,
                count=min(float(count), policy.max_count_per_signal),
                source_mapping_confidence=confidence,
                reading_confidence=1.0,
                observation_source=BROWSING_OBSERVATION_SOURCE_MAPPING,
            )
            debug_rows.append(
                signal_debug_row(
                    candidate=candidate,
                    side=BROWSING_SIGNAL_SOURCE,
                    count=count,
                    confidence=confidence,
                    observation_source=BROWSING_OBSERVATION_SOURCE_MAPPING,
                    evidence=term,
                )
            )
    target_surface_counts = collect_target_surface_counts(
        documents,
        target_index=target_index,
        policy=policy,
    )
    exact_ruby_counts = collect_exact_ruby_counts(documents, exact_pairs=exact_pairs)
    for (surface, reading), count in exact_ruby_counts.most_common():
        add_signal(
            rows,
            target_lemma=surface,
            target_reading=reading,
            side=BROWSING_SIGNAL_TARGET,
            count=min(float(count), policy.max_count_per_signal),
            source_mapping_confidence=1.0,
            reading_confidence=1.0,
            observation_source=BROWSING_OBSERVATION_TARGET_SURFACE,
        )
        debug_rows.append(
            {
                "target_key": build_browsing_target_key(
                    target_lemma=surface,
                    target_reading=reading,
                ),
                "target_lemma": surface,
                "target_reading": reading,
                "side": BROWSING_SIGNAL_TARGET,
                "count": count,
                "confidence": 1.0,
                "observation_source": BROWSING_OBSERVATION_TARGET_SURFACE,
                "evidence": f"{surface}/{reading}",
                "mapping": "page_ruby",
            }
        )
    for surface, count in target_surface_counts.most_common(policy.max_target_surface_candidates):
        if any(surface == exact_surface for exact_surface, _reading in exact_ruby_counts):
            continue
        candidates = tuple(target_index.get(surface) or ())
        if not candidates:
            continue
        candidate = candidates[0]
        reading_confidence = ambiguity_confidence(len(candidates))
        add_signal(
            rows,
            target_lemma=candidate.target_lemma,
            target_reading=candidate.target_reading,
            side=BROWSING_SIGNAL_TARGET,
            count=min(float(count), policy.max_count_per_signal),
            source_mapping_confidence=1.0,
            reading_confidence=reading_confidence,
            observation_source=BROWSING_OBSERVATION_TARGET_SURFACE,
        )
        debug_rows.append(
            signal_debug_row(
                candidate=candidate,
                side=BROWSING_SIGNAL_TARGET,
                count=count,
                confidence=reading_confidence,
                observation_source=BROWSING_OBSERVATION_TARGET_SURFACE,
                evidence=surface,
            )
        )
    signals = sorted(
        rows.values(),
        key=lambda row: (
            str(row.get("observation_source")),
            -float(row.get("count") or 0.0),
            str(row.get("target_key")),
        ),
    )[: policy.max_signal_rows]
    debug_rows.sort(
        key=lambda row: (
            str(row.get("observation_source")),
            -float(row.get("count") or 0.0),
            str(row.get("target_key")),
        )
    )
    return signals, debug_rows


def add_signal(
    rows: dict[tuple[str, str], dict[str, object]],
    *,
    target_lemma: str,
    target_reading: str,
    side: str,
    count: float,
    source_mapping_confidence: float,
    reading_confidence: float,
    observation_source: str,
) -> None:
    target_key = build_browsing_target_key(
        target_lemma=target_lemma,
        target_reading=target_reading,
    )
    row_key = (target_key, observation_source)
    current = rows.get(row_key)
    if current is None:
        rows[row_key] = {
            "target_key": target_key,
            "target_lemma": target_lemma,
            "target_reading": target_reading,
            "side": side,
            "count": round(float(count), 6),
            "source_mapping_confidence": round(float(source_mapping_confidence), 6),
            "reading_confidence": round(float(reading_confidence), 6),
            "observation_source": observation_source,
        }
        return
    current["count"] = round(float(current.get("count") or 0.0) + float(count), 6)
    current["source_mapping_confidence"] = round(
        max(float(current.get("source_mapping_confidence") or 0.0), source_mapping_confidence),
        6,
    )
    current["reading_confidence"] = round(
        max(float(current.get("reading_confidence") or 0.0), reading_confidence),
        6,
    )


def ingest_signals(*, pair: str, signals: Sequence[Mapping[str, object]]) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="lexishift-saved-page-browsing-") as tmp:
        paths = build_helper_paths(Path(tmp))
        return ingest_browsing_admission_signals(
            paths,
            pair=pair,
            profile_id="saved_page_probe",
            captured_at="2026-07-03T00:00:00Z",
            opt_in=True,
            signals=signals,
            policy=BrowsingSignalIngestPolicy(max_items_per_store=500, max_signals_per_packet=300),
            resolve_profile_id_fn=lambda _paths, profile_id="default": str(profile_id),
        )


def signal_debug_row(
    *,
    candidate: JmdictCandidate,
    side: str,
    count: float,
    confidence: float,
    observation_source: str,
    evidence: str,
) -> dict[str, object]:
    return {
        "target_key": candidate.target_key,
        "target_lemma": candidate.target_lemma,
        "target_reading": candidate.target_reading,
        "side": side,
        "count": count,
        "confidence": round(float(confidence), 6),
        "observation_source": observation_source,
        "evidence": evidence,
        "frequency_rank": (
            None if candidate.frequency_rank >= 999999999.0 else int(candidate.frequency_rank)
        ),
        "frequency_known": candidate.frequency_rank < 999999999.0,
        "priority_rank": None if candidate.priority_rank >= 999 else int(candidate.priority_rank),
        "glosses": list(candidate.glosses[:3]),
    }


def build_findings(
    *,
    manifest: Mapping[str, object],
    signals: Sequence[Mapping[str, object]],
    ingest_result: Mapping[str, object],
    documents: Sequence[SavedDocument],
) -> list[dict[str, object]]:
    expectations = manifest.get("expectations") if isinstance(manifest, Mapping) else {}
    expectations = expectations if isinstance(expectations, Mapping) else {}
    findings = []
    source_count = sum(
        1
        for signal in signals
        if signal.get("observation_source") == BROWSING_OBSERVATION_SOURCE_MAPPING
    )
    target_count = sum(
        1
        for signal in signals
        if signal.get("observation_source") == BROWSING_OBSERVATION_TARGET_SURFACE
    )
    findings.append(
        finding(
            "source_mapping_signals_present",
            source_count >= int(expectations.get("min_source_mapping_signals") or 1),
            {"count": source_count},
        )
    )
    findings.append(
        finding(
            "target_surface_signals_present",
            target_count >= int(expectations.get("min_target_surface_signals") or 1),
            {"count": target_count},
        )
    )
    observed_sources = {str(signal.get("observation_source") or "") for signal in signals}
    for source in expectations.get("required_observation_sources") or ():
        findings.append(
            finding(
                f"required_observation_source:{source}",
                str(source) in observed_sources,
                {"observed_sources": sorted(observed_sources)},
            )
        )
    aggregate_store = ingest_result.get("aggregate_store")
    item_count = (
        int(aggregate_store.get("item_count") or 0) if isinstance(aggregate_store, Mapping) else 0
    )
    findings.append(
        finding("helper_aggregate_store_populated", item_count > 0, {"count": item_count})
    )
    ruby_count = sum(sum(document.ruby_pairs.values()) for document in documents)
    findings.append(finding("target_ruby_pairs_detected", ruby_count > 0, {"count": ruby_count}))
    privacy = ingest_result.get("privacy") if isinstance(ingest_result, Mapping) else {}
    findings.append(
        finding(
            "helper_privacy_contract",
            bool(isinstance(privacy, Mapping) and privacy.get("raw_text_stored") is False),
            dict(privacy) if isinstance(privacy, Mapping) else {},
        )
    )
    return findings


def finding(name: str, passed: bool, details: Mapping[str, object]) -> dict[str, object]:
    return {
        "name": name,
        "status": "pass" if passed else "fail",
        "details": dict(details),
    }


def summarize_findings(findings: Sequence[Mapping[str, object]]) -> dict[str, int]:
    return {
        "pass": sum(1 for finding_row in findings if finding_row.get("status") == "pass"),
        "warn": sum(1 for finding_row in findings if finding_row.get("status") == "warn"),
        "fail": sum(1 for finding_row in findings if finding_row.get("status") == "fail"),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# SRS Browsing Admission Saved-Page Pack en-ja",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Pair: `{report.get('pair')}`",
        f"- Runtime scope: `{report.get('runtime_scope')}`",
        f"- Raw text stored in aggregate report: `{report.get('privacy', {}).get('aggregate_report_stores_raw_text')}`",
        "",
        "## Inputs",
        "",
    ]
    inputs = report.get("inputs") if isinstance(report.get("inputs"), Mapping) else {}
    for document in inputs.get("documents", []) if isinstance(inputs, Mapping) else []:
        if not isinstance(document, Mapping):
            continue
        lines.append(
            "- "
            f"`{document.get('document_id')}` "
            f"side=`{document.get('side')}` "
            f"chars=`{document.get('text_char_count')}` "
            f"ruby_pairs=`{document.get('ruby_pair_count')}` "
            f"sha256=`{document.get('sha256')}`"
        )
    lines.extend(["", "## Signal Summary", ""])
    signals = report.get("signals") if isinstance(report.get("signals"), Mapping) else {}
    lines.append(f"- Total signals: `{signals.get('count')}`")
    lines.append(f"- Source-mapping signals: `{signals.get('source_mapping_count')}`")
    lines.append(f"- Target-surface signals: `{signals.get('target_surface_count')}`")
    lines.extend(["", "### Top Signals", ""])
    lines.append("| Target | Source | Count | Confidence | Freq. rank | Priority | Evidence |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")
    for row in signals.get("top", [])[:20] if isinstance(signals, Mapping) else []:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            f"`{row.get('target_key')}` | "
            f"`{row.get('observation_source')}` | "
            f"{row.get('count')} | "
            f"{row.get('confidence')} | "
            f"{row.get('frequency_rank') if row.get('frequency_known') else ''} | "
            f"{row.get('priority_rank') or ''} | "
            f"`{row.get('evidence')}` |"
        )
    lines.extend(["", "## Aggregate Store", ""])
    aggregate_store = report.get("helper_ingest", {}).get("aggregate_store", {})
    lines.append(f"- Items: `{aggregate_store.get('item_count')}`")
    lines.append("")
    lines.append("| Target | Source | Target | Replacement | Reading Conf. | Sources |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for row in aggregate_store.get("top_items", [])[:20]:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            f"`{row.get('target_key')}` | "
            f"{row.get('source_hit_count')} | "
            f"{row.get('target_hit_count')} | "
            f"{row.get('replacement_exposure_count')} | "
            f"{row.get('reading_confidence')} | "
            f"`{', '.join(row.get('observation_sources') or [])}` |"
        )
    lines.extend(["", "## Findings", ""])
    for row in report.get("findings") or []:
        if isinstance(row, Mapping):
            lines.append(f"- `{row.get('status')}` {row.get('name')}: `{row.get('details')}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
