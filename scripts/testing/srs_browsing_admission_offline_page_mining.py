#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Mapping
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
HELPER_ROOT = PROJECT_ROOT / "scripts" / "helper"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))
if str(HELPER_ROOT) not in sys.path:
    sys.path.insert(0, str(HELPER_ROOT))

from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs.browsing_admission import (  # noqa: E402
    BrowsingAdmissionCandidate,
    BrowsingSignalIngestPolicy,
    browsing_context_count,
    browsing_evidence_value,
    browsing_signal_value,
    load_browsing_signal_store,
    simulate_browsing_admission_presets,
)
from srs_browsing_admission_offline_page_mining_html import SavedPageTextExtractor  # noqa: E402
from srs_browsing_admission_offline_page_mining_render import render_markdown  # noqa: E402


DEFAULT_CONFIG = (
    PROJECT_ROOT / "docs/test_inputs/srs_browsing_admission_offline_page_mining_cases.json"
)
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs/test_outputs"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_browsing_admission_offline_page_mining_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_browsing_admission_offline_page_mining_latest.md"
EXTENSION_SIGNAL_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_browsing_admission_signals.js"
)
EXTENSION_SOURCE_MINING_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_browsing_source_mining.js"
)
EXTENSION_PAGE_MINING_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_browsing_page_mining.js"
)
NATIVE_HOST_SCRIPT = PROJECT_ROOT / "scripts/helper/lexishift_native_host.py"
FIXED_CAPTURED_AT = datetime(2026, 5, 23, tzinfo=timezone.utc)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run saved/local page mining fixtures through the extension JS packet builder "
            "and isolated native-host browsing aggregate ingest."
        )
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(config_path=args.config)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"status: {report['status']}")
    print(f"json_out: {args.json_out}")
    print(f"markdown_out: {args.markdown_out}")
    return 0 if report["status"] == "PASS" else 1


def build_report(
    *,
    config_path: Path = DEFAULT_CONFIG,
    generated_at: str = "2026-07-03T00:00:00Z",
) -> dict[str, object]:
    resolved_config = _resolve_project_path(config_path)
    config = _load_json(resolved_config)
    prepared_cases = prepare_cases(config, config_path=resolved_config)
    extension_cases = build_extension_payloads(prepared_cases)
    case_reports = [
        build_case_report(case, extension_case)
        for case, extension_case in zip(prepared_cases, extension_cases)
    ]
    return {
        "schema_version": 1,
        "status": "PASS"
        if case_reports and all(case["status"] == "PASS" for case in case_reports)
        else "FAIL",
        "generated_at": generated_at,
        "config_path": str(resolved_config.relative_to(PROJECT_ROOT)),
        "scope": "offline_saved_page_extension_js_native_ingest",
        "live_user_data_touched": False,
        "case_count": len(case_reports),
        "cases": case_reports,
    }


def prepare_cases(config: Mapping[str, object], *, config_path: Path) -> list[dict[str, object]]:
    raw_cases = config.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError(f"{config_path} must contain a cases list.")
    prepared: list[dict[str, object]] = []
    for raw_case in raw_cases:
        if not isinstance(raw_case, Mapping):
            continue
        case = dict(raw_case)
        documents = []
        for raw_document in _list_of_mappings(case.get("documents")):
            documents.append(prepare_document(raw_document))
        case["documents"] = documents
        prepared.append(case)
    return prepared


def prepare_document(raw_document: Mapping[str, object]) -> dict[str, object]:
    path = _resolve_project_path(raw_document.get("path"))
    encoding = str(raw_document.get("encoding") or "utf-8")
    content = path.read_text(encoding=encoding)
    extractor = SavedPageTextExtractor()
    extractor.feed(content)
    extractor.close()
    return {
        "document_id": str(raw_document.get("document_id") or path.stem),
        "side": str(raw_document.get("side") or "").strip().lower(),
        "format": str(raw_document.get("format") or path.suffix.lstrip(".") or "text"),
        "path": str(path.relative_to(PROJECT_ROOT)),
        "sha256": hashlib.sha256(content.encode(encoding)).hexdigest(),
        "visible_text": extractor.visible_text,
        "visible_text_char_count": len(extractor.visible_text),
        "ruby_pairs": extractor.ruby_pairs,
        "ruby_pair_count": len(extractor.ruby_pairs),
        "page_context_key": str(
            raw_document.get("page_context_key") or raw_document.get("document_id")
        ),
    }


