#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.frequency.sqlite_store import SqliteFrequencyConfig, SqliteFrequencyStore  # noqa: E402
from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_frequency_db_path,
    default_jmdict_path,
    resolve_pair_capability,
)
from lexishift_core.helper.pair_resources import resolve_stopwords_path  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths, resolve_data_root  # noqa: E402
from lexishift_core.pos.normalization import normalize_pos  # noqa: E402
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402


CANONICAL_POS_ORDER = (
    "noun",
    "adjective",
    "verb",
    "adverb",
    "pronoun",
    "determiner",
    "adposition",
    "conjunction",
    "interjection",
    "numeral",
    "punctuation",
    "other",
)


@dataclass(frozen=True)
class CanonicalPosResult:
    canonical: str
    mapped: bool
    rule: str


def _target_language(pair: str) -> str:
    parts = str(pair or "").strip().lower().split("-", 1)
    if len(parts) != 2:
        return ""
    return parts[1]


def _canonical_bucket(canonical: str) -> str:
    if canonical in {"noun", "adjective", "verb", "adverb"}:
        return canonical
    return "other"


def _split_tokens(value: str) -> list[str]:
    return [token for token in re.split(r"[\s:|+_/\-,.;]+", value) if token]


def _infer_canonical_pos(raw_pos: str | None, *, pair: str) -> CanonicalPosResult:
    raw = str(raw_pos or "").strip()
    normalized = normalize_pos(
        raw,
        language_pair=pair,
        source_kind="frequency",
    )
    return CanonicalPosResult(
        canonical=normalized.canonical,
        mapped=bool(normalized.mapped),
        rule=normalized.matched_rule,
    )


def _infer_ja_canonical_pos(raw: str) -> CanonicalPosResult:
    head = raw.split("-", 1)[0].strip()
    if "数詞" in raw:
        return CanonicalPosResult(canonical="numeral", mapped=True, rule="ja_contains_numeric")
    mapping = {
        "名詞": "noun",
        "代名詞": "pronoun",
        "形容詞": "adjective",
        "形状詞": "adjective",
        "連体詞": "determiner",
        "動詞": "verb",
        "助動詞": "verb",
        "副詞": "adverb",
        "助詞": "adposition",
        "接続詞": "conjunction",
        "感動詞": "interjection",
        "記号": "punctuation",
        "補助記号": "punctuation",
    }
    canonical = mapping.get(head)
    if canonical:
        return CanonicalPosResult(canonical=canonical, mapped=True, rule=f"ja_head:{head}")
    return CanonicalPosResult(canonical="other", mapped=False, rule=f"ja_unmapped:{head or raw}")


def _infer_de_canonical_pos(raw: str) -> CanonicalPosResult:
    upper = raw.upper()
    tokens = set(_split_tokens(upper))
    if "SUB" in tokens or "NOUN" in tokens or "NOMEN" in tokens or "NN" in tokens:
        return CanonicalPosResult(canonical="noun", mapped=True, rule="de_token:noun")
    if (
        "ADJ" in tokens
        or "ADJA" in tokens
        or "ADJD" in tokens
        or any(token.startswith("ADJ") for token in tokens)
    ):
        return CanonicalPosResult(canonical="adjective", mapped=True, rule="de_token:adj")
    if (
        "VER" in tokens
        or "VERB" in tokens
        or any(token.startswith("VV") for token in tokens)
        or any(token.startswith("VA") for token in tokens)
        or any(token.startswith("VM") for token in tokens)
    ):
        return CanonicalPosResult(canonical="verb", mapped=True, rule="de_token:verb")
    if "ADV" in tokens:
        return CanonicalPosResult(canonical="adverb", mapped=True, rule="de_token:adv")
    if "ART" in tokens or "DET" in tokens:
        return CanonicalPosResult(canonical="determiner", mapped=True, rule="de_token:det")
    if "PRO" in tokens or any(token.startswith("P") and len(token) <= 5 for token in tokens):
        return CanonicalPosResult(canonical="pronoun", mapped=True, rule="de_token:pron")
    if (
        "APPR" in tokens
        or "APPO" in tokens
        or "APZR" in tokens
        or "PRP" in tokens
        or "PREP" in tokens
    ):
        return CanonicalPosResult(canonical="adposition", mapped=True, rule="de_token:adp")
    if "KON" in tokens or "KOUS" in tokens or "KOUI" in tokens or "CONJ" in tokens:
        return CanonicalPosResult(canonical="conjunction", mapped=True, rule="de_token:conj")
    if "ITJ" in tokens or "INTJ" in tokens:
        return CanonicalPosResult(canonical="interjection", mapped=True, rule="de_token:intj")
    if "CARD" in tokens or "NUM" in tokens:
        return CanonicalPosResult(canonical="numeral", mapped=True, rule="de_token:num")
    if "PUNCT" in tokens or "$." in raw or "$," in raw:
        return CanonicalPosResult(canonical="punctuation", mapped=True, rule="de_token:punct")
    return CanonicalPosResult(canonical="other", mapped=False, rule=f"de_unmapped:{raw}")


