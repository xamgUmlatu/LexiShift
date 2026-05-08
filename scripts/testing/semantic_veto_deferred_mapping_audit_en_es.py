#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
from typing import Mapping, Sequence
import unicodedata


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
for candidate in (str(CORE_ROOT), str(Path(__file__).resolve().parent)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_reverse_translation_dictionary_path,
    default_translation_dictionary_path,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _load_json,
    _mapping_rows,
    _repo_path,
    _resolve_repo_path,
)


DEFAULT_TRUSTED_SEED = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_trusted_eval_seed_v1.json"
)
DEFAULT_REPAIRED_PILOT = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_repaired_pilot_v1.json"
)
DEFAULT_DRAFT_DATASET = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_representative_manual_v1.json"
)
DEFAULT_SRS_ZIPF_BRIDGE = TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_latest.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_deferred_mapping_audit_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_deferred_mapping_audit_en_es_latest.md"


DEFERRED_MAPPINGS: tuple[dict[str, str], ...] = (
    {
        "family_id": "en-es:full-family-representative:bar:cercar",
        "source": "bar",
        "target": "cercar",
    },
    {
        "family_id": "en-es:full-family-representative:offset:distancia",
        "source": "offset",
        "target": "distancia",
    },
    {
        "family_id": "en-es:full-family-representative:demand:deduccion",
        "source": "demand",
        "target": "deducción",
    },
)

