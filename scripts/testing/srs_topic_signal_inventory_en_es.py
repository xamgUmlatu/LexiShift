#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import types
from typing import Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
FREQUENCY_VALUE_COLUMNS = (
    "pmw",
    "core_pmw",
    "frequency",
    "core_frequency",
    "freq",
    "freq_per_million",
    "count",
    "ipm",
)
RANK_COLUMNS = ("core_rank", "rank", "id", "index")


def _load_admission_features_module() -> object:
    core_pkg_root = CORE_ROOT / "lexishift_core"
    srs_root = core_pkg_root / "srs"
    lexishift_core_pkg = sys.modules.get("lexishift_core")
    if lexishift_core_pkg is None:
        lexishift_core_pkg = types.ModuleType("lexishift_core")
        lexishift_core_pkg.__path__ = [str(core_pkg_root)]  # type: ignore[attr-defined]
        sys.modules["lexishift_core"] = lexishift_core_pkg
    srs_pkg = sys.modules.get("lexishift_core.srs")
    if srs_pkg is None:
        srs_pkg = types.ModuleType("lexishift_core.srs")
        srs_pkg.__path__ = [str(srs_root)]  # type: ignore[attr-defined]
        sys.modules["lexishift_core.srs"] = srs_pkg
    full_name = "lexishift_core.srs.admission_features"
    if full_name in sys.modules:
        return sys.modules[full_name]
    module_path = srs_root / "admission_features.py"
    spec = importlib.util.spec_from_file_location(full_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec for {full_name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    setattr(srs_pkg, "admission_features", module)
    spec.loader.exec_module(module)
    return module


_ADMISSION_FEATURES = _load_admission_features_module()
normalize_topic_string_list = _ADMISSION_FEATURES.normalize_topic_string_list
normalize_topic_string_list_with_origins = (
    _ADMISSION_FEATURES.normalize_topic_string_list_with_origins
)


DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_KAIKKI_FORWARD_DB = DEFAULT_DATA_ROOT / "language_packs" / "wiktionary-es-en.sqlite"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_topic_signal_inventory_en_es_current_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_topic_signal_inventory_en_es_current_latest.md"
)
DEFAULT_TOP_N = 10000
TOPIC_CHANNELS = (
    "sense_topics",
    "sense_tags",
    "sense_categories",
    "entry_tags",
    "entry_categories",
)
TRUSTED_PROFILE_CHANNELS = ("sense_topics",)
REVIEW_ONLY_CHANNELS = (
    "sense_tags",
    "sense_categories",
    "entry_tags",
    "entry_categories",
)
PRODUCT_TOPIC_EXAMPLES = (
    "medicine",
    "health",
    "finance",
    "business",
    "sports",
    "games",
    "music",
    "literature",
    "psychology",
    "education",
    "law",
    "politics",
    "technology",
    "computing",
    "science",
    "travel",
    "food",
    "emotions",
)
EXAM_PREFERENCES_REQUIRING_SOURCE_REVIEW = ("sat", "toefl")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory installed en-es topic/tag/category signals that could enrich SRS "
            "candidate packs. This is read-only and does not write overlays."
        )
    )
    parser.add_argument(
        "--frequency-db",
        action="append",
        required=True,
        help="Candidate SQLite path, optionally prefixed as label=/path/to/db.sqlite.",
    )
    parser.add_argument("--kaikki-forward-db", type=Path, default=DEFAULT_KAIKKI_FORWARD_DB)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    candidates = [_parse_candidate_arg(value) for value in args.frequency_db]
    report = build_report(
        candidates=candidates,
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
    candidates: Sequence[tuple[str, Path]],
    kaikki_forward_db: Path = DEFAULT_KAIKKI_FORWARD_DB,
    top_n: int = DEFAULT_TOP_N,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    signal_index = load_kaikki_topic_signal_index(kaikki_forward_db)
    audits = [
        audit_candidate_pack(
            label=label,
            frequency_db=path,
            signal_index=signal_index,
            top_n=top_n,
        )
        for label, path in candidates
    ]
    findings = _build_findings(audits=audits, signal_index=signal_index)
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_topic_signal_inventory_completed"
            if status == "ok"
            else "srs_topic_signal_inventory_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "kaikki_forward_db": str(Path(kaikki_forward_db).expanduser().resolve(strict=False)),
            "frequency_dbs": [
                {"label": label, "path": str(path.expanduser().resolve(strict=False))}
                for label, path in candidates
            ],
            "top_n": int(top_n),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "helper_state_mutation": "none",
            "overlay_write": "none",
            "trusted_profile_channels": list(TRUSTED_PROFILE_CHANNELS),
            "review_only_channels": list(REVIEW_ONLY_CHANNELS),
            "channel_policy": (
                "sense_topics are treated as the first trusted profile-lift signal. "
                "tags and categories are inventoried because they are available, but "
                "remain review-only due to grammar, maintenance, region, register, "
                "and Wiktionary housekeeping noise."
            ),
        },
        "signal_index": {
            key: value for key, value in signal_index.items() if not key.startswith("_")
        },
        "audits": audits,
        "findings": findings,
        "summary": _summary(audits, findings),
        "planned_preferences": {
            "product_topic_examples": list(PRODUCT_TOPIC_EXAMPLES),
            "exam_preferences_requiring_source_review": list(
                EXAM_PREFERENCES_REQUIRING_SOURCE_REVIEW
            ),
            "exam_preference_policy": (
                "SAT and TOEFL should be preference families only after a legal "
                "source decision identifies allowed vocabulary/skill data. They are "
                "not inferred from current Wiktionary topic labels."
            ),
        },
        "limitations": [
            "This audit inventories available signals only; it does not create a normalized topic overlay.",
            "Kaikki categories are broad and noisy, so they should not be promoted into profile topics without allowlist mapping and sample review.",
            "SAT and TOEFL preferences need legally allowed exam-prep source data or an internally defined skill taxonomy before product use.",
            "Counts depend on the installed local Kaikki/Wiktionary pack and should be refreshed when that resource changes.",
        ],
    }