def _infer_compact_latin_canonical_pos(raw: str) -> CanonicalPosResult:
    tokens = _split_tokens(raw.lower())
    token = tokens[0] if tokens else raw.lower()
    one_char_map = {
        "n": "noun",
        "j": "adjective",
        "a": "adjective",
        "v": "verb",
        "r": "adverb",
        "p": "pronoun",
        "d": "determiner",
        "l": "determiner",
        "e": "adposition",
        "c": "conjunction",
        "i": "interjection",
        "m": "numeral",
        "-": "punctuation",
    }
    if token in one_char_map:
        return CanonicalPosResult(
            canonical=one_char_map[token],
            mapped=True,
            rule=f"latin_compact:{token}",
        )

    penn_map = {
        "nn": "noun",
        "nns": "noun",
        "nnp": "noun",
        "nnps": "noun",
        "jj": "adjective",
        "jjr": "adjective",
        "jjs": "adjective",
        "vb": "verb",
        "vbd": "verb",
        "vbg": "verb",
        "vbn": "verb",
        "vbp": "verb",
        "vbz": "verb",
        "rb": "adverb",
        "rbr": "adverb",
        "rbs": "adverb",
        "prp": "pronoun",
        "prp$": "pronoun",
        "dt": "determiner",
        "in": "adposition",
        "cc": "conjunction",
        "uh": "interjection",
        "cd": "numeral",
    }
    if token in penn_map:
        return CanonicalPosResult(canonical=penn_map[token], mapped=True, rule=f"penn:{token}")

    return CanonicalPosResult(canonical="other", mapped=False, rule=f"latin_unmapped:{token}")


def _infer_generic_canonical_pos(raw: str) -> CanonicalPosResult:
    lowered = raw.lower()
    checks: tuple[tuple[str, str], ...] = (
        ("noun", "noun"),
        ("adj", "adjective"),
        ("verb", "verb"),
        ("adv", "adverb"),
        ("pron", "pronoun"),
        ("det", "determiner"),
        ("adp", "adposition"),
        ("prep", "adposition"),
        ("conj", "conjunction"),
        ("intj", "interjection"),
        ("interj", "interjection"),
        ("num", "numeral"),
        ("punct", "punctuation"),
    )
    for needle, canonical in checks:
        if needle in lowered:
            return CanonicalPosResult(canonical=canonical, mapped=True, rule=f"generic:{needle}")
    return CanonicalPosResult(canonical="other", mapped=False, rule=f"generic_unmapped:{raw}")


