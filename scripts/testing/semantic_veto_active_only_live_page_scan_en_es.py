#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from typing import Callable, Iterable, Mapping, Sequence
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
EXPERIMENT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_veto_source_packaging"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.use_cases.semantic_admission import semantic_admit_batch  # noqa: E402


DEFAULT_MANIFEST = TEST_INPUTS_ROOT / "semantic_veto_active_only_live_page_scan_en_es.json"
DEFAULT_FIXTURE_ROOT = EXPERIMENT_ROOT / "en-es-active-only-poc-v5-helper-runtime-smoke-data-root"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_active_only_live_page_scan_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_live_page_scan_en_es_latest.md"
)
DEFAULT_USER_AGENT = "LexiShiftSemanticVetoReview/0.1 (+local manual testing)"

_WORD_CHARS = r"A-Za-z0-9À-ÖØ-öø-ÿ'"
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"“])")
_SPACE_RE = re.compile(r"\s+")
_REFERENCE_RE = re.compile(r"\[[0-9A-Za-z]+\]")


@dataclass(frozen=True)
class RulePointer:
    source_phrase: str
    replacement: str
    semantic_admission: Mapping[str, object]


class _TextHTMLParser(HTMLParser):
    _SKIP_TAGS = {"script", "style", "noscript", "template", "svg", "math"}
    _BLOCK_TAGS = {"p", "div", "section", "article", "li", "br", "h1", "h2", "h3", "h4"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        if normalized in self._SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth == 0 and normalized in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if normalized in self._SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth == 0 and normalized in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = str(data or "").strip()
        if text:
            self._parts.append(text)

    def text(self) -> str:
        return "\n".join(self._parts)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch public pages, extract trigger-bearing sentences, and run them through the "
            "active-only semantic-veto helper fixture for manual product-feel review."
        )
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--fixture-root", type=Path, default=DEFAULT_FIXTURE_ROOT)
    parser.add_argument("--profile-id", default="default")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--max-sentences-per-trigger", type=int, default=4)
    parser.add_argument("--max-sentences-per-page", type=int, default=10)
    parser.add_argument("--max-total-matches", type=int, default=120)
    parser.add_argument("--timeout-seconds", type=float, default=12.0)
    parser.add_argument("--request-delay-seconds", type=float, default=2.5)
    parser.add_argument("--fetch-retries", type=int, default=4)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_live_page_scan_report(
        manifest_payload=_load_json(args.manifest),
        manifest_path=args.manifest,
        fixture_root=args.fixture_root,
        profile_id=args.profile_id,
        max_sentences_per_trigger=args.max_sentences_per_trigger,
        max_sentences_per_page=args.max_sentences_per_page,
        max_total_matches=args.max_total_matches,
        request_delay_seconds=max(0.0, float(args.request_delay_seconds)),
        fetch_text=lambda page: fetch_page_text(
            str(page.get("url") or ""),
            timeout_seconds=float(args.timeout_seconds),
            fetch_retries=max(0, int(args.fetch_retries)),
            user_agent=str(args.user_agent or DEFAULT_USER_AGENT),
        ),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_live_page_scan_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_live_page_scan_report(
    *,
    manifest_payload: Mapping[str, object],
    manifest_path: Path | None = None,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    profile_id: str = "default",
    max_sentences_per_trigger: int = 8,
    max_sentences_per_page: int = 40,
    max_total_matches: int = 140,
    request_delay_seconds: float = 0.0,
    fetch_text: Callable[[Mapping[str, object]], str] | None = None,
) -> dict[str, object]:
    normalized_profile = str(profile_id or "").strip() or "default"
    paths = build_helper_paths(fixture_root)
    ruleset_path = paths.ruleset_path("en-es", profile_id=normalized_profile)
    inventory_path = paths.semantic_inventory_path("en-es", profile_id=normalized_profile)
    issues: list[str] = []
    if not ruleset_path.exists():
        issues.append("fixture_ruleset_missing")
    if not inventory_path.exists():
        issues.append("fixture_semantic_inventory_missing")
    rules = _load_rule_pointers(ruleset_path) if ruleset_path.exists() else []
    if not rules:
        issues.append("no_fixture_rules")
    fetcher = fetch_text or (lambda page: "")
    page_rows: list[dict[str, object]] = []
    match_rows: list[dict[str, object]] = []
    for page_index, page in enumerate(_mapping_rows(manifest_payload.get("pages"))):
        page_id = str(page.get("page_id") or "").strip()
        url = str(page.get("url") or "").strip()
        try:
            if page_index and request_delay_seconds > 0:
                time.sleep(request_delay_seconds)
            text = fetcher(page)
            fetch_status = "ok"
            fetch_error = ""
        except Exception as exc:  # pragma: no cover - exercised by live CLI only.
            text = ""
            fetch_status = "error"
            fetch_error = f"{type(exc).__name__}: {exc}"
        sentences = extract_review_sentences(
            text,
            rules=rules,
            page_id=page_id,
            url=url,
            max_sentences_per_trigger=max_sentences_per_trigger,
            max_sentences_per_page=max_sentences_per_page,
            remaining_match_budget=max(0, int(max_total_matches) - len(match_rows)),
        )
        page_rows.append(
            {
                "page_id": page_id,
                "url": url,
                "fetch_status": fetch_status,
                "fetch_error": fetch_error,
                "text_char_count": len(text),
                "matched_sentence_count": len(sentences),
                "expected_triggers": list(page.get("expected_triggers") or []),
            }
        )
        match_rows.extend(sentences)
        if len(match_rows) >= max_total_matches:
            break
    if any(row["fetch_status"] != "ok" for row in page_rows):
        issues.append("page_fetch_errors")
    if not match_rows:
        issues.append("no_trigger_sentences_extracted")
    decisions = _admit_matches(
        paths=paths,
        profile_id=normalized_profile,
        match_rows=match_rows,
    )
    decision_by_id = {str(row.get("match_id") or ""): row for row in decisions}
    review_rows = []
    for row in match_rows:
        decision = _as_mapping(decision_by_id.get(str(row.get("match_id") or "")))
        review_rows.append(_review_row(row, decision))
    decision_counts = Counter(str(row.get("decision") or "") for row in review_rows)
    source_counts = Counter(str(row.get("decision_source") or "") for row in review_rows)
    trigger_counts: dict[str, dict[str, int]] = {}
    for trigger, rows in _group_by_trigger(review_rows).items():
        trigger_counts[trigger] = dict(Counter(str(row.get("decision") or "") for row in rows))
    status = "ok" if not issues else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "manual_review_packet_ready"
        if status == "ok"
        else "live_page_scan_needs_review",
        "pair": "en-es",
        "manifest_path": _repo_path(manifest_path),
        "scan_id": str(manifest_payload.get("scan_id") or ""),
        "fixture": {
            "data_root": str(fixture_root.resolve()),
            "ruleset_path": str(ruleset_path.resolve()),
            "semantic_inventory_path": str(inventory_path.resolve()),
            "profile_id": normalized_profile,
        },
        "methodology": {
            "promotion_claim": "none",
            "review_goal": "manual product-feel review of real online sentences",
            "sentence_splitter": "simple punctuation splitter after HTML text extraction",
            "runtime_path": "helper semantic_admit_batch against isolated active-only fixture",
            "decision_policy": "browser-style inventory default; active-only en-es fixture resolves to en_es_sentence_veto_v2",
            "limits": {
                "max_sentences_per_trigger": int(max_sentences_per_trigger),
                "max_sentences_per_page": int(max_sentences_per_page),
                "max_total_matches": int(max_total_matches),
                "request_delay_seconds": float(request_delay_seconds),
            },
        },
        "summary": {
            "manifest_page_count": len(_mapping_rows(manifest_payload.get("pages"))),
            "scanned_page_count": len(page_rows),
            "scan_stopped_reason": (
                "max_total_matches"
                if len(match_rows) >= max_total_matches
                else "manifest_exhausted"
            ),
            "page_error_count": sum(1 for row in page_rows if row["fetch_status"] != "ok"),
            "rule_count": len(rules),
            "review_row_count": len(review_rows),
            "decision_counts": dict(sorted(decision_counts.items())),
            "decision_source_counts": dict(sorted(source_counts.items())),
            "trigger_decision_counts": dict(sorted(trigger_counts.items())),
        },
        "pages": page_rows,
        "review_rows": review_rows,
        "issues": issues,
    }