PAIR_AUDIT_GUIDANCE: dict[str, dict[str, object]] = {
    "bar->cercar": {
        "audit_status": "salvageable_with_corrected_active_sense",
        "confidence": "medium",
        "source_support_terms": ("obstruct", "passage", "lock", "bolt"),
        "target_support_terms": ("corral", "fence", "fence off", "obstruct"),
        "corrected_active_gloss": "bar as a verb: obstruct, block, or fence off passage",
        "recommended_action": (
            "Do not revive the alcohol-bar draft rows. Author a fresh pending-review "
            "family around verb contexts such as 'bar the entrance' or 'bar the way', "
            "with shadows for pub/counter/legal-bar senses."
        ),
    },
    "offset->distancia": {
        "audit_status": "salvageable_with_corrected_active_sense",
        "confidence": "medium_low",
        "source_support_terms": ("distance by which", "out of alignment", "short distance"),
        "target_support_terms": ("distance",),
        "corrected_active_gloss": (
            "offset as a noun: the distance or displacement by which one thing is out "
            "of alignment with another"
        ),
        "recommended_action": (
            "Author fresh pending-review technical/spatial rows only if the product "
            "accepts the broad target 'distancia' for this sense; otherwise replace the "
            "target with a more specific Spanish competitor such as 'desfase'."
        ),
    },
    "demand->deducción": {
        "audit_status": "reject_mapping_source_target_mismatch",
        "confidence": "high",
        "source_support_terms": ("request", "claim", "purchase goods", "summons"),
        "target_support_terms": ("deduction",),
        "corrected_active_gloss": "",
        "recommended_action": (
            "Keep excluded from trusted evaluation. Treat the reverse FreeDict mapping "
            "as insufficient or erroneous unless an independent source proves a valid "
            "sense; sample a replacement family for this cell instead."
        ),
    },
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit the full-family pilot mappings that were deferred because the "
            "draft active sense did not match the Spanish target."
        )
    )
    parser.add_argument("--trusted-seed-json", type=Path, default=DEFAULT_TRUSTED_SEED)
    parser.add_argument("--repaired-pilot-json", type=Path, default=DEFAULT_REPAIRED_PILOT)
    parser.add_argument("--draft-dataset-json", type=Path, default=DEFAULT_DRAFT_DATASET)
    parser.add_argument("--srs-zipf-bridge-json", type=Path, default=DEFAULT_SRS_ZIPF_BRIDGE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    trusted_path = _resolve_repo_path(args.trusted_seed_json)
    repaired_path = _resolve_repo_path(args.repaired_pilot_json)
    draft_path = _resolve_repo_path(args.draft_dataset_json)
    bridge_path = _resolve_repo_path(args.srs_zipf_bridge_json)
    report = build_deferred_mapping_audit_report(
        trusted_seed_payload=_load_json(trusted_path),
        repaired_pilot_payload=_load_json(repaired_path),
        draft_dataset_payload=_load_json(draft_path),
        srs_zipf_bridge_payload=_load_json(bridge_path),
        trusted_seed_path=trusted_path,
        repaired_pilot_path=repaired_path,
        draft_dataset_path=draft_path,
        srs_zipf_bridge_path=bridge_path,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_deferred_mapping_audit_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_deferred_mapping_audit_report(
    *,
    trusted_seed_payload: Mapping[str, object],
    repaired_pilot_payload: Mapping[str, object],
    draft_dataset_payload: Mapping[str, object],
    srs_zipf_bridge_payload: Mapping[str, object],
    trusted_seed_path: Path | None = None,
    repaired_pilot_path: Path | None = None,
    draft_dataset_path: Path | None = None,
    srs_zipf_bridge_path: Path | None = None,
    installed_evidence_by_pair: Mapping[str, Mapping[str, object]] | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    installed_evidence_by_pair = (
        dict(installed_evidence_by_pair)
        if installed_evidence_by_pair is not None
        else collect_installed_evidence_by_pair()
    )
    mapping_rows = [
        _audit_mapping(
            mapping,
            trusted_seed_payload=trusted_seed_payload,
            repaired_pilot_payload=repaired_pilot_payload,
            draft_dataset_payload=draft_dataset_payload,
            srs_zipf_bridge_payload=srs_zipf_bridge_payload,
            installed_evidence=_as_mapping(installed_evidence_by_pair.get(_pair_key(mapping))),
        )
        for mapping in DEFERRED_MAPPINGS
    ]
    status_counts = Counter(str(row.get("audit_status") or "") for row in mapping_rows)
    issues = []
    if not all(row.get("present_in_repaired_deferred_families") for row in mapping_rows):
        issues.append("some_mappings_missing_from_repaired_pilot_deferred_families")
    if not all(row.get("excluded_from_trusted_seed") for row in mapping_rows):
        issues.append("some_deferred_mappings_leaked_into_trusted_seed")
    if not all(row.get("srs_source_target_pair_present") for row in mapping_rows):
        issues.append("some_mappings_missing_from_srs_source_target_bridge")
    if any(row.get("installed_evidence_status") == "missing" for row in mapping_rows):
        issues.append("installed_dictionary_evidence_missing_for_some_mappings")
    return {
        "schema_version": 1,
        "pair": "en-es",
        "status": "review" if issues else "ok",
        "decision": (
            "deferred_mapping_audit_complete"
            if not issues
            else "deferred_mapping_audit_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "trusted_seed_path": _repo_path(trusted_seed_path),
            "repaired_pilot_path": _repo_path(repaired_pilot_path),
            "draft_dataset_path": _repo_path(draft_dataset_path),
            "srs_zipf_bridge_path": _repo_path(srs_zipf_bridge_path),
            "installed_dictionary_scope": (
                "local installed en-es source/target packs; paths are environment-specific"
            ),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "score_promotion": "none",
            "trusted_seed_change": "none",
            "audit_question": (
                "For each deferred mapping, determine whether the source-target pair is "
                "supported by independent dictionary/sense evidence and whether it can "
                "be rewritten into a coherent pending-review test family."
            ),
            "authority_boundary": (
                "This audit does not make new rows trusted. Salvageable mappings need "
                "fresh row authoring and user review before they enter any trusted lane."
            ),
        },
        "summary": {
            "mapping_count": len(mapping_rows),
            "salvageable_with_corrected_active_sense_count": status_counts.get(
                "salvageable_with_corrected_active_sense", 0
            ),
            "reject_mapping_source_target_mismatch_count": status_counts.get(
                "reject_mapping_source_target_mismatch", 0
            ),
            "trusted_seed_leak_count": sum(
                1 for row in mapping_rows if not row.get("excluded_from_trusted_seed")
            ),
            "status_counts": dict(sorted(status_counts.items())),
        },
        "e2e_checks": {
            "all_mappings_present_in_repaired_deferred_families": all(
                row.get("present_in_repaired_deferred_families") for row in mapping_rows
            ),
            "all_deferred_mappings_excluded_from_trusted_seed": all(
                row.get("excluded_from_trusted_seed") for row in mapping_rows
            ),
            "all_mappings_trace_to_srs_source_target_bridge": all(
                row.get("srs_source_target_pair_present") for row in mapping_rows
            ),
            "all_mappings_have_installed_dictionary_evidence": all(
                row.get("installed_evidence_status") != "missing" for row in mapping_rows
            ),
            "no_mapping_promoted_to_trusted": all(
                str(row.get("trusted_seed_status") or "") == "excluded" for row in mapping_rows
            ),
        },
        "issues": issues,
        "mapping_rows": mapping_rows,
        "next_steps": [
            "Keep demand -> deducción excluded unless an independent source disproves the mismatch.",
            "If desired, author pending-review repaired rows for bar -> cercar and offset -> distancia from corrected active senses only.",
            "User-review any newly authored rows before adding them to the trusted eval seed.",
            "Replace the rejected demand-family slot with a fresh representative family from the same sampling cell.",
        ],
    }


def collect_installed_evidence_by_pair() -> dict[str, dict[str, object]]:
    try:
        paths = build_helper_paths()
        target_to_source_pack = default_translation_dictionary_path(
            "en-es",
            language_packs_dir=paths.language_packs_dir,
        )
        source_to_target_pack = default_reverse_translation_dictionary_path(
            "en-es",
            language_packs_dir=paths.language_packs_dir,
        )
        target_gloss_pack = paths.language_packs_dir / "wiktionary-es-en.sqlite"
    except Exception as exc:  # pragma: no cover - defensive for non-app environments.
        return {
            _pair_key(mapping): {
                "installed_evidence_status": "missing",
                "error": f"{type(exc).__name__}: {exc}",
            }
            for mapping in DEFERRED_MAPPINGS
        }
    result: dict[str, dict[str, object]] = {}
    for mapping in DEFERRED_MAPPINGS:
        source = mapping["source"]
        target = mapping["target"]
        result[_pair_key(mapping)] = {
            "installed_evidence_status": "found",
            "target_to_source_pack": _pack_label(target_to_source_pack),
            "source_to_target_pack": _pack_label(source_to_target_pack),
            "target_gloss_pack": _pack_label(target_gloss_pack),
            "target_to_source_exact": _query_exact_entries(
                target_to_source_pack,
                headword=target,
                translation=source,
            ),
            "source_to_target_exact": _query_exact_entries(
                source_to_target_pack,
                headword=source,
                translation=target,
            ),
            "source_sense_rows": _query_headword_sense_rows(
                source_to_target_pack,
                headword=source,
                limit=24,
            ),
            "target_gloss_rows": _query_headword_sense_rows(
                target_gloss_pack,
                headword=target,
                limit=8,
            ),
        }
    return result


def render_deferred_mapping_audit_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Deferred Mapping Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Mappings audited: `{summary.get('mapping_count', 0)}`",
        f"- Salvageable with corrected active sense: "
        f"`{summary.get('salvageable_with_corrected_active_sense_count', 0)}`",
        f"- Rejected source-target mismatch: "
        f"`{summary.get('reject_mapping_source_target_mismatch_count', 0)}`",
        "",
        "## Methodology",
        "",
        str(_as_mapping(report.get("methodology")).get("audit_question") or ""),
        "",
        str(_as_mapping(report.get("methodology")).get("authority_boundary") or ""),
        "",
        "## Checks",
        "",
        "| Check | Value |",
        "| --- | --- |",
    ]
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{_escape_md(key)}` | `{value}` |")
    lines.extend(["", "## Mapping Decisions", "", _mapping_decision_table(report)])
    lines.extend(["", "## Evidence Details", "", _evidence_detail_table(report)])
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines).rstrip() + "\n"


def _audit_mapping(
    mapping: Mapping[str, str],
    *,
    trusted_seed_payload: Mapping[str, object],
    repaired_pilot_payload: Mapping[str, object],
    draft_dataset_payload: Mapping[str, object],
    srs_zipf_bridge_payload: Mapping[str, object],
    installed_evidence: Mapping[str, object],
) -> dict[str, object]:
    pair_key = _pair_key(mapping)
    guidance = PAIR_AUDIT_GUIDANCE[pair_key]
    source = mapping["source"]
    target = mapping["target"]
    draft_family = _find_family(draft_dataset_payload, family_id=mapping["family_id"])
    active = _as_mapping(draft_family.get("active"))
    evidence = _as_mapping(active.get("evidence_views"))
    source_sense_text = _joined_evidence_text(installed_evidence.get("source_sense_rows"))
    target_gloss_text = _joined_evidence_text(installed_evidence.get("target_gloss_rows"))
    source_support_hits = _matched_terms(
        source_sense_text,
        _string_sequence(guidance.get("source_support_terms")),
    )
    target_support_hits = _matched_terms(
        target_gloss_text,
        _string_sequence(guidance.get("target_support_terms")),
    )
    target_to_source_exact = _mapping_rows(installed_evidence.get("target_to_source_exact"))
    source_to_target_exact = _mapping_rows(installed_evidence.get("source_to_target_exact"))
    srs_pair = _find_srs_pair(srs_zipf_bridge_payload, source=source, target=target)
    return {
        "mapping_id": pair_key,
        "family_id": mapping["family_id"],
        "source": source,
        "target": target,
        "audit_status": str(guidance["audit_status"]),
        "confidence": str(guidance["confidence"]),
        "trusted_seed_status": "excluded"
        if _is_family_deferred(trusted_seed_payload, family_id=mapping["family_id"])
        and not _find_family(trusted_seed_payload, family_id=mapping["family_id"])
        else "present_or_unclear",
        "excluded_from_trusted_seed": _is_family_deferred(
            trusted_seed_payload,
            family_id=mapping["family_id"],
        )
        and not _find_family(trusted_seed_payload, family_id=mapping["family_id"]),
        "present_in_repaired_deferred_families": _is_family_deferred(
            repaired_pilot_payload,
            family_id=mapping["family_id"],
        ),
        "srs_source_target_pair_present": bool(srs_pair),
        "srs_source_target_pair": srs_pair,
        "installed_evidence_status": str(
            installed_evidence.get("installed_evidence_status") or "missing"
        ),
        "source_to_target_exact_count": len(source_to_target_exact),
        "target_to_source_exact_count": len(target_to_source_exact),
        "source_support_hits": source_support_hits,
        "target_support_hits": target_support_hits,
        "draft_active_gloss": str(evidence.get("gloss_text") or ""),
        "draft_active_label": str(evidence.get("sense_label") or ""),
        "corrected_active_gloss": str(guidance.get("corrected_active_gloss") or ""),
        "recommended_action": str(guidance.get("recommended_action") or ""),
        "evidence_summary": _evidence_summary(
            source_to_target_exact=source_to_target_exact,
            target_to_source_exact=target_to_source_exact,
            source_support_hits=source_support_hits,
            target_support_hits=target_support_hits,
        ),
        "source_sense_examples": _trim_evidence_rows(
            installed_evidence.get("source_sense_rows"),
            preferred_terms=_string_sequence(guidance.get("source_support_terms")),
        ),
        "target_gloss_examples": _trim_evidence_rows(
            installed_evidence.get("target_gloss_rows"),
            preferred_terms=_string_sequence(guidance.get("target_support_terms")),
        ),
    }


def _query_exact_entries(
    db_path: Path | None,
    *,
    headword: str,
    translation: str,
) -> list[dict[str, object]]:
    if db_path is None or not db_path.exists():
        return []
    variants = _lower_variants(translation)
    query = (
        "select headword, translation, rank, pos, entry_ord, gloss_ord "
        "from entries where headword_lc = ? and translation_lc in "
        f"({','.join('?' for _ in variants)}) order by rank limit 12"
    )
    return _sqlite_rows(db_path, query, [_lc(headword), *variants])


def _query_headword_sense_rows(
    db_path: Path | None,
    *,
    headword: str,
    limit: int,
) -> list[dict[str, object]]:
    if db_path is None or not db_path.exists() or "sense_glosses" not in _sqlite_tables(db_path):
        return []
    query = (
        "select headword, translation, pos, raw_glosses_json "
        "from sense_glosses where headword_lc = ? "
        "order by entry_ord, sense_ord, gloss_ord limit ?"
    )
    return _sqlite_rows(db_path, query, [_lc(headword), int(limit)])


def _sqlite_rows(db_path: Path, query: str, params: Sequence[object]) -> list[dict[str, object]]:
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute(query, tuple(params))]
    except sqlite3.Error:
        return []


def _sqlite_tables(db_path: Path) -> set[str]:
    try:
        with sqlite3.connect(db_path) as conn:
            return {
                str(row[0])
                for row in conn.execute("select name from sqlite_master where type='table'")
            }
    except sqlite3.Error:
        return set()


def _find_family(payload: Mapping[str, object], *, family_id: str) -> dict[str, object]:
    for family in _mapping_rows(payload.get("families")):
        if str(family.get("family_id") or "") == family_id:
            return dict(family)
    return {}


def _is_family_deferred(payload: Mapping[str, object], *, family_id: str) -> bool:
    return any(
        str(row.get("family_id") or "") == family_id
        for key in ("deferred_families", "excluded_families")
        for row in _mapping_rows(payload.get(key))
    )


def _find_srs_pair(
    payload: Mapping[str, object],
    *,
    source: str,
    target: str,
) -> dict[str, object]:
    for row in _mapping_rows(payload.get("full_source_target_pairs")):
        if str(row.get("source") or "") == source and str(row.get("target") or "") == target:
            return dict(row)
    return {}


def _evidence_summary(
    *,
    source_to_target_exact: Sequence[Mapping[str, object]],
    target_to_source_exact: Sequence[Mapping[str, object]],
    source_support_hits: Sequence[str],
    target_support_hits: Sequence[str],
) -> str:
    fragments = []
    fragments.append(
        "source->target exact found" if source_to_target_exact else "source->target exact not found"
    )
    fragments.append(
        "target->source exact found" if target_to_source_exact else "target->source exact not found"
    )
    fragments.append(f"source sense hits: {', '.join(source_support_hits) or 'none'}")
    fragments.append(f"target gloss hits: {', '.join(target_support_hits) or 'none'}")
    return "; ".join(fragments)


def _mapping_decision_table(report: Mapping[str, object]) -> str:
    rows = _mapping_rows(report.get("mapping_rows"))
    lines = [
        "| Mapping | Status | Confidence | Evidence Summary | Recommended Action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('mapping_id') or ''))}`",
                    f"`{_escape_md(str(row.get('audit_status') or ''))}`",
                    f"`{_escape_md(str(row.get('confidence') or ''))}`",
                    _escape_md(str(row.get("evidence_summary") or "")),
                    _escape_md(str(row.get("recommended_action") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _evidence_detail_table(report: Mapping[str, object]) -> str:
    rows = _mapping_rows(report.get("mapping_rows"))
    lines = [
        "| Mapping | Draft Active Gloss | Corrected Active Gloss | Source Evidence | Target Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        source_evidence = _evidence_cell(row.get("source_sense_examples"))
        target_evidence = _evidence_cell(row.get("target_gloss_examples"))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('mapping_id') or ''))}`",
                    _escape_md(str(row.get("draft_active_gloss") or "")),
                    _escape_md(str(row.get("corrected_active_gloss") or "")),
                    source_evidence,
                    target_evidence,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _evidence_cell(value: object) -> str:
    fragments = []
    for row in _mapping_rows(value)[:3]:
        translation = str(row.get("translation") or "").strip()
        gloss = _jsonish_text(row.get("raw_glosses_json"))
        fragments.append(f"{translation}: {gloss}" if translation else gloss)
    return _escape_md("; ".join(fragment for fragment in fragments if fragment) or "none")


def _joined_evidence_text(value: object) -> str:
    fragments = []
    for row in _mapping_rows(value):
        fragments.extend(
            str(row.get(key) or "") for key in ("translation", "pos", "raw_glosses_json")
        )
    return " ".join(fragments).lower()


def _matched_terms(text: str, terms: Sequence[str]) -> list[str]:
    lower_text = text.lower()
    return [term for term in terms if term.lower() in lower_text]


def _trim_evidence_rows(
    value: object,
    *,
    preferred_terms: Sequence[str] = (),
) -> list[dict[str, object]]:
    source_rows = _mapping_rows(value)
    preferred = []
    fallback = []
    for row in source_rows:
        text = _joined_evidence_text([row])
        if preferred_terms and _matched_terms(text, preferred_terms):
            preferred.append(row)
        else:
            fallback.append(row)
    rows = []
    for row in [*preferred, *fallback][:6]:
        rows.append(
            {
                "headword": row.get("headword"),
                "translation": row.get("translation"),
                "pos": row.get("pos"),
                "raw_glosses_json": row.get("raw_glosses_json"),
            }
        )
    return rows


def _jsonish_text(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(parsed, list):
        return "; ".join(str(item) for item in parsed)
    return str(parsed)


def _pair_key(mapping: Mapping[str, str]) -> str:
    return f"{mapping['source']}->{mapping['target']}"


def _pack_label(path: Path | None) -> str:
    if path is None:
        return "missing"
    parts = path.parts
    if "language_packs" in parts:
        index = parts.index("language_packs")
        return "/".join(parts[index : index + 3])
    return path.name


def _lower_variants(value: str) -> list[str]:
    variants = {_lc(value), _ascii_fold(_lc(value))}
    return sorted(variant for variant in variants if variant)


def _lc(value: str) -> str:
    return str(value or "").strip().lower()


def _ascii_fold(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char)
    )


def _string_sequence(value: object) -> tuple[str, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(str(item) for item in value)
    return ()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