def _counter_to_rows(counter: Counter[str], *, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        rows.append({"value": value, "count": int(count)})
        if limit is not None and len(rows) >= limit:
            break
    return rows


def _load_settings_maps(settings_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    if not settings_path.exists():
        return {}, {}
    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}, {}
    synonyms = payload.get("synonyms")
    if not isinstance(synonyms, dict):
        return {}, {}
    language_packs = synonyms.get("language_packs")
    frequency_packs = synonyms.get("frequency_packs")
    return (
        dict(language_packs) if isinstance(language_packs, dict) else {},
        dict(frequency_packs) if isinstance(frequency_packs, dict) else {},
    )


def _resolve_frequency_db_for_pair(
    pair: str,
    *,
    frequency_packs_dir: Path,
    settings_frequency_packs: dict[str, str],
) -> tuple[Path | None, str]:
    default_db_path = default_frequency_db_path(pair, frequency_packs_dir=frequency_packs_dir)
    if default_db_path is None:
        return None, "no_default_declared"
    default_name = default_db_path.name
    lookup_keys: list[str] = []
    if default_name.endswith(".sqlite"):
        lookup_keys.append(default_name[: -len(".sqlite")])
    lookup_keys.append(default_name)

    for key in lookup_keys:
        raw_path = str(settings_frequency_packs.get(key, "")).strip()
        if not raw_path:
            continue
        candidate = Path(raw_path).expanduser().resolve(strict=False)
        if candidate.is_file():
            return candidate, f"linked:{key}"
        if candidate.is_dir():
            nested = candidate / default_name
            if nested.is_file():
                return nested, f"linked_dir:{key}"

    fallback = default_db_path.expanduser().resolve(strict=False)
    if fallback.is_file():
        return fallback, "fallback_default"
    return None, "missing"


def _resolve_jmdict_for_pair(
    pair: str,
    *,
    language_packs_dir: Path,
    settings_language_packs: dict[str, str],
) -> Path | None:
    default_jmdict = default_jmdict_path(pair, language_packs_dir=language_packs_dir)
    if default_jmdict is None:
        return None
    lookup_keys = ("jmdict-ja-en", default_jmdict.name)
    for key in lookup_keys:
        raw_path = str(settings_language_packs.get(key, "")).strip()
        if not raw_path:
            continue
        candidate = Path(raw_path).expanduser().resolve(strict=False)
        if candidate.is_file():
            return candidate
        if candidate.is_dir():
            nested = candidate / default_jmdict.name
            if nested.is_file():
                return nested
    if default_jmdict.is_file():
        return default_jmdict
    return None


def _build_source_pack_probe(
    *,
    db_path: Path,
    top_n: int,
    sample_limit: int,
) -> dict[str, Any]:
    raw_counter: Counter[str] = Counter()
    sample_lemmas: dict[str, list[str]] = defaultdict(list)
    with SqliteFrequencyStore(SqliteFrequencyConfig(path=db_path)) as store:
        columns = store.column_names()
        resolved_pos_column = store.resolve_column("pos", available_columns=columns)
        resolved_lemma_column = store.resolve_column("lemma", available_columns=columns)
        resolved_rank_column = store.resolve_rank_column(available_columns=columns)
        selected_columns = []
        if resolved_pos_column:
            selected_columns.append(resolved_pos_column)
        for row in store.iter_top_by_rank(
            limit=top_n,
            rank_column=resolved_rank_column,
            pmw_column=None,
            columns=selected_columns,
        ):
            if resolved_pos_column and row[resolved_pos_column] is not None:
                raw_pos = str(row[resolved_pos_column]).strip() or "<EMPTY>"
            elif resolved_pos_column:
                raw_pos = "<EMPTY>"
            else:
                raw_pos = "<NO_POS_COLUMN>"
            raw_counter[raw_pos] += 1
            lemma = ""
            if resolved_lemma_column and row[resolved_lemma_column] is not None:
                lemma = str(row[resolved_lemma_column]).strip()
            if lemma and len(sample_lemmas[raw_pos]) < sample_limit:
                sample_lemmas[raw_pos].append(lemma)
    return {
        "path": str(db_path),
        "top_n": int(top_n),
        "raw_tag_distribution": _counter_to_rows(raw_counter),
        "raw_tag_examples": {
            key: sample_lemmas[key]
            for key, _count in sorted(raw_counter.items(), key=lambda item: (-item[1], item[0]))
            if key in sample_lemmas
        },
    }


def _seed_example(
    seed: Any, *, raw_pos: str, canonical_pos: str, expected_bucket: str
) -> dict[str, Any]:
    return {
        "lemma": str(seed.lemma),
        "raw_pos": raw_pos,
        "canonical_pos": canonical_pos,
        "expected_bucket": expected_bucket,
        "runtime_bucket": str(seed.pos_bucket),
        "core_rank": seed.core_rank,
        "pmw": seed.pmw,
    }


def _build_pair_probe(
    *,
    pair: str,
    top_n: int,
    sample_limit: int,
    paths: Any,
    settings_language_packs: dict[str, str],
    settings_frequency_packs: dict[str, str],
) -> dict[str, Any]:
    capability = resolve_pair_capability(pair)
    frequency_path, frequency_resolution = _resolve_frequency_db_for_pair(
        pair,
        frequency_packs_dir=paths.frequency_packs_dir,
        settings_frequency_packs=settings_frequency_packs,
    )
    stopwords_path = resolve_stopwords_path(paths, pair=pair)
    require_jmdict = bool(capability.requires_jmdict_for_seed)
    jmdict_path = None
    if require_jmdict:
        jmdict_path = _resolve_jmdict_for_pair(
            pair,
            language_packs_dir=paths.language_packs_dir,
            settings_language_packs=settings_language_packs,
        )

    pair_payload: dict[str, Any] = {
        "pair": pair,
        "srs_selectable": bool(capability.srs_selectable),
        "status": "ok",
        "top_n": int(top_n),
        "frequency_db_path": str(frequency_path) if frequency_path else None,
        "frequency_resolution": frequency_resolution,
        "require_jmdict": require_jmdict,
        "jmdict_path": str(jmdict_path) if jmdict_path else None,
        "stopwords_path": str(stopwords_path) if stopwords_path else None,
    }

    if frequency_path is None:
        pair_payload["status"] = "missing_frequency_db"
        pair_payload["error"] = "Could not resolve frequency DB for pair."
        return pair_payload
    if require_jmdict and jmdict_path is None:
        pair_payload["status"] = "missing_jmdict"
        pair_payload["error"] = "JMDict is required for this pair but could not be resolved."
        return pair_payload

    seed_config = SeedSelectionConfig(
        language_pair=pair,
        top_n=top_n,
        require_jmdict=require_jmdict,
        jmdict_path=jmdict_path,
        stopwords_path=stopwords_path,
    )
    try:
        seeds = build_seed_candidates(frequency_db=frequency_path, config=seed_config)
    except Exception as exc:  # noqa: BLE001
        pair_payload["status"] = "seed_error"
        pair_payload["error"] = str(exc)
        return pair_payload

    raw_counter: Counter[str] = Counter()
    canonical_counter: Counter[str] = Counter()
    bucket_counter: Counter[str] = Counter()
    expected_bucket_counter: Counter[str] = Counter()
    unknown_counter: Counter[str] = Counter()
    mapping_rule_counter: Counter[str] = Counter()
    mismatch_counter: Counter[str] = Counter()
    samples_by_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    samples_by_canonical: dict[str, list[dict[str, Any]]] = defaultdict(list)
    mismatch_examples: list[dict[str, Any]] = []
    unknown_examples: list[dict[str, Any]] = []

    for seed in seeds:
        raw_pos = str(seed.pos or "").strip() or "<EMPTY>"
        raw_counter[raw_pos] += 1
        inferred = _infer_canonical_pos(seed.pos, pair=pair)
        mapping_rule_counter[inferred.rule] += 1
        canonical_counter[inferred.canonical] += 1
        runtime_bucket = str(seed.pos_bucket or "other")
        bucket_counter[runtime_bucket] += 1
        expected_bucket = _canonical_bucket(inferred.canonical)
        expected_bucket_counter[expected_bucket] += 1

        example = _seed_example(
            seed,
            raw_pos=raw_pos,
            canonical_pos=inferred.canonical,
            expected_bucket=expected_bucket,
        )
        if len(samples_by_bucket[runtime_bucket]) < sample_limit:
            samples_by_bucket[runtime_bucket].append(example)
        if len(samples_by_canonical[inferred.canonical]) < sample_limit:
            samples_by_canonical[inferred.canonical].append(example)

        if not inferred.mapped and raw_pos != "<EMPTY>":
            unknown_counter[raw_pos] += 1
            if len(unknown_examples) < sample_limit:
                unknown_examples.append(example)

        if runtime_bucket != expected_bucket:
            mismatch_key = f"{expected_bucket} -> {runtime_bucket}"
            mismatch_counter[mismatch_key] += 1
            if len(mismatch_examples) < sample_limit:
                mismatch_examples.append(example)

    seed_count = len(seeds)
    mapped_seed_count = seed_count - sum(unknown_counter.values())
    pair_payload.update(
        {
            "seed_count": seed_count,
            "pos_nonempty_count": seed_count - int(raw_counter.get("<EMPTY>", 0)),
            "raw_tag_distribution": _counter_to_rows(raw_counter),
            "canonical_distribution": [
                {"value": tag, "count": int(canonical_counter.get(tag, 0))}
                for tag in CANONICAL_POS_ORDER
                if canonical_counter.get(tag, 0) > 0
            ],
            "runtime_bucket_distribution": _counter_to_rows(bucket_counter),
            "expected_bucket_distribution_from_canonical": _counter_to_rows(
                expected_bucket_counter
            ),
            "mapping_rule_distribution": _counter_to_rows(mapping_rule_counter, limit=20),
            "unmapped_raw_tags": _counter_to_rows(unknown_counter),
            "bucket_mismatch_distribution": _counter_to_rows(mismatch_counter),
            "bucket_mismatch_count": int(sum(mismatch_counter.values())),
            "bucket_mismatch_rate": (
                float(sum(mismatch_counter.values())) / float(seed_count) if seed_count else 0.0
            ),
            "mapped_seed_count": int(mapped_seed_count),
            "mapped_seed_rate": float(mapped_seed_count) / float(seed_count) if seed_count else 0.0,
            "samples_by_runtime_bucket": dict(samples_by_bucket),
            "samples_by_canonical": dict(samples_by_canonical),
            "bucket_mismatch_examples": mismatch_examples,
            "unmapped_examples": unknown_examples,
        }
    )
    return pair_payload


def _render_summary_text(report: dict[str, Any]) -> str:
    lines = [
        "LexiShift POS Normalization Baseline Probe",
        f"- generated_at_utc: {report['generated_at_utc']}",
        f"- data_root: {report['data_root']}",
        f"- pairs: {', '.join(report['pairs'])}",
        f"- top_n: {report['top_n']}",
        "",
    ]

    headers = (
        "pair",
        "status",
        "seeds",
        "nonempty_pos",
        "mapped_rate",
        "bucket_mismatch_rate",
        "frequency_db",
    )
    rows: list[tuple[str, ...]] = []
    for pair in report["pairs"]:
        payload = report["pair_reports"].get(pair, {})
        frequency_name = "-"
        frequency_path = payload.get("frequency_db_path")
        if isinstance(frequency_path, str) and frequency_path:
            frequency_name = Path(frequency_path).name
        rows.append(
            (
                pair,
                str(payload.get("status", "missing")),
                str(payload.get("seed_count", "-")),
                str(payload.get("pos_nonempty_count", "-")),
                f"{float(payload.get('mapped_seed_rate', 0.0)):.3f}",
                f"{float(payload.get('bucket_mismatch_rate', 0.0)):.3f}",
                frequency_name,
            )
        )

    widths = [len(item) for item in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    header_line = " | ".join(headers[index].ljust(widths[index]) for index in range(len(headers)))
    separator = "-+-".join("-" * widths[index] for index in range(len(headers)))
    lines.append(header_line)
    lines.append(separator)
    for row in rows:
        lines.append(" | ".join(row[index].ljust(widths[index]) for index in range(len(headers))))
    return "\n".join(lines)


def _build_report(
    *,
    pairs: list[str],
    top_n: int,
    sample_limit: int,
    data_root: Path,
) -> dict[str, Any]:
    paths = build_helper_paths(root=data_root)
    settings_language_packs, settings_frequency_packs = _load_settings_maps(paths.app_settings_path)
    pair_reports: dict[str, dict[str, Any]] = {}
    source_pack_reports: dict[str, dict[str, Any]] = {}
    used_frequency_paths: set[Path] = set()

    for pair in pairs:
        payload = _build_pair_probe(
            pair=pair,
            top_n=top_n,
            sample_limit=sample_limit,
            paths=paths,
            settings_language_packs=settings_language_packs,
            settings_frequency_packs=settings_frequency_packs,
        )
        pair_reports[pair] = payload
        frequency_path = payload.get("frequency_db_path")
        if isinstance(frequency_path, str) and frequency_path:
            used_frequency_paths.add(Path(frequency_path).expanduser().resolve(strict=False))

    for frequency_path in sorted(used_frequency_paths):
        if not frequency_path.is_file():
            continue
        source_pack_reports[frequency_path.name] = _build_source_pack_probe(
            db_path=frequency_path,
            top_n=top_n,
            sample_limit=sample_limit,
        )

    errors = [
        {
            "pair": pair,
            "status": payload.get("status"),
            "error": payload.get("error"),
        }
        for pair, payload in pair_reports.items()
        if payload.get("status") != "ok"
    ]
    report = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_root": str(data_root),
        "pairs": pairs,
        "top_n": int(top_n),
        "sample_limit": int(sample_limit),
        "pair_reports": pair_reports,
        "source_pack_reports": source_pack_reports,
        "errors": errors,
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 0 POS baseline probe. Reports raw POS by source pack, inferred canonical POS "
            "distribution, and runtime admission bucket distribution by pair."
        )
    )
    parser.add_argument(
        "--pairs",
        default="en-ja,en-es,es-en,en-de",
        help="Comma-separated language pairs to probe.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=2000,
        help="Top-N frequency rows to probe for each pair.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=5,
        help="How many representative samples to keep per bucket/tag.",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        help="LexiShift data root override (default uses platform path / LEXISHIFT_DATA_DIR).",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional path for JSON output artifact.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any pair has non-ok status or any mismatch rate > 0.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pairs = [item.strip() for item in str(args.pairs).split(",") if item.strip()]
    if not pairs:
        print("No pairs provided.")
        return 1
    data_root = (args.data_root or resolve_data_root()).expanduser().resolve(strict=False)
    report = _build_report(
        pairs=pairs,
        top_n=max(1, int(args.top_n)),
        sample_limit=max(1, int(args.sample_limit)),
        data_root=data_root,
    )

    print(_render_summary_text(report))

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\nWrote JSON report: {args.json_out}")

    has_errors = bool(report.get("errors"))
    has_mismatch = any(
        float(report["pair_reports"][pair].get("bucket_mismatch_rate", 0.0)) > 0.0
        for pair in pairs
        if pair in report["pair_reports"] and report["pair_reports"][pair].get("status") == "ok"
    )
    if has_errors:
        return 1
    if args.strict and has_mismatch:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