def audit_candidate_pack(
    *,
    label: str,
    frequency_db: Path,
    signal_index: Mapping[str, object],
    top_n: int,
) -> dict[str, object]:
    resolved = Path(frequency_db).expanduser().resolve(strict=False)
    if not resolved.exists():
        return {
            "label": label,
            "frequency_db": str(resolved),
            "exists": False,
            "row_count": 0,
            "unique_lemma_count": 0,
            "channel_coverage": {},
            "combined_coverage": {},
            "top_trusted_topics": [],
            "top_available_review_topics": [],
            "product_topic_examples": [],
        }
    lemmas = _candidate_lemmas(resolved, top_n=top_n)
    unique_lemmas = list(dict.fromkeys(lemmas))
    by_channel = _as_mapping(signal_index.get("_by_channel"))
    channel_coverage: dict[str, object] = {}
    trusted_counter: Counter[str] = Counter()
    review_counter: Counter[str] = Counter()
    trusted_lemmas: set[str] = set()
    review_lemmas: set[str] = set()
    for channel in TOPIC_CHANNELS:
        lemma_signals = _as_mapping(by_channel.get(channel))
        row_count = 0
        canonical_counter: Counter[str] = Counter()
        sample_rows: list[dict[str, object]] = []
        for lemma in unique_lemmas:
            signals = _string_list(lemma_signals.get(lemma))
            if not signals:
                continue
            row_count += 1
            expanded = _expanded_topic_values(signals)
            canonical_counter.update(expanded)
            if channel in TRUSTED_PROFILE_CHANNELS:
                trusted_lemmas.add(lemma)
                trusted_counter.update(expanded)
            else:
                review_lemmas.add(lemma)
                review_counter.update(expanded)
            if len(sample_rows) < 10:
                sample_rows.append(
                    {
                        "lemma": lemma,
                        "raw": signals[:12],
                        "canonical": expanded[:12],
                    }
                )
        channel_coverage[channel] = {
            "row_count": row_count,
            "row_share": _ratio(row_count, len(unique_lemmas)),
            "distinct_canonical_topic_count": len(canonical_counter),
            "top_canonical_topics": _counter_rows(canonical_counter, limit=20),
            "sample_rows": sample_rows,
            "profile_policy": (
                "trusted_profile_signal"
                if channel in TRUSTED_PROFILE_CHANNELS
                else "review_only_inventory_signal"
            ),
        }
    combined_available_lemmas = trusted_lemmas | review_lemmas
    product_examples = [
        {
            "topic": topic,
            "trusted_count": trusted_counter.get(topic, 0),
            "review_only_count": review_counter.get(topic, 0),
        }
        for topic in PRODUCT_TOPIC_EXAMPLES
        if trusted_counter.get(topic, 0) or review_counter.get(topic, 0)
    ]
    return {
        "label": label,
        "frequency_db": str(resolved),
        "exists": True,
        "row_count": len(lemmas),
        "unique_lemma_count": len(unique_lemmas),
        "channel_coverage": channel_coverage,
        "combined_coverage": {
            "trusted_profile_row_count": len(trusted_lemmas),
            "trusted_profile_row_share": _ratio(len(trusted_lemmas), len(unique_lemmas)),
            "review_only_signal_row_count": len(review_lemmas),
            "review_only_signal_row_share": _ratio(len(review_lemmas), len(unique_lemmas)),
            "any_available_signal_row_count": len(combined_available_lemmas),
            "any_available_signal_row_share": _ratio(
                len(combined_available_lemmas), len(unique_lemmas)
            ),
        },
        "top_trusted_topics": _counter_rows(trusted_counter, limit=30),
        "top_available_review_topics": _counter_rows(review_counter, limit=30),
        "product_topic_examples": product_examples,
    }


