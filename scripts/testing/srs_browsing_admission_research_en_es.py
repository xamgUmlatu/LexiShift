#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
DEV_SCRIPT_ROOT = PROJECT_ROOT / "scripts" / "dev"
for path in (CORE_ROOT, DEV_SCRIPT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from lexishift_core.srs.profile_bootstrap import score_seed_words_for_profile  # noqa: E402
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from srs_admission_lab_server import (  # noqa: E402
    DEFAULT_TOPIC_OVERLAY_SOURCE_PATHS,
    DEFAULT_ZIPF_BRIDGE_PATH,
    prepare_overlay_source_for_lab,
    resolve_frequency_db,
)
from srs_admission_lab_source_support import (  # noqa: E402
    prepare_lab_frequency_db,
    resolve_kaikki_forward_db,
)
from srs_browsing_admission_research_support import (  # noqa: E402
    BrowsingAdmissionPolicy,
    BrowsingSignal,
    TextDocument,
    as_mapping,
    browsing_boost_value,
    browsing_signal_value,
    build_bridge_indexes,
    build_research_findings,
    clamp01,
    compute_browsing_signals,
    extract_document_signals,
    mapping_rows,
    normalize_document_side,
    public_rows,
    safe_float,
    summarize_browsing_signals,
)


TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_browsing_admission_research_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_browsing_admission_research_en_es_latest.md"
DEFAULT_PAIR = "en-es"
DEFAULT_SET_TOP_N = 10000

DEFAULT_FIXTURES: tuple[tuple[str, str], ...] = (
    (
        "finance_mortgage",
        (
            "The bank approved the mortgage after reviewing income, credit, "
            "interest, property value, and monthly payments. Mortgage rates "
            "changed again before the buyer signed the loan documents."
        ),
    ),
    (
        "medical_treatment",
        (
            "The doctor discussed diagnosis, treatment, symptoms, medicine, "
            "infection, pain, and recovery after the patient visited the clinic."
        ),
    ),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a read-only browsing-based SRS admission research pass for en-es. "
            "The harness consumes local text fixtures, stores no raw text in artifacts, "
            "and does not mutate helper/SRS state."
        )
    )
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--text-file", action="append", type=Path, default=[])
    parser.add_argument(
        "--text-side",
        choices=("source", "target", "mixed"),
        default="source",
        help="Language side for supplied text fixtures; controls source vs target lookup.",
    )
    parser.add_argument("--zipf-bridge-json", type=Path, default=DEFAULT_ZIPF_BRIDGE_PATH)
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument(
        "--overlay-json",
        action="append",
        type=Path,
        default=[],
        help="Topic overlay JSON for lab-style augmented seed candidates. May be repeated.",
    )
    parser.add_argument("--kaikki-forward-db", type=Path)
    parser.add_argument("--set-top-n", type=int, default=DEFAULT_SET_TOP_N)
    parser.add_argument("--preview-count", type=int, default=20)
    parser.add_argument("--proficiency", type=float, default=0.45)
    parser.add_argument(
        "--topic-weight",
        action="append",
        default=[],
        help="Optional explicit profile topic weight in topic=weight form.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        documents=load_documents(args.text_file, side=str(args.text_side)),
        pair=str(args.pair),
        zipf_bridge_payload=load_json(args.zipf_bridge_json),
        zipf_bridge_path=args.zipf_bridge_json,
        frequency_db=args.frequency_db,
        overlay_paths=args.overlay_json or list(DEFAULT_TOPIC_OVERLAY_SOURCE_PATHS),
        kaikki_forward_db=args.kaikki_forward_db,
        set_top_n=max(1, int(args.set_top_n)),
        preview_count=max(1, int(args.preview_count)),
        profile_context=build_profile_context(
            proficiency=args.proficiency,
            topic_weight_args=args.topic_weight,
        ),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.markdown_out.write_text(render_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    documents: Sequence[TextDocument],
    pair: str,
    zipf_bridge_payload: Mapping[str, object],
    zipf_bridge_path: Path | None = None,
    frequency_db: Path | None = None,
    overlay_paths: Sequence[Path] = (),
    kaikki_forward_db: Path | None = None,
    set_top_n: int = DEFAULT_SET_TOP_N,
    preview_count: int = 20,
    profile_context: Mapping[str, object] | None = None,
    policy: BrowsingAdmissionPolicy = BrowsingAdmissionPolicy(),
    generated_at: str | None = None,
) -> dict[str, object]:
    source_index, target_index, bridge_summary = build_bridge_indexes(
        zipf_bridge_payload,
        policy=policy,
    )
    extraction = extract_document_signals(
        documents,
        source_index=source_index,
        target_index=target_index,
        policy=policy,
    )
    browsing_by_lemma = compute_browsing_signals(
        extraction["source_token_counts"],
        extraction["target_token_counts"],
        source_index=source_index,
        target_index=target_index,
        policy=policy,
    )
    with tempfile.TemporaryDirectory(prefix="lexishift-browsing-admission-research-") as tmp:
        tmp_root = Path(tmp)
        seeds, seed_source = build_research_seed_candidates(
            pair=pair,
            frequency_db=frequency_db,
            overlay_paths=overlay_paths,
            zipf_bridge_path=zipf_bridge_path,
            kaikki_forward_db=kaikki_forward_db,
            set_top_n=set_top_n,
            work_dir=tmp_root,
        )
    admission = compare_neutral_and_browsing_admission(
        seeds,
        browsing_by_lemma=browsing_by_lemma,
        profile_context=profile_context or {},
        preview_count=preview_count,
        policy=policy,
    )
    status = "ok" if seeds else "review"
    signal_summary = summarize_browsing_signals(browsing_by_lemma, policy=policy)
    research_findings = build_research_findings(
        extraction_summary=as_mapping(extraction["summary"]),
        signal_summary=signal_summary,
        admission_delta=admission,
    )
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_browsing_admission_research_ready"
            if status == "ok"
            else "srs_browsing_admission_research_needs_review"
        ),
        "generated_at": generated_at or utc_now(),
        "language_pair": pair,
        "policy": policy.to_dict(),
        "profile_context": dict(profile_context or {}),
        "inputs": {
            "zipf_bridge_json": repo_path(zipf_bridge_path),
            "overlay_json": [repo_path(path) for path in overlay_paths],
            "text_documents": [
                {
                    "document_id": document.document_id,
                    "source_path": document.source_path,
                    "text_sha256": hashlib.sha256(document.text.encode("utf-8")).hexdigest(),
                    "raw_text_stored": False,
                    "side": normalize_document_side(document.side),
                }
                for document in documents
            ],
        },
        "privacy": {
            "raw_text_stored": False,
            "url_stored": False,
            "runtime_mutation": False,
            "scope": "local_read_only_research",
        },
        "source_target_bridge": bridge_summary,
        "seed_source": seed_source,
        "extraction": extraction["summary"],
        "browsing_signal_summary": signal_summary,
        "admission_delta": admission,
        "research_findings": research_findings,
        "limitations": [
            "This is a read-only research harness; it does not capture live browser pages.",
            "Topic inference from browsing is intentionally out of scope for P0.",
            "Source-target ambiguity is dampened, not solved semantically.",
            "Visible-text extraction is approximated from supplied plain text fixtures.",
            "Browsing boosts admission scores only in this diagnostic report; scheduling is untouched.",
        ],
    }