def fetch_page_text(
    url: str,
    *,
    timeout_seconds: float,
    fetch_retries: int,
    user_agent: str,
) -> str:
    if not str(url or "").strip():
        return ""
    wikipedia_text = _fetch_wikipedia_extract(
        str(url),
        timeout_seconds=timeout_seconds,
        fetch_retries=fetch_retries,
        user_agent=user_agent,
    )
    if wikipedia_text:
        return wikipedia_text
    request = Request(
        str(url),
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5",
        },
    )
    with _urlopen_with_retries(
        request,
        timeout_seconds=timeout_seconds,
        fetch_retries=fetch_retries,
    ) as response:
        content_type = str(response.headers.get("content-type") or "")
        raw = response.read(2_000_000)
    encoding = "utf-8"
    match = re.search(r"charset=([A-Za-z0-9._-]+)", content_type)
    if match:
        encoding = match.group(1)
    text = raw.decode(encoding, errors="replace")
    if "html" in content_type.lower() or "<html" in text[:500].lower():
        return html_to_text(text)
    return normalize_page_text(text)


def _fetch_wikipedia_extract(
    url: str,
    *,
    timeout_seconds: float,
    fetch_retries: int,
    user_agent: str,
) -> str:
    parsed = urlparse(str(url or ""))
    host = parsed.netloc.lower()
    if host not in {"en.wikipedia.org", "www.en.wikipedia.org"}:
        return ""
    path_prefix = "/wiki/"
    if not parsed.path.startswith(path_prefix):
        return ""
    title = unquote(parsed.path[len(path_prefix) :]).strip()
    if not title:
        return ""
    api_url = (
        "https://en.wikipedia.org/w/api.php"
        "?action=query&prop=extracts&explaintext=1&exsectionformat=plain"
        f"&redirects=1&format=json&titles={quote(title)}"
    )
    request = Request(
        api_url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
    )
    with _urlopen_with_retries(
        request,
        timeout_seconds=timeout_seconds,
        fetch_retries=fetch_retries,
    ) as response:
        payload = json.loads(response.read(2_000_000).decode("utf-8", errors="replace"))
    pages = _as_mapping(_as_mapping(_as_mapping(payload.get("query")).get("pages")))
    extracts = [
        str(page.get("extract") or "").strip()
        for page in _mapping_rows(pages)
        if str(page.get("extract") or "").strip()
    ]
    return normalize_page_text("\n".join(extracts))


