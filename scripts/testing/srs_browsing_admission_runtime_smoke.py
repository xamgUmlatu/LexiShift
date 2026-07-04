#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
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


TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_browsing_admission_runtime_smoke_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_browsing_admission_runtime_smoke_latest.md"
EXTENSION_SIGNAL_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_browsing_admission_signals.js"
)
EXTENSION_SOURCE_MORPHOLOGY_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_browsing_source_morphology.js"
)
EXTENSION_SOURCE_MINING_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_browsing_source_mining.js"
)
EXTENSION_PAGE_MINING_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_browsing_page_mining.js"
)
NATIVE_HOST_SCRIPT = PROJECT_ROOT / "scripts" / "helper" / "lexishift_native_host.py"
DEFAULT_PAIR = "en-ja"
DEFAULT_PROFILE_ID = "runtime smoke/profile"
INGESTED_AT = datetime(2026, 5, 23, tzinfo=timezone.utc)
MAINTAINED_AT = datetime(2026, 6, 6, tzinfo=timezone.utc)


def smoke_pair_config(pair: str) -> dict[str, object]:
    normalized = str(pair or "").strip().lower() or DEFAULT_PAIR
    configs: dict[str, dict[str, object]] = {
        "en-ja": {
            "target_language_tag": "ja",
            "core_candidates": [
                {"lemma": "する", "neutral_score": 1.00, "commonness": 1.0},
                {"lemma": "いる", "neutral_score": 0.96, "commonness": 1.0},
                {"lemma": "言う", "neutral_score": 0.90, "commonness": 0.96},
                {"lemma": "犬", "neutral_score": 0.84, "commonness": 0.70},
            ],
            "interest": {"lemma": "料理", "commonness": 0.35},
            "single_context": {"lemma": "会社", "commonness": 0.85},
            "context_target": {"lemma": "辛い", "reading": "つらい", "commonness": 0.45},
            "source_target": {
                "source": "fermentation",
                "lemma": "発酵",
                "reading": "はっこう",
                "commonness": 0.32,
            },
            "ambiguous_source_targets": [
                {"source": "light", "lemma": "光", "reading": "ひかり"},
                {"source": "light", "lemma": "軽い", "reading": "かるい"},
            ],
            "extra_source_target": {"source": "work", "lemma": "仕事", "reading": "しごと"},
            "tail_candidate": {"lemma": "旅行", "commonness": 0.55},
            "ruby_targets": [
                {"surface": "発酵", "reading": "はっこう"},
                {"surface": "発酵", "reading": "はっこう"},
                {"surface": "未確認", "reading": "not-kana"},
            ],
        },
        "en-es": {
            "target_language_tag": "es",
            "core_candidates": [
                {"lemma": "casa", "neutral_score": 1.00, "commonness": 1.0},
                {"lemma": "ser", "neutral_score": 0.96, "commonness": 1.0},
                {"lemma": "decir", "neutral_score": 0.90, "commonness": 0.96},
                {"lemma": "perro", "neutral_score": 0.84, "commonness": 0.70},
            ],
            "interest": {"lemma": "cocina", "commonness": 0.35},
            "single_context": {"lemma": "empresa", "commonness": 0.85},
            "context_target": {"lemma": "picante", "commonness": 0.45},
            "source_target": {
                "source": "fermentation",
                "lemma": "fermentación",
                "commonness": 0.32,
            },
            "ambiguous_source_targets": [
                {"source": "light", "lemma": "luz"},
                {"source": "light", "lemma": "ligero"},
            ],
            "extra_source_target": {"source": "work", "lemma": "trabajo"},
            "tail_candidate": {"lemma": "viaje", "commonness": 0.55},
            "ruby_targets": [],
        },
        "en-de": {
            "target_language_tag": "de",
            "core_candidates": [
                {"lemma": "Haus", "neutral_score": 1.00, "commonness": 1.0},
                {"lemma": "sein", "neutral_score": 0.96, "commonness": 1.0},
                {"lemma": "sagen", "neutral_score": 0.90, "commonness": 0.96},
                {"lemma": "Hund", "neutral_score": 0.84, "commonness": 0.70},
            ],
            "interest": {"lemma": "Küche", "commonness": 0.35},
            "single_context": {"lemma": "Firma", "commonness": 0.85},
            "context_target": {"lemma": "scharf", "commonness": 0.45},
            "source_target": {
                "source": "fermentation",
                "lemma": "Fermentation",
                "commonness": 0.32,
            },
            "ambiguous_source_targets": [
                {"source": "light", "lemma": "Licht"},
                {"source": "light", "lemma": "leicht"},
            ],
            "extra_source_target": {"source": "work", "lemma": "Arbeit"},
            "tail_candidate": {"lemma": "Reise", "commonness": 0.55},
            "ruby_targets": [],
        },
    }
    return configs.get(normalized, configs[DEFAULT_PAIR])