def load_documents(paths: Sequence[Path], *, side: str = "source") -> list[TextDocument]:
    normalized_side = normalize_document_side(side)
    if not paths:
        return [
            TextDocument(document_id=document_id, text=text, side=normalized_side)
            for document_id, text in DEFAULT_FIXTURES
        ]
    documents: list[TextDocument] = []
    for path in paths:
        text = path.expanduser().read_text(encoding="utf-8")
        documents.append(
            TextDocument(
                document_id=path.stem,
                text=text,
                source_path=repo_path(path),
                side=normalized_side,
            )
        )
    return documents


def build_profile_context(
    *, proficiency: float, topic_weight_args: Sequence[str]
) -> dict[str, object]:
    topic_weights: dict[str, float] = {}
    for item in topic_weight_args:
        key, separator, raw_value = str(item or "").partition("=")
        if not separator:
            continue
        topic = key.strip()
        weight = safe_float(raw_value)
        if topic and weight is not None:
            topic_weights[topic] = clamp01(weight)
    context: dict[str, object] = {
        "proficiency": {"estimated_value": clamp01(proficiency)},
    }
    if topic_weights:
        context["topic_weights"] = topic_weights
        context["interests"] = sorted(topic_weights)
    return context


def build_research_seed_candidates(
    *,
    pair: str,
    frequency_db: Path | None,
    overlay_paths: Sequence[Path],
    zipf_bridge_path: Path | None,
    kaikki_forward_db: Path | None,
    set_top_n: int,
    work_dir: Path,
) -> tuple[list[object], dict[str, object]]:
    resolved_frequency_db = resolve_frequency_db(pair, frequency_db)
    overlay_source_path = prepare_overlay_source_for_lab(
        work_dir=work_dir,
        pair=pair,
        overlay_source_paths=overlay_paths,
    )
    resolved_kaikki = resolve_kaikki_forward_db(pair, kaikki_forward_db)
    preview_frequency_db, augmentation = prepare_lab_frequency_db(
        base_frequency_db=resolved_frequency_db,
        pair=pair,
        work_dir=work_dir,
        overlay_source_path=overlay_source_path,
        augment_with_zipf_bridge=True,
        zipf_bridge_path=zipf_bridge_path,
        kaikki_forward_db=resolved_kaikki,
    )
    seeds = build_seed_candidates(
        frequency_db=preview_frequency_db,
        config=SeedSelectionConfig(
            language_pair=pair,
            top_n=set_top_n,
            require_jmdict=False,
            source_label="srs-browsing-admission-research",
            sort_by_admission_weight=True,
        ),
    )
    return seeds, {
        "frequency_db": public_artifact_path(resolved_frequency_db, temp_root=work_dir),
        "preview_frequency_db": public_artifact_path(preview_frequency_db, temp_root=work_dir),
        "overlay_source_path": (
            public_artifact_path(overlay_source_path, temp_root=work_dir)
            if overlay_source_path
            else None
        ),
        "kaikki_forward_db": (
            public_artifact_path(resolved_kaikki, temp_root=work_dir) if resolved_kaikki else None
        ),
        "seed_count": len(seeds),
        "augmentation": sanitize_artifact_paths(augmentation, temp_root=work_dir),
    }