def _urlopen_with_retries(
    request: Request,
    *,
    timeout_seconds: float,
    fetch_retries: int,
) -> object:
    last_error: HTTPError | None = None
    for attempt in range(fetch_retries + 1):
        try:
            return urlopen(request, timeout=timeout_seconds)
        except HTTPError as exc:
            if exc.code != 429 or attempt >= fetch_retries:
                raise
            last_error = exc
            retry_after = str(exc.headers.get("retry-after") or "").strip()
            if retry_after.isdigit():
                delay = min(float(retry_after), 8.0)
            else:
                delay = min(2.0 * (attempt + 1), 8.0)
            time.sleep(delay)
    if last_error is not None:
        raise last_error
    raise RuntimeError("urlopen retry loop exhausted without an HTTP response")


def html_to_text(html: str) -> str:
    parser = _TextHTMLParser()
    parser.feed(str(html or ""))
    return normalize_page_text(parser.text())


def normalize_page_text(text: str) -> str:
    text = _REFERENCE_RE.sub("", str(text or ""))
    text = text.replace("\xa0", " ")
    text = text.replace("[edit]", " ")
    return _SPACE_RE.sub(" ", text).strip()


def extract_review_sentences(
    text: str,
    *,
    rules: Sequence[RulePointer],
    page_id: str,
    url: str,
    max_sentences_per_trigger: int,
    max_sentences_per_page: int,
    remaining_match_budget: int,
) -> list[dict[str, object]]:
    if remaining_match_budget <= 0:
        return []
    by_trigger_count: Counter[str] = Counter()
    rows: list[dict[str, object]] = []
    seen_sentence_trigger: set[tuple[str, str]] = set()
    for sentence in split_sentences(text):
        if len(rows) >= max_sentences_per_page or len(rows) >= remaining_match_budget:
            break
        for rule in rules:
            source_phrase = rule.source_phrase
            if by_trigger_count[source_phrase] >= max_sentences_per_trigger:
                continue
            if not _contains_phrase(sentence, source_phrase):
                continue
            key = (_compact_for_dedupe(sentence), source_phrase.lower())
            if key in seen_sentence_trigger:
                continue
            seen_sentence_trigger.add(key)
            row_index = len(rows) + 1
            rows.append(
                {
                    "match_id": f"{page_id}:{row_index}:{_slug(source_phrase)}",
                    "page_id": page_id,
                    "url": url,
                    "source_phrase": source_phrase,
                    "replacement": rule.replacement,
                    "context_text": sentence,
                    "semantic_admission": dict(rule.semantic_admission),
                }
            )
            by_trigger_count[source_phrase] += 1
            if len(rows) >= max_sentences_per_page or len(rows) >= remaining_match_budget:
                break
    return rows