def load_kaikki_topic_signal_index(path: Path) -> dict[str, object]:
    resolved = Path(path).expanduser().resolve(strict=False)
    base: dict[str, object] = {
        "path": str(resolved),
        "exists": resolved.exists(),
        "channel_row_counts": {},
        "channel_lemma_counts": {},
        "channel_top_raw": {},
        "channel_top_canonical": {},
        "_by_channel": {channel: defaultdict(set) for channel in TOPIC_CHANNELS},
    }
    if not resolved.exists():
        return base
    by_channel = _as_mapping(base["_by_channel"])
    with sqlite3.connect(resolved) as conn:
        for lemma, tags_json, categories_json in conn.execute(
            "SELECT headword_lc, tags_json, categories_json FROM entry_meta"
        ):
            normalized = _normalize_lemma(lemma)
            if not normalized:
                continue
            _add_values(by_channel["entry_tags"], normalized, _json_string_list(tags_json))
            _add_values(
                by_channel["entry_categories"],
                normalized,
                _json_string_list(categories_json),
            )
        for lemma, topics_json, tags_json, categories_json in conn.execute(
            "SELECT headword_lc, topics_json, tags_json, categories_json FROM sense_glosses"
        ):
            normalized = _normalize_lemma(lemma)
            if not normalized:
                continue
            _add_values(by_channel["sense_topics"], normalized, _json_string_list(topics_json))
            _add_values(by_channel["sense_tags"], normalized, _json_string_list(tags_json))
            _add_values(
                by_channel["sense_categories"],
                normalized,
                _json_string_list(categories_json),
            )
    channel_row_counts: dict[str, int] = {}
    channel_lemma_counts: dict[str, int] = {}
    channel_top_raw: dict[str, list[dict[str, object]]] = {}
    channel_top_canonical: dict[str, list[dict[str, object]]] = {}
    for channel in TOPIC_CHANNELS:
        lemma_values = _as_mapping(by_channel[channel])
        raw_counter: Counter[str] = Counter()
        canonical_counter: Counter[str] = Counter()
        row_count = 0
        for values in lemma_values.values():
            signals = _string_list(values)
            if not signals:
                continue
            row_count += len(signals)
            raw_counter.update(signals)
            canonical_counter.update(_expanded_topic_values(signals))
        channel_row_counts[channel] = row_count
        channel_lemma_counts[channel] = sum(1 for values in lemma_values.values() if values)
        channel_top_raw[channel] = _counter_rows(raw_counter, limit=20)
        channel_top_canonical[channel] = _counter_rows(canonical_counter, limit=20)
    base.update(
        {
            "channel_row_counts": channel_row_counts,
            "channel_lemma_counts": channel_lemma_counts,
            "channel_top_raw": channel_top_raw,
            "channel_top_canonical": channel_top_canonical,
        }
    )
    return base


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es SRS Topic Signal Inventory",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Candidate packs: `{summary.get('candidate_pack_count', 0)}`",
        "",
        "## Scope",
        "",
        "This is a read-only inventory of topic/tag/category signals available for SRS enrichment. It does not write overlays, change SRS admission, or promote any new preference category.",
        "",
        "## Findings",
        "",
    ]
    for finding in report.get("findings", []):
        item = _as_mapping(finding)
        lines.append(
            f"- `{item.get('level', '')}` `{item.get('code', '')}`: {item.get('message', '')}"
        )
    lines.extend(["", "## Candidate Audits", ""])
    for audit in report.get("audits", []):
        item = _as_mapping(audit)
        lines.extend(
            [
                f"### `{item.get('label', '')}`",
                "",
                f"- exists: `{item.get('exists', False)}`",
                f"- rows: `{item.get('row_count', 0)}`",
                f"- unique lemmas: `{item.get('unique_lemma_count', 0)}`",
            ]
        )
        combined = _as_mapping(item.get("combined_coverage"))
        if combined:
            lines.extend(
                [
                    f"- trusted profile signal rows: `{combined.get('trusted_profile_row_count', 0)}` ({_pct(combined.get('trusted_profile_row_share'))})",
                    f"- review-only signal rows: `{combined.get('review_only_signal_row_count', 0)}` ({_pct(combined.get('review_only_signal_row_share'))})",
                    f"- any available signal rows: `{combined.get('any_available_signal_row_count', 0)}` ({_pct(combined.get('any_available_signal_row_share'))})",
                    "",
                    "#### Channel Coverage",
                    "",
                    _channel_table(item.get("channel_coverage")),
                    "",
                    "#### Top Trusted Topics",
                    "",
                    _topic_table(item.get("top_trusted_topics")),
                    "",
                    "#### Product Topic Examples",
                    "",
                    _product_topic_table(item.get("product_topic_examples")),
                    "",
                ]
            )
    planned = _as_mapping(report.get("planned_preferences"))
    lines.extend(
        [
            "## Planned Preference Families",
            "",
            f"- product topic examples: `{', '.join(planned.get('product_topic_examples', []))}`",
            f"- exam preferences requiring source/legal review: `{', '.join(planned.get('exam_preferences_requiring_source_review', []))}`",
            f"- exam policy: {planned.get('exam_preference_policy', '')}",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines) + "\n"


def _candidate_lemmas(path: Path, *, top_n: int) -> list[str]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        columns = _column_names(conn, "frequency")
        lemma_column = _resolve_column("lemma", columns)
        if not lemma_column:
            return []
        rank_column = _resolve_first_column(RANK_COLUMNS, columns)
        pmw_column = _resolve_first_column(FREQUENCY_VALUE_COLUMNS, columns)
        selected_columns = [lemma_column]
        if rank_column and rank_column not in selected_columns:
            selected_columns.append(rank_column)
        if pmw_column and pmw_column not in selected_columns:
            selected_columns.append(pmw_column)
        order_terms: list[str] = []
        if rank_column:
            order_terms.append(f"{_quote_identifier(rank_column)} IS NULL ASC")
            order_terms.append(f"{_quote_identifier(rank_column)} ASC")
        if pmw_column:
            order_terms.append(f"{_quote_identifier(pmw_column)} DESC")
        order_sql = f" ORDER BY {', '.join(order_terms)}" if order_terms else ""
        sql = (
            f"SELECT {', '.join(_quote_identifier(column) for column in selected_columns)} "
            f"FROM frequency{order_sql} LIMIT ?"
        )
        return [
            _normalize_lemma(row[lemma_column])
            for row in conn.execute(sql, (max(1, int(top_n)),))
            if _normalize_lemma(row[lemma_column])
        ]
    finally:
        conn.close()


def _column_names(conn: sqlite3.Connection, table_name: str) -> list[str]:
    return [str(row[1]) for row in conn.execute(f"PRAGMA table_info({table_name})")]


def _resolve_column(requested: str, columns: Sequence[str]) -> str | None:
    lowered = {column.lower(): column for column in columns}
    return lowered.get(str(requested).strip().lower())


def _resolve_first_column(candidates: Sequence[str], columns: Sequence[str]) -> str | None:
    for candidate in candidates:
        resolved = _resolve_column(candidate, columns)
        if resolved:
            return resolved
    return None


def _quote_identifier(value: object) -> str:
    return '"' + str(value).replace('"', '""') + '"'


def _build_findings(
    *, audits: Sequence[Mapping[str, object]], signal_index: Mapping[str, object]
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if signal_index.get("exists"):
        findings.append(
            _finding(
                "PASS", "kaikki_signal_source_available", "Kaikki/Wiktionary signal DB exists."
            )
        )
    else:
        findings.append(
            _finding(
                "FAIL", "kaikki_signal_source_missing", "Kaikki/Wiktionary signal DB is missing."
            )
        )
    for audit in audits:
        label = str(audit.get("label") or "candidate")
        if not audit.get("exists"):
            findings.append(
                _finding("FAIL", f"candidate_missing:{label}", "Candidate frequency DB is missing.")
            )
            continue
        combined = _as_mapping(audit.get("combined_coverage"))
        if int(combined.get("trusted_profile_row_count") or 0) > 0:
            findings.append(
                _finding(
                    "PASS",
                    f"trusted_topics_available:{label}",
                    "Explicit sense-topic rows can enrich this candidate pack.",
                )
            )
        else:
            findings.append(
                _finding(
                    "WARN",
                    f"trusted_topics_absent:{label}",
                    "No explicit sense-topic rows were found for this candidate pack.",
                )
            )
        if int(combined.get("review_only_signal_row_count") or 0) > int(
            combined.get("trusted_profile_row_count") or 0
        ):
            findings.append(
                _finding(
                    "PASS",
                    f"review_only_signals_expand_surface:{label}",
                    "Tags/categories expose more candidate rows, but require mapping before use.",
                )
            )
    return findings


def _summary(
    audits: Sequence[Mapping[str, object]], findings: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    return {
        "candidate_pack_count": len(audits),
        "finding_counts": dict(Counter(str(row.get("level") or "") for row in findings)),
        "issues": [row.get("code") for row in findings if row.get("level") == "FAIL"],
        "warnings": [row.get("code") for row in findings if row.get("level") == "WARN"],
    }


def _parse_candidate_arg(value: str) -> tuple[str, Path]:
    text = str(value or "").strip()
    if "=" in text:
        label, path_text = text.split("=", 1)
        return label.strip() or Path(path_text).stem, Path(path_text).expanduser()
    path = Path(text).expanduser()
    return path.stem, path


def _add_values(target: object, lemma: str, values: Iterable[str]) -> None:
    if not isinstance(target, defaultdict):
        return
    for value in values:
        normalized = str(value or "").strip()
        if normalized:
            target[lemma].add(normalized)


def _expanded_topic_values(values: object) -> list[str]:
    canonical, _origins = normalize_topic_string_list_with_origins(sorted(_string_list(values)))
    return canonical


def _json_string_list(value: object) -> list[str]:
    if value is None:
        return []
    text = str(value or "").strip()
    if not text or text == "[]":
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return normalize_topic_string_list(text)
    return normalize_topic_string_list(payload)


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, set):
        return sorted(str(item) for item in value if str(item).strip())
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return []


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _counter_rows(counter: Counter[str], *, limit: int) -> list[dict[str, object]]:
    return [
        {"topic": topic, "count": count} for topic, count in counter.most_common(max(1, int(limit)))
    ]


def _channel_table(value: object) -> str:
    channels = _as_mapping(value)
    lines = [
        "| Channel | Policy | Rows | Share | Distinct Topics | Top Topics |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for channel in TOPIC_CHANNELS:
        row = _as_mapping(channels.get(channel))
        top_topics = ", ".join(
            f"{item.get('topic')}={item.get('count')}"
            for item in _mapping_rows(row.get("top_canonical_topics"))[:5]
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{channel}`",
                    f"`{row.get('profile_policy', '')}`",
                    str(row.get("row_count", 0)),
                    _pct(row.get("row_share")),
                    str(row.get("distinct_canonical_topic_count", 0)),
                    top_topics or "none",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _topic_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "No trusted topics found."
    lines = ["| Topic | Count |", "| --- | ---: |"]
    for row in rows[:20]:
        lines.append(f"| `{row.get('topic', '')}` | {row.get('count', 0)} |")
    return "\n".join(lines)


def _product_topic_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "No configured product topic examples found in this candidate."
    lines = [
        "| Topic | Trusted Count | Review-Only Count |",
        "| --- | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{row.get('topic', '')}` | {row.get('trusted_count', 0)} | {row.get('review_only_count', 0)} |"
        )
    return "\n".join(lines)


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _normalize_lemma(value: object) -> str:
    return str(value or "").strip().casefold()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