def compare_neutral_and_browsing_admission(
    seeds: Sequence[object],
    *,
    browsing_by_lemma: Mapping[str, BrowsingSignal],
    profile_context: Mapping[str, object],
    preview_count: int,
    policy: BrowsingAdmissionPolicy,
) -> dict[str, object]:
    scored_entries, diagnostics = score_seed_words_for_profile(
        seeds,
        profile_context=profile_context,
        preview_limit=preview_count,
    )
    neutral_rows = []
    for index, entry in enumerate(scored_entries, start=1):
        lemma = str(getattr(entry.seed, "lemma", "") or "").strip()
        signal = browsing_by_lemma.get(lemma)
        browsing_signal = browsing_signal_value(signal, policy=policy)
        browsing_boost = browsing_boost_value(browsing_signal, policy=policy)
        neutral_score = float(entry.scored_candidate.breakdown.final_score)
        neutral_rows.append(
            {
                "lemma": lemma,
                "neutral_rank": index,
                "neutral_score": neutral_score,
                "browsing_signal": browsing_signal,
                "browsing_boost": browsing_boost,
                "browsing_score": neutral_score * browsing_boost,
                "readiness_multiplier": float(entry.signal_pack.readiness_multiplier),
                "difficulty_estimate": float(entry.signal_pack.difficulty_estimate),
                "topic_affinity": float(entry.signal_pack.preference_affinity),
                "admission_weight": float(getattr(entry.seed, "admission_weight", 0.0) or 0.0),
                "source_terms": list(signal.source_terms) if signal else [],
                "target_terms": list(signal.target_terms) if signal else [],
                "ambiguous_source_terms": list(signal.ambiguous_source_terms) if signal else [],
            }
        )
    browsing_rows = sorted(
        neutral_rows,
        key=lambda row: (
            -float(row["browsing_score"]),
            int(row["neutral_rank"]),
            str(row["lemma"]),
        ),
    )
    browsing_rank_by_lemma = {
        str(row["lemma"]): index + 1 for index, row in enumerate(browsing_rows)
    }
    for row in neutral_rows:
        row["browsing_rank"] = browsing_rank_by_lemma.get(str(row["lemma"]))
        row["rank_delta"] = int(row["neutral_rank"]) - int(row["browsing_rank"] or 0)
    moved_up = [
        row
        for row in browsing_rows
        if float(row["browsing_signal"]) > 0.0 and int(row["rank_delta"]) > 0
    ]
    boosted_candidates = [row for row in browsing_rows if float(row["browsing_signal"]) > 0.0]
    return {
        "neutral_top": public_rows(neutral_rows[:preview_count]),
        "browsing_top": public_rows(browsing_rows[:preview_count]),
        "moved_up": public_rows(moved_up[:preview_count]),
        "boosted_candidates": public_rows(boosted_candidates[:preview_count]),
        "profile_diagnostics": {
            "selector_version": diagnostics.get("selector_version"),
            "selector_policy_version": diagnostics.get("selector_policy_version"),
            "profile_context": diagnostics.get("profile_context"),
            "selection_weights": diagnostics.get("selection_weights"),
        },
    }


