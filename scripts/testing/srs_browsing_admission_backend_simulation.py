#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.srs.browsing_admission import (  # noqa: E402
    BROWSING_SIGNAL_SOURCE,
    BROWSING_SIGNAL_TARGET,
    BrowsingAdmissionCandidate,
    BrowsingSignalAggregate,
    BrowsingSignalIngestPolicy,
    BrowsingSignalStore,
    browsing_raw_value,
    browsing_signal_value,
    load_browsing_signal_store,
    save_browsing_signal_store,
    simulate_browsing_admission_presets,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.use_cases.browsing_admission import (  # noqa: E402
    ingest_browsing_admission_signals,
)
from lexishift_core.srs.admission_suppression import (  # noqa: E402
    SUPPRESSION_REASON_SUSPENDED,
    SrsAdmissionSuppressionPolicy,
    SrsAdmissionSuppressionStore,
    active_suppressed_lemmas,
    create_admission_suppression,
    upsert_admission_suppression,
)

TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_browsing_admission_backend_simulation_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_browsing_admission_backend_simulation_latest.md"
DEFAULT_PAIR = "en-es"
DEFAULT_PROFILE_ID = "default"
DEFAULT_NOW = datetime(2026, 5, 23, tzinfo=timezone.utc)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a synthetic read-only backend simulation for browsing-based "
            "SRS admission aggregate storage and strength presets."
        )
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--admission-budget", type=int, default=6)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(admission_budget=max(1, int(args.admission_budget)))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_report(*, admission_budget: int = 6) -> dict[str, object]:
    policy = BrowsingSignalIngestPolicy(
        max_signals_per_packet=12,
        max_count_per_signal=5.0,
        max_items_per_store=8,
        prune_signal_below=0.02,
        half_life_days=14.0,
    )
    with tempfile.TemporaryDirectory() as tmp:
        paths = build_helper_paths(Path(tmp))
        helper_store_path = paths.srs_browsing_signal_store_path_for(
            DEFAULT_PROFILE_ID,
            DEFAULT_PAIR,
        )
        save_browsing_signal_store(
            BrowsingSignalStore(
                pair=DEFAULT_PAIR,
                profile_id=DEFAULT_PROFILE_ID,
                items={
                    "arcaico": BrowsingSignalAggregate(
                        target_lemma="arcaico",
                        source_hit_count=0.04,
                        last_seen_at="2026-01-01T00:00:00Z",
                        decayed_at="2026-01-01T00:00:00Z",
                    )
                },
                updated_at="2026-01-01T00:00:00Z",
                policy_version=policy.version,
            ),
            helper_store_path,
        )
        helper_ingest = ingest_browsing_admission_signals(
            paths,
            pair=DEFAULT_PAIR,
            profile_id=DEFAULT_PROFILE_ID,
            captured_at="2026-05-23T00:00:00Z",
            opt_in=True,
            signals=build_signal_payloads(),
            policy=policy,
            now=DEFAULT_NOW,
            resolve_profile_id_fn=lambda helper_paths, *, profile_id, **_kwargs: (
                helper_paths.normalize_profile_id(profile_id)
            ),
        )
        persisted_store = load_browsing_signal_store(helper_store_path)
    ingest_result = _as_mapping(helper_ingest.get("ingest_result"))
    candidates = build_candidates()
    suppression_store = build_suppression_store()
    suppressed_lemmas = active_suppressed_lemmas(
        suppression_store,
        pair=DEFAULT_PAIR,
        now=DEFAULT_NOW,
    )
    simulations = simulate_browsing_admission_presets(
        candidates,
        store=persisted_store,
        admission_budget=admission_budget,
        policy=policy,
        suppressed_lemmas=suppressed_lemmas,
    )
    return {
        "schema_version": 1,
        "status": "ok",
        "decision": "srs_browsing_admission_backend_simulation_ready",
        "generated_at": "2026-05-23T00:00:00Z",
        "language_pair": DEFAULT_PAIR,
        "profile_id": DEFAULT_PROFILE_ID,
        "privacy": {
            "raw_text_stored": False,
            "url_stored": False,
            "runtime_srs_mutation": False,
            "synthetic_fixture_only": True,
            "helper_persisted_fixture": True,
            "opt_in_required": True,
        },
        "policy": {
            "version": policy.version,
            "max_signals_per_packet": policy.max_signals_per_packet,
            "max_count_per_signal": policy.max_count_per_signal,
            "max_items_per_store": policy.max_items_per_store,
            "prune_signal_below": policy.prune_signal_below,
            "half_life_days": policy.half_life_days,
            "browsing_signal_cap": policy.browsing_signal_cap,
            "replacement_exposure_weight": policy.replacement_exposure_weight,
        },
        "helper_ingest": {
            "status": helper_ingest.get("status"),
            "runtime_srs_mutation": helper_ingest.get("runtime_srs_mutation"),
            "private_payload_fields_ignored": _as_mapping(helper_ingest.get("privacy")).get(
                "private_payload_fields_ignored",
                0,
            ),
        },
        "ingest_result": ingest_result,
        "suppression": {
            "active_suppressed_lemmas": suppressed_lemmas,
            "entry_count": len(suppression_store.entries),
            "runtime_srs_mutation": False,
        },
        "aggregate_store": summarize_store(persisted_store, policy=policy),
        "admission_budget": admission_budget,
        "simulations": {name: result.to_dict() for name, result in simulations.items()},
        "findings": build_findings(
            ingest_result=ingest_result,
            simulations={name: result.to_dict() for name, result in simulations.items()},
        ),
    }


