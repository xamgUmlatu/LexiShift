#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from srs_topic_family_depth_audit_config import (  # noqa: E402
    DEFAULT_KAIKKI_FORWARD_DB,
    DEFAULT_TAXONOMY,
    DEFAULT_TOP_N,
)
from srs_topic_family_depth_audit_en_es import (  # noqa: E402
    _default_frontiers,
    _float,
    _taxonomy_families,
)
from srs_topic_source_policy_en_es import (  # noqa: E402
    seed_info as source_seed_info,
    trusted_labels_for_seed,
    trusted_source_exclusion,
    trusted_source_exclusions,
    trusted_source_mappings,
)
from srs_topic_signal_inventory_en_es import load_kaikki_topic_signal_index  # noqa: E402


TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_PRECISION_REVIEW = (
    TEST_OUTPUTS_ROOT / "srs_source_topic_precision_review_en_es_spalex_10k_latest.json"
)
DEFAULT_OVERLAY_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "srs_source_topic_overlay_en_es_spalex_10k_latest.json"
)
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_source_topic_overlay_en_es_spalex_10k_latest.md"
DEFAULT_FRONTIER_LABEL = "spalex_10k_research"
SOURCE_READY_STATES = {"source_ready", "partial"}
STRONG_SCORE_FLOOR = 0.75
LIGHT_SCORE_FLOOR = 0.5
STRONG_MEMBERSHIP = 1.0
LIGHT_MEMBERSHIP = 0.65


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a guarded source-backed en-es topic overlay for SRS admission lab/MVP "
            "testing from local taxonomy, Kaikki/Wiktionary topic signals, and the selected "
            "frequency frontier. Read-only; no source downloads or helper state mutation."
        )
    )
    parser.add_argument("--taxonomy-json", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--kaikki-forward-db", type=Path, default=DEFAULT_KAIKKI_FORWARD_DB)
    parser.add_argument("--frontier-label", default=DEFAULT_FRONTIER_LABEL)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--precision-review-json", type=Path, default=DEFAULT_PRECISION_REVIEW)
    parser.add_argument("--overlay-json-out", type=Path, default=DEFAULT_OVERLAY_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    taxonomy_path = _resolve_path(args.taxonomy_json)
    signal_db = _resolve_path(args.kaikki_forward_db)
    frequency_db = _frontier_frequency_db(str(args.frontier_label))
    taxonomy = _load_json(taxonomy_path)
    signal_index = load_kaikki_topic_signal_index(signal_db)
    seeds = build_seed_candidates(
        frequency_db=frequency_db,
        config=SeedSelectionConfig(
            language_pair="en-es",
            top_n=max(1, int(args.top_n)),
            require_jmdict=False,
            source_label=str(args.frontier_label),
            sort_by_admission_weight=True,
        ),
    )
    by_channel = _as_mapping(signal_index.get("_by_channel"))
    seed_infos = [source_seed_info(seed, index) for index, seed in enumerate(seeds, start=1)]
    source_labels_by_lemma = {
        str(seed_info.get("lemma") or ""): trusted_labels_for_seed(
            seed,
            lemma=str(seed_info.get("lemma") or ""),
            by_channel=by_channel,
        )
        for seed, seed_info in zip(seeds, seed_infos, strict=True)
    }
    precision_path = _resolve_path(args.precision_review_json)
    precision_payload = _load_json_if_exists(precision_path)
    overlay = build_topic_overlay(
        taxonomy_payload=taxonomy,
        source_labels_by_lemma=source_labels_by_lemma,
        seed_infos=seed_infos,
        taxonomy_path=taxonomy_path,
        frequency_db=frequency_db,
        signal_db=signal_db,
        precision_review_path=precision_path,
        precision_review_payload=precision_payload,
    )
    overlay_json_out = _resolve_path(args.overlay_json_out)
    markdown_out = _resolve_path(args.markdown_out)
    overlay_json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    overlay_json_out.write_text(
        json.dumps(overlay, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(overlay), encoding="utf-8")
    print(f"Wrote overlay artifact to {overlay_json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    if args.fail_on_review and overlay["status"] != "ok":
        return 1
    return 0


def build_topic_overlay(
    *,
    taxonomy_payload: Mapping[str, object],
    source_labels_by_lemma: Mapping[str, Sequence[str]],
    seed_infos: Sequence[Mapping[str, object]],
    taxonomy_path: Path | None = None,
    frequency_db: Path | None = None,
    signal_db: Path | None = None,
    precision_review_path: Path | None = None,
    precision_review_payload: Mapping[str, object] | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    family_rows = _taxonomy_families(taxonomy_payload)
    source_mappings = trusted_source_mappings(taxonomy_payload)
    source_exclusions = trusted_source_exclusions(taxonomy_payload)
    precision_families = _precision_reviewed_families(precision_review_payload)
    include_families = {
        family_id
        for family_id, family in family_rows.items()
        if str(family.get("axis") or "") == "topic"
        and str(family.get("readiness_state") or "") in SOURCE_READY_STATES
    }
    if precision_families:
        include_families = include_families & precision_families
    rows_by_key: dict[tuple[str, str], dict[str, object]] = {}
    excluded_counts: Counter[str] = Counter()
    for seed_info in seed_infos:
        lemma = str(seed_info.get("lemma") or "").strip()
        if not lemma:
            continue
        matches_by_family: dict[str, dict[str, object]] = {}
        for label_token in source_labels_by_lemma.get(lemma, ()):
            for mapping in source_mappings.get(label_token, ()):
                family_id = str(mapping.get("target_family") or "")
                if family_id not in include_families:
                    continue
                exclusion = trusted_source_exclusion(
                    source_exclusions,
                    lemma=lemma,
                    seed_info=seed_info,
                    source_label=label_token,
                    target_family=family_id,
                )
                if exclusion:
                    excluded_counts[f"{family_id}:{label_token}"] += 1
                    continue
                score = _float(mapping.get("weight")) * _float(mapping.get("confidence"))
                if score < LIGHT_SCORE_FLOOR:
                    continue
                match = matches_by_family.setdefault(
                    family_id,
                    {"score": 0.0, "source_labels": []},
                )
                match["score"] = max(_float(match.get("score")), score)
                source_labels = match.get("source_labels")
                if isinstance(source_labels, list) and label_token not in source_labels:
                    source_labels.append(label_token)
        for family_id, match in matches_by_family.items():
            row = _overlay_row(
                family_id=family_id,
                seed_info=seed_info,
                source_labels=[
                    str(label) for label in match.get("source_labels", []) if str(label).strip()
                ],
                score=_float(match.get("score")),
                precision_review_path=precision_review_path,
            )
            key = (str(row["lemma"]), str(row["topic"]))
            existing = rows_by_key.get(key)
            if existing is None or float(row["membership"]) > float(existing["membership"]):
                rows_by_key[key] = row

    rows = sorted(
        rows_by_key.values(),
        key=lambda row: (str(row["topic"]), -float(row["membership"]), str(row["lemma"])),
    )
    precision_summary = _precision_summary(precision_review_payload)
    counts_by_topic = Counter(str(row["topic"]) for row in rows)
    counts_by_confidence = Counter(str(row["confidence_label"]) for row in rows)
    status = "ok" if rows else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_source_topic_overlay_ready"
            if status == "ok"
            else "srs_source_topic_overlay_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "overlay_id": "srs_source_topic_overlay_en_es_spalex_10k_v1",
        "language_pair": "en-es",
        "inputs": {
            "taxonomy_json": _repo_path(taxonomy_path),
            "frequency_db": _repo_path(frequency_db),
            "kaikki_forward_db": _repo_path(signal_db),
            "precision_review_json": _repo_path(precision_review_path),
        },
        "overlay_policy": {
            "promotion_state": "precision_backed_poc_candidate_not_product_overlay",
            "runtime_policy_change": "none",
            "source_download": "none",
            "source": "taxonomy sense-topic mappings with candidate exclusions",
            "membership_from_score": {
                "strong": f">= {STRONG_SCORE_FLOOR} -> {STRONG_MEMBERSHIP}",
                "light": f">= {LIGHT_SCORE_FLOOR} -> {LIGHT_MEMBERSHIP}",
            },
            "excluded_candidate_count": sum(excluded_counts.values()),
            "excluded_candidate_top_labels": [
                {"label": label, "count": count} for label, count in excluded_counts.most_common(12)
            ],
            "precision_family_filter": sorted(precision_families),
        },
        "precision_review_summary": precision_summary,
        "summary": {
            "row_count": len(rows),
            "topic_count": len(counts_by_topic),
            "counts_by_topic": dict(sorted(counts_by_topic.items())),
            "counts_by_confidence": dict(sorted(counts_by_confidence.items())),
        },
        "rows": rows,
        "limitations": [
            "This overlay is generated from source mappings and sampled precision evidence; it is not a product-shipped overlay yet.",
            "Rows are not individually human-reviewed beyond the sampled precision packet.",
            "Topic coverage depth still follows the guarded source frontier and may be clumpy.",
        ],
    }


def render_markdown(overlay: Mapping[str, object]) -> str:
    summary = _as_mapping(overlay.get("summary"))
    precision = _as_mapping(overlay.get("precision_review_summary"))
    lines = [
        "# en-es Source Topic Overlay",
        "",
        f"- Status: `{overlay.get('status', '')}`",
        f"- Decision: `{overlay.get('decision', '')}`",
        f"- Generated: `{overlay.get('generated_at', '')}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        f"- Topics: `{summary.get('topic_count', 0)}`",
        f"- Precision reviewed rows: `{precision.get('reviewed_count', 0)}`",
        f"- Precision accepted rate: `{_format_percent(precision.get('accepted_rate'))}`",
        "",
        "## Topic Counts",
        "",
        "| Topic | Rows |",
        "| --- | ---: |",
    ]
    for topic, count in _as_mapping(summary.get("counts_by_topic")).items():
        lines.append(f"| `{topic}` | {count} |")
    lines.extend(["", "## Limitations", ""])
    for item in _string_list(overlay.get("limitations")):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _overlay_row(
    *,
    family_id: str,
    seed_info: Mapping[str, object],
    source_labels: Sequence[str],
    score: float,
    precision_review_path: Path | None,
) -> dict[str, object]:
    confidence_label = "strong" if score >= STRONG_SCORE_FLOOR else "light"
    membership = STRONG_MEMBERSHIP if confidence_label == "strong" else LIGHT_MEMBERSHIP
    return {
        "language_pair": "en-es",
        "lemma": str(seed_info.get("lemma") or ""),
        "topic": family_id,
        "review_id": f"srs-source-topic:{family_id}:{seed_info.get('lemma') or ''}",
        "membership": membership,
        "confidence_label": confidence_label,
        "evidence_score": round(score, 6),
        "evidence_band": _difficulty_band(seed_info.get("difficulty")),
        "seed_rank": seed_info.get("seed_rank"),
        "difficulty": seed_info.get("difficulty"),
        "admission_weight": seed_info.get("admission_weight"),
        "pos_bucket": seed_info.get("pos_bucket"),
        "source_channel": "sense_topics",
        "source_label": ",".join(sorted(source_labels)),
        "source_labels": sorted(source_labels),
        "review_state": "sampled_precision_backed_pending_user_approval",
        "provenance": {
            "promotion_state": "precision_backed_poc_candidate_not_product_overlay",
            "precision_review": _repo_path(precision_review_path),
            "source": "taxonomy sense-topic mappings with candidate exclusions",
        },
    }


def _frontier_frequency_db(frontier_label: str) -> Path:
    for label, path, _required in _default_frontiers():
        if label == frontier_label:
            resolved = path.expanduser().resolve(strict=False)
            if resolved.exists():
                return resolved
    raise FileNotFoundError(f"Could not resolve frontier frequency DB: {frontier_label}")


def _precision_summary(payload: Mapping[str, object] | None) -> dict[str, object]:
    if not payload:
        return {"exists": False}
    summary = _as_mapping(payload.get("summary"))
    return {
        "exists": True,
        "reviewed_count": int(summary.get("count") or 0),
        "accepted_count": int(summary.get("accepted_count") or 0),
        "accepted_rate": float(summary.get("accepted_rate") or 0.0),
        "rejected_count": int(summary.get("rejected_count") or 0),
        "rejected_rate": float(summary.get("rejected_rate") or 0.0),
    }


def _precision_reviewed_families(payload: Mapping[str, object] | None) -> set[str]:
    if not payload:
        return set()
    families: set[str] = set()
    for row in _mapping_rows(payload.get("precision_by_family")):
        family = str(row.get("label") or "").strip()
        accepted_count = int(row.get("accepted_count") or 0)
        rejected_rate = float(row.get("rejected_rate") or 0.0)
        if family and accepted_count > 0 and rejected_rate < 0.4:
            families.add(family)
    return families


def _difficulty_band(value: object) -> str:
    difficulty = _float(value)
    if difficulty < 0.2:
        return "0.00-0.20"
    if difficulty < 0.4:
        return "0.20-0.40"
    if difficulty < 0.6:
        return "0.40-0.60"
    if difficulty < 0.8:
        return "0.60-0.80"
    return "0.80-1.00"


def _load_json(path: Path) -> Mapping[str, object]:
    return _as_mapping(json.loads(path.expanduser().read_text(encoding="utf-8")))


def _load_json_if_exists(path: Path) -> Mapping[str, object] | None:
    return _load_json(path) if path.exists() else None


def _resolve_path(path: Path) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(Path(path).resolve(strict=False).relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _format_percent(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
