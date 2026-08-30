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
    aggregate_target_key,
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
DEFAULT_PAIR = "en-ja"
DEFAULT_PROFILE_ID = "default"
DEFAULT_NOW = datetime(2026, 5, 23, tzinfo=timezone.utc)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a synthetic read-only backend simulation for browsing-based "
            "SRS admission aggregate storage and strength presets."
        )
    )
    parser.add_argument(
        "--pair",
        default=DEFAULT_PAIR,
        help="Language pair for the synthetic fixture, for example en-ja or en-es.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--admission-budget", type=int, default=6)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        pair=str(args.pair),
        admission_budget=max(1, int(args.admission_budget)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_report(*, pair: str = DEFAULT_PAIR, admission_budget: int = 6) -> dict[str, object]:
    normalized_pair = str(pair or "").strip() or DEFAULT_PAIR
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
            normalized_pair,
        )
        save_browsing_signal_store(
            BrowsingSignalStore(
                pair=normalized_pair,
                profile_id=DEFAULT_PROFILE_ID,
                items={
                    stale_fixture_lemma(normalized_pair): BrowsingSignalAggregate(
                        target_lemma=stale_fixture_lemma(normalized_pair),
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
            pair=normalized_pair,
            profile_id=DEFAULT_PROFILE_ID,
            captured_at="2026-05-23T00:00:00Z",
            opt_in=True,
            signals=build_signal_payloads(normalized_pair),
            policy=policy,
            now=DEFAULT_NOW,
            resolve_profile_id_fn=lambda helper_paths, *, profile_id, **_kwargs: (
                helper_paths.normalize_profile_id(profile_id)
            ),
        )
        persisted_store = load_browsing_signal_store(helper_store_path)
    ingest_result = _as_mapping(helper_ingest.get("ingest_result"))
    candidates = build_candidates(normalized_pair)
    suppression_store = build_suppression_store(normalized_pair)
    suppressed_lemmas = active_suppressed_lemmas(
        suppression_store,
        pair=normalized_pair,
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
        "language_pair": normalized_pair,
        "profile_id": DEFAULT_PROFILE_ID,
        "fixture": fixture_summary(normalized_pair),
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


def build_signal_payloads(pair: str) -> tuple[dict[str, object], ...]:
    pair_rows = {
        "en-ja": (
            ("料理", BROWSING_SIGNAL_SOURCE, 9.0, 0.90),
            ("野菜", BROWSING_SIGNAL_SOURCE, 7.0, 0.80),
            ("病院", BROWSING_SIGNAL_TARGET, 4.0, None),
            ("診断", BROWSING_SIGNAL_SOURCE, 4.0, 0.75),
            ("銀行", BROWSING_SIGNAL_SOURCE, 2.0, 0.45),
            ("金利", BROWSING_SIGNAL_SOURCE, 2.0, 0.70),
            ("治療", BROWSING_SIGNAL_TARGET, 2.0, None),
            ("犬", BROWSING_SIGNAL_TARGET, 1.0, None),
            ("猫", BROWSING_SIGNAL_TARGET, 1.0, None),
            ("旅行", BROWSING_SIGNAL_TARGET, 1.0, None),
            ("会社", BROWSING_SIGNAL_TARGET, 1.0, None),
            ("切捨て確認", BROWSING_SIGNAL_TARGET, 1.0, None),
        ),
        "en-es": (
            ("hipoteca", BROWSING_SIGNAL_SOURCE, 9.0, 0.90),
            ("préstamo", BROWSING_SIGNAL_SOURCE, 7.0, 0.80),
            ("salud", BROWSING_SIGNAL_TARGET, 4.0, None),
            ("diagnóstico", BROWSING_SIGNAL_SOURCE, 4.0, 0.75),
            ("banco", BROWSING_SIGNAL_SOURCE, 2.0, 0.45),
            ("interés", BROWSING_SIGNAL_SOURCE, 2.0, 0.70),
            ("tratamiento", BROWSING_SIGNAL_TARGET, 2.0, None),
            ("clínica", BROWSING_SIGNAL_TARGET, 1.0, None),
            ("perro", BROWSING_SIGNAL_TARGET, 1.0, None),
            ("gato", BROWSING_SIGNAL_TARGET, 1.0, None),
            ("cocina", BROWSING_SIGNAL_TARGET, 1.0, None),
            ("viaje", BROWSING_SIGNAL_TARGET, 1.0, None),
            ("descartado_por_cap", BROWSING_SIGNAL_TARGET, 1.0, None),
        ),
    }
    return signal_payload_rows(pair_rows.get(pair) or generic_signal_rows(pair))


def generic_signal_rows(pair: str) -> tuple[tuple[str, str, float, float | None], ...]:
    prefix = generic_fixture_prefix(pair)
    return (
        (f"{prefix}_domain_primary", BROWSING_SIGNAL_SOURCE, 9.0, 0.90),
        (f"{prefix}_domain_secondary", BROWSING_SIGNAL_SOURCE, 7.0, 0.80),
        (f"{prefix}_target_primary", BROWSING_SIGNAL_TARGET, 4.0, None),
        (f"{prefix}_domain_tertiary", BROWSING_SIGNAL_SOURCE, 4.0, 0.75),
        (f"{prefix}_ambiguous", BROWSING_SIGNAL_SOURCE, 2.0, 0.45),
        (f"{prefix}_support", BROWSING_SIGNAL_SOURCE, 2.0, 0.70),
        (f"{prefix}_target_secondary", BROWSING_SIGNAL_TARGET, 2.0, None),
        (f"{prefix}_target_tertiary", BROWSING_SIGNAL_TARGET, 1.0, None),
        (f"{prefix}_low_a", BROWSING_SIGNAL_TARGET, 1.0, None),
        (f"{prefix}_low_b", BROWSING_SIGNAL_TARGET, 1.0, None),
        (f"{prefix}_low_c", BROWSING_SIGNAL_TARGET, 1.0, None),
        (f"{prefix}_suppressed", BROWSING_SIGNAL_TARGET, 1.0, None),
        (f"{prefix}_dropped_by_cap", BROWSING_SIGNAL_TARGET, 1.0, None),
    )


def signal_payload_rows(
    rows: tuple[tuple[str, str, float, float | None], ...],
) -> tuple[dict[str, object], ...]:
    payloads: list[dict[str, object]] = []
    for lemma, side, count, confidence in rows:
        payload: dict[str, object] = {
            "target_lemma": lemma,
            "side": side,
            "count": count,
        }
        if confidence is not None:
            payload["source_mapping_confidence"] = confidence
        payloads.append(payload)
    return tuple(payloads)


def build_candidates(pair: str) -> tuple[BrowsingAdmissionCandidate, ...]:
    pair_rows = {
        "en-ja": (
            ("する", 1.00),
            ("いる", 0.96),
            ("言う", 0.90),
            ("犬", 0.84),
            ("猫", 0.82),
            ("会社", 0.80),
            ("料理", 0.64, 0.92, 0.65, 0.90),
            ("野菜", 0.62, 0.88, 0.60, 0.85),
            ("病院", 0.60, 0.86, 0.55, 0.90),
            ("診断", 0.58, 0.74, 0.50, 0.80),
            ("治療", 0.56, 0.72, 0.50, 0.82),
            ("旅行", 0.54),
        ),
        "en-es": (
            ("casa", 1.00),
            ("ser", 0.96),
            ("banco", 0.90),
            ("perro", 0.84),
            ("gato", 0.82),
            ("comida", 0.80),
            ("hipoteca", 0.64, 0.92, 0.65, 0.90),
            ("préstamo", 0.62, 0.88, 0.60, 0.85),
            ("salud", 0.60, 0.86, 0.55, 0.90),
            ("diagnóstico", 0.58, 0.74, 0.50, 0.80),
            ("tratamiento", 0.56, 0.72, 0.50, 0.82),
            ("viaje", 0.54),
        ),
    }
    if pair in pair_rows:
        return candidate_rows(pair_rows[pair])
    prefix = generic_fixture_prefix(pair)
    return candidate_rows(
        (
            ("casa", 1.00),
            ("ser", 0.96),
            (f"{prefix}_general_1", 0.90),
            (f"{prefix}_low_a", 0.84),
            (f"{prefix}_low_b", 0.82),
            (f"{prefix}_low_c", 0.80),
            (f"{prefix}_domain_primary", 0.64, 0.92, 0.65, 0.90),
            (f"{prefix}_domain_secondary", 0.62, 0.88, 0.60, 0.85),
            (f"{prefix}_target_primary", 0.60, 0.86, 0.55, 0.90),
            (f"{prefix}_domain_tertiary", 0.58, 0.74, 0.50, 0.80),
            (f"{prefix}_target_secondary", 0.56, 0.72, 0.50, 0.82),
            (f"{prefix}_suppressed", 0.54),
        )
    )


def candidate_rows(rows: tuple[tuple[object, ...], ...]) -> tuple[BrowsingAdmissionCandidate, ...]:
    candidates = []
    for row in rows:
        lemma, neutral_score, *optional = row
        candidates.append(
            BrowsingAdmissionCandidate(
                lemma=str(lemma),
                neutral_score=float(neutral_score),
                readiness_multiplier=float(optional[0]) if len(optional) >= 1 else 1.0,
                explicit_preference_fit=float(optional[1]) if len(optional) >= 2 else 0.0,
                source_confidence=float(optional[2]) if len(optional) >= 3 else 1.0,
            )
        )
    return tuple(candidates)


def build_suppression_store(pair: str) -> SrsAdmissionSuppressionStore:
    policy = SrsAdmissionSuppressionPolicy(suspended_cooldown_days=365)
    store = SrsAdmissionSuppressionStore(profile_id=DEFAULT_PROFILE_ID)
    entry = create_admission_suppression(
        pair=pair,
        lemma=suppressed_fixture_lemma(pair),
        reason=SUPPRESSION_REASON_SUSPENDED,
        policy=policy,
        now=DEFAULT_NOW,
        note="Synthetic cooldown fixture; not runtime user data.",
    )
    return upsert_admission_suppression(store, entry, now=DEFAULT_NOW)


def suppressed_fixture_lemma(pair: str) -> str:
    if pair == "en-ja":
        return "旅行"
    if pair == "en-es":
        return "viaje"
    return f"{generic_fixture_prefix(pair)}_suppressed"


def stale_fixture_lemma(pair: str) -> str:
    if pair == "en-ja":
        return "古い信号"
    if pair == "en-es":
        return "arcaico"
    return f"{generic_fixture_prefix(pair)}_stale"


def generic_fixture_prefix(pair: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in pair.strip().lower()) or "pair"


def fixture_summary(pair: str) -> dict[str, object]:
    return {
        "pair": pair,
        "fixture_family": pair if pair in {"en-ja", "en-es"} else "generic",
        "signal_lemmas": [
            str(row.get("target_lemma") or "") for row in build_signal_payloads(pair)
        ],
        "candidate_lemmas": [candidate.lemma for candidate in build_candidates(pair)],
        "suppressed_lemma": suppressed_fixture_lemma(pair),
    }


def summarize_store(
    store: BrowsingSignalStore,
    *,
    policy: BrowsingSignalIngestPolicy,
) -> dict[str, object]:
    rows = []
    for aggregate in store.items.values():
        rows.append(
            {
                "target_key": aggregate_target_key(aggregate),
                "target_lemma": aggregate.target_lemma,
                "target_reading": aggregate.target_reading,
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
                "reading_confidence": round(aggregate.reading_confidence, 4),
                "observation_sources": list(aggregate.observation_sources),
                "raw_browsing": round(browsing_raw_value(aggregate, policy=policy), 4),
                "browsing_signal": round(browsing_signal_value(aggregate, policy=policy), 4),
                "last_seen_at": aggregate.last_seen_at,
            }
        )
    rows.sort(key=lambda row: (-float(row["browsing_signal"]), str(row["target_key"])))
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
    if off.get("selected_lemmas") == off.get("neutral_selected_lemmas"):
        findings.append(
            {
                "severity": "info",
                "finding": "off_strength_matches_neutral_baseline",
                "detail": "No-history/off-strength admission preserves neutral ordering.",
            }
        )
    if int(strong.get("suppressed_count", 0)) > 0 and not _selected_suppressed(strong):
        findings.append(
            {
                "severity": "info",
                "finding": "suppressed_lemmas_not_selected",
                "detail": "Browsing signals do not override active admission suppression.",
            }
        )
    return findings


def _selected_suppressed(result: Mapping[str, object]) -> bool:
    for row in _rows(result.get("rows")):
        if row.get("suppressed_reason") and row.get("selected"):
            return True
    return False


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
            "| Target Key | Lemma | Signal | Raw | Source | Target | Source Conf. | Reading Conf. | Sources |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in _rows(aggregate.get("items")):
        sources = ", ".join(str(item) for item in row.get("observation_sources", []) or [])
        lines.append(
            f"| `{row.get('target_key', '')}` | `{row.get('target_lemma', '')}` | "
            f"{row.get('browsing_signal', '')} | "
            f"{row.get('raw_browsing', '')} | {row.get('source_hit_count', '')} | "
            f"{row.get('target_hit_count', '')} | "
            f"{row.get('source_mapping_confidence', '')} | "
            f"{row.get('reading_confidence', '')} | {sources} |"
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