def build_signal_payloads() -> tuple[dict[str, object], ...]:
    return (
        {
            "target_lemma": "hipoteca",
            "side": BROWSING_SIGNAL_SOURCE,
            "count": 9.0,
            "source_mapping_confidence": 0.90,
        },
        {
            "target_lemma": "préstamo",
            "side": BROWSING_SIGNAL_SOURCE,
            "count": 7.0,
            "source_mapping_confidence": 0.80,
        },
        {
            "target_lemma": "salud",
            "side": BROWSING_SIGNAL_TARGET,
            "count": 4.0,
        },
        {
            "target_lemma": "diagnóstico",
            "side": BROWSING_SIGNAL_SOURCE,
            "count": 4.0,
            "source_mapping_confidence": 0.75,
        },
        {
            "target_lemma": "banco",
            "side": BROWSING_SIGNAL_SOURCE,
            "count": 2.0,
            "source_mapping_confidence": 0.45,
        },
        {
            "target_lemma": "interés",
            "side": BROWSING_SIGNAL_SOURCE,
            "count": 2.0,
            "source_mapping_confidence": 0.70,
        },
        {
            "target_lemma": "tratamiento",
            "side": BROWSING_SIGNAL_TARGET,
            "count": 2.0,
        },
        {
            "target_lemma": "clínica",
            "side": BROWSING_SIGNAL_TARGET,
            "count": 1.0,
        },
        {
            "target_lemma": "perro",
            "side": BROWSING_SIGNAL_TARGET,
            "count": 1.0,
        },
        {
            "target_lemma": "gato",
            "side": BROWSING_SIGNAL_TARGET,
            "count": 1.0,
        },
        {
            "target_lemma": "cocina",
            "side": BROWSING_SIGNAL_TARGET,
            "count": 1.0,
        },
        {
            "target_lemma": "viaje",
            "side": BROWSING_SIGNAL_TARGET,
            "count": 1.0,
        },
        {
            "target_lemma": "descartado_por_cap",
            "side": BROWSING_SIGNAL_TARGET,
            "count": 1.0,
        },
    )


