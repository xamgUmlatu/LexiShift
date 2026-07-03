#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import importlib.util
import json
from pathlib import Path
import re
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
    BrowsingSignalIngestPolicy,
    browsing_context_count,
    browsing_evidence_value,
    browsing_signal_value,
    load_browsing_signal_store,
)


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


class SavedPageTextExtractor(HTMLParser):
    SKIP_TAGS = {
        "script",
        "style",
        "noscript",
        "textarea",
        "select",
        "option",
        "template",
        "svg",
        "canvas",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[tuple[str, bool]] = []
        self._skip_depth = 0
        self._ruby_depth = 0
        self._rt_depth = 0
        self._rp_depth = 0
        self._ruby_surface: list[str] = []
        self._ruby_reading: list[str] = []
        self._visible_parts: list[str] = []
        self.ruby_pairs: list[dict[str, str]] = []

    @property
    def visible_text(self) -> str:
        return _collapse_spaces(" ".join(self._visible_parts))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        attrs_map = {key.lower(): value or "" for key, value in attrs}
        starts_skip = self._skip_depth > 0 or self._starts_skip(normalized_tag, attrs_map)
        self._stack.append((normalized_tag, starts_skip))
        if starts_skip:
            self._skip_depth += 1
            return
        if normalized_tag == "ruby":
            self._ruby_depth += 1
            if self._ruby_depth == 1:
                self._ruby_surface = []
                self._ruby_reading = []
        elif self._ruby_depth and normalized_tag == "rt":
            self._rt_depth += 1
        elif self._ruby_depth and normalized_tag == "rp":
            self._rp_depth += 1

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        stack_tag, started_skip = self._pop_stack(normalized_tag)
        _ = stack_tag
        if started_skip:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._ruby_depth and normalized_tag == "rt":
            self._rt_depth = max(0, self._rt_depth - 1)
        elif self._ruby_depth and normalized_tag == "rp":
            self._rp_depth = max(0, self._rp_depth - 1)
        elif normalized_tag == "ruby" and self._ruby_depth:
            if self._ruby_depth == 1:
                pair = _normalize_ruby_pair(
                    "".join(self._ruby_surface),
                    "".join(self._ruby_reading),
                )
                if pair:
                    self.ruby_pairs.append(pair)
                self._ruby_surface = []
                self._ruby_reading = []
            self._ruby_depth = max(0, self._ruby_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = str(data or "")
        if not text.strip():
            return
        if self._ruby_depth:
            if self._rt_depth:
                self._ruby_reading.append(text)
                return
            if self._rp_depth:
                return
            self._ruby_surface.append(text)
        self._visible_parts.append(text)

    def _starts_skip(self, tag: str, attrs: Mapping[str, str]) -> bool:
        if tag in self.SKIP_TAGS:
            return True
        if attrs.get("data-lexishift-scan-skip", "").strip().lower() == "true":
            return True
        class_names = {part.strip() for part in attrs.get("class", "").split()}
        return bool({"lexishift-replacement", "lexishift-popup"} & class_names)

    def _pop_stack(self, tag: str) -> tuple[str, bool]:
        if not self._stack:
            return tag, False
        if self._stack[-1][0] == tag:
            return self._stack.pop()
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                _, started_skip = self._stack.pop(index)
                return tag, started_skip
        return tag, False


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
    checks = build_case_checks(
        case=case,
        extension_case=extension_case,
        extension_summary=extension_summary,
        ingest_responses=ingest_responses,
        store_summary=store_summary,
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
        "checks": checks,
    }


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
    srs_store_exists: bool,
) -> list[dict[str, object]]:
    expectations = _as_mapping(case.get("expectations"))
    target_keys = set(extension_summary.get("target_keys") or [])
    store_rows = _rows_by_key(store_summary)
    serialized_payloads = json.dumps(extension_case.get("payloads") or [], ensure_ascii=False)
    checks = [
        _check(
            "extension_payload_count",
            int(extension_summary.get("packet_count") or 0)
            >= int(expectations.get("min_packet_count") or 1),
            "At least one extension packet was built from saved pages.",
        ),
        _check(
            "extension_signal_count",
            int(extension_summary.get("signal_count") or 0)
            >= int(expectations.get("min_signal_count") or 1),
            "Saved pages produced the expected minimum signal volume.",
        ),
        _check(
            "source_mapping_signal_count",
            int(extension_summary.get("source_signal_count") or 0)
            >= int(expectations.get("min_source_mapping_signals") or 0),
            "Source-language pages produced mapped target-language signals.",
        ),
        _check(
            "target_surface_signal_count",
            int(extension_summary.get("target_signal_count") or 0)
            >= int(expectations.get("min_target_surface_signals") or 0),
            "Target-language ruby pages produced reading-aware target signals.",
        ),
        _check(
            "native_host_ingest_succeeds_without_srs_mutation",
            bool(ingest_responses)
            and all(response.get("status") == "ok" for response in ingest_responses)
            and all(response.get("runtime_srs_mutation") is False for response in ingest_responses)
            and not srs_store_exists,
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
        if min_key not in required:
            continue
        checks.append(
            _check(
                f"aggregate_{field}_min:{target}",
                float(row.get(field) or 0) >= float(required.get(min_key) or 0),
                f"`{target}` has {field} >= {required.get(min_key)}.",
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


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# SRS Browsing Admission Offline Page Mining",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Scope: `{report.get('scope', '')}`",
        f"- Config: `{report.get('config_path', '')}`",
        f"- Live user data touched: `{report.get('live_user_data_touched')}`",
        "",
    ]
    for case in _list_of_mappings(report.get("cases")):
        lines.extend(render_case_markdown(case))
    return "\n".join(lines)


def render_case_markdown(case: Mapping[str, object]) -> list[str]:
    lines = [
        f"## {case.get('name')}",
        "",
        f"- Status: `{case.get('status')}`",
        f"- Pair: `{case.get('pair')}`",
        f"- Profile: `{case.get('profile_id')}`",
        "",
        "### Checks",
        "",
    ]
    for check in _list_of_mappings(case.get("checks")):
        lines.append(f"- `{check.get('status')}` `{check.get('name')}`: {check.get('detail')}")
    lines.extend(["", "### Documents", ""])
    lines.extend(
        [
            "| document | side | text chars | ruby pairs | sha256 |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for document in _list_of_mappings(case.get("documents")):
        lines.append(
            "| "
            f"`{document.get('document_id')}` | "
            f"`{document.get('side')}` | "
            f"{document.get('visible_text_char_count')} | "
            f"{document.get('ruby_pair_count')} | "
            f"`{str(document.get('sha256') or '')[:12]}` |"
        )
    lines.extend(["", "### Extension Signals", ""])
    extension = _as_mapping(case.get("extension_payload"))
    lines.extend(
        [
            f"- Packet count: `{extension.get('packet_count')}`",
            f"- Signal count: `{extension.get('signal_count')}`",
            f"- Source signal count: `{extension.get('source_signal_count')}`",
            f"- Target signal count: `{extension.get('target_signal_count')}`",
            "",
            "| target | side | source | count | confidence | context |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in _list_of_mappings(extension.get("signals")):
        lines.append(
            "| "
            f"`{row.get('target_key')}` | "
            f"`{row.get('side')}` | "
            f"`{row.get('observation_source')}` | "
            f"{row.get('count')} | "
            f"{row.get('source_mapping_confidence')} | "
            f"`{row.get('context_key_prefix')}` |"
        )
    lines.extend(["", "### Aggregate Store", ""])
    lines.extend(
        [
            "| target | reading | source | target | contexts | evidence | signal | sources |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    store = _as_mapping(case.get("aggregate_store"))
    for row in _list_of_mappings(store.get("items")):
        lines.append(
            "| "
            f"`{row.get('target_lemma')}` | "
            f"`{row.get('target_reading') or ''}` | "
            f"{row.get('source_hit_count')} | "
            f"{row.get('target_hit_count')} | "
            f"{row.get('browsing_context_count')} | "
            f"{row.get('browsing_evidence')} | "
            f"{row.get('browsing_signal')} | "
            f"`{', '.join(map(str, row.get('observation_sources') or []))}` |"
        )
    lines.append("")
    return lines


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


def _normalize_ruby_pair(surface: str, reading: str) -> dict[str, str] | None:
    clean_surface = re.sub(r"\s+", "", surface or "").strip()
    clean_reading = re.sub(r"\s+", "", reading or "").strip()
    if not clean_surface or not clean_reading:
        return None
    return {"surface": clean_surface, "reading": clean_reading}


def _collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


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