def render_markdown(report: Mapping[str, object]) -> str:
    extraction = as_mapping(report.get("extraction"))
    signal_summary = as_mapping(report.get("browsing_signal_summary"))
    delta = as_mapping(report.get("admission_delta"))
    research_findings = mapping_rows(report.get("research_findings"))
    lines = [
        "# en-es Browsing-Based SRS Admission Research",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Documents: `{extraction.get('document_count', 0)}`",
        f"- Source lookup hits: `{extraction.get('source_lookup_hit_count', 0)}`",
        f"- Target lookup hits: `{extraction.get('target_lookup_hit_count', 0)}`",
        f"- Unmapped tokens: `{extraction.get('unmapped_token_count', 0)}`",
        f"- Boosted lemmas: `{signal_summary.get('boosted_lemma_count', 0)}`",
        f"- Ambiguous boosted lemmas: `{signal_summary.get('ambiguous_boosted_lemma_count', 0)}`",
        "",
        "## Policy",
        "",
    ]
    policy = as_mapping(report.get("policy"))
    for key in (
        "browsing_signal_cap",
        "browsing_alpha",
        "max_browsing_boost",
        "replacement_exposure_weight",
        "ambiguity_confidence_exponent",
        "max_unique_tokens_per_document",
        "max_count_per_token_per_document",
    ):
        lines.append(f"- `{key}`: `{policy.get(key, '')}`")

    lines.extend(
        [
            "",
            "## Top Browsing Signals",
            "",
            "| Lemma | Signal | Boost | Source Terms | Target Terms | Ambiguous Source Terms |",
            "| --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    for row in mapping_rows(signal_summary.get("top_boosted_lemmas"))[:20]:
        lines.append(
            f"| `{row.get('lemma', '')}` | {row.get('browsing_signal', '')} | "
            f"{row.get('browsing_boost', '')} | "
            f"{', '.join(str(item) for item in row.get('source_terms', [])) or '-'} | "
            f"{', '.join(str(item) for item in row.get('target_terms', [])) or '-'} | "
            f"{', '.join(str(item) for item in row.get('ambiguous_source_terms', [])) or '-'} |"
        )

    top_unmapped = mapping_rows(extraction.get("top_unmapped_tokens"))[:20]
    if top_unmapped:
        lines.extend(
            [
                "",
                "## Top Unmapped Tokens",
                "",
                "| Token | Count |",
                "| --- | ---: |",
            ]
        )
        for row in top_unmapped:
            lines.append(f"| `{row.get('token', '')}` | {row.get('count', '')} |")

    lines.extend(
        [
            "",
            "## Browsing-Boosted Top Admission Preview",
            "",
            "| Lemma | Neutral Rank | Browsing Rank | Delta | Signal | Boost | Readiness | Difficulty | Source Terms |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in mapping_rows(delta.get("browsing_top"))[:20]:
        lines.append(
            f"| `{row.get('lemma', '')}` | {row.get('neutral_rank', '')} | "
            f"{row.get('browsing_rank', '')} | {row.get('rank_delta', '')} | "
            f"{row.get('browsing_signal', '')} | {row.get('browsing_boost', '')} | "
            f"{row.get('readiness_multiplier', '')} | {row.get('difficulty_estimate', '')} | "
            f"{', '.join(str(item) for item in row.get('source_terms', [])) or '-'} |"
        )

    if research_findings:
        lines.extend(
            [
                "",
                "## Research Findings",
                "",
                "| Severity | Finding | Detail |",
                "| --- | --- | --- |",
            ]
        )
        for finding in research_findings:
            lines.append(
                f"| `{finding.get('severity', '')}` | `{finding.get('finding', '')}` | "
                f"{finding.get('detail', '')} |"
            )

    lines.extend(["", "## Limitations", ""])
    for limitation in report.get("limitations", []):
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"


def load_json(path: Path | None) -> Mapping[str, object]:
    if path is None:
        return {}
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else {}


def repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(Path(path).resolve(strict=False).relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def public_artifact_path(path: Path | None, *, temp_root: Path | None = None) -> str:
    if path is None:
        return ""
    resolved = Path(path).resolve(strict=False)
    if temp_root is not None:
        try:
            relative = resolved.relative_to(temp_root.resolve(strict=False))
        except ValueError:
            pass
        else:
            return f"<temporary>/{relative.as_posix()}"
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def sanitize_artifact_paths(value: object, *, temp_root: Path | None = None) -> object:
    if isinstance(value, Mapping):
        return {
            key: sanitize_artifact_paths(item, temp_root=temp_root) for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_artifact_paths(item, temp_root=temp_root) for item in value]
    if isinstance(value, str) and ("/" in value or "\\" in value):
        return public_artifact_path(Path(value), temp_root=temp_root)
    return value


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