def target_key(target: Mapping[str, object]) -> str:
    lemma = str(target.get("lemma") or target.get("surface") or "").strip()
    reading = str(target.get("reading") or "").strip()
    return f"{lemma}|{reading}" if reading and reading != lemma else lemma


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run an isolated extension-payload -> native-host -> helper-store -> "
            "admission-preview smoke for SRS browsing admission."
        )
    )
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--admission-budget", type=int, default=4)
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
    print(f"status: {report['status']}")
    print(f"json_out: {args.json_out}")
    print(f"markdown_out: {args.markdown_out}")
    return 0 if report["status"] == "PASS" else 1


def build_report(*, pair: str = DEFAULT_PAIR, admission_budget: int = 4) -> dict[str, object]:
    pair = str(pair or "").strip() or DEFAULT_PAIR
    pair_config = smoke_pair_config(pair)
    policy = BrowsingSignalIngestPolicy()
    extension_result = build_extension_payloads(pair=pair, pair_config=pair_config)
    payloads = list(extension_result["payloads"])
    native_host = load_native_host_module()

    with tempfile.TemporaryDirectory() as tmp:
        paths = build_helper_paths(Path(tmp))
        with patch.object(native_host, "build_helper_paths", return_value=paths):
            ingest_responses = [
                native_host._handle_request("srs_browsing_signal_ingest", payload)
                for payload in payloads
            ]
            persisted_before = load_browsing_signal_store(
                paths.srs_browsing_signal_store_path_for(
                    paths.normalize_profile_id(DEFAULT_PROFILE_ID),
                    pair,
                )
            )
            maintenance_response = native_host._handle_request(
                "srs_browsing_signal_ingest",
                {
                    "pair": pair,
                    "profile_id": DEFAULT_PROFILE_ID,
                    "captured_at": MAINTAINED_AT.isoformat().replace("+00:00", "Z"),
                    "opt_in": False,
                    "signals": [],
                },
            )
            persisted_after = load_browsing_signal_store(
                paths.srs_browsing_signal_store_path_for(
                    paths.normalize_profile_id(DEFAULT_PROFILE_ID),
                    pair,
                )
            )
            srs_store_exists = paths.srs_store_path_for(DEFAULT_PROFILE_ID).exists()

    simulations = simulate_browsing_admission_presets(
        build_candidates(pair, pair_config=pair_config),
        store=persisted_before,
        admission_budget=admission_budget,
        policy=policy,
        now=INGESTED_AT,
    )
    checks = build_checks(
        extension_result=extension_result,
        ingest_responses=ingest_responses,
        before_store_summary=summarize_store(persisted_before, policy=policy),
        after_store_summary=summarize_store(persisted_after, policy=policy),
        simulations={name: result.to_dict() for name, result in simulations.items()},
        maintenance_response=maintenance_response,
        srs_store_exists=srs_store_exists,
        pair_config=pair_config,
    )
    status = "PASS" if all(check["status"] == "pass" for check in checks) else "FAIL"
    return {
        "schema_version": 1,
        "status": status,
        "generated_at": "2026-07-03T00:00:00Z",
        "pair": pair,
        "target_language_tag": pair_config.get("target_language_tag"),
        "profile_id": DEFAULT_PROFILE_ID,
        "scope": "isolated_extension_payload_native_host_helper_admission_smoke",
        "live_user_data_touched": False,
        "extension_payload": summarize_extension_result(extension_result),
        "native_host_ingest": summarize_native_ingest(ingest_responses),
        "aggregate_store_before_maintenance": summarize_store(persisted_before, policy=policy),
        "maintenance": {
            "captured_at": MAINTAINED_AT.isoformat().replace("+00:00", "Z"),
            "response_status": maintenance_response.get("status"),
            "reason": maintenance_response.get("reason"),
            "runtime_srs_mutation": maintenance_response.get("runtime_srs_mutation"),
            "aggregate_store_after": summarize_store(persisted_after, policy=policy),
        },
        "admission_budget": admission_budget,
        "simulations": {name: result.to_dict() for name, result in simulations.items()},
        "checks": checks,
    }