def split_sentences(text: str) -> list[str]:
    rows: list[str] = []
    for segment in _SENTENCE_SPLIT_RE.split(normalize_page_text(text)):
        sentence = _SPACE_RE.sub(" ", segment).strip()
        if not 40 <= len(sentence) <= 420:
            continue
        if sentence.count(" ") < 5:
            continue
        if _is_boilerplate_sentence(sentence):
            continue
        rows.append(sentence)
    return rows


def _is_boilerplate_sentence(sentence: str) -> bool:
    lowered = sentence.lower()
    if lowered.startswith(("for other uses", "this article is about", "this article needs")):
        return True
    boilerplate_markers = (
        "retrieved ",
        "archived from",
        "isbn ",
        "doi:",
        "pmid ",
        "wikimedia commons",
        "official website",
    )
    return any(marker in lowered for marker in boilerplate_markers)


def render_live_page_scan_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    fixture = _as_mapping(report.get("fixture"))
    lines = [
        "# en-es Semantic Veto Live Page Scan",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Scan: `{report.get('scan_id', '')}`",
        f"- Fixture data root: `{fixture.get('data_root', '')}`",
        f"- Pages scanned: `{summary.get('scanned_page_count', 0)}` / "
        f"`{summary.get('manifest_page_count', 0)}`",
        f"- Page fetch errors: `{summary.get('page_error_count', 0)}`",
        f"- Scan stopped reason: `{summary.get('scan_stopped_reason', '')}`",
        f"- Review rows: `{summary.get('review_row_count', 0)}`",
        f"- Decision counts: `{summary.get('decision_counts', {})}`",
        f"- Decision source counts: `{summary.get('decision_source_counts', {})}`",
        "",
        "## How To Review",
        "",
        "- `replace` means the user would see the Spanish replacement.",
        "- `abstain` means the user would keep the original English text.",
        "- Treat this as product-feel review, not a promotion metric.",
        "",
        "## Pages",
        "",
        "| Page | Status | Rows | Error | URL |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for page in _mapping_rows(report.get("pages")):
        lines.append(
            f"| `{page.get('page_id', '')}` | `{page.get('fetch_status', '')}` | "
            f"{page.get('matched_sentence_count', 0)} | "
            f"{_markdown_cell(page.get('fetch_error'))} | {page.get('url', '')} |"
        )
    lines.extend(
        [
            "",
            "## Review Rows",
            "",
            "| Page | Trigger -> Target | Decision | Source | Active | Shadow | Margin | Your read | Sentence |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in _mapping_rows(report.get("review_rows")):
        lines.append(
            f"| `{row.get('page_id', '')}` | `{row.get('source_phrase', '')}` -> "
            f"`{row.get('replacement', '')}` | `{row.get('decision', '')}` | "
            f"`{row.get('decision_source', '')}` | {_fmt(row.get('active_score'))} | "
            f"{_fmt(row.get('top_shadow_score'))} | {_fmt(row.get('score_margin'))} |  | "
            f"{_markdown_cell(row.get('context_text'))} |"
        )
    if report.get("issues"):
        lines.extend(["", "## Issues", ""])
        lines.extend(f"- `{issue}`" for issue in report.get("issues", ()))
    return "\n".join(lines) + "\n"


def _admit_matches(
    *,
    paths: object,
    profile_id: str,
    match_rows: Sequence[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    if not match_rows:
        return []
    payload_matches = [
        {
            "match_id": str(row.get("match_id") or ""),
            "source_phrase": str(row.get("source_phrase") or ""),
            "context_text": str(row.get("context_text") or ""),
            "semantic_admission": dict(_as_mapping(row.get("semantic_admission"))),
        }
        for row in match_rows
    ]
    response = semantic_admit_batch(
        paths,  # type: ignore[arg-type]
        payload={
            "schema_version": 1,
            "pair": "en-es",
            "profile_id": profile_id,
            "fallback_policy": "abstain_on_unavailable",
            "surface_kind": "live_page_scan",
            "matches": payload_matches,
        },
    )
    return _mapping_rows(response.get("decisions"))


def _review_row(
    match_row: Mapping[str, object], decision: Mapping[str, object]
) -> dict[str, object]:
    return {
        "match_id": str(match_row.get("match_id") or ""),
        "page_id": str(match_row.get("page_id") or ""),
        "url": str(match_row.get("url") or ""),
        "source_phrase": str(match_row.get("source_phrase") or ""),
        "replacement": str(match_row.get("replacement") or ""),
        "context_text": str(match_row.get("context_text") or ""),
        "decision": str(decision.get("decision") or ""),
        "decision_source": str(decision.get("decision_source") or ""),
        "reason_codes": list(decision.get("reason_codes") or []),
        "active_score": float(decision.get("active_score") or 0.0),
        "top_shadow_score": float(decision.get("top_shadow_score") or 0.0),
        "score_margin": float(decision.get("score_margin") or 0.0),
    }


def _load_rule_pointers(ruleset_path: Path) -> list[RulePointer]:
    payload = _load_json(ruleset_path)
    pointers: list[RulePointer] = []
    for rule in _mapping_rows(payload.get("rules")):
        metadata = _as_mapping(rule.get("metadata"))
        semantic_admission = _as_mapping(metadata.get("semantic_admission"))
        if str(semantic_admission.get("status") or "") != "ready":
            continue
        source_phrase = str(rule.get("source_phrase") or "").strip()
        replacement = str(rule.get("replacement") or "").strip()
        if not source_phrase or not replacement:
            continue
        pointers.append(
            RulePointer(
                source_phrase=source_phrase,
                replacement=replacement,
                semantic_admission=dict(semantic_admission),
            )
        )
    return sorted(pointers, key=lambda row: (-len(row.source_phrase.split()), row.source_phrase))


def _contains_phrase(sentence: str, phrase: str) -> bool:
    tokens = [re.escape(token) for token in str(phrase or "").split() if token]
    if not tokens:
        return False
    phrase_pattern = r"\s+".join(tokens)
    pattern = rf"(?<![{_WORD_CHARS}]){phrase_pattern}(?![{_WORD_CHARS}])"
    return re.search(pattern, sentence, flags=re.IGNORECASE) is not None


def _group_by_trigger(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, list[Mapping[str, object]]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("source_phrase") or "")].append(row)
    return grouped


def _compact_for_dedupe(text: str) -> str:
    return _SPACE_RE.sub(" ", str(text or "").strip().lower())


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-") or "row"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Mapping):
        iterable: Iterable[object] = value.values()
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        iterable = value
    else:
        return []
    return [item for item in iterable if isinstance(item, Mapping)]


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _fmt(value: object) -> str:
    return f"{float(value or 0.0):.4f}"


def _markdown_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
