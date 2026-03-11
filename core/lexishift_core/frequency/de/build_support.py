from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
from typing import Any, Callable, Optional
import unicodedata
from xml.etree import ElementTree

_normalize_pos: Optional[Callable[..., Any]]
try:
    from lexishift_core.pos.normalization import normalize_pos as _normalize_pos_impl
except Exception:  # noqa: BLE001
    _normalize_pos = None
else:
    _normalize_pos = _normalize_pos_impl

TOKEN_ALLOWED = re.compile(
    r"^[A-Za-z\u00C4\u00D6\u00DC\u00E4\u00F6\u00FC\u00DF]"
    r"[A-Za-z\u00C4\u00D6\u00DC\u00E4\u00F6\u00FC\u00DF'-]*$"
)
TRIM_PUNCT = '.,;:!?"`~^()[]{}<>|/\\'
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

PROPER_NOUN_TOKENS = {
    "NE",
    "EIG",
    "NPROP",
    "PROPN",
    "EIGENNAME",
    "PROPER",
    "NAMED",
    "NNP",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a German frequency SQLite DB (table=frequency) from Leipzig words.txt "
            "([id]\\t[surface]\\t[count])."
        )
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Path to deu_news_2023_1M-words.txt"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("freq-de-default.sqlite"),
        help="Output SQLite path (default: ./freq-de-default.sqlite)",
    )
    parser.add_argument("--lang", default="de", help="Lemmatizer language code (default: de)")
    parser.add_argument(
        "--min-count",
        type=int,
        default=1,
        help="Drop source rows with count below this value (default: 1)",
    )
    parser.add_argument(
        "--min-lemma-length",
        type=int,
        default=2,
        help="Drop lemmas shorter than this length after normalization (default: 2)",
    )
    parser.add_argument(
        "--min-lemma-count",
        type=int,
        default=2,
        help="Drop aggregated lemmas with count below this value (default: 2; removes hapax)",
    )
    parser.add_argument(
        "--whitelist-min-count",
        type=int,
        default=20,
        help=(
            "If whitelist is enabled, keep non-whitelist lemmas only when count >= this value "
            "(default: 20)"
        ),
    )
    parser.add_argument(
        "--disable-lexicon-whitelist",
        action="store_true",
        help="Disable DE lexicon whitelist filtering (FreeDict/OdeNet/OpenThesaurus)",
    )
    parser.add_argument(
        "--language-packs-dir",
        type=Path,
        default=None,
        help="Language packs directory (default: app data language_packs)",
    )
    parser.add_argument(
        "--freedict-de-en-path",
        type=Path,
        default=None,
        help="Path to deu-eng.tei (overrides auto-discovery)",
    )
    parser.add_argument(
        "--odenet-path",
        type=Path,
        default=None,
        help="Path to odenet_oneline.xml (overrides auto-discovery)",
    )
    parser.add_argument(
        "--openthesaurus-path",
        type=Path,
        default=None,
        help="Path to openthesaurus.txt (overrides auto-discovery)",
    )
    parser.add_argument(
        "--pos-lexicon",
        type=Path,
        default=None,
        help="Optional POS lexicon file (TSV/CSV/semicolon; first 2 columns used by default)",
    )
    parser.add_argument(
        "--pos-delimiter",
        default="auto",
        choices=("auto", "tab", "comma", "semicolon", "pipe"),
        help="POS lexicon delimiter (default: auto)",
    )
    parser.add_argument(
        "--pos-format",
        default="auto",
        choices=("auto", "german_pos_dict", "generic_compact"),
        help=(
            "POS lexicon format: auto (heuristic), german_pos_dict (surface<TAB>lemma<TAB>tag), "
            "or generic_compact (lemma<TAB>tag1|tag2)"
        ),
    )
    parser.add_argument(
        "--pos-lemma-col",
        type=int,
        default=0,
        help="0-based column index for lemma in POS lexicon (default: 0)",
    )
    parser.add_argument(
        "--pos-tag-col",
        type=int,
        default=1,
        help="0-based column index for POS tag in POS lexicon (default: 1)",
    )
    parser.add_argument(
        "--drop-proper-nouns",
        action="store_true",
        help="Drop lemmas tagged as proper nouns when POS lexicon is provided",
    )
    parser.add_argument(
        "--no-lemmatize",
        action="store_true",
        help="Skip lemmatization and use normalized surface forms as lemmas",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite output DB if it already exists"
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=0,
        help="Optional cap for source rows processed (0 means no cap)",
    )
    parser.add_argument(
        "--report-top",
        type=int,
        default=15,
        help="How many top lemmas to print in summary output (default: 15)",
    )
    return parser.parse_args()


def default_language_packs_dir() -> Path:
    return Path.home() / "Library/Application Support/LexiShift/LexiShift/language_packs"


def normalize_token(value: str) -> Optional[str]:
    token = unicodedata.normalize("NFC", str(value or "")).strip()
    if not token:
        return None

    token = token.replace("\u2019", "'").replace("\u2018", "'")
    token = token.replace("\u2013", "-").replace("\u2014", "-")
    token = token.strip(TRIM_PUNCT)
    token = token.strip("-'")
    if not token:
        return None

    if any(ch.isdigit() for ch in token):
        return None

    if not TOKEN_ALLOWED.fullmatch(token):
        return None

    normalized = token.lower()
    if not any(ch.isalpha() for ch in normalized):
        return None
    return normalized


