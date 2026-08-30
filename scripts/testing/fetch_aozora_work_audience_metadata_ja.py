#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
import urllib.request
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACK_ID = "freq-ja-aozora-word"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_aozora_work_audience_probe_en_ja_latest.json"
)
DEFAULT_PROVIDERS = (
    "aozora-card",
    "ndl",
    "wikipedia",
    "wikidata",
    "yozora",
    "bungo-kids",
)
BUNGO_KIDS_CATEGORIES = ("all", "flash", "shortshort", "short", "novelette", "novel")
USER_AGENT = "LexiShift research sidecar work-audience probe"
MAX_DEFAULT_WORKS = 50
ORTHOGRAPHY_VALUES = {"新字新仮名", "新字旧仮名", "旧字新仮名", "旧字旧仮名", "その他"}

JUVENILE_TERMS = (
    "児童",
    "童話",
    "童謡",
    "子供",
    "子ども",
    "こども",
    "少年",
    "少女",
    "小学生",
    "中学生",
    "幼年",
    "絵本",
    "えほん",
    "お伽",
    "おとぎ",
    "赤い鳥",
    "子供之友",
    "少年少女",
    "ヤングアダルト",
    "YA",
)
SCHOOL_TERMS = (
    "教科書",
    "学習",
    "国語",
    "小学校",
    "中学校",
    "高校",
    "学校図書",
)
WARNING_TERMS = (
    "R15",
    "R-15",
    "R18",
    "R-18",
    "成人",
    "アダルト",
    "性的",
    "暴力",
    "自殺",
    "差別",
    "不適切",
    "グロテスク",
    "残酷",
)
AOZORA_CARD_LABELS = (
    "作品名",
    "作品名読み",
    "著者名",
    "著者名読み",
    "分類",
    "初出",
    "作品について",
    "文字遣い種別",
    "備考",
    "底本",
    "出版社",
    "初版発行日",
    "底本の親本",
    "入力に使用",
    "校正に使用",
    "入力",
    "校正",
    "ファイル種別",
    "圧縮",
    "ファイル名",
    "文字集合",
    "サイズ",
    "初登録日",
    "最終更新日",
    "人物について",
    "生年",
    "没年",
)
SRU_USEFUL_FIELD_NAMES = {
    "title",
    "titleTranscription",
    "creator",
    "creatorTranscription",
    "publisher",
    "date",
    "issued",
    "seriesTitle",
    "subject",
    "description",
    "type",
    "identifier",
    "source",
    "relation",
    "audience",
}


@dataclass(frozen=True)
class WorkRow:
    work_id: str
    title: str
    title_reading: str
    ndc: str
    orthography_type: str
    card_url: str
    author_ids: tuple[str, ...]
    author_names: tuple[str, ...]
    published_on: str
    updated_on: str
    local_profile: dict[str, Any]


class TextAndLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        payload = {key: value or "" for key, value in attrs}
        href = payload.get("href", "")
        if href:
            self.links.append(payload)

    def handle_data(self, data: str) -> None:
        for line in data.splitlines():
            normalized = _normalize_space(line)
            if normalized:
                self.lines.append(normalized)