def build_candidates() -> tuple[BrowsingAdmissionCandidate, ...]:
    return (
        BrowsingAdmissionCandidate(lemma="casa", neutral_score=1.00),
        BrowsingAdmissionCandidate(lemma="ser", neutral_score=0.96),
        BrowsingAdmissionCandidate(lemma="banco", neutral_score=0.90),
        BrowsingAdmissionCandidate(lemma="perro", neutral_score=0.84),
        BrowsingAdmissionCandidate(lemma="gato", neutral_score=0.82),
        BrowsingAdmissionCandidate(lemma="comida", neutral_score=0.80),
        BrowsingAdmissionCandidate(
            lemma="hipoteca",
            neutral_score=0.64,
            readiness_multiplier=0.92,
            explicit_preference_fit=0.65,
            source_confidence=0.90,
        ),
        BrowsingAdmissionCandidate(
            lemma="préstamo",
            neutral_score=0.62,
            readiness_multiplier=0.88,
            explicit_preference_fit=0.60,
            source_confidence=0.85,
        ),
        BrowsingAdmissionCandidate(
            lemma="salud",
            neutral_score=0.60,
            readiness_multiplier=0.86,
            explicit_preference_fit=0.55,
            source_confidence=0.90,
        ),
        BrowsingAdmissionCandidate(
            lemma="diagnóstico",
            neutral_score=0.58,
            readiness_multiplier=0.74,
            explicit_preference_fit=0.50,
            source_confidence=0.80,
        ),
        BrowsingAdmissionCandidate(
            lemma="tratamiento",
            neutral_score=0.56,
            readiness_multiplier=0.72,
            explicit_preference_fit=0.50,
            source_confidence=0.82,
        ),
        BrowsingAdmissionCandidate(lemma="viaje", neutral_score=0.54),
    )


def build_suppression_store() -> SrsAdmissionSuppressionStore:
    policy = SrsAdmissionSuppressionPolicy(suspended_cooldown_days=365)
    store = SrsAdmissionSuppressionStore(profile_id=DEFAULT_PROFILE_ID)
    entry = create_admission_suppression(
        pair=DEFAULT_PAIR,
        lemma="viaje",
        reason=SUPPRESSION_REASON_SUSPENDED,
        policy=policy,
        now=DEFAULT_NOW,
        note="Synthetic cooldown fixture; not runtime user data.",
    )
    return upsert_admission_suppression(store, entry, now=DEFAULT_NOW)


def summarize_store(
    store: BrowsingSignalStore,
    *,
    policy: BrowsingSignalIngestPolicy,
) -> dict[str, object]:
    rows = []
    for aggregate in store.items.values():
        rows.append(
            {
                "target_lemma": aggregate.target_lemma,
                "source_hit_count": round(aggregate.source_hit_count, 4),
                "target_hit_count": round(aggregate.target_hit_count, 4),
                "replacement_exposure_count": round(
                    aggregate.replacement_exposure_count,
                    4,
                ),
                "source_mapping_confidence": round(
                    aggregate.source_mapping_confidence,
                    4,
                ),
                "raw_browsing": round(browsing_raw_value(aggregate, policy=policy), 4),
                "browsing_signal": round(browsing_signal_value(aggregate, policy=policy), 4),
                "last_seen_at": aggregate.last_seen_at,
            }
        )
    rows.sort(key=lambda row: (-float(row["browsing_signal"]), str(row["target_lemma"])))
    return {
        "pair": store.pair,
        "profile_id": store.profile_id,
        "updated_at": store.updated_at,
        "item_count": len(rows),
        "items": rows,
    }