def build_extension_payloads(
    *,
    pair: str,
    pair_config: Mapping[str, object],
) -> dict[str, object]:
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const signalModulePath = {json.dumps(str(EXTENSION_SIGNAL_JS))};
const sourceMorphologyModulePath = {json.dumps(str(EXTENSION_SOURCE_MORPHOLOGY_JS))};
const sourceMiningModulePath = {json.dumps(str(EXTENSION_SOURCE_MINING_JS))};
const miningModulePath = {json.dumps(str(EXTENSION_PAGE_MINING_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(signalModulePath, "utf8"), context, {{ filename: signalModulePath }});
vm.runInContext(
  fs.readFileSync(sourceMorphologyModulePath, "utf8"),
  context,
  {{ filename: sourceMorphologyModulePath }}
);
vm.runInContext(fs.readFileSync(sourceMiningModulePath, "utf8"), context, {{ filename: sourceMiningModulePath }});
vm.runInContext(fs.readFileSync(miningModulePath, "utf8"), context, {{ filename: miningModulePath }});

const signals = context.LexiShift.srsBrowsingAdmissionSignals;
const pageMining = context.LexiShift.srsBrowsingPageMining;
const pending = new Map();
const pair = {json.dumps(pair)};
const pairConfig = {json.dumps(pair_config, ensure_ascii=False)};
const settings = {{
  srsProfileId: {json.dumps(DEFAULT_PROFILE_ID)},
  srsPair: pair
}};
const options = {{
  nowMs: () => 0,
  maxCountPerSignal: 5,
  maxSignalsPerPacket: 20,
  pageContextKey: "runtime-smoke-page"
}};
const interest = pairConfig.interest;
const singleContext = pairConfig.single_context;
const contextTarget = pairConfig.context_target;
const sourceTarget = pairConfig.source_target;
const ambiguousSourceTargets = Array.from(pairConfig.ambiguous_source_targets || []);
const extraSourceTarget = pairConfig.extra_source_target;
const targetLanguageTag = pairConfig.target_language_tag || "";
function exposureFor(target, extras) {{
  const row = {{ language_pair: pair, lemma: target.lemma, ...(extras || {{}}) }};
  if (target.reading) {{
    row.target_reading = target.reading;
  }}
  return row;
}}
const exposures = [
  exposureFor(interest, {{ document_id: "runtime-smoke-interest-a", url: "https://example.invalid/interest-a", raw_text: "private text one" }}),
  exposureFor(interest, {{ document_id: "runtime-smoke-interest-a" }}),
  exposureFor(interest, {{ document_id: "runtime-smoke-interest-a" }}),
  exposureFor(interest, {{ document_id: "runtime-smoke-interest-a" }}),
  exposureFor(interest, {{ document_id: "runtime-smoke-interest-a" }}),
  exposureFor(interest, {{ document_id: "runtime-smoke-interest-b", page_text: "private text two" }}),
  exposureFor(interest, {{ document_id: "runtime-smoke-interest-b" }}),
  exposureFor(interest, {{ document_id: "runtime-smoke-interest-b" }}),
  exposureFor(interest, {{ document_id: "runtime-smoke-interest-b" }}),
  exposureFor(interest, {{ document_id: "runtime-smoke-interest-b" }}),
  exposureFor(singleContext),
  exposureFor(singleContext),
  exposureFor(singleContext),
  exposureFor(singleContext),
  exposureFor(singleContext),
  exposureFor(contextTarget, {{ document_id: "runtime-smoke-context-a", reading_confidence: contextTarget.reading ? 0.6 : 1 }}),
  exposureFor(contextTarget, {{ document_id: "runtime-smoke-context-a", reading_confidence: contextTarget.reading ? 0.6 : 1 }}),
  exposureFor(contextTarget, {{ document_id: "runtime-smoke-context-b", reading_confidence: contextTarget.reading ? 0.6 : 1 }}),
  exposureFor(contextTarget, {{ document_id: "runtime-smoke-context-b", reading_confidence: contextTarget.reading ? 0.6 : 1 }}),
  {{ language_pair: "all", lemma: "ignored" }}
];
const rubySignals = pageMining.buildRubyTargetSignals(
  Array.from(pairConfig.ruby_targets || []),
  settings,
  {{ maxCountPerTarget: 5 }}
);
function srsRule(source, replacement, reading) {{
  const scriptForms = reading
    ? {{ kanji: replacement, kana: reading }}
    : {{ surface: replacement }};
  return {{
    source_phrase: source,
    replacement,
    enabled: true,
    metadata: {{
      lexishift_origin: "srs",
      language_pair: pair,
      word_package: {{
        version: 1,
        language_tag: targetLanguageTag,
        surface: replacement,
        reading,
        script_forms: scriptForms,
        source: {{ provider: "runtime_smoke" }}
      }}
    }}
  }};
}}
const sourceRules = [
  srsRule(sourceTarget.source, sourceTarget.lemma, sourceTarget.reading || ""),
  ...ambiguousSourceTargets.map((target) => srsRule(target.source, target.lemma, target.reading || "")),
  srsRule(extraSourceTarget.source, extraSourceTarget.lemma, extraSourceTarget.reading || "")
];
const sourceSignalsA = pageMining.buildSourceMappingSignals(
  "Fermentation appears in this source page. fermentation fermentation.",
  sourceRules,
  settings,
  {{ maxSourceCountPerTarget: 3 }}
);
const sourceSignalsB = pageMining.buildSourceMappingSignals(
  "A second page discusses fermentation without exposing the Japanese target.",
  sourceRules,
  settings,
  {{ maxSourceCountPerTarget: 3 }}
);
let accepted = signals.addExposureBatchToPending(
  pending,
  exposures.concat(rubySignals),
  settings,
  options
);
accepted += signals.addExposureBatchToPending(
  pending,
  sourceSignalsA,
  settings,
  {{ ...options, pageContextKey: "runtime-smoke-source-page-a" }}
);
accepted += signals.addExposureBatchToPending(
  pending,
  sourceSignalsB,
  settings,
  {{ ...options, pageContextKey: "runtime-smoke-source-page-b" }}
);
const payloads = signals.buildPacketPayloads(pending, {{
  nowIso: () => "2026-05-23T00:00:00.000Z",
  maxSignalsPerPacket: 20
}});
const serialized = JSON.stringify(payloads);
assert.equal(serialized.includes("example.invalid"), false);
assert.equal(serialized.includes("private text"), false);
assert.equal(serialized.includes("runtime-smoke-cooking"), false);
console.log(JSON.stringify({{
  accepted,
  payloads,
  private_strings_absent: true,
  ruby_signal_count: rubySignals.length,
  source_signal_count: sourceSignalsA.length + sourceSignalsB.length,
  signal_count: payloads.reduce((sum, payload) => sum + payload.signals.length, 0),
  context_keys: payloads.flatMap((payload) => payload.signals.map((row) => row.context_key))
}}));
"""
    completed = subprocess.run(
        ["node"],
        input=script,
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Extension browsing-admission packet build failed.\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    parsed = json.loads(completed.stdout)
    if not isinstance(parsed, dict):
        raise RuntimeError("Extension packet builder did not return an object.")
    return parsed


def load_native_host_module():
    spec = importlib.util.spec_from_file_location(
        "lexishift_native_host_browsing_runtime_smoke",
        NATIVE_HOST_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load native host module from {NATIVE_HOST_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_candidates(
    pair: str,
    *,
    pair_config: Mapping[str, object],
) -> tuple[BrowsingAdmissionCandidate, ...]:
    del pair
    rows: list[BrowsingAdmissionCandidate] = []
    for core in _list_of_mappings(pair_config.get("core_candidates")):
        rows.append(
            BrowsingAdmissionCandidate(
                lemma=str(core.get("lemma") or ""),
                neutral_score=float(core.get("neutral_score") or 0.0),
                lexical_commonness=float(core.get("commonness") or 0.0),
                lexical_commonness_known=True,
            )
        )
    interest = _as_mapping(pair_config.get("interest"))
    single_context = _as_mapping(pair_config.get("single_context"))
    source_target = _as_mapping(pair_config.get("source_target"))
    context_target = _as_mapping(pair_config.get("context_target"))
    tail_candidate = _as_mapping(pair_config.get("tail_candidate"))
    rows.extend(
        [
            BrowsingAdmissionCandidate(
                lemma=str(interest.get("lemma") or ""),
                target_reading=str(interest.get("reading") or ""),
                neutral_score=0.64,
                readiness_multiplier=0.92,
                explicit_preference_fit=0.70,
                source_confidence=0.90,
                lexical_commonness=float(interest.get("commonness") or 0.35),
                lexical_commonness_known=True,
            ),
            BrowsingAdmissionCandidate(
                lemma=str(single_context.get("lemma") or ""),
                target_reading=str(single_context.get("reading") or ""),
                neutral_score=0.62,
                readiness_multiplier=0.92,
                explicit_preference_fit=0.50,
                source_confidence=0.90,
                lexical_commonness=float(single_context.get("commonness") or 0.85),
                lexical_commonness_known=True,
            ),
            BrowsingAdmissionCandidate(
                lemma=str(source_target.get("lemma") or ""),
                target_reading=str(source_target.get("reading") or ""),
                neutral_score=0.59,
                readiness_multiplier=0.90,
                explicit_preference_fit=0.72,
                source_confidence=0.86,
                lexical_commonness=float(source_target.get("commonness") or 0.32),
                lexical_commonness_known=True,
            ),
            BrowsingAdmissionCandidate(
                lemma=str(context_target.get("lemma") or ""),
                target_reading=str(context_target.get("reading") or ""),
                neutral_score=0.60,
                readiness_multiplier=0.86,
                explicit_preference_fit=0.55,
                source_confidence=0.82,
                lexical_commonness=float(context_target.get("commonness") or 0.45),
                lexical_commonness_known=True,
            ),
            BrowsingAdmissionCandidate(
                lemma=str(tail_candidate.get("lemma") or ""),
                target_reading=str(tail_candidate.get("reading") or ""),
                neutral_score=0.58,
                lexical_commonness=float(tail_candidate.get("commonness") or 0.55),
                lexical_commonness_known=True,
            ),
        ]
    )
    return tuple(rows)


def summarize_extension_result(result: Mapping[str, object]) -> dict[str, object]:
    payloads = _list_of_mappings(result.get("payloads"))
    signals = [
        signal for payload in payloads for signal in _list_of_mappings(payload.get("signals"))
    ]
    return {
        "accepted_exposures": int(result.get("accepted") or 0),
        "packet_count": len(payloads),
        "signal_count": len(signals),
        "ruby_signal_count": int(result.get("ruby_signal_count") or 0),
        "source_signal_count": int(result.get("source_signal_count") or 0),
        "private_strings_absent": bool(result.get("private_strings_absent")),
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
                "context_key_prefix": str(signal.get("context_key") or "").split(":", 1)[0],
            }
            for signal in signals
        ],
    }


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


def build_checks(
    *,
    extension_result: Mapping[str, object],
    ingest_responses: list[Mapping[str, object]],
    before_store_summary: Mapping[str, object],
    after_store_summary: Mapping[str, object],
    simulations: Mapping[str, Mapping[str, object]],
    maintenance_response: Mapping[str, object],
    srs_store_exists: bool,
    pair_config: Mapping[str, object],
) -> list[dict[str, object]]:
    before_rows = _rows_by_key(before_store_summary)
    after_rows = _rows_by_key(after_store_summary)
    strong_rows = {
        str(row.get("target_key") or row.get("lemma") or ""): row
        for row in _list_of_mappings(_as_mapping(simulations.get("strong")).get("rows"))
    }
    interest_key = target_key(_as_mapping(pair_config.get("interest")))
    single_context_key = target_key(_as_mapping(pair_config.get("single_context")))
    context_target_key = target_key(_as_mapping(pair_config.get("context_target")))
    source_target_key = target_key(_as_mapping(pair_config.get("source_target")))
    ambiguous_source_keys = {
        target_key(target)
        for target in _list_of_mappings(pair_config.get("ambiguous_source_targets"))
    }
    ruby_targets = _list_of_mappings(pair_config.get("ruby_targets"))
    ruby_expected = bool(ruby_targets)
    interest_row = _row_for_key(before_rows, interest_key)
    context_target_row = _row_for_key(before_rows, context_target_key)
    source_target_row = _row_for_key(before_rows, source_target_key)
    source_target_after_row = _row_for_key(after_rows, source_target_key)
    interest_after_row = _row_for_key(after_rows, interest_key)
    single_context_strong_row = _row_for_key(strong_rows, single_context_key)
    interest_strong_row = _row_for_key(strong_rows, interest_key)
    checks = [
        _check(
            "extension_payload_is_privacy_safe",
            bool(extension_result.get("private_strings_absent"))
            and all(
                str(key or "").startswith(("ctxh:", "pageh:"))
                for key in _list(extension_result.get("context_keys"))
            ),
            "Extension packet has only hashed/bucketed context keys and no raw private strings.",
        ),
        _check(
            "native_host_ingest_succeeds_without_srs_mutation",
            bool(ingest_responses)
            and all(response.get("status") == "ok" for response in ingest_responses)
            and all(response.get("runtime_srs_mutation") is False for response in ingest_responses)
            and not srs_store_exists,
            "Native-host route persists only the browsing aggregate store.",
        ),
        _check(
            "multi_context_signal_survives_ingest",
            interest_row.get("browsing_context_count", 0) >= 2
            and context_target_row.get("browsing_context_count", 0) >= 2,
            "Repeated exposures across separate contexts become per-target context evidence.",
        ),
        _check(
            "target_surface_channel_scope",
            (
                source_target_row.get("target_hit_count", 0) >= 2
                and "target_surface" in source_target_row.get("observation_sources", [])
            )
            if ruby_expected
            else int(extension_result.get("ruby_signal_count") or 0) == 0
            and all(
                "target_surface" not in row.get("observation_sources", [])
                for row in _list_of_mappings(before_store_summary.get("items"))
            ),
            (
                "Ruby page mining emits reading-aware target-surface evidence."
                if ruby_expected
                else "Ruby target-surface mining stays scoped out for this target language."
            ),
        ),
        _check(
            "source_mapping_survives_ingest",
            source_target_row.get("source_hit_count", 0) >= 2.3
            and "source_mapping"
            in source_target_row.get(
                "observation_sources",
                [],
            )
            and not any(key in before_rows for key in ambiguous_source_keys),
            "Conservative source-language mining emits mapped evidence and rejects ambiguous source terms.",
        ),
        _check(
            "single_context_high_count_is_not_enough",
            single_context_strong_row.get("browsing_count_multiplier") == 0,
            "A high count from one context is gated out before admission boost.",
        ),
        _check(
            "strong_preset_can_move_context_supported_interest",
            int(_as_mapping(simulations.get("strong")).get("browsing_driven_count", 0)) >= 1
            and interest_strong_row.get("selected_lane") == "browsing",
            "Context-supported browsing interest can enter through the browsing lane.",
        ),
        _check(
            "opt_out_maintains_existing_store",
            maintenance_response.get("status") == "skipped"
            and maintenance_response.get("runtime_srs_mutation") is False
            and interest_after_row.get("replacement_exposure_count", 0)
            < interest_row.get("replacement_exposure_count", 0)
            and source_target_after_row.get("source_hit_count", 0)
            <= source_target_row.get("source_hit_count", 0),
            "An opt-out packet decays existing aggregate state without adding new evidence.",
        ),
    ]
    return checks


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# SRS Browsing Admission Runtime Smoke",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Pair: `{report.get('pair', '')}`",
        f"- Scope: `{report.get('scope', '')}`",
        f"- Live user data touched: `{report.get('live_user_data_touched')}`",
        f"- Admission budget: `{report.get('admission_budget')}`",
        "",
        "## Checks",
        "",
    ]
    for check in _list_of_mappings(report.get("checks")):
        lines.append(f"- `{check.get('status')}` `{check.get('name')}`: {check.get('detail')}")
    lines.extend(["", "## Extension Payload", ""])
    extension = _as_mapping(report.get("extension_payload"))
    lines.extend(
        [
            f"- Accepted exposures: `{extension.get('accepted_exposures')}`",
            f"- Packet count: `{extension.get('packet_count')}`",
            f"- Signal count: `{extension.get('signal_count')}`",
            f"- Ruby signal count: `{extension.get('ruby_signal_count')}`",
            f"- Source signal count: `{extension.get('source_signal_count')}`",
            f"- Context key prefixes: `{', '.join(map(str, extension.get('context_key_prefixes', [])))}`",
            f"- Private strings absent: `{extension.get('private_strings_absent')}`",
            "",
            "| target | side | source | count | context |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in _list_of_mappings(extension.get("signals")):
        lines.append(
            "| "
            f"`{row.get('target_key')}` | "
            f"`{row.get('side')}` | "
            f"`{row.get('observation_source')}` | "
            f"{row.get('count')} | "
            f"`{row.get('context_key_prefix')}` |"
        )
    lines.extend(
        [
            "",
            "## Aggregate Before Maintenance",
            "",
            "| target | reading | source | target | repl | contexts | evidence | signal | sources |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    before = _as_mapping(report.get("aggregate_store_before_maintenance"))
    for row in _list_of_mappings(before.get("items")):
        lines.append(
            "| "
            f"`{row.get('target_lemma')}` | "
            f"`{row.get('target_reading') or ''}` | "
            f"{row.get('source_hit_count')} | "
            f"{row.get('target_hit_count')} | "
            f"{row.get('replacement_exposure_count')} | "
            f"{row.get('browsing_context_count')} | "
            f"{row.get('browsing_evidence')} | "
            f"{row.get('browsing_signal')} | "
            f"`{', '.join(map(str, row.get('observation_sources') or []))}` |"
        )
    lines.extend(["", "## Strong Admission Rows", ""])
    strong = _as_mapping(_as_mapping(report.get("simulations")).get("strong"))
    lines.extend(
        [
            f"- Selected: `{', '.join(map(str, strong.get('selected_lemmas', [])))}`",
            f"- Browsing driven count: `{strong.get('browsing_driven_count')}`",
            "",
            "| target | lane | selected | contexts | count_mult | effective_signal | boost |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in _list_of_mappings(strong.get("rows")):
        if row.get("browsing_signal") or row.get("selected"):
            lines.append(
                "| "
                f"`{row.get('lemma')}` | "
                f"`{row.get('selected_lane')}` | "
                f"{row.get('selected')} | "
                f"{row.get('browsing_context_count')} | "
                f"{row.get('browsing_count_multiplier')} | "
                f"{row.get('effective_browsing_signal')} | "
                f"{row.get('browsing_boost')} |"
            )
    lines.extend(["", "## Maintenance", ""])
    maintenance = _as_mapping(report.get("maintenance"))
    after = _as_mapping(maintenance.get("aggregate_store_after"))
    lines.extend(
        [
            f"- Response status: `{maintenance.get('response_status')}`",
            f"- Reason: `{maintenance.get('reason')}`",
            f"- Runtime SRS mutation: `{maintenance.get('runtime_srs_mutation')}`",
            f"- Aggregate items after: `{after.get('item_count')}`",
            "",
        ]
    )
    return "\n".join(lines)


def _check(name: str, condition: bool, detail: str) -> dict[str, object]:
    return {"name": name, "status": "pass" if condition else "fail", "detail": detail}


def _rows_by_key(summary: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row.get("target_key") or row.get("target_lemma") or ""): row
        for row in _list_of_mappings(summary.get("items"))
    }


def _row_for_key(rows: Mapping[str, Mapping[str, object]], key: str) -> Mapping[str, object]:
    text = str(key or "").strip()
    return rows.get(text) or rows.get(text.casefold()) or {}


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _list_of_mappings(value: object) -> list[Mapping[str, object]]:
    return [item for item in _list(value) if isinstance(item, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