class FetchCache:
    def __init__(self, cache_dir: Path, *, force: bool, delay_seconds: float) -> None:
        self.cache_dir = cache_dir
        self.force = force
        self.delay_seconds = max(0.0, float(delay_seconds))
        self.last_fetch_monotonic = 0.0
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_text(self, url: str) -> tuple[str, dict[str, Any]]:
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        body_path = self.cache_dir / f"{key}.body"
        meta_path = self.cache_dir / f"{key}.json"
        if body_path.exists() and meta_path.exists() and not self.force:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            body = body_path.read_bytes()
            encoding = str(meta.get("encoding") or "utf-8")
            return body.decode(encoding, errors="replace"), {**meta, "cache_status": "hit"}

        wait = self.delay_seconds - (time.monotonic() - self.last_fetch_monotonic)
        if wait > 0:
            time.sleep(wait)
        self.last_fetch_monotonic = time.monotonic()

        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                body = response.read()
                status = int(getattr(response, "status", 200))
                content_type = response.headers.get("Content-Type", "")
                encoding = _detect_encoding(body, response.headers.get_content_charset())
        except HTTPError as exc:
            body = exc.read()
            status = int(exc.code)
            content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
            encoding = _detect_encoding(
                body, exc.headers.get_content_charset() if exc.headers else None
            )
        except URLError as exc:
            meta = {
                "url": url,
                "status": "url_error",
                "error": str(exc.reason),
                "fetched_at_utc": _utc_now(),
            }
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return "", {**meta, "cache_status": "miss"}

        body_path.write_bytes(body)
        meta = {
            "url": url,
            "status": status,
            "content_type": content_type,
            "encoding": encoding,
            "size_bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "fetched_at_utc": _utc_now(),
        }
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return body.decode(encoding, errors="replace"), {**meta, "cache_status": "miss"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch work-level intended-audience evidence for selected Aozora works. "
            "This is a stress-test sidecar and does not modify the accepted learner "
            "difficulty scorer or rebuild the Aozora token database."
        )
    )
    parser.add_argument(
        "--input-sqlite",
        type=Path,
        default=None,
        help="Aozora word sidecar SQLite. Defaults to the local LexiShift data root pack.",
    )
    parser.add_argument(
        "--work-id",
        action="append",
        default=[],
        help="Aozora work id to probe. May be repeated. Accepts zero-padded or plain ids.",
    )
    parser.add_argument(
        "--title",
        action="append",
        default=[],
        help="Exact Aozora title to probe. May be repeated.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional small sample limit from work_metadata when no title/work-id is enough.",
    )
    parser.add_argument(
        "--allow-large-run",
        action="store_true",
        help="Allow more than the guarded default of 50 works. Intended only after review.",
    )
    parser.add_argument(
        "--provider",
        action="append",
        choices=DEFAULT_PROVIDERS,
        default=[],
        help="Provider to query. Defaults to all providers. May be repeated.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="JSON artifact path for the probe result.",
    )
    parser.add_argument(
        "--output-sqlite",
        type=Path,
        default=None,
        help=(
            "Optional normalized SQLite artifact path. When omitted, the probe only "
            "writes JSON and does not persist a database."
        ),
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="HTTP response cache directory. Defaults beside the local Aozora pack.",
    )
    parser.add_argument("--force-fetch", action="store_true")
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=1.0,
        help="Minimum delay between non-cached HTTP requests.",
    )
    parser.add_argument(
        "--ndl-count",
        type=int,
        default=5,
        help="Maximum NDL OpenSearch records per work.",
    )
    parser.add_argument(
        "--ndl-dpid",
        action="append",
        default=[],
        help=(
            "Optional NDL data provider id to constrain an extra NDL query, e.g. aozora. "
            "When omitted, only the broad title/creator query is made."
        ),
    )
    parser.add_argument(
        "--ndl-sru-records",
        type=int,
        default=3,
        help=(
            "Maximum NDL SRU records to fetch per work, plus SRU facets. "
            "Set to 0 to skip SRU enrichment."
        ),
    )
    parser.add_argument(
        "--bungo-index-pages",
        type=int,
        default=0,
        help=(
            "Optional number of Bungo Search for Kids listing pages to scan for explicit "
            "juvenile-list inclusion. Direct detail pages are not audience evidence by themselves."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    input_sqlite = _resolve_input_sqlite(args.input_sqlite)
    cache_dir = _resolve_cache_dir(args.cache_dir)
    providers = tuple(args.provider or DEFAULT_PROVIDERS)
    work_rows = _load_work_rows(
        input_sqlite=input_sqlite,
        work_ids=tuple(args.work_id),
        titles=tuple(args.title),
        limit=max(0, int(args.limit)),
    )
    if not work_rows:
        raise SystemExit("No works matched. Pass --work-id, --title, or --limit.")
    if len(work_rows) > MAX_DEFAULT_WORKS and not args.allow_large_run:
        raise SystemExit(
            f"Refusing to probe {len(work_rows)} works without --allow-large-run. "
            f"Keep stress tests <= {MAX_DEFAULT_WORKS} works."
        )

    fetcher = FetchCache(
        cache_dir=cache_dir,
        force=bool(args.force_fetch),
        delay_seconds=float(args.delay_seconds),
    )
    results = []
    for index, work in enumerate(work_rows, start=1):
        print(f"[{index}/{len(work_rows)}] {work.work_id} {work.title}", flush=True)
        results.append(
            _probe_work(
                work=work,
                providers=providers,
                fetcher=fetcher,
                ndl_count=max(1, int(args.ndl_count)),
                ndl_dpids=tuple(args.ndl_dpid),
                ndl_sru_records=max(0, int(args.ndl_sru_records)),
                bungo_index_pages=max(0, int(args.bungo_index_pages)),
            )
        )

    payload = {
        "schema_version": 1,
        "generated_at_utc": _utc_now(),
        "input_sqlite": str(input_sqlite),
        "providers": list(providers),
        "notes": (
            "This artifact is work-level intended-audience evidence only. It is not a "
            "difficulty score and is not wired into the accepted learner-difficulty scorer."
        ),
        "source_use_notes": {
            "ndl": (
                "NDL Search metadata is API/provider-licensed metadata. Keep cached raw "
                "responses and provider provenance; review NDL/provider terms before product use."
            ),
            "wikipedia_wikidata": "Opportunistic coverage; absence of a page is not negative evidence.",
            "bungo_kids": (
                "Third-party rendered page evidence. Direct detail pages supply read-time/PV cues; "
                "only explicit juvenile listing-page matches count as audience evidence."
            ),
            "yozora": "Static juvenile NDC page match against Aozora card URLs.",
        },
        "works": results,
    }
    output_json = _resolve_path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {output_json}")
    if args.output_sqlite is not None:
        output_sqlite = _resolve_path(args.output_sqlite)
        run_id = _write_audience_sqlite(payload=payload, sqlite_path=output_sqlite)
        print(f"Wrote {output_sqlite} run_id={run_id}")
    return 0


def _probe_work(
    *,
    work: WorkRow,
    providers: tuple[str, ...],
    fetcher: FetchCache,
    ndl_count: int,
    ndl_dpids: tuple[str, ...],
    ndl_sru_records: int,
    bungo_index_pages: int,
) -> dict[str, Any]:
    provider_payloads: dict[str, Any] = {}
    if "aozora-card" in providers:
        provider_payloads["aozora_card"] = _probe_aozora_card(work, fetcher)
    if "ndl" in providers:
        provider_payloads["ndl"] = _probe_ndl(
            work,
            fetcher,
            ndl_count=ndl_count,
            dpids=ndl_dpids,
            sru_records=ndl_sru_records,
        )
    if "wikipedia" in providers:
        provider_payloads["wikipedia"] = _probe_wikipedia(work, fetcher)
    if "wikidata" in providers:
        provider_payloads["wikidata"] = _probe_wikidata(work, fetcher)
    if "yozora" in providers:
        provider_payloads["yozora"] = _probe_yozora(work, fetcher)
    if "bungo-kids" in providers:
        provider_payloads["bungo_kids"] = _probe_bungo_kids(
            work,
            fetcher,
            index_pages=bungo_index_pages,
        )

    signals = _summarize_signals(work, provider_payloads)
    return {
        "work": {
            "work_id": work.work_id,
            "title": work.title,
            "title_reading": work.title_reading,
            "ndc": work.ndc,
            "orthography_type": work.orthography_type,
            "card_url": work.card_url,
            "author_ids": list(work.author_ids),
            "author_names": list(work.author_names),
            "published_on": work.published_on,
            "updated_on": work.updated_on,
            "local_profile": work.local_profile,
        },
        "signals": signals,
        "providers": provider_payloads,
    }


def _probe_aozora_card(work: WorkRow, fetcher: FetchCache) -> dict[str, Any]:
    if not work.card_url:
        return {"status": "missing_card_url"}
    text, fetch_meta = fetcher.fetch_text(work.card_url.replace("http://", "https://", 1))
    parser = _parse_html(text)
    joined = "\n".join(parser.lines)
    labeled_fields = _extract_aozora_card_labeled_fields(parser.lines)
    fields = {
        "card_no": _extract_first_regex(joined, r"図書カード：No\.?(\d+)"),
        "classification": _first_card_field(labeled_fields, "分類")
        or _extract_colon_field(parser.lines, "分類"),
        "first_appearance": _first_card_field(labeled_fields, "初出")
        or _extract_colon_field(parser.lines, "初出"),
        "about_work": _first_card_field(labeled_fields, "作品について")
        or _extract_colon_field(parser.lines, "作品について"),
        "orthography_type": _first_card_field(labeled_fields, "文字遣い種別")
        or _extract_colon_field(parser.lines, "文字遣い種別"),
        "notes": _first_card_field(labeled_fields, "備考")
        or _extract_colon_field(parser.lines, "備考"),
        "base_book": _first_card_field(labeled_fields, "底本")
        or _extract_colon_field(parser.lines, "底本"),
        "publisher": _first_card_field(labeled_fields, "出版社")
        or _extract_colon_field(parser.lines, "出版社"),
        "first_edition": _first_card_field(labeled_fields, "初版発行日")
        or _extract_colon_field(parser.lines, "初版発行日"),
        "parent_base_book": _first_card_field(labeled_fields, "底本の親本")
        or _extract_colon_field(parser.lines, "底本の親本"),
        "author_about": _first_card_field(labeled_fields, "人物について")
        or _extract_colon_field(parser.lines, "人物について"),
    }
    work_evidence_text = "\n".join(
        [
            *(value for key, value in fields.items() if value and key != "author_about"),
            *(
                value
                for label, values in labeled_fields.items()
                for value in values
                if value and label not in {"人物について", "著者名", "著者名読み", "生年", "没年"}
            ),
        ]
    )
    return {
        "status": "ok" if fetch_meta.get("status") == 200 else "fetch_issue",
        "fetch": _compact_fetch_meta(fetch_meta),
        "fields": fields,
        "labeled_fields": labeled_fields,
        "download_links": _extract_aozora_download_links(parser.links),
        "juvenile_terms": _matched_terms(work_evidence_text, JUVENILE_TERMS),
        "school_terms": _matched_terms(work_evidence_text, SCHOOL_TERMS),
        "warning_terms": _matched_terms(work_evidence_text, WARNING_TERMS),
        "links": [link.get("href", "") for link in parser.links[:30]],
    }


def _probe_ndl(
    work: WorkRow,
    fetcher: FetchCache,
    *,
    ndl_count: int,
    dpids: tuple[str, ...],
    sru_records: int,
) -> dict[str, Any]:
    query_results = []
    query_results.append(_fetch_ndl_query(work, fetcher, ndl_count=ndl_count, dpid=""))
    for dpid in dpids:
        normalized = str(dpid or "").strip()
        if normalized:
            query_results.append(
                _fetch_ndl_query(work, fetcher, ndl_count=ndl_count, dpid=normalized)
            )
    sru = _fetch_ndl_sru(work, fetcher, record_count=sru_records) if sru_records else None
    return {
        "status": "ok",
        "queries": query_results,
        "sru": sru,
    }


def _fetch_ndl_query(
    work: WorkRow,
    fetcher: FetchCache,
    *,
    ndl_count: int,
    dpid: str,
) -> dict[str, Any]:
    creator = work.author_names[0] if work.author_names else ""
    params = {"cnt": str(ndl_count), "title": work.title}
    if creator:
        params["creator"] = creator
    if dpid:
        params["dpid"] = dpid
    url = "https://ndlsearch.ndl.go.jp/api/opensearch?" + urlencode(params)
    text, fetch_meta = fetcher.fetch_text(url)
    return _parse_ndl_response(text, fetch_meta=fetch_meta, work=work, dpid=dpid)


def _fetch_ndl_sru(
    work: WorkRow,
    fetcher: FetchCache,
    *,
    record_count: int,
) -> dict[str, Any]:
    creator = work.author_names[0] if work.author_names else ""
    query = f'title="{work.title}"'
    if creator:
        query = f'{query} AND creator="{creator}"'
    params = {
        "operation": "searchRetrieve",
        "maximumRecords": str(record_count),
        "query": query,
    }
    url = "https://ndlsearch.ndl.go.jp/api/sru?" + urlencode(params)
    text, fetch_meta = fetcher.fetch_text(url)
    return _parse_ndl_sru_response(text, fetch_meta=fetch_meta, work=work)


def _parse_ndl_sru_response(
    text: str,
    *,
    fetch_meta: dict[str, Any],
    work: WorkRow,
) -> dict[str, Any]:
    if not text:
        return {"fetch": _compact_fetch_meta(fetch_meta), "records": [], "facets": {}}
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return {
            "fetch": _compact_fetch_meta(fetch_meta),
            "parse_error": str(exc),
            "records": [],
            "facets": {},
        }
    number_of_records = _first_descendant_text(root, "numberOfRecords")
    next_record_position = _first_descendant_text(root, "nextRecordPosition")
    facets = _parse_ndl_sru_facets(_first_descendant_text(root, "extraResponseData"))
    records = []
    for record in _descendants_by_local_name(root, "record"):
        record_data = _first_child_by_local_name(record, "recordData")
        if record_data is None:
            continue
        fields = _collect_sru_record_fields(record_data)
        evidence_text = "\n".join(value for values in fields.values() for value in values if value)
        titles = fields.get("title", [])
        creators = fields.get("creator", [])
        series_titles = fields.get("seriesTitle", [])
        subjects = fields.get("subject", [])
        publishers = fields.get("publisher", [])
        dates = fields.get("date", []) + fields.get("issued", [])
        ndc_values = _extract_ndc_values(evidence_text)
        title_match = any(
            _normalize_title(value) == _normalize_title(work.title) for value in titles
        )
        creator_overlap = bool(set(creators) & set(work.author_names))
        relevant_match = title_match or (
            creator_overlap
            and any(_normalize_title(work.title) in _normalize_title(value) for value in titles)
        )
        juvenile_terms = _matched_terms(evidence_text, JUVENILE_TERMS)
        school_terms = _matched_terms(evidence_text, SCHOOL_TERMS)
        warning_terms = _matched_terms(evidence_text, WARNING_TERMS)
        records.append(
            {
                "record_position": _first_descendant_text(record, "recordPosition"),
                "titles": titles,
                "creators": creators,
                "publishers": publishers,
                "dates": dates,
                "series_titles": series_titles,
                "subjects": subjects,
                "ndc_values": ndc_values,
                "juvenile_terms": juvenile_terms,
                "school_terms": school_terms,
                "warning_terms": warning_terms,
                "relevant_match": relevant_match,
                "audience_evidence_match": bool(
                    relevant_match
                    and (
                        juvenile_terms
                        or school_terms
                        or any(str(value).startswith("K") for value in ndc_values)
                    )
                ),
                "selected_fields": _select_sru_fields(fields),
            }
        )
    return {
        "fetch": _compact_fetch_meta(fetch_meta),
        "number_of_records": int(number_of_records)
        if str(number_of_records).isdigit()
        else number_of_records,
        "next_record_position": (
            int(next_record_position)
            if str(next_record_position).isdigit()
            else next_record_position
        ),
        "facets": facets,
        "facet_summary": _summarize_ndl_facets(facets),
        "records": records,
    }


def _parse_ndl_response(
    text: str,
    *,
    fetch_meta: dict[str, Any],
    work: WorkRow,
    dpid: str,
) -> dict[str, Any]:
    if not text:
        return {"dpid": dpid or None, "fetch": _compact_fetch_meta(fetch_meta), "items": []}
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return {
            "dpid": dpid or None,
            "fetch": _compact_fetch_meta(fetch_meta),
            "parse_error": str(exc),
            "items": [],
        }
    namespaces = {
        "os": "http://a9.com/-/spec/opensearchrss/1.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "dcndl": "http://ndl.go.jp/dcndl/terms/",
        "dcterms": "http://purl.org/dc/terms/",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    }
    channel = root.find("channel")
    total = _element_text(
        channel.find("os:totalResults", namespaces) if channel is not None else None
    )
    items = []
    for item in root.findall(".//item"):
        title = _element_text(item.find("title"))
        link = _element_text(item.find("link"))
        description = _element_text(item.find("description"))
        authors = [_element_text(value) for value in item.findall("dc:creator", namespaces)]
        creator_transcriptions = [
            _element_text(value) for value in item.findall("dcndl:creatorTranscription", namespaces)
        ]
        publishers = [_element_text(value) for value in item.findall("dc:publisher", namespaces)]
        dates = [_element_text(value) for value in item.findall("dc:date", namespaces)]
        issued_dates = [
            _element_text(value) for value in item.findall("dcterms:issued", namespaces)
        ]
        series_titles = [
            _element_text(value) for value in item.findall("dcndl:seriesTitle", namespaces)
        ]
        title_transcriptions = [
            _element_text(value) for value in item.findall("dcndl:titleTranscription", namespaces)
        ]
        descriptions = [
            _element_text(value) for value in item.findall("dc:description", namespaces)
        ]
        subjects = [_element_text(value) for value in item.findall("dc:subject", namespaces)]
        subject_types = [
            _local_xml_name(
                str(value.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type") or "")
            )
            for value in item.findall("dc:subject", namespaces)
        ]
        categories = [_element_text(value) for value in item.findall("category")]
        see_also = [
            str(value.attrib.get(f"{{{namespaces['rdf']}}}resource") or "")
            for value in item.findall("rdfs:seeAlso", namespaces)
        ]
        evidence_text = "\n".join(
            [
                title,
                description,
                *authors,
                *creator_transcriptions,
                *publishers,
                *dates,
                *issued_dates,
                *series_titles,
                *title_transcriptions,
                *descriptions,
                *subjects,
                *subject_types,
                *categories,
                *see_also,
            ]
        )
        ndc_values = _extract_ndc_values(evidence_text)
        juvenile_terms = _matched_terms(evidence_text, JUVENILE_TERMS)
        school_terms = _matched_terms(evidence_text, SCHOOL_TERMS)
        warning_terms = _matched_terms(evidence_text, WARNING_TERMS)
        aozora_card_match = _contains_card_match(see_also + [link, description], work)
        exact_title_match = _normalize_title(title) == _normalize_title(work.title)
        creator_overlap = bool(set(authors) & set(work.author_names))
        relevant_match = (
            aozora_card_match
            or exact_title_match
            or (creator_overlap and _normalize_title(work.title) in _normalize_title(title))
        )
        items.append(
            {
                "title": title,
                "link": link,
                "authors": authors,
                "creator_transcriptions": creator_transcriptions,
                "publishers": publishers,
                "dates": dates,
                "issued_dates": issued_dates,
                "series_titles": series_titles,
                "title_transcriptions": title_transcriptions,
                "descriptions": descriptions,
                "subjects": subjects,
                "subject_types": subject_types,
                "categories": categories,
                "see_also": see_also,
                "ndc_values": ndc_values,
                "juvenile_terms": juvenile_terms,
                "school_terms": school_terms,
                "warning_terms": warning_terms,
                "aozora_card_match": aozora_card_match,
                "exact_title_match": exact_title_match,
                "creator_overlap": creator_overlap,
                "relevant_match": relevant_match,
                "audience_evidence_match": bool(
                    relevant_match
                    and (
                        juvenile_terms
                        or school_terms
                        or any(str(value).startswith("K") for value in ndc_values)
                    )
                ),
            }
        )
    return {
        "dpid": dpid or None,
        "fetch": _compact_fetch_meta(fetch_meta),
        "total_results": int(total) if str(total).isdigit() else total,
        "items": items,
    }


def _probe_wikipedia(work: WorkRow, fetcher: FetchCache) -> dict[str, Any]:
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "titles": work.title,
        "prop": "categories|pageprops|description",
        "cllimit": "50",
        "redirects": "1",
    }
    url = "https://ja.wikipedia.org/w/api.php?" + urlencode(params)
    text, fetch_meta = fetcher.fetch_text(url)
    payload = _loads_json(text)
    pages = (payload.get("query") or {}).get("pages") if isinstance(payload, dict) else []
    parsed_pages = []
    for page in pages or []:
        categories = [str(item.get("title") or "") for item in page.get("categories") or []]
        evidence_text = "\n".join(
            [
                str(page.get("title") or ""),
                str(page.get("description") or ""),
                *categories,
            ]
        )
        parsed_pages.append(
            {
                "title": page.get("title"),
                "pageid": page.get("pageid"),
                "missing": "missing" in page,
                "description": page.get("description"),
                "wikibase_item": (page.get("pageprops") or {}).get("wikibase_item"),
                "categories": categories,
                "juvenile_terms": _matched_terms(evidence_text, JUVENILE_TERMS),
                "school_terms": _matched_terms(evidence_text, SCHOOL_TERMS),
                "warning_terms": _matched_terms(evidence_text, WARNING_TERMS),
            }
        )
    return {
        "status": "ok",
        "fetch": _compact_fetch_meta(fetch_meta),
        "pages": parsed_pages,
    }


def _probe_wikidata(work: WorkRow, fetcher: FetchCache) -> dict[str, Any]:
    search_params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "ja",
        "uselang": "ja",
        "search": work.title,
        "limit": "5",
    }
    search_url = "https://www.wikidata.org/w/api.php?" + urlencode(search_params)
    text, fetch_meta = fetcher.fetch_text(search_url)
    search_payload = _loads_json(text)
    search_rows = search_payload.get("search") if isinstance(search_payload, dict) else []
    ids = [str(row.get("id") or "") for row in search_rows or [] if row.get("id")]
    entity_rows = []
    entity_fetch_meta: dict[str, Any] | None = None
    if ids:
        entity_params = {
            "action": "wbgetentities",
            "format": "json",
            "languages": "ja|en",
            "props": "labels|descriptions|claims",
            "ids": "|".join(ids[:5]),
        }
        entity_url = "https://www.wikidata.org/w/api.php?" + urlencode(entity_params)
        entity_text, entity_fetch_meta = fetcher.fetch_text(entity_url)
        entity_payload = _loads_json(entity_text)
        entities = entity_payload.get("entities") if isinstance(entity_payload, dict) else {}
        entity_rows = [_summarize_wikidata_entity(qid, entity) for qid, entity in entities.items()]
    return {
        "status": "ok",
        "search_fetch": _compact_fetch_meta(fetch_meta),
        "entity_fetch": _compact_fetch_meta(entity_fetch_meta) if entity_fetch_meta else None,
        "search": [
            {
                "id": row.get("id"),
                "label": row.get("label"),
                "description": row.get("description"),
                "match": row.get("match"),
                "juvenile_terms": _matched_terms(
                    "\n".join([str(row.get("label") or ""), str(row.get("description") or "")]),
                    JUVENILE_TERMS,
                ),
            }
            for row in search_rows or []
        ],
        "entities": entity_rows,
    }


def _summarize_wikidata_entity(qid: str, entity: dict[str, Any]) -> dict[str, Any]:
    labels = entity.get("labels") or {}
    descriptions = entity.get("descriptions") or {}
    label = (labels.get("ja") or labels.get("en") or {}).get("value", "")
    description = (descriptions.get("ja") or descriptions.get("en") or {}).get("value", "")
    claims = entity.get("claims") or {}
    claim_target_ids = []
    for prop in ("P31", "P136", "P921", "P2360"):
        for claim in claims.get(prop) or []:
            mainsnak = claim.get("mainsnak") or {}
            datavalue = mainsnak.get("datavalue") or {}
            value = datavalue.get("value") or {}
            target = value.get("id") if isinstance(value, dict) else None
            if target:
                claim_target_ids.append({"property": prop, "target": target})
    evidence_text = "\n".join([str(label), str(description)])
    return {
        "id": qid,
        "label": label,
        "description": description,
        "claim_target_ids": claim_target_ids,
        "juvenile_terms": _matched_terms(evidence_text, JUVENILE_TERMS),
        "school_terms": _matched_terms(evidence_text, SCHOOL_TERMS),
        "warning_terms": _matched_terms(evidence_text, WARNING_TERMS),
    }


def _probe_yozora(work: WorkRow, fetcher: FetchCache) -> dict[str, Any]:
    ndc_digits = _first_ndc_digits(work.ndc)
    if not _has_k_ndc(work.ndc) or not ndc_digits:
        return {"status": "not_k_ndc", "candidate_url": None, "card_match": False}
    candidate_url = _yozora_ndc_url(ndc_digits)
    text, fetch_meta = fetcher.fetch_text(candidate_url)
    parser = _parse_html(text)
    hrefs = [link.get("href", "") for link in parser.links]
    lines_joined = "\n".join(parser.lines)
    return {
        "status": "ok" if fetch_meta.get("status") == 200 else "fetch_issue",
        "candidate_url": candidate_url,
        "fetch": _compact_fetch_meta(fetch_meta),
        "link_count": len(hrefs),
        "page_title": parser.lines[0] if parser.lines else "",
        "category_item_count": _extract_first_count_marker(lines_joined),
        "card_match": _contains_card_match(hrefs, work),
    }


def _probe_bungo_kids(work: WorkRow, fetcher: FetchCache, *, index_pages: int) -> dict[str, Any]:
    author_numbers = [_safe_int(value) for value in work.author_ids]
    author_numbers = [value for value in author_numbers if value is not None]
    work_number = _safe_int(work.work_id)
    if not author_numbers or work_number is None:
        return {
            "status": "missing_numeric_ids",
            "juvenile_listing_matches": [],
            "detail_matches": [],
        }
    listing_matches = _probe_bungo_kids_listings(
        work=work,
        fetcher=fetcher,
        work_number=work_number,
        author_numbers=tuple(author_numbers),
        pages=index_pages,
    )
    attempts = []
    for author_number in author_numbers[:3]:
        for category in BUNGO_KIDS_CATEGORIES:
            url = (
                "https://search.bungo.app/juvenile/authors/"
                f"{author_number}/categories/{category}/books/{work_number}"
            )
            text, fetch_meta = fetcher.fetch_text(url)
            parsed = _parse_bungo_kids_page(
                text, fetch_meta=fetch_meta, work=work, category=category
            )
            attempts.append(parsed)
            if parsed.get("card_match") and (
                parsed.get("title_match") or parsed.get("author_match")
            ):
                return {
                    "status": "ok",
                    "juvenile_listing_matches": listing_matches,
                    "detail_matches": [parsed],
                    "attempts": attempts,
                }
    return {
        "status": "no_detail_match",
        "juvenile_listing_matches": listing_matches,
        "detail_matches": [],
        "attempts": attempts,
    }


def _probe_bungo_kids_listings(
    *,
    work: WorkRow,
    fetcher: FetchCache,
    work_number: int,
    author_numbers: tuple[int, ...],
    pages: int,
) -> list[dict[str, Any]]:
    matches = []
    if pages <= 0:
        return matches
    for page in range(1, pages + 1):
        url = (
            "https://search.bungo.app/juvenile"
            if page == 1
            else f"https://search.bungo.app/juvenile/page/{page}"
        )
        text, fetch_meta = fetcher.fetch_text(url)
        parser = _parse_html(text)
        lines_joined = "\n".join(parser.lines)
        hrefs = [link.get("href", "") for link in parser.links]
        author_fragments = tuple(f"/authors/{author_number}/" for author_number in author_numbers)
        matching_hrefs = [
            href
            for href in hrefs
            if _href_matches_bungo_work(
                href, work_number=work_number, author_fragments=author_fragments
            )
        ]
        if matching_hrefs:
            matches.append(
                {
                    "page": page,
                    "url": url,
                    "fetch": _compact_fetch_meta(fetch_meta),
                    "hrefs": matching_hrefs,
                    "title_seen": work.title in lines_joined,
                    "author_seen": any(
                        author and author in lines_joined for author in work.author_names
                    ),
                }
            )
    return matches


def _href_matches_bungo_work(
    href: str,
    *,
    work_number: int,
    author_fragments: tuple[str, ...],
) -> bool:
    normalized = str(href or "").split("?", 1)[0].rstrip("/")
    return normalized.endswith(f"/books/{work_number}") and any(
        author_fragment in normalized for author_fragment in author_fragments
    )


def _parse_bungo_kids_page(
    text: str,
    *,
    fetch_meta: dict[str, Any],
    work: WorkRow,
    category: str,
) -> dict[str, Any]:
    parser = _parse_html(text)
    joined = "\n".join(parser.lines)
    hrefs = [link.get("href", "") for link in parser.links]
    reading_time = _line_after_label(parser.lines, "文字数")
    popularity_line = _line_after_label(parser.lines, "人気")
    char_count = _extract_number_near_label(parser.lines, "文字数")
    popularity_pv = _extract_number_near_label(parser.lines, "人気")
    first_excerpt = _line_after_label(parser.lines, "書き出し") or _line_after_label(
        parser.lines, "書出"
    )
    first_appearance = _line_after_label(parser.lines, "初出")
    base_book = _line_after_label(parser.lines, "底本")
    orthography_values = [
        value
        for value in _values_after_label_until_label(
            parser.lines,
            "表記",
            stop_labels=("メールで分割して読む", "青空文庫で読む", "読了時間"),
            max_values=8,
        )
        if value in ORTHOGRAPHY_VALUES
    ]
    evidence_text = joined[:5000]
    title_match = work.title in joined
    author_match = any(author and author in joined for author in work.author_names)
    card_match = _contains_card_match(hrefs + [joined], work)
    status = fetch_meta.get("status")
    not_found = bool(
        (isinstance(status, int) and status >= 400) or (not card_match and not title_match)
    )
    return {
        "url": str(fetch_meta.get("url") or ""),
        "category": category,
        "fetch": _compact_fetch_meta(fetch_meta),
        "not_found": not_found,
        "title_match": title_match,
        "author_match": author_match,
        "card_match": card_match,
        "reading_time_bucket": reading_time,
        "character_count": char_count,
        "popularity_pv": popularity_pv,
        "popularity_line": popularity_line,
        "first_excerpt": first_excerpt,
        "first_appearance": first_appearance,
        "base_book": base_book,
        "orthography_values": orthography_values,
        "juvenile_terms": _matched_terms(evidence_text, JUVENILE_TERMS),
        "school_terms": _matched_terms(evidence_text, SCHOOL_TERMS),
        "warning_terms": _matched_terms(evidence_text, WARNING_TERMS),
    }


def _summarize_signals(work: WorkRow, providers: dict[str, Any]) -> dict[str, Any]:
    positive_sources = []
    warning_sources = []
    if _has_k_ndc(work.ndc):
        positive_sources.append("aozora_metadata_ndc_k")
    for name, payload in providers.items():
        if _payload_has_positive_audience_evidence(payload):
            positive_sources.append(name)
        if _payload_has_warning_evidence(payload):
            warning_sources.append(name)
    return {
        "aozora_metadata_ndc_k": _has_k_ndc(work.ndc),
        "juvenile_or_school_evidence_sources": sorted(set(positive_sources)),
        "warning_or_adultish_evidence_sources": sorted(set(warning_sources)),
        "external_source_positive_count": len(
            set(source for source in positive_sources if source != "aozora_metadata_ndc_k")
        ),
        "provider_count": len(providers),
    }


def _payload_has_positive_audience_evidence(value: Any) -> bool:
    if isinstance(value, dict):
        if isinstance(value.get("juvenile_listing_matches"), list) and value.get(
            "juvenile_listing_matches"
        ):
            return True
        if "detail_matches" in value and "attempts" in value:
            return False
        if value.get("audience_evidence_match"):
            return True
        if value.get("card_match") is True and "yozora" in str(value.get("candidate_url", "")):
            return True
        for key in ("juvenile_terms", "school_terms"):
            if value.get(key):
                return True
        return any(_payload_has_positive_audience_evidence(child) for child in value.values())
    if isinstance(value, list):
        return any(_payload_has_positive_audience_evidence(child) for child in value)
    return False


def _payload_has_warning_evidence(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("warning_terms"):
            return True
        return any(_payload_has_warning_evidence(child) for child in value.values())
    if isinstance(value, list):
        return any(_payload_has_warning_evidence(child) for child in value)
    return False


def _load_work_rows(
    *,
    input_sqlite: Path,
    work_ids: tuple[str, ...],
    titles: tuple[str, ...],
    limit: int,
) -> list[WorkRow]:
    filters = []
    params: list[Any] = []
    normalized_ids = tuple(_normalize_work_id(value) for value in work_ids if str(value).strip())
    if normalized_ids:
        placeholders = ", ".join("?" for _value in normalized_ids)
        filters.append(f"m.work_id IN ({placeholders})")
        params.extend(normalized_ids)
    title_values = tuple(str(value).strip() for value in titles if str(value).strip())
    if title_values:
        placeholders = ", ".join("?" for _value in title_values)
        filters.append(f"m.title IN ({placeholders})")
        params.extend(title_values)
    where = f"WHERE {' OR '.join(filters)}" if filters else ""
    limit_clause = "LIMIT ?" if limit else ""
    if limit:
        params.append(limit)
    query = f"""
        SELECT
            m.work_id AS work_id,
            m.title AS title,
            m.title_reading AS title_reading,
            m.ndc AS ndc,
            m.orthography_type AS orthography_type,
            m.card_url AS card_url,
            m.published_on AS published_on,
            m.updated_on AS updated_on,
            MAX(p.token_count) AS profile_token_count,
            MAX(p.content_token_count) AS profile_content_token_count,
            MAX(p.unique_content_count) AS profile_unique_content_count,
            MAX(p.common_content_share) AS profile_common_content_share,
            MAX(p.mid_content_share) AS profile_mid_content_share,
            MAX(p.tail_content_share) AS profile_tail_content_share,
            MAX(p.rare_unique_content_share) AS profile_rare_unique_content_share,
            MAX(p.function_token_share) AS profile_function_token_share,
            MAX(p.accessibility_percentile) AS profile_accessibility_percentile,
            MAX(p.accessibility_band) AS profile_accessibility_band,
            GROUP_CONCAT(DISTINCT m.author_id) AS author_ids,
            GROUP_CONCAT(DISTINCT m.author_name) AS author_names
        FROM work_metadata AS m
        LEFT JOIN work_profile AS p ON p.work_id = m.work_id
        {where}
        GROUP BY
            m.work_id,
            m.title,
            m.title_reading,
            m.ndc,
            m.orthography_type,
            m.card_url,
            m.published_on,
            m.updated_on
        ORDER BY m.work_id
        {limit_clause}
    """
    rows = []
    with sqlite3.connect(input_sqlite) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute(query, params):
            rows.append(
                WorkRow(
                    work_id=str(row["work_id"] or ""),
                    title=str(row["title"] or ""),
                    title_reading=str(row["title_reading"] or ""),
                    ndc=str(row["ndc"] or ""),
                    orthography_type=str(row["orthography_type"] or ""),
                    card_url=str(row["card_url"] or ""),
                    author_ids=_split_group_concat(row["author_ids"]),
                    author_names=_split_group_concat(row["author_names"]),
                    published_on=str(row["published_on"] or ""),
                    updated_on=str(row["updated_on"] or ""),
                    local_profile=_local_work_profile_from_row(row),
                )
            )
    return rows


def _parse_html(text: str) -> TextAndLinkParser:
    parser = TextAndLinkParser()
    parser.feed(text)
    return parser


def _extract_aozora_card_labeled_fields(lines: list[str]) -> dict[str, list[str]]:
    labels = set(AOZORA_CARD_LABELS)
    fields: dict[str, list[str]] = {}
    for index, line in enumerate(lines):
        label, inline_value = _split_card_label_value(line, labels)
        if not label:
            continue
        values = []
        if inline_value:
            values.append(inline_value)
        for candidate in lines[index + 1 : index + 6]:
            next_label, next_inline = _split_card_label_value(candidate, labels)
            if next_label:
                if not values and next_inline:
                    values.append(next_inline)
                break
            if candidate and candidate not in {"［ファイルのダウンロード｜いますぐXHTML版で読む］"}:
                values.append(candidate)
                break
        if values:
            fields.setdefault(label, [])
            for value in values:
                if value not in fields[label]:
                    fields[label].append(value)
    return fields


def _split_card_label_value(line: str, labels: set[str]) -> tuple[str, str]:
    text = _normalize_space(line)
    for separator in ("：", ":"):
        if separator in text:
            head, tail = text.split(separator, 1)
            label = _normalize_space(head)
            if label in labels:
                return label, _normalize_space(tail)
    normalized = text.rstrip("：:")
    if normalized in labels:
        return normalized, ""
    return "", ""


def _first_card_field(fields: dict[str, list[str]], label: str) -> str:
    values = fields.get(label) or []
    return str(values[0]) if values else ""


def _extract_aozora_download_links(links: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    seen = set()
    for link in links:
        href = str(link.get("href") or "")
        lower = href.lower()
        filename = Path(lower.split("?", 1)[0]).name
        if not href or not any(fragment in lower for fragment in (".zip", ".html", ".txt", ".ebk")):
            continue
        if "files/" not in lower and not re.match(
            r"^\d+[_a-z0-9-]*\.(zip|html|txt|ebk)$", filename
        ):
            continue
        if href in seen:
            continue
        seen.add(href)
        rows.append(
            {
                "href": href,
                "filename": Path(href.split("?", 1)[0]).name,
                "kind": _download_link_kind(href),
            }
        )
    return rows


def _download_link_kind(href: str) -> str:
    lower = href.lower()
    if lower.endswith(".zip"):
        return "zip"
    if lower.endswith(".html") or lower.endswith(".xhtml"):
        return "html"
    if lower.endswith(".txt"):
        return "text"
    if lower.endswith(".ebk"):
        return "expanded_book"
    return "other"


def _extract_colon_field(lines: list[str], label: str) -> str:
    prefix = f"{label}："
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            return _normalize_space(line[len(prefix) :])
        if line == f"{label}:":
            return _next_nonempty(lines, index + 1)
        if line == f"{label}：":
            return _next_nonempty(lines, index + 1)
    return ""


def _line_after_label(lines: list[str], label: str) -> str:
    for index, line in enumerate(lines):
        if line == label:
            return _next_nonempty(lines, index + 1)
    return ""


def _values_after_label_until_label(
    lines: list[str],
    label: str,
    *,
    stop_labels: tuple[str, ...],
    max_values: int,
) -> list[str]:
    values = []
    for index, line in enumerate(lines):
        if line != label:
            continue
        for candidate in lines[index + 1 :]:
            if candidate in stop_labels:
                return values
            if candidate and candidate not in values:
                values.append(candidate)
            if len(values) >= max_values:
                return values
    return values


def _extract_number_near_label(lines: list[str], label: str) -> int | None:
    for index, line in enumerate(lines):
        if line != label:
            continue
        for candidate in lines[index + 1 : index + 6]:
            normalized = candidate.replace(",", "")
            if normalized.isdigit():
                return int(normalized)
    return None


def _next_nonempty(lines: list[str], start: int) -> str:
    for line in lines[start:]:
        if line:
            return line
    return ""


def _extract_first_regex(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1) if match else ""


def _extract_first_count_marker(text: str) -> int | None:
    match = re.search(r"\(([0-9,]+)件\)", str(text or ""))
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _matched_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    haystack = str(text or "")
    return [term for term in terms if term and term in haystack]


def _extract_ndc_values(text: str) -> list[str]:
    values = []
    for match in re.finditer(r"NDC(?:\(\d+\))?[：: ]*([K]?\d+(?:\.\d+)?)", text):
        values.append(match.group(1))
    for match in re.finditer(r"dcndl:NDC\d+[^>]*>([K]?\d+(?:\.\d+)?)", text):
        values.append(match.group(1))
    return sorted(set(values))


def _contains_card_match(values: list[str], work: WorkRow) -> bool:
    card_id = str(_safe_int(work.work_id) or "").strip()
    if not card_id:
        return False
    expected_fragments = {
        f"card{card_id}.html",
        f"card{card_id}",
        f"I{work.work_id}card",
    }
    haystack = "\n".join(str(value or "") for value in values)
    return any(fragment in haystack for fragment in expected_fragments)


def _first_ndc_digits(value: str) -> str:
    match = re.search(r"K?(\d{1,3})", str(value or ""))
    return match.group(1) if match else ""


def _has_k_ndc(value: str) -> bool:
    return any(token.startswith("K") for token in str(value or "").replace("NDC", " ").split())


def _yozora_ndc_url(ndc_digits: str) -> str:
    digits = str(ndc_digits or "").strip()
    if len(digits) >= 3:
        return f"https://yozora.main.jp/{digits[0]}/{digits[1]}/ndck{digits[:3]}.html"
    if len(digits) == 2:
        return f"https://yozora.main.jp/{digits[0]}/ndck{digits}.html"
    if len(digits) == 1:
        return f"https://yozora.main.jp/ndck{digits}.html"
    return "https://yozora.main.jp/"


def _normalize_title(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).replace("：", ":")


def _normalize_work_id(value: str) -> str:
    text = str(value or "").strip()
    if text.isdigit():
        return text.zfill(6)
    return text


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u3000", " ")).strip()


def _split_group_concat(value: object) -> tuple[str, ...]:
    parts = [part.strip() for part in str(value or "").split(",") if part.strip()]
    return tuple(dict.fromkeys(parts))


def _local_work_profile_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "token_count": _safe_int(row["profile_token_count"]),
        "content_token_count": _safe_int(row["profile_content_token_count"]),
        "unique_content_count": _safe_int(row["profile_unique_content_count"]),
        "common_content_share": _safe_float(row["profile_common_content_share"]),
        "mid_content_share": _safe_float(row["profile_mid_content_share"]),
        "tail_content_share": _safe_float(row["profile_tail_content_share"]),
        "rare_unique_content_share": _safe_float(row["profile_rare_unique_content_share"]),
        "function_token_share": _safe_float(row["profile_function_token_share"]),
        "accessibility_percentile": _safe_float(row["profile_accessibility_percentile"]),
        "accessibility_band": str(row["profile_accessibility_band"] or ""),
    }


def _safe_int(value: object) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _safe_float(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _element_text(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return str(element.text).strip()


def _local_xml_name(name: str) -> str:
    text = str(name or "")
    if "}" in text:
        return text.rsplit("}", 1)[1]
    if ":" in text:
        return text.rsplit(":", 1)[1]
    return text


def _descendants_by_local_name(element: ET.Element, local_name: str) -> list[ET.Element]:
    return [value for value in element.iter() if _local_xml_name(value.tag) == local_name]


def _first_child_by_local_name(element: ET.Element, local_name: str) -> ET.Element | None:
    for child in list(element):
        if _local_xml_name(child.tag) == local_name:
            return child
    return None


def _first_descendant_text(element: ET.Element, local_name: str) -> str:
    for value in element.iter():
        if _local_xml_name(value.tag) == local_name:
            return _element_text(value)
    return ""


def _collect_local_text_values(element: ET.Element) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for value in element.iter():
        local_name = _local_xml_name(value.tag)
        if local_name not in SRU_USEFUL_FIELD_NAMES:
            continue
        text = _normalize_space("".join(value.itertext()))
        if not text:
            continue
        fields.setdefault(local_name, [])
        if text not in fields[local_name]:
            fields[local_name].append(text[:500])
    return fields


def _collect_sru_record_fields(record_data: ET.Element) -> dict[str, list[str]]:
    fields = _collect_local_text_values(record_data)
    if fields:
        return fields
    inner_xml = unescape("".join(record_data.itertext()).strip())
    if not inner_xml:
        return {}
    try:
        inner_root = ET.fromstring(inner_xml)
    except ET.ParseError:
        return {}
    return _collect_local_text_values(inner_root)


def _select_sru_fields(fields: dict[str, list[str]]) -> dict[str, list[str]]:
    selected = {}
    for key in sorted(SRU_USEFUL_FIELD_NAMES):
        values = fields.get(key) or []
        if values:
            selected[key] = values[:10]
    return selected


def _parse_ndl_sru_facets(raw: str) -> dict[str, dict[str, int]]:
    text = _normalize_space(unescape(str(raw or "")))
    if not text:
        return {}
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return {}
    facets: dict[str, dict[str, int]] = {}
    for node in _descendants_by_local_name(root, "lst"):
        name = str(node.attrib.get("name") or "")
        if not name:
            continue
        values = {}
        for child in list(node):
            if _local_xml_name(child.tag) != "int":
                continue
            key = str(child.attrib.get("name") or "")
            count = _safe_int(_element_text(child))
            if key and count is not None:
                values[key] = count
        if values:
            facets[name] = values
    return facets


def _summarize_ndl_facets(facets: dict[str, dict[str, int]]) -> dict[str, Any]:
    ndc_counts = facets.get("NDC") or {}
    issued_counts = facets.get("ISSUED_DATE") or {}
    years = sorted(int(key) for key in issued_counts if str(key).isdigit())
    return {
        "ndc_k_count": int(ndc_counts.get("K", 0)) + int(ndc_counts.get("Ｋ", 0)),
        "top_ndc": _top_count_rows(ndc_counts, limit=8),
        "top_repositories": _top_count_rows(facets.get("REPOSITORY_NO") or {}, limit=8),
        "top_libraries": _top_count_rows(facets.get("LIBRARY") or {}, limit=8),
        "issued_year_min": years[0] if years else None,
        "issued_year_max": years[-1] if years else None,
        "issued_year_count": len(years),
    }


def _top_count_rows(counts: dict[str, int], *, limit: int) -> list[dict[str, int | str]]:
    return [
        {"value": key, "count": int(count)}
        for key, count in sorted(counts.items(), key=lambda item: (-int(item[1]), str(item[0])))[
            :limit
        ]
    ]


def _loads_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _compact_fetch_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    if not meta:
        return {}
    return {
        key: meta.get(key)
        for key in (
            "url",
            "status",
            "cache_status",
            "content_type",
            "encoding",
            "size_bytes",
            "sha256",
        )
        if key in meta
    }


def _write_audience_sqlite(*, payload: dict[str, Any], sqlite_path: Path) -> str:
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    run_id = _audience_run_id(payload)
    with sqlite3.connect(sqlite_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        _create_audience_schema(conn)
        conn.execute(
            """
            INSERT OR REPLACE INTO work_audience_run (
                run_id,
                generated_at_utc,
                schema_version,
                input_sqlite,
                providers_json,
                notes,
                source_use_notes_json,
                work_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                str(payload.get("generated_at_utc") or ""),
                _safe_int(payload.get("schema_version")) or 0,
                str(payload.get("input_sqlite") or ""),
                _json_dumps(payload.get("providers") or []),
                str(payload.get("notes") or ""),
                _json_dumps(payload.get("source_use_notes") or {}),
                len(_as_list(payload.get("works"))),
            ),
        )
        for result in _as_list(payload.get("works")):
            if isinstance(result, dict):
                _insert_audience_work(conn, run_id=run_id, result=result)
        conn.commit()
    return run_id


def _create_audience_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS work_audience_run (
            run_id TEXT PRIMARY KEY,
            generated_at_utc TEXT NOT NULL,
            schema_version INTEGER NOT NULL,
            input_sqlite TEXT NOT NULL,
            providers_json TEXT NOT NULL,
            notes TEXT NOT NULL,
            source_use_notes_json TEXT NOT NULL,
            work_count INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS work_audience_work (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            title TEXT NOT NULL,
            title_reading TEXT NOT NULL,
            ndc TEXT NOT NULL,
            orthography_type TEXT NOT NULL,
            card_url TEXT NOT NULL,
            author_ids_json TEXT NOT NULL,
            author_names_json TEXT NOT NULL,
            published_on TEXT NOT NULL,
            updated_on TEXT NOT NULL,
            local_profile_json TEXT NOT NULL,
            signals_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id),
            FOREIGN KEY (run_id) REFERENCES work_audience_run(run_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS work_audience_provider_payload (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            status TEXT,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id, provider),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS provider_fetch (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            source_key TEXT NOT NULL,
            fetch_index INTEGER NOT NULL,
            url TEXT,
            status_code INTEGER,
            status_text TEXT,
            cache_status TEXT,
            content_type TEXT,
            encoding TEXT,
            size_bytes INTEGER,
            sha256 TEXT,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id, provider, source_key, fetch_index),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS aozora_card_field (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            field_source TEXT NOT NULL,
            field_name TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id, field_source, field_name, ordinal),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS aozora_card_download (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            kind TEXT,
            filename TEXT,
            href TEXT,
            PRIMARY KEY (run_id, work_id, ordinal),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ndl_opensearch_item (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            query_index INTEGER NOT NULL,
            item_index INTEGER NOT NULL,
            dpid TEXT,
            total_results INTEGER,
            title TEXT,
            link TEXT,
            exact_title_match INTEGER NOT NULL,
            creator_overlap INTEGER NOT NULL,
            relevant_match INTEGER NOT NULL,
            aozora_card_match INTEGER NOT NULL,
            audience_evidence_match INTEGER NOT NULL,
            ndc_values_json TEXT NOT NULL,
            series_titles_json TEXT NOT NULL,
            publishers_json TEXT NOT NULL,
            dates_json TEXT NOT NULL,
            subjects_json TEXT NOT NULL,
            subject_types_json TEXT NOT NULL,
            categories_json TEXT NOT NULL,
            see_also_json TEXT NOT NULL,
            juvenile_terms_json TEXT NOT NULL,
            school_terms_json TEXT NOT NULL,
            warning_terms_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id, query_index, item_index),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ndl_sru_facet (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            facet_name TEXT NOT NULL,
            facet_value TEXT NOT NULL,
            count INTEGER NOT NULL,
            PRIMARY KEY (run_id, work_id, facet_name, facet_value),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ndl_sru_record (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            record_index INTEGER NOT NULL,
            record_position TEXT,
            relevant_match INTEGER NOT NULL,
            audience_evidence_match INTEGER NOT NULL,
            titles_json TEXT NOT NULL,
            creators_json TEXT NOT NULL,
            publishers_json TEXT NOT NULL,
            dates_json TEXT NOT NULL,
            series_titles_json TEXT NOT NULL,
            subjects_json TEXT NOT NULL,
            ndc_values_json TEXT NOT NULL,
            juvenile_terms_json TEXT NOT NULL,
            school_terms_json TEXT NOT NULL,
            warning_terms_json TEXT NOT NULL,
            selected_fields_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id, record_index),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS yozora_work_match (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            candidate_url TEXT,
            status TEXT,
            card_match INTEGER NOT NULL,
            page_title TEXT,
            link_count INTEGER,
            category_item_count INTEGER,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS bungo_work_detail (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            match_index INTEGER NOT NULL,
            url TEXT,
            category TEXT,
            card_match INTEGER NOT NULL,
            title_match INTEGER NOT NULL,
            author_match INTEGER NOT NULL,
            reading_time_bucket TEXT,
            character_count INTEGER,
            popularity_pv INTEGER,
            first_appearance TEXT,
            base_book TEXT,
            orthography_values_json TEXT NOT NULL,
            first_excerpt TEXT,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id, source_kind, match_index),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS bungo_juvenile_listing_match (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            match_index INTEGER NOT NULL,
            page INTEGER,
            url TEXT,
            hrefs_json TEXT NOT NULL,
            title_seen INTEGER NOT NULL,
            author_seen INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id, match_index),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS wiki_page (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            page_index INTEGER NOT NULL,
            title TEXT,
            pageid TEXT,
            missing INTEGER NOT NULL,
            description TEXT,
            wikibase_item TEXT,
            categories_json TEXT NOT NULL,
            juvenile_terms_json TEXT NOT NULL,
            school_terms_json TEXT NOT NULL,
            warning_terms_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id, page_index),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS wikidata_search_result (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            result_index INTEGER NOT NULL,
            entity_id TEXT,
            label TEXT,
            description TEXT,
            match_json TEXT NOT NULL,
            juvenile_terms_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id, result_index),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS wikidata_entity (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            entity_index INTEGER NOT NULL,
            entity_id TEXT,
            label TEXT,
            description TEXT,
            claim_target_ids_json TEXT NOT NULL,
            juvenile_terms_json TEXT NOT NULL,
            school_terms_json TEXT NOT NULL,
            warning_terms_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id, entity_index),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS work_audience_feature (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            feature_name TEXT NOT NULL,
            value_num REAL,
            value_text TEXT,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id, feature_name),
            FOREIGN KEY (run_id, work_id) REFERENCES work_audience_work(run_id, work_id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_work_audience_work_work_id
            ON work_audience_work(work_id);
        CREATE INDEX IF NOT EXISTS idx_provider_fetch_provider
            ON provider_fetch(provider);
        CREATE INDEX IF NOT EXISTS idx_ndl_item_work
            ON ndl_opensearch_item(work_id, relevant_match, audience_evidence_match);
        CREATE INDEX IF NOT EXISTS idx_ndl_sru_facet_work_name
            ON ndl_sru_facet(work_id, facet_name);
        CREATE INDEX IF NOT EXISTS idx_work_audience_feature_name_value
            ON work_audience_feature(feature_name, value_num);
        """
    )


def _insert_audience_work(conn: sqlite3.Connection, *, run_id: str, result: dict[str, Any]) -> None:
    work = _as_dict(result.get("work"))
    signals = _as_dict(result.get("signals"))
    providers = _as_dict(result.get("providers"))
    work_id = str(work.get("work_id") or "")
    if not work_id:
        return
    conn.execute(
        """
        INSERT OR REPLACE INTO work_audience_work (
            run_id,
            work_id,
            title,
            title_reading,
            ndc,
            orthography_type,
            card_url,
            author_ids_json,
            author_names_json,
            published_on,
            updated_on,
            local_profile_json,
            signals_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            work_id,
            str(work.get("title") or ""),
            str(work.get("title_reading") or ""),
            str(work.get("ndc") or ""),
            str(work.get("orthography_type") or ""),
            str(work.get("card_url") or ""),
            _json_dumps(work.get("author_ids") or []),
            _json_dumps(work.get("author_names") or []),
            str(work.get("published_on") or ""),
            str(work.get("updated_on") or ""),
            _json_dumps(work.get("local_profile") or {}),
            _json_dumps(signals),
        ),
    )
    for provider, provider_payload in providers.items():
        _insert_provider_payload(
            conn,
            run_id=run_id,
            work_id=work_id,
            provider=str(provider),
            payload=provider_payload,
        )
    for provider, provider_payload in providers.items():
        _insert_provider_fetches(
            conn,
            run_id=run_id,
            work_id=work_id,
            provider=str(provider),
            payload=provider_payload,
        )
    _insert_aozora_card_rows(
        conn, run_id=run_id, work_id=work_id, payload=providers.get("aozora_card")
    )
    _insert_ndl_rows(conn, run_id=run_id, work_id=work_id, payload=providers.get("ndl"))
    _insert_yozora_rows(conn, run_id=run_id, work_id=work_id, payload=providers.get("yozora"))
    _insert_bungo_rows(conn, run_id=run_id, work_id=work_id, payload=providers.get("bungo_kids"))
    _insert_wikipedia_rows(conn, run_id=run_id, work_id=work_id, payload=providers.get("wikipedia"))
    _insert_wikidata_rows(conn, run_id=run_id, work_id=work_id, payload=providers.get("wikidata"))
    for feature in _extract_audience_features(result):
        conn.execute(
            """
            INSERT OR REPLACE INTO work_audience_feature (
                run_id,
                work_id,
                feature_name,
                value_num,
                value_text,
                evidence_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                work_id,
                feature["feature_name"],
                feature.get("value_num"),
                feature.get("value_text"),
                feature["evidence_json"],
            ),
        )


def _insert_provider_payload(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    work_id: str,
    provider: str,
    payload: Any,
) -> None:
    payload_dict = _as_dict(payload)
    conn.execute(
        """
        INSERT OR REPLACE INTO work_audience_provider_payload (
            run_id,
            work_id,
            provider,
            status,
            payload_json
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            run_id,
            work_id,
            provider,
            str(payload_dict.get("status") or "") if payload_dict else "",
            _json_dumps(payload if payload is not None else {}),
        ),
    )


def _insert_provider_fetches(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    work_id: str,
    provider: str,
    payload: Any,
) -> None:
    for fetch_index, (source_key, fetch_meta) in enumerate(
        _iter_provider_fetches(payload), start=1
    ):
        status = fetch_meta.get("status")
        conn.execute(
            """
            INSERT OR REPLACE INTO provider_fetch (
                run_id,
                work_id,
                provider,
                source_key,
                fetch_index,
                url,
                status_code,
                status_text,
                cache_status,
                content_type,
                encoding,
                size_bytes,
                sha256,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                work_id,
                provider,
                source_key,
                fetch_index,
                str(fetch_meta.get("url") or ""),
                status if isinstance(status, int) else None,
                str(status or ""),
                str(fetch_meta.get("cache_status") or ""),
                str(fetch_meta.get("content_type") or ""),
                str(fetch_meta.get("encoding") or ""),
                _safe_int(fetch_meta.get("size_bytes")),
                str(fetch_meta.get("sha256") or ""),
                _json_dumps(fetch_meta),
            ),
        )


def _insert_aozora_card_rows(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    work_id: str,
    payload: Any,
) -> None:
    card = _as_dict(payload)
    if not card:
        return
    fields = _as_dict(card.get("fields"))
    for field_name, value in sorted(fields.items()):
        if value is None or value == "":
            continue
        _insert_aozora_field(
            conn,
            run_id=run_id,
            work_id=work_id,
            field_source="selected",
            field_name=str(field_name),
            ordinal=0,
            value=str(value),
        )
    labeled_fields = _as_dict(card.get("labeled_fields"))
    for field_name, values in sorted(labeled_fields.items()):
        for ordinal, value in enumerate(_as_list(values)):
            if value is None or value == "":
                continue
            _insert_aozora_field(
                conn,
                run_id=run_id,
                work_id=work_id,
                field_source="labeled",
                field_name=str(field_name),
                ordinal=ordinal,
                value=str(value),
            )
    for ordinal, row in enumerate(_as_list(card.get("download_links"))):
        row_dict = _as_dict(row)
        conn.execute(
            """
            INSERT OR REPLACE INTO aozora_card_download (
                run_id,
                work_id,
                ordinal,
                kind,
                filename,
                href
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                work_id,
                ordinal,
                str(row_dict.get("kind") or ""),
                str(row_dict.get("filename") or ""),
                str(row_dict.get("href") or ""),
            ),
        )


def _insert_aozora_field(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    work_id: str,
    field_source: str,
    field_name: str,
    ordinal: int,
    value: str,
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO aozora_card_field (
            run_id,
            work_id,
            field_source,
            field_name,
            ordinal,
            value
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (run_id, work_id, field_source, field_name, ordinal, value),
    )


def _insert_ndl_rows(conn: sqlite3.Connection, *, run_id: str, work_id: str, payload: Any) -> None:
    ndl = _as_dict(payload)
    if not ndl:
        return
    for query_index, query in enumerate(_as_list(ndl.get("queries"))):
        query_dict = _as_dict(query)
        total_results = _safe_int(query_dict.get("total_results"))
        for item_index, item in enumerate(_as_list(query_dict.get("items"))):
            item_dict = _as_dict(item)
            conn.execute(
                """
                INSERT OR REPLACE INTO ndl_opensearch_item (
                    run_id,
                    work_id,
                    query_index,
                    item_index,
                    dpid,
                    total_results,
                    title,
                    link,
                    exact_title_match,
                    creator_overlap,
                    relevant_match,
                    aozora_card_match,
                    audience_evidence_match,
                    ndc_values_json,
                    series_titles_json,
                    publishers_json,
                    dates_json,
                    subjects_json,
                    subject_types_json,
                    categories_json,
                    see_also_json,
                    juvenile_terms_json,
                    school_terms_json,
                    warning_terms_json,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    work_id,
                    query_index,
                    item_index,
                    str(query_dict.get("dpid") or ""),
                    total_results,
                    str(item_dict.get("title") or ""),
                    str(item_dict.get("link") or ""),
                    _bool_int(item_dict.get("exact_title_match")),
                    _bool_int(item_dict.get("creator_overlap")),
                    _bool_int(item_dict.get("relevant_match")),
                    _bool_int(item_dict.get("aozora_card_match")),
                    _bool_int(item_dict.get("audience_evidence_match")),
                    _json_dumps(item_dict.get("ndc_values") or []),
                    _json_dumps(item_dict.get("series_titles") or []),
                    _json_dumps(item_dict.get("publishers") or []),
                    _json_dumps(
                        (item_dict.get("dates") or []) + (item_dict.get("issued_dates") or [])
                    ),
                    _json_dumps(item_dict.get("subjects") or []),
                    _json_dumps(item_dict.get("subject_types") or []),
                    _json_dumps(item_dict.get("categories") or []),
                    _json_dumps(item_dict.get("see_also") or []),
                    _json_dumps(item_dict.get("juvenile_terms") or []),
                    _json_dumps(item_dict.get("school_terms") or []),
                    _json_dumps(item_dict.get("warning_terms") or []),
                    _json_dumps(item_dict),
                ),
            )
    sru = _as_dict(ndl.get("sru"))
    facets = _as_dict(sru.get("facets"))
    for facet_name, facet_values in sorted(facets.items()):
        for facet_value, count in sorted(_as_dict(facet_values).items()):
            conn.execute(
                """
                INSERT OR REPLACE INTO ndl_sru_facet (
                    run_id,
                    work_id,
                    facet_name,
                    facet_value,
                    count
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, work_id, str(facet_name), str(facet_value), _safe_int(count) or 0),
            )
    for record_index, record in enumerate(_as_list(sru.get("records"))):
        record_dict = _as_dict(record)
        conn.execute(
            """
            INSERT OR REPLACE INTO ndl_sru_record (
                run_id,
                work_id,
                record_index,
                record_position,
                relevant_match,
                audience_evidence_match,
                titles_json,
                creators_json,
                publishers_json,
                dates_json,
                series_titles_json,
                subjects_json,
                ndc_values_json,
                juvenile_terms_json,
                school_terms_json,
                warning_terms_json,
                selected_fields_json,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                work_id,
                record_index,
                str(record_dict.get("record_position") or ""),
                _bool_int(record_dict.get("relevant_match")),
                _bool_int(record_dict.get("audience_evidence_match")),
                _json_dumps(record_dict.get("titles") or []),
                _json_dumps(record_dict.get("creators") or []),
                _json_dumps(record_dict.get("publishers") or []),
                _json_dumps(record_dict.get("dates") or []),
                _json_dumps(record_dict.get("series_titles") or []),
                _json_dumps(record_dict.get("subjects") or []),
                _json_dumps(record_dict.get("ndc_values") or []),
                _json_dumps(record_dict.get("juvenile_terms") or []),
                _json_dumps(record_dict.get("school_terms") or []),
                _json_dumps(record_dict.get("warning_terms") or []),
                _json_dumps(record_dict.get("selected_fields") or {}),
                _json_dumps(record_dict),
            ),
        )


def _insert_yozora_rows(
    conn: sqlite3.Connection, *, run_id: str, work_id: str, payload: Any
) -> None:
    yozora = _as_dict(payload)
    if not yozora:
        return
    conn.execute(
        """
        INSERT OR REPLACE INTO yozora_work_match (
            run_id,
            work_id,
            candidate_url,
            status,
            card_match,
            page_title,
            link_count,
            category_item_count,
            payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            work_id,
            str(yozora.get("candidate_url") or ""),
            str(yozora.get("status") or ""),
            _bool_int(yozora.get("card_match")),
            str(yozora.get("page_title") or ""),
            _safe_int(yozora.get("link_count")),
            _safe_int(yozora.get("category_item_count")),
            _json_dumps(yozora),
        ),
    )


def _insert_bungo_rows(
    conn: sqlite3.Connection, *, run_id: str, work_id: str, payload: Any
) -> None:
    bungo = _as_dict(payload)
    if not bungo:
        return
    for source_kind, key in (("detail_match", "detail_matches"), ("attempt", "attempts")):
        for match_index, row in enumerate(_as_list(bungo.get(key))):
            row_dict = _as_dict(row)
            conn.execute(
                """
                INSERT OR REPLACE INTO bungo_work_detail (
                    run_id,
                    work_id,
                    source_kind,
                    match_index,
                    url,
                    category,
                    card_match,
                    title_match,
                    author_match,
                    reading_time_bucket,
                    character_count,
                    popularity_pv,
                    first_appearance,
                    base_book,
                    orthography_values_json,
                    first_excerpt,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    work_id,
                    source_kind,
                    match_index,
                    str(row_dict.get("url") or ""),
                    str(row_dict.get("category") or ""),
                    _bool_int(row_dict.get("card_match")),
                    _bool_int(row_dict.get("title_match")),
                    _bool_int(row_dict.get("author_match")),
                    str(row_dict.get("reading_time_bucket") or ""),
                    _safe_int(row_dict.get("character_count")),
                    _safe_int(row_dict.get("popularity_pv")),
                    str(row_dict.get("first_appearance") or ""),
                    str(row_dict.get("base_book") or ""),
                    _json_dumps(row_dict.get("orthography_values") or []),
                    str(row_dict.get("first_excerpt") or ""),
                    _json_dumps(row_dict),
                ),
            )
    for match_index, row in enumerate(_as_list(bungo.get("juvenile_listing_matches"))):
        row_dict = _as_dict(row)
        conn.execute(
            """
            INSERT OR REPLACE INTO bungo_juvenile_listing_match (
                run_id,
                work_id,
                match_index,
                page,
                url,
                hrefs_json,
                title_seen,
                author_seen,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                work_id,
                match_index,
                _safe_int(row_dict.get("page")),
                str(row_dict.get("url") or ""),
                _json_dumps(row_dict.get("hrefs") or []),
                _bool_int(row_dict.get("title_seen")),
                _bool_int(row_dict.get("author_seen")),
                _json_dumps(row_dict),
            ),
        )


def _insert_wikipedia_rows(
    conn: sqlite3.Connection, *, run_id: str, work_id: str, payload: Any
) -> None:
    wikipedia = _as_dict(payload)
    if not wikipedia:
        return
    for page_index, page in enumerate(_as_list(wikipedia.get("pages"))):
        page_dict = _as_dict(page)
        conn.execute(
            """
            INSERT OR REPLACE INTO wiki_page (
                run_id,
                work_id,
                page_index,
                title,
                pageid,
                missing,
                description,
                wikibase_item,
                categories_json,
                juvenile_terms_json,
                school_terms_json,
                warning_terms_json,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                work_id,
                page_index,
                str(page_dict.get("title") or ""),
                str(page_dict.get("pageid") or ""),
                _bool_int(page_dict.get("missing")),
                str(page_dict.get("description") or ""),
                str(page_dict.get("wikibase_item") or ""),
                _json_dumps(page_dict.get("categories") or []),
                _json_dumps(page_dict.get("juvenile_terms") or []),
                _json_dumps(page_dict.get("school_terms") or []),
                _json_dumps(page_dict.get("warning_terms") or []),
                _json_dumps(page_dict),
            ),
        )


def _insert_wikidata_rows(
    conn: sqlite3.Connection, *, run_id: str, work_id: str, payload: Any
) -> None:
    wikidata = _as_dict(payload)
    if not wikidata:
        return
    for result_index, row in enumerate(_as_list(wikidata.get("search"))):
        row_dict = _as_dict(row)
        conn.execute(
            """
            INSERT OR REPLACE INTO wikidata_search_result (
                run_id,
                work_id,
                result_index,
                entity_id,
                label,
                description,
                match_json,
                juvenile_terms_json,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                work_id,
                result_index,
                str(row_dict.get("id") or ""),
                str(row_dict.get("label") or ""),
                str(row_dict.get("description") or ""),
                _json_dumps(row_dict.get("match") or {}),
                _json_dumps(row_dict.get("juvenile_terms") or []),
                _json_dumps(row_dict),
            ),
        )
    for entity_index, row in enumerate(_as_list(wikidata.get("entities"))):
        row_dict = _as_dict(row)
        conn.execute(
            """
            INSERT OR REPLACE INTO wikidata_entity (
                run_id,
                work_id,
                entity_index,
                entity_id,
                label,
                description,
                claim_target_ids_json,
                juvenile_terms_json,
                school_terms_json,
                warning_terms_json,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                work_id,
                entity_index,
                str(row_dict.get("id") or ""),
                str(row_dict.get("label") or ""),
                str(row_dict.get("description") or ""),
                _json_dumps(row_dict.get("claim_target_ids") or []),
                _json_dumps(row_dict.get("juvenile_terms") or []),
                _json_dumps(row_dict.get("school_terms") or []),
                _json_dumps(row_dict.get("warning_terms") or []),
                _json_dumps(row_dict),
            ),
        )


def _extract_audience_features(result: dict[str, Any]) -> list[dict[str, Any]]:
    work = _as_dict(result.get("work"))
    signals = _as_dict(result.get("signals"))
    providers = _as_dict(result.get("providers"))
    rows: list[dict[str, Any]] = []
    positive_sources = _as_list(signals.get("juvenile_or_school_evidence_sources"))
    warning_sources = _as_list(signals.get("warning_or_adultish_evidence_sources"))
    _append_feature(
        rows, "aozora_metadata_ndc_k", bool(signals.get("aozora_metadata_ndc_k")), signals
    )
    _append_feature(rows, "positive_source_count", len(positive_sources), signals)
    _append_feature(
        rows,
        "external_source_positive_count",
        signals.get("external_source_positive_count"),
        signals,
    )
    _append_feature(rows, "warning_source_count", len(warning_sources), signals)
    _append_feature(rows, "provider_count", signals.get("provider_count"), signals)

    local_profile = _as_dict(work.get("local_profile"))
    for key in (
        "token_count",
        "content_token_count",
        "unique_content_count",
        "common_content_share",
        "mid_content_share",
        "tail_content_share",
        "rare_unique_content_share",
        "function_token_share",
        "accessibility_percentile",
    ):
        _append_feature(rows, f"local_profile_{key}", local_profile.get(key), local_profile)
    _append_feature(
        rows,
        "local_profile_accessibility_band",
        local_profile.get("accessibility_band"),
        local_profile,
    )

    aozora = _as_dict(providers.get("aozora_card"))
    _append_feature(
        rows, "aozora_card_juvenile_term_count", len(_as_list(aozora.get("juvenile_terms"))), aozora
    )
    _append_feature(
        rows, "aozora_card_school_term_count", len(_as_list(aozora.get("school_terms"))), aozora
    )
    _append_feature(
        rows, "aozora_card_warning_term_count", len(_as_list(aozora.get("warning_terms"))), aozora
    )
    _append_feature(
        rows, "aozora_card_download_count", len(_as_list(aozora.get("download_links"))), aozora
    )

    ndl = _as_dict(providers.get("ndl"))
    ndl_items = [
        _as_dict(item)
        for query in _as_list(ndl.get("queries"))
        for item in _as_list(_as_dict(query).get("items"))
    ]
    _append_feature(
        rows,
        "ndl_opensearch_relevant_item_count",
        sum(1 for item in ndl_items if item.get("relevant_match")),
        ndl_items,
    )
    _append_feature(
        rows,
        "ndl_opensearch_audience_item_count",
        sum(1 for item in ndl_items if item.get("audience_evidence_match")),
        ndl_items,
    )
    _append_feature(
        rows,
        "ndl_opensearch_ndc_k_item_count",
        sum(1 for item in ndl_items if _has_any_k_ndc(item.get("ndc_values"))),
        ndl_items,
    )
    sru = _as_dict(ndl.get("sru"))
    sru_records = [_as_dict(record) for record in _as_list(sru.get("records"))]
    facet_summary = _as_dict(sru.get("facet_summary"))
    _append_feature(rows, "ndl_sru_record_count", len(sru_records), sru_records)
    _append_feature(
        rows,
        "ndl_sru_relevant_record_count",
        sum(1 for record in sru_records if record.get("relevant_match")),
        sru_records,
    )
    _append_feature(
        rows,
        "ndl_sru_audience_record_count",
        sum(1 for record in sru_records if record.get("audience_evidence_match")),
        sru_records,
    )
    _append_feature(rows, "ndl_sru_number_of_records", _safe_int(sru.get("number_of_records")), sru)
    for key in ("ndc_k_count", "issued_year_min", "issued_year_max", "issued_year_count"):
        _append_feature(rows, f"ndl_sru_facet_{key}", facet_summary.get(key), facet_summary)

    yozora = _as_dict(providers.get("yozora"))
    _append_feature(rows, "yozora_card_match", bool(yozora.get("card_match")), yozora)
    _append_feature(rows, "yozora_link_count", yozora.get("link_count"), yozora)
    _append_feature(rows, "yozora_category_item_count", yozora.get("category_item_count"), yozora)

    bungo = _as_dict(providers.get("bungo_kids"))
    detail_matches = [_as_dict(row) for row in _as_list(bungo.get("detail_matches"))]
    listing_matches = [_as_dict(row) for row in _as_list(bungo.get("juvenile_listing_matches"))]
    _append_feature(rows, "bungo_detail_match_count", len(detail_matches), detail_matches)
    _append_feature(
        rows, "bungo_juvenile_listing_match_count", len(listing_matches), listing_matches
    )
    _append_feature(
        rows,
        "bungo_character_count_max",
        _max_int(row.get("character_count") for row in detail_matches),
        detail_matches,
    )
    _append_feature(
        rows,
        "bungo_popularity_pv_max",
        _max_int(row.get("popularity_pv") for row in detail_matches),
        detail_matches,
    )

    wikipedia = _as_dict(providers.get("wikipedia"))
    wiki_pages = [_as_dict(row) for row in _as_list(wikipedia.get("pages"))]
    _append_feature(rows, "wikipedia_page_count", len(wiki_pages), wiki_pages)
    _append_feature(
        rows,
        "wikipedia_existing_page_count",
        sum(1 for page in wiki_pages if not page.get("missing")),
        wiki_pages,
    )
    _append_feature(
        rows,
        "wikipedia_positive_term_count",
        sum(
            len(_as_list(page.get("juvenile_terms"))) + len(_as_list(page.get("school_terms")))
            for page in wiki_pages
        ),
        wiki_pages,
    )
    _append_feature(
        rows,
        "wikipedia_warning_term_count",
        sum(len(_as_list(page.get("warning_terms"))) for page in wiki_pages),
        wiki_pages,
    )

    wikidata = _as_dict(providers.get("wikidata"))
    wikidata_search = [_as_dict(row) for row in _as_list(wikidata.get("search"))]
    wikidata_entities = [_as_dict(row) for row in _as_list(wikidata.get("entities"))]
    _append_feature(rows, "wikidata_search_result_count", len(wikidata_search), wikidata_search)
    _append_feature(rows, "wikidata_entity_count", len(wikidata_entities), wikidata_entities)
    _append_feature(
        rows,
        "wikidata_positive_term_count",
        sum(
            len(_as_list(row.get("juvenile_terms"))) + len(_as_list(row.get("school_terms")))
            for row in wikidata_search + wikidata_entities
        ),
        wikidata_search + wikidata_entities,
    )
    _append_feature(
        rows,
        "wikidata_warning_term_count",
        sum(len(_as_list(row.get("warning_terms"))) for row in wikidata_entities),
        wikidata_entities,
    )
    return rows


def _append_feature(rows: list[dict[str, Any]], name: str, value: Any, evidence: Any) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        rows.append(
            {
                "feature_name": name,
                "value_num": 1.0 if value else 0.0,
                "value_text": "true" if value else "false",
                "evidence_json": _json_dumps(evidence),
            }
        )
        return
    if isinstance(value, int | float):
        rows.append(
            {
                "feature_name": name,
                "value_num": float(value),
                "value_text": str(value),
                "evidence_json": _json_dumps(evidence),
            }
        )
        return
    text = str(value)
    if not text:
        return
    rows.append(
        {
            "feature_name": name,
            "value_num": _safe_float(text),
            "value_text": text,
            "evidence_json": _json_dumps(evidence),
        }
    )


def _iter_provider_fetches(payload: Any, prefix: str = "root") -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    if isinstance(payload, dict):
        for key in ("fetch", "search_fetch", "entity_fetch"):
            value = payload.get(key)
            if isinstance(value, dict) and value:
                rows.append((f"{prefix}.{key}", value))
        for key, value in payload.items():
            if key in {"fetch", "search_fetch", "entity_fetch"}:
                continue
            rows.extend(_iter_provider_fetches(value, prefix=f"{prefix}.{key}"))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            rows.extend(_iter_provider_fetches(value, prefix=f"{prefix}[{index}]"))
    return rows


def _audience_run_id(payload: dict[str, Any]) -> str:
    generated = str(payload.get("generated_at_utc") or _utc_now())
    compact_time = re.sub(r"[^0-9A-Za-z]+", "", generated)[:16] or "unknown"
    digest_basis = {
        "generated_at_utc": generated,
        "input_sqlite": payload.get("input_sqlite"),
        "providers": payload.get("providers"),
        "work_ids": [
            _as_dict(_as_dict(row).get("work")).get("work_id")
            for row in _as_list(payload.get("works"))
        ],
    }
    digest = hashlib.sha256(_json_dumps(digest_basis).encode("utf-8")).hexdigest()[:10]
    return f"audience_{compact_time}_{digest}"


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _bool_int(value: Any) -> int:
    return 1 if bool(value) else 0


def _has_any_k_ndc(values: Any) -> bool:
    return any(str(value).startswith("K") for value in _as_list(values))


def _max_int(values: Any) -> int | None:
    max_value: int | None = None
    for value in values:
        parsed = _safe_int(value)
        if parsed is None:
            continue
        if max_value is None or parsed > max_value:
            max_value = parsed
    return max_value


def _detect_encoding(body: bytes, header_encoding: str | None) -> str:
    if header_encoding:
        return header_encoding
    head = body[:4096].decode("ascii", errors="ignore")
    match = re.search(r"charset=[\"']?([A-Za-z0-9_\-]+)", head, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    for encoding in ("utf-8", "cp932", "shift_jis", "euc_jp"):
        try:
            body.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "utf-8"


def _resolve_input_sqlite(value: Path | None) -> Path:
    if value is not None:
        return _resolve_path(value)
    return _resolve_data_root() / "frequency_packs" / PACK_ID / "main.sqlite"


def _resolve_cache_dir(value: Path | None) -> Path:
    if value is not None:
        return _resolve_path(value)
    return _resolve_data_root() / "frequency_packs" / PACK_ID / "audience_metadata_cache"


def _resolve_path(value: Path) -> Path:
    if value.is_absolute():
        return value
    return (PROJECT_ROOT / value).resolve()


def _resolve_data_root() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "LexiShift" / "LexiShift"
    if sys.platform.startswith("win"):
        return Path.home() / "AppData" / "Roaming" / "LexiShift" / "LexiShift"
    return home / ".local" / "share" / "LexiShift" / "LexiShift"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