def normalize_pos_tag(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return raw.upper().replace("-", "_").replace(" ", "_")


def split_pos_tags(value: str) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    parts = [part.strip() for part in re.split(r"[|/,;]+", text) if part.strip()]
    return parts or [text]


def counter_to_ranked(counter: Counter[str], *, limit: int = 100) -> list[dict[str, object]]:
    ranked: list[dict[str, object]] = []
    for tag, count in counter.most_common(max(1, int(limit))):
        ranked.append({"tag": tag, "count": int(count)})
    return ranked


def is_pos_unmapped(raw_tag: str) -> bool:
    if _normalize_pos is None:
        return False
    normalized = _normalize_pos(
        raw_tag,
        source_provider="freq-de-default",
        source_kind="frequency",
        source_profile="freq-de-default",
    )
    return not bool(normalized.mapped)


def build_pos_inventory(pos_by_lemma: dict[str, Optional[str]]) -> dict[str, object]:
    rows_with_pos = 0
    rows_without_pos = 0
    pos_tag_counter: Counter[str] = Counter()
    unknown_pos_tag_counter: Counter[str] = Counter()

    for raw_value in pos_by_lemma.values():
        raw_text = str(raw_value or "").strip()
        if not raw_text:
            rows_without_pos += 1
            continue
        rows_with_pos += 1
        for tag in split_pos_tags(raw_text):
            pos_tag_counter[tag] += 1
            if is_pos_unmapped(tag):
                unknown_pos_tag_counter[tag] += 1

    return {
        "rows_with_pos": rows_with_pos,
        "rows_without_pos": rows_without_pos,
        "pos_inventory_size": len(pos_tag_counter),
        "pos_inventory_top": counter_to_ranked(pos_tag_counter),
        "unknown_pos_inventory_size": len(unknown_pos_tag_counter),
        "unknown_pos_inventory_top": counter_to_ranked(unknown_pos_tag_counter),
        "pos_source_provider": "freq-de-default",
        "pos_source_kind": "frequency",
        "pos_mapping_profile": "freq-de-default" if _normalize_pos is not None else None,
        "pos_mapping_available": bool(_normalize_pos is not None),
    }


def is_proper_noun_tag(tag: str) -> bool:
    normalized = normalize_pos_tag(tag)
    if not normalized:
        return False
    parts = [part for part in re.split(r"[:_|]", normalized) if part]
    part_set = set(parts)
    for token in PROPER_NOUN_TOKENS:
        if token in part_set:
            return True
    return False


def load_freedict_headwords(path: Path) -> set[str]:
    lemmas: set[str] = set()
    if not path.exists():
        return lemmas
    try:
        for _event, elem in ElementTree.iterparse(path, events=("end",)):
            if elem.tag != f"{{{TEI_NS['tei']}}}entry":
                continue
            for orth in elem.findall("tei:form/tei:orth", TEI_NS):
                text = (orth.text or "").strip()
                lemma = normalize_token(text)
                if lemma:
                    lemmas.add(lemma)
            elem.clear()
    except (ElementTree.ParseError, OSError):
        return set()
    return lemmas


def load_openthesaurus_lemmas(path: Path) -> set[str]:
    lemmas: set[str] = set()
    if not path.exists():
        return lemmas
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(";") if part.strip()]
        for word in parts:
            lemma = normalize_token(word)
            if lemma:
                lemmas.add(lemma)
    return lemmas


def load_odenet_lemmas(path: Path) -> set[str]:
    lemmas: set[str] = set()
    if not path.exists():
        return lemmas
    try:
        for event, elem in ElementTree.iterparse(path, events=("start", "end")):
            if event == "start" and elem.tag.endswith("Lemma"):
                value = elem.get("writtenForm")
                lemma = normalize_token(value or "")
                if lemma:
                    lemmas.add(lemma)
    except ElementTree.ParseError:
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return set()
        for value in re.findall(r'writtenForm="([^"]+)"', raw):
            lemma = normalize_token(value)
            if lemma:
                lemmas.add(lemma)
    except OSError:
        return set()
    return lemmas


def discover_dictionary_paths(
    *,
    language_packs_dir: Path,
    freedict_de_en_path: Optional[Path],
    odenet_path: Optional[Path],
    openthesaurus_path: Optional[Path],
) -> tuple[Optional[Path], Optional[Path], Optional[Path]]:
    resolved_freedict = Path(freedict_de_en_path) if freedict_de_en_path else None
    if resolved_freedict is None:
        candidates = [
            language_packs_dir / "deu-eng.tei",
            language_packs_dir / "freedict-de-en" / "deu-eng.tei",
        ]
        for candidate in candidates:
            if candidate.exists():
                resolved_freedict = candidate
                break

    resolved_odenet = Path(odenet_path) if odenet_path else None
    if resolved_odenet is None:
        candidate = language_packs_dir / "odenet_oneline.xml"
        if candidate.exists():
            resolved_odenet = candidate

    resolved_open = Path(openthesaurus_path) if openthesaurus_path else None
    if resolved_open is None:
        candidate = language_packs_dir / "openthesaurus.txt"
        if candidate.exists():
            resolved_open = candidate

    return resolved_freedict, resolved_odenet, resolved_open