def build_findings(
    *,
    ingest_result: Mapping[str, object],
    simulations: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if int(ingest_result.get("dropped_signal_count", 0)) > 0:
        findings.append(
            {
                "severity": "info",
                "finding": "packet_cap_applied",
                "detail": "Signals beyond the per-packet cap were dropped.",
            }
        )
    if int(ingest_result.get("capped_signal_count", 0)) > 0:
        findings.append(
            {
                "severity": "info",
                "finding": "per_signal_count_cap_applied",
                "detail": "Large repeated counts were capped before aggregation.",
            }
        )
    off = simulations.get("off", {})
    balanced = simulations.get("balanced", {})
    strong = simulations.get("strong", {})
    if (
        float(off.get("browsing_lane_share", 0.0))
        <= float(balanced.get("browsing_lane_share", 0.0))
        <= float(strong.get("browsing_lane_share", 0.0))
    ):
        findings.append(
            {
                "severity": "info",
                "finding": "preset_browsing_share_is_monotonic",
                "detail": "Off, Balanced, and Strong increase browsing-lane share as intended.",
            }
        )
    return findings


def render_markdown(report: Mapping[str, object]) -> str:
    aggregate = _as_mapping(report.get("aggregate_store"))
    simulations = _as_mapping(report.get("simulations"))
    lines = [
        "# SRS Browsing Admission Backend Simulation",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Pair: `{report.get('language_pair', '')}`",
        f"- Aggregate items retained: `{aggregate.get('item_count', 0)}`",
        f"- Admission budget: `{report.get('admission_budget', 0)}`",
        "- Runtime SRS mutation: `False`",
        "- Raw text stored: `False`",
        "- URL stored: `False`",
        "- Helper-persisted fixture: `True`",
        "- Opt-in required: `True`",
        "",
        "## Ingest",
        "",
    ]
    helper_ingest = _as_mapping(report.get("helper_ingest"))
    lines.append(f"- `helper_status`: `{helper_ingest.get('status', '')}`")
    lines.append(
        f"- `private_payload_fields_ignored`: "
        f"`{helper_ingest.get('private_payload_fields_ignored', 0)}`"
    )
    ingest = _as_mapping(report.get("ingest_result"))
    for key in (
        "input_signal_count",
        "accepted_signal_count",
        "dropped_signal_count",
        "capped_signal_count",
        "pruned_item_count",
        "retained_item_count",
    ):
        lines.append(f"- `{key}`: `{ingest.get(key, '')}`")

    suppression = _as_mapping(report.get("suppression"))
    suppressed_lemmas = _as_mapping(suppression.get("active_suppressed_lemmas"))
    lines.extend(["", "## Suppression Guard", ""])
    lines.append(f"- Active suppressed lemmas: `{len(suppressed_lemmas)}`")
    lines.append(f"- Runtime SRS mutation: `{suppression.get('runtime_srs_mutation', False)}`")
    if suppressed_lemmas:
        lines.append(
            "- Suppressed fixture rows: "
            + ", ".join(f"`{lemma}` ({reason})" for lemma, reason in suppressed_lemmas.items())
        )

    lines.extend(
        [
            "",
            "## Aggregate Store Preview",
            "",
            "| Lemma | Signal | Raw | Source | Target | Confidence |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _rows(aggregate.get("items")):
        lines.append(
            f"| `{row.get('target_lemma', '')}` | {row.get('browsing_signal', '')} | "
            f"{row.get('raw_browsing', '')} | {row.get('source_hit_count', '')} | "
            f"{row.get('target_hit_count', '')} | "
            f"{row.get('source_mapping_confidence', '')} |"
        )

    lines.extend(
        [
            "",
            "## Strength Simulation",
            "",
            "| Strength | Browsing Budget | Browsing Lane Share | Relevant Share | Driven Share | Selected |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for name in ("off", "balanced", "strong"):
        result = _as_mapping(simulations.get(name))
        lines.append(
            f"| `{name}` | {result.get('browsing_budget', '')} | "
            f"{result.get('browsing_lane_share', '')} | "
            f"{result.get('browsing_relevant_share', '')} | "
            f"{result.get('browsing_driven_share', '')} | "
            f"{', '.join(str(item) for item in result.get('selected_lemmas', []))} |"
        )

    lines.extend(
        [
            "",
            "## Probability Preview",
            "",
            "The deterministic column is exact for this read-only simulation. The approximate column estimates inclusion probability if the lane uses weighted sampling without replacement.",
            "",
            "| Strength | Lemma | Selected | Suppressed | Deterministic P | Approx P | Browsing P | General P |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for name in ("off", "balanced", "strong"):
        result = _as_mapping(simulations.get(name))
        for row in _rows(result.get("rows"))[:8]:
            lines.append(
                f"| `{name}` | `{row.get('lemma', '')}` | "
                f"{row.get('selected', False)} | "
                f"{row.get('suppressed_reason', '') or '-'} | "
                f"{row.get('deterministic_selection_probability', '')} | "
                f"{row.get('approximate_selection_probability', '')} | "
                f"{row.get('browsing_lane_probability', '')} | "
                f"{row.get('general_lane_probability', '')} |"
            )

    lines.extend(
        [
            "",
            "## Findings",
            "",
            "| Severity | Finding | Detail |",
            "| --- | --- | --- |",
        ]
    )
    for finding in _rows(report.get("findings")):
        lines.append(
            f"| `{finding.get('severity', '')}` | `{finding.get('finding', '')}` | "
            f"{finding.get('detail', '')} |"
        )
    return "\n".join(lines) + "\n"


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