def build_extension_payloads(cases: list[dict[str, object]]) -> list[dict[str, object]]:
    node_input = {"cases": cases}
    script = f"""
const fs = require("node:fs");
const vm = require("node:vm");

const signalModulePath = {json.dumps(str(EXTENSION_SIGNAL_JS))};
const sourceMiningModulePath = {json.dumps(str(EXTENSION_SOURCE_MINING_JS))};
const miningModulePath = {json.dumps(str(EXTENSION_PAGE_MINING_JS))};
const input = JSON.parse(fs.readFileSync(0, "utf8"));
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(signalModulePath, "utf8"), context, {{ filename: signalModulePath }});
vm.runInContext(fs.readFileSync(sourceMiningModulePath, "utf8"), context, {{ filename: sourceMiningModulePath }});
vm.runInContext(fs.readFileSync(miningModulePath, "utf8"), context, {{ filename: miningModulePath }});

const signals = context.LexiShift.srsBrowsingAdmissionSignals;
const pageMining = context.LexiShift.srsBrowsingPageMining;
const defaultNowIso = {json.dumps(FIXED_CAPTURED_AT.isoformat().replace("+00:00", "Z"))};

function mineCase(testCase) {{
  const pair = String(testCase.pair || "").trim().toLowerCase();
  const profileId = String(testCase.profile_id || "default").trim() || "default";
  const settings = {{
    srsProfileId: profileId,
    srsPair: pair,
    srsBrowsingAdmissionSignalsEnabled: true
  }};
  const pending = new Map();
  const documentResults = [];
  let accepted = 0;
  let sourceSignalCount = 0;
  let targetSignalCount = 0;

  for (const document of Array.isArray(testCase.documents) ? testCase.documents : []) {{
    const options = {{
      nowMs: () => 0,
      maxCountPerSignal: 5,
      maxSignalsPerPacket: Number(testCase.max_signals_per_packet || 50),
      maxCountPerTarget: Number(testCase.max_count_per_target || 5),
      maxSourceCountPerTarget: Number(testCase.max_source_count_per_target || 3),
      pageContextKey: document.page_context_key
    }};
    let rows = [];
    if (document.side === "source") {{
      rows = pageMining.buildSourceMappingSignals(
        document.visible_text || "",
        testCase.active_rules || [],
        settings,
        options
      );
      sourceSignalCount += rows.length;
    }} else if (document.side === "target") {{
      rows = pageMining.buildRubyTargetSignals(document.ruby_pairs || [], settings, options);
      targetSignalCount += rows.length;
    }}
    accepted += signals.addExposureBatchToPending(pending, rows, settings, options);
    documentResults.push({{
      document_id: document.document_id,
      side: document.side,
      sha256: document.sha256,
      visible_text_char_count: document.visible_text_char_count,
      ruby_pair_count: document.ruby_pair_count,
      signal_count: rows.length,
      accepted_count: rows.reduce((sum, row) => sum + Number(row.count || 0), 0),
      signals: rows.map((row) => ({{
        target_key: row.target_key || row.lemma,
        side: row.side,
        observation_source: row.observation_source,
        count: row.count,
        source_mapping_confidence: row.source_mapping_confidence
      }}))
    }});
  }}

  const payloads = signals.buildPacketPayloads(pending, {{
    nowIso: () => String(testCase.captured_at || defaultNowIso),
    maxSignalsPerPacket: Number(testCase.max_signals_per_packet || 50)
  }});
  return {{
    name: testCase.name,
    pair,
    profile_id: profileId,
    accepted,
    source_signal_count: sourceSignalCount,
    target_signal_count: targetSignalCount,
    signal_count: payloads.reduce((sum, payload) => sum + payload.signals.length, 0),
    packet_count: payloads.length,
    documents: documentResults,
    payloads
  }};
}}

console.log(JSON.stringify((input.cases || []).map(mineCase)));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        input=json.dumps(node_input, ensure_ascii=False),
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Offline page-mining extension packet build failed.\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    parsed = json.loads(completed.stdout)
    if not isinstance(parsed, list):
        raise RuntimeError("Offline page-mining extension builder did not return a list.")
    return [dict(item) for item in parsed if isinstance(item, Mapping)]


def build_case_report(
    case: Mapping[str, object],
    extension_case: Mapping[str, object],
) -> dict[str, object]:
    policy = BrowsingSignalIngestPolicy()
    native_host = load_native_host_module()
    pair = str(case.get("pair") or "").strip().lower()
    profile_id = str(case.get("profile_id") or "default").strip() or "default"
    payloads = _list_of_mappings(extension_case.get("payloads"))

    with tempfile.TemporaryDirectory() as tmp:
        paths = build_helper_paths(Path(tmp))
        with patch.object(native_host, "build_helper_paths", return_value=paths):
            ingest_responses = [
                native_host._handle_request("srs_browsing_signal_ingest", payload)
                for payload in payloads
            ]
            persisted = load_browsing_signal_store(
                paths.srs_browsing_signal_store_path_for(
                    paths.normalize_profile_id(profile_id),
                    pair,
                )
            )
            srs_store_exists = paths.srs_store_path_for(profile_id).exists()

    extension_summary = summarize_extension_case(extension_case)
    store_summary = summarize_store(persisted, policy=policy)
    admission_simulations = build_admission_simulations(case, persisted, policy=policy)
    checks = build_case_checks(
        case=case,
        extension_case=extension_case,
        extension_summary=extension_summary,
        ingest_responses=ingest_responses,
        store_summary=store_summary,
        admission_simulations=admission_simulations,
        srs_store_exists=srs_store_exists,
    )
    return {
        "name": case.get("name"),
        "status": "PASS" if all(check["status"] == "pass" for check in checks) else "FAIL",
        "pair": pair,
        "profile_id": profile_id,
        "documents": summarize_documents(_list_of_mappings(case.get("documents"))),
        "extension_payload": extension_summary,
        "native_host_ingest": summarize_native_ingest(ingest_responses),
        "aggregate_store": store_summary,
        "admission_simulations": admission_simulations,
        "checks": checks,
    }


def build_admission_simulations(
    case: Mapping[str, object],
    store,
    *,
    policy: BrowsingSignalIngestPolicy,
) -> dict[str, object]:
    admission = _as_mapping(case.get("admission"))
    candidates = tuple(
        candidate
        for row in _list_of_mappings(admission.get("candidates"))
        if (candidate := _candidate_from_mapping(row)) is not None
    )
    if not candidates:
        return {}
    budget = max(1, int(float(admission.get("admission_budget") or 4)))
    return {
        name: result.to_dict()
        for name, result in simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=budget,
            policy=policy,
            now=FIXED_CAPTURED_AT,
        ).items()
    }


def _candidate_from_mapping(row: Mapping[str, object]) -> BrowsingAdmissionCandidate | None:
    lemma = str(row.get("lemma") or "").strip()
    if not lemma:
        return None
    return BrowsingAdmissionCandidate(
        lemma=lemma,
        target_key=str(row.get("target_key") or "").strip(),
        target_reading=str(row.get("target_reading") or "").strip(),
        neutral_score=float(row.get("neutral_score") or 0),
        readiness_multiplier=float(row.get("readiness_multiplier") or 1),
        explicit_preference_fit=float(row.get("explicit_preference_fit") or 0),
        source_confidence=float(row.get("source_confidence") or 1),
        admission_suitability=float(row.get("admission_suitability") or 1),
        lexical_commonness=float(row.get("lexical_commonness") or 0),
        lexical_commonness_known=bool(row.get("lexical_commonness_known")),
    )


def summarize_extension_case(case: Mapping[str, object]) -> dict[str, object]:
    payloads = _list_of_mappings(case.get("payloads"))
    signals = [
        signal for payload in payloads for signal in _list_of_mappings(payload.get("signals"))
    ]
    return {
        "accepted_exposures": round(float(case.get("accepted") or 0), 6),
        "packet_count": len(payloads),
        "signal_count": len(signals),
        "source_signal_count": int(case.get("source_signal_count") or 0),
        "target_signal_count": int(case.get("target_signal_count") or 0),
        "target_keys": sorted({str(signal.get("target_key") or "") for signal in signals}),
        "context_key_prefixes": sorted(
            {str(signal.get("context_key") or "").split(":", 1)[0] for signal in signals}
        ),
        "signals": [
            {
                "target_key": signal.get("target_key"),
                "target_lemma": signal.get("target_lemma"),
                "target_reading": signal.get("target_reading"),
                "side": signal.get("side"),
                "observation_source": signal.get("observation_source"),
                "count": signal.get("count"),
                "source_mapping_confidence": signal.get("source_mapping_confidence"),
                "context_key_prefix": str(signal.get("context_key") or "").split(":", 1)[0],
            }
            for signal in signals
        ],
        "documents": _list(case.get("documents")),
    }


def summarize_documents(documents: list[Mapping[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "document_id": document.get("document_id"),
            "side": document.get("side"),
            "path": document.get("path"),
            "sha256": document.get("sha256"),
            "visible_text_char_count": document.get("visible_text_char_count"),
            "ruby_pair_count": document.get("ruby_pair_count"),
        }
        for document in documents
    ]


def summarize_native_ingest(responses: list[Mapping[str, object]]) -> dict[str, object]:
    return {
        "response_count": len(responses),
        "statuses": [response.get("status") for response in responses],
        "runtime_srs_mutation_values": [
            response.get("runtime_srs_mutation") for response in responses
        ],
        "responses": responses,
    }


def summarize_store(store, *, policy: BrowsingSignalIngestPolicy) -> dict[str, object]:
    rows = []
    for target_key, aggregate in sorted(store.items.items()):
        rows.append(
            {
                "target_key": target_key,
                "target_lemma": aggregate.target_lemma,
                "target_reading": aggregate.target_reading,
                "source_hit_count": round(float(aggregate.source_hit_count), 6),
                "target_hit_count": round(float(aggregate.target_hit_count), 6),
                "replacement_exposure_count": round(
                    float(aggregate.replacement_exposure_count),
                    6,
                ),
                "reading_confidence": round(float(aggregate.reading_confidence), 6),
                "observation_sources": list(aggregate.observation_sources),
                "browsing_evidence": round(browsing_evidence_value(aggregate, policy=policy), 6),
                "browsing_context_count": browsing_context_count(aggregate, policy=policy),
                "browsing_signal": round(browsing_signal_value(aggregate, policy=policy), 6),
                "context_evidence": [
                    {
                        "context_key_prefix": context.context_key.split(":", 1)[0],
                        "source_hit_count": round(float(context.source_hit_count), 6),
                        "target_hit_count": round(float(context.target_hit_count), 6),
                        "replacement_exposure_count": round(
                            float(context.replacement_exposure_count),
                            6,
                        ),
                    }
                    for context in aggregate.context_evidence
                ],
                "last_seen_at": aggregate.last_seen_at,
                "decayed_at": aggregate.decayed_at,
            }
        )
    return {
        "pair": store.pair,
        "profile_id": store.profile_id,
        "updated_at": store.updated_at,
        "item_count": len(rows),
        "items": rows,
    }


def build_case_checks(
    *,
    case: Mapping[str, object],
    extension_case: Mapping[str, object],
    extension_summary: Mapping[str, object],
    ingest_responses: list[Mapping[str, object]],
    store_summary: Mapping[str, object],
    admission_simulations: Mapping[str, object],
    srs_store_exists: bool,
) -> list[dict[str, object]]:
    expectations = _as_mapping(case.get("expectations"))
    target_keys = set(extension_summary.get("target_keys") or [])
    store_rows = _rows_by_key(store_summary)
    serialized_payloads = json.dumps(extension_case.get("payloads") or [], ensure_ascii=False)
    checks = [
        _check(
            "extension_payload_count",
            _count_in_expected_range(extension_summary, expectations, "packet_count"),
            "Extension packet count is inside the expected range.",
        ),
        _check(
            "extension_signal_count",
            _count_in_expected_range(extension_summary, expectations, "signal_count"),
            "Extension signal count is inside the expected range.",
        ),
        _check(
            "source_mapping_signal_count",
            _count_in_expected_range(
                extension_summary,
                expectations,
                "source_signal_count",
                expectation_name="source_mapping_signals",
            ),
            "Source-language signal count is inside the expected range.",
        ),
        _check(
            "target_surface_signal_count",
            _count_in_expected_range(
                extension_summary,
                expectations,
                "target_signal_count",
                expectation_name="target_surface_signals",
            ),
            "Target-language signal count is inside the expected range.",
        ),
        _check(
            "native_host_ingest_succeeds_without_srs_mutation",
            _native_ingest_matches_expectation(
                ingest_responses,
                expectations=expectations,
                srs_store_exists=srs_store_exists,
            ),
            "Native-host route persists browsing aggregates without mutating runtime SRS.",
        ),
    ]
    for target in _list(expectations.get("required_payload_targets")):
        checks.append(
            _check(
                f"required_payload_target:{target}",
                str(target) in target_keys,
                f"Payload includes `{target}`.",
            )
        )
    for target in _list(expectations.get("absent_payload_targets")):
        checks.append(
            _check(
                f"absent_payload_target:{target}",
                str(target) not in target_keys and str(target) not in store_rows,
                f"Payload/store exclude broad or wrong-pair target `{target}`.",
            )
        )
    for required in _list_of_mappings(expectations.get("required_aggregate_targets")):
        target = str(required.get("target_key") or "")
        row = store_rows.get(target, {})
        checks.extend(_aggregate_checks(target, required, row))
    checks.extend(_admission_checks(expectations, admission_simulations))
    for private_string in _list(expectations.get("private_strings_absent")):
        needle = str(private_string)
        checks.append(
            _check(
                f"private_string_absent:{_safe_check_name(needle)}",
                needle not in serialized_payloads,
                "Raw page text and raw context identifiers are absent from extension packets.",
            )
        )
    return checks


def _count_in_expected_range(
    summary: Mapping[str, object],
    expectations: Mapping[str, object],
    field: str,
    *,
    expectation_name: str | None = None,
) -> bool:
    name = expectation_name or field
    actual = int(summary.get(field) or 0)
    min_key = f"min_{name}"
    max_key = f"max_{name}"
    minimum = (
        int(expectations[min_key])
        if min_key in expectations
        else (1 if field == "packet_count" else 0)
    )
    maximum = int(expectations[max_key]) if max_key in expectations else None
    return actual >= minimum and (maximum is None or actual <= maximum)


def _native_ingest_matches_expectation(
    responses: list[Mapping[str, object]],
    *,
    expectations: Mapping[str, object],
    srs_store_exists: bool,
) -> bool:
    require_ingest = bool(expectations.get("require_native_ingest", True))
    if not responses:
        return not require_ingest and not srs_store_exists
    return (
        all(response.get("status") == "ok" for response in responses)
        and all(response.get("runtime_srs_mutation") is False for response in responses)
        and not srs_store_exists
    )


def _admission_checks(
    expectations: Mapping[str, object],
    simulations: Mapping[str, object],
) -> list[dict[str, object]]:
    admission_expectations = _as_mapping(expectations.get("admission"))
    if not admission_expectations:
        return []
    strength = str(admission_expectations.get("strength") or "strong")
    simulation = _as_mapping(simulations.get(strength))
    rows = {
        str(row.get("target_key") or row.get("lemma") or ""): row
        for row in _list_of_mappings(simulation.get("rows"))
    }
    checks = [
        _check(
            f"admission_simulation_exists:{strength}",
            bool(simulation),
            f"Admission simulation includes `{strength}` strength.",
        )
    ]
    if "browsing_driven_count_min" in admission_expectations:
        checks.append(
            _check(
                f"admission_browsing_driven_count_min:{strength}",
                int(simulation.get("browsing_driven_count") or 0)
                >= int(admission_expectations.get("browsing_driven_count_min") or 0),
                f"`{strength}` has enough browsing-driven selections.",
            )
        )
    for expected_row in _list_of_mappings(admission_expectations.get("required_rows")):
        target = str(expected_row.get("target_key") or "")
        row = rows.get(target, {})
        checks.extend(_admission_row_checks(strength, target, expected_row, row))
    return checks


def _admission_row_checks(
    strength: str,
    target: str,
    expected: Mapping[str, object],
    row: Mapping[str, object],
) -> list[dict[str, object]]:
    checks = [
        _check(
            f"admission_row_exists:{strength}:{target}",
            bool(row),
            f"`{strength}` admission rows include `{target}`.",
        )
    ]
    if "selected" in expected:
        checks.append(
            _check(
                f"admission_selected:{strength}:{target}",
                bool(row.get("selected")) is bool(expected.get("selected")),
                f"`{target}` selected state matches expectation.",
            )
        )
    if expected.get("selected_lane"):
        checks.append(
            _check(
                f"admission_lane:{strength}:{target}",
                str(row.get("selected_lane") or "") == str(expected.get("selected_lane")),
                f"`{target}` selected lane is `{expected.get('selected_lane')}`.",
            )
        )
    if "effective_browsing_signal_min" in expected:
        checks.append(
            _check(
                f"admission_effective_signal_min:{strength}:{target}",
                float(row.get("effective_browsing_signal") or 0)
                >= float(expected.get("effective_browsing_signal_min") or 0),
                f"`{target}` has enough effective browsing signal.",
            )
        )
    return checks


def _aggregate_checks(
    target: str,
    required: Mapping[str, object],
    row: Mapping[str, object],
) -> list[dict[str, object]]:
    checks = [
        _check(
            f"required_aggregate_target:{target}",
            bool(row),
            f"Aggregate store includes `{target}`.",
        )
    ]
    numeric_fields = (
        "source_hit_count",
        "target_hit_count",
        "replacement_exposure_count",
        "browsing_context_count",
    )
    for field in numeric_fields:
        min_key = f"{field}_min"
        if min_key not in required and not (
            field == "browsing_context_count" and "context_count_min" in required
        ):
            continue
        expected_min = required.get(min_key)
        if field == "browsing_context_count" and "context_count_min" in required:
            expected_min = required.get("context_count_min")
        checks.append(
            _check(
                f"aggregate_{field}_min:{target}",
                float(row.get(field) or 0) >= float(expected_min or 0),
                f"`{target}` has {field} >= {expected_min}.",
            )
        )
    expected_sources = {str(item) for item in _list(required.get("observation_sources"))}
    if expected_sources:
        actual_sources = {str(item) for item in _list(row.get("observation_sources"))}
        checks.append(
            _check(
                f"aggregate_observation_sources:{target}",
                expected_sources <= actual_sources,
                f"`{target}` has observation sources {sorted(expected_sources)}.",
            )
        )
    return checks


def load_native_host_module():
    spec = importlib.util.spec_from_file_location(
        "lexishift_native_host_offline_page_mining",
        NATIVE_HOST_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load native host module from {NATIVE_HOST_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_project_path(value: object) -> Path:
    path = Path(str(value or ""))
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _check(name: str, condition: bool, detail: str) -> dict[str, object]:
    return {"name": name, "status": "pass" if condition else "fail", "detail": detail}


def _rows_by_key(summary: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row.get("target_key") or row.get("target_lemma") or ""): row
        for row in _list_of_mappings(summary.get("items"))
    }


def _safe_check_name(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"value_sha256_{digest}"


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _list_of_mappings(value: object) -> list[Mapping[str, object]]:
    return [item for item in _list(value) if isinstance(item, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
