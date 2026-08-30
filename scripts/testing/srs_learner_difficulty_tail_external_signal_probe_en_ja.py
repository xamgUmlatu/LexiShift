#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import lzma
import math
from pathlib import Path
import re
import sqlite3
import sys
from typing import Mapping, Sequence
from xml.etree import ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
    _repo_or_home_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)


PAIR = "en-ja"
DATA_ROOT = Path.home() / "Library" / "Application Support" / "LexiShift" / "LexiShift"
DEFAULT_WORKING_SET_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_tail_litmus_working_set_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_tail_external_signal_probe_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_tail_external_signal_probe_en_ja_latest.md"
)
DEFAULT_JMDICT = DATA_ROOT / "language_packs" / "jmdict-ja-en" / "JMdict_e"
DEFAULT_BCCWJ_SQLITE = DATA_ROOT / "frequency_packs" / "freq-ja-bccwj" / "main.sqlite"
DEFAULT_TUBELEX_TSV_XZ = (
    DATA_ROOT / "frequency_packs" / "freq-ja-tubelex" / "tubelex-ja-lemma-pos.tsv.xz"
)

KATAKANA_START = ord("ァ")
KATAKANA_END = ord("ヶ")
HIRAGANA_OFFSET = ord("ぁ") - ord("ァ")
ASCIIISH_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 .'+/_-]*$")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'+-]*")
COMMON_FUNCTION_POS_PREFIXES = ("助詞", "助動詞", "補助記号", "空白")
ENGLISH_GLOSS_STOPWORDS = {
    "a",
    "an",
    "and",
    "another",
    "as",
    "at",
    "by",
    "etc",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "one",
    "or",
    "other",
    "the",
    "to",
    "used",
    "using",
    "with",
}
DOMAIN_OR_MARKED_TERMS = {
    "archaism",
    "archaic",
    "dated term",
    "derogatory",
    "historical term",
    "humble language",
    "honorific or respectful",
    "obscure term",
    "obsolete term",
    "rare term",
    "slang",
    "vulgar expression or word",
}
TECHNICAL_FIELDS = {
    "anatomy",
    "biology",
    "botany",
    "business",
    "chemistry",
    "computing",
    "dentistry",
    "engineering",
    "law",
    "medicine",
    "physics",
    "zoology",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Attach external/raw lexical evidence to the fixed en-ja upper-tail "
            "working set. This is a diagnostic artifact, not a production scorer."
        )
    )
    parser.add_argument("--working-set-json", type=Path, default=DEFAULT_WORKING_SET_JSON)
    parser.add_argument("--jmdict", type=Path, default=DEFAULT_JMDICT)
    parser.add_argument("--bccwj-sqlite", type=Path, default=DEFAULT_BCCWJ_SQLITE)
    parser.add_argument("--tubelex-tsv-xz", type=Path, default=DEFAULT_TUBELEX_TSV_XZ)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        working_set_json_path=_resolve_path(args.working_set_json),
        jmdict_path=_resolve_path(args.jmdict),
        bccwj_sqlite_path=_resolve_path(args.bccwj_sqlite),
        tubelex_tsv_xz_path=_resolve_path(args.tubelex_tsv_xz),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    working_set_json_path: Path,
    jmdict_path: Path,
    bccwj_sqlite_path: Path,
    tubelex_tsv_xz_path: Path,
) -> dict[str, object]:
    working_payload = json.loads(working_set_json_path.read_text(encoding="utf-8"))
    working_rows = [
        row for row in _rows(working_payload.get("working_set")) if bool(row.get("found"))
    ]
    sudachi_probe = SudachiProbe()
    bccwj_probe = BccwjProbe(bccwj_sqlite_path)
    wordfreq_probe = WordfreqProbe()
    sudachi_by_key = {
        _row_key(row): sudachi_probe.analyze(str(row["lemma"])) for row in working_rows
    }
    family_terms_by_key = {
        key: tuple(_family_terms(str(row["lemma"]), sudachi_by_key[key]))
        for key, row in ((_row_key(row), row) for row in working_rows)
    }
    all_terms = {str(row["lemma"]) for row in working_rows} | {
        term for terms in family_terms_by_key.values() for term in terms
    }
    tubelex_probe = TubelexProbe(tubelex_tsv_xz_path, all_terms)
    jmdict_probe = JmdictProbe(jmdict_path, working_rows)
    enriched_rows = []
    for row in working_rows:
        key = _row_key(row)
        lemma = str(row["lemma"])
        reading = str(row["reading"])
        sudachi = sudachi_by_key[key]
        family_terms = family_terms_by_key[key]
        jmdict = jmdict_probe.lookup(lemma, reading)
        bccwj = bccwj_probe.lookup(lemma, family_terms=family_terms)
        tubelex = tubelex_probe.lookup(lemma, family_terms=family_terms)
        english = _english_source_probe(
            jmdict=jmdict,
            bccwj=bccwj,
            wordfreq_probe=wordfreq_probe,
        )
        wordfreq = {
            "surface_zipf": wordfreq_probe.zipf(lemma, "ja"),
            "best_family_zipf": _best_wordfreq_zipf(wordfreq_probe, family_terms, lang="ja"),
        }
        probes = {
            "sudachi": sudachi,
            "jmdict_raw": jmdict,
            "bccwj_raw": bccwj,
            "tubelex_raw": tubelex,
            "wordfreq": wordfreq,
            "english_source": english,
            "empirical_hints": _empirical_hints(
                row=row,
                sudachi=sudachi,
                jmdict=jmdict,
                bccwj=bccwj,
                tubelex=tubelex,
                wordfreq=wordfreq,
                english=english,
            ),
        }
        enriched_rows.append({**row, "external_signal_probe": probes})
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "model_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Gather raw/external evidence for the frozen upper-tail failure "
                "working set before proposing another model rule. The probes are "
                "diagnostic signals: they are not added to the production model here."
            ),
            "probe_groups": [
                "Sudachi segmentation and dictionary-form family behavior",
                "Raw BCCWJ exact and family frequency rows",
                "Raw Tubelex exact and family spoken-video counts",
                "Raw JMDict pair/surface breadth, priority, field, misc, source, glosses",
                "wordfreq Japanese surface/family Zipf frequency",
                "English-source candidate frequency for gairaigo/loanword rows",
            ],
        },
        "inputs": {
            "working_set_json": _repo_or_home_path(working_set_json_path),
            "jmdict": _repo_or_home_path(jmdict_path),
            "bccwj_sqlite": _repo_or_home_path(bccwj_sqlite_path),
            "tubelex_tsv_xz": _repo_or_home_path(tubelex_tsv_xz_path),
            "working_row_count": len(working_rows),
            "tubelex_terms_scanned": len(all_terms),
            "wordfreq_available": wordfreq_probe.available,
            "sudachi_available": sudachi_probe.available,
        },
        "rows": enriched_rows,
        "pattern_summary": _pattern_summary(enriched_rows),
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "working_set_json": working_set_json_path,
                "jmdict": jmdict_path,
                "bccwj_sqlite": bccwj_sqlite_path,
                "tubelex_tsv_xz": tubelex_tsv_xz_path,
            },
            code_paths={
                **_srs_difficulty_code_paths(),
                "external_signal_probe": Path(__file__),
            },
        ),
    }


class SudachiProbe:
    def __init__(self) -> None:
        try:
            from sudachipy import dictionary, tokenizer
        except Exception as exc:  # pragma: no cover - diagnostic fallback.
            self.available = False
            self.error = f"{type(exc).__name__}: {exc}"
            self._tokenizer = None
            self._modes = {}
            return
        self.available = True
        self.error = None
        self._tokenizer = dictionary.Dictionary().create()
        self._modes = {
            "A": tokenizer.Tokenizer.SplitMode.A,
            "B": tokenizer.Tokenizer.SplitMode.B,
            "C": tokenizer.Tokenizer.SplitMode.C,
        }

    def analyze(self, surface: str) -> dict[str, object]:
        if not self.available or self._tokenizer is None:
            return {"available": False, "error": self.error}
        modes = {}
        for name, mode in self._modes.items():
            tokens = [
                self._token_payload(morpheme)
                for morpheme in self._tokenizer.tokenize(surface, mode)
            ]
            modes[name] = {
                "token_count": len(tokens),
                "tokens": tokens,
            }
        c_tokens = list(_rows(modes["C"]["tokens"]))
        content_tokens = [
            token
            for token in c_tokens
            if not str(token.get("pos", "")).startswith(COMMON_FUNCTION_POS_PREFIXES)
        ]
        content_base_forms = tuple(
            dict.fromkeys(str(token.get("dictionary_form") or "") for token in content_tokens)
        )
        return {
            "available": True,
            "mode_token_counts": {name: modes[name]["token_count"] for name in modes},
            "mode_c_tokens": modes["C"]["tokens"],
            "content_token_count_c": len(content_tokens),
            "content_dictionary_forms_c": list(content_base_forms),
            "single_content_token_c": len(content_tokens) == 1,
            "has_function_tail_c": len(content_tokens) < len(c_tokens),
            "has_oov_c": any(bool(token.get("is_oov")) for token in c_tokens),
            "base_form_differs_c": any(
                str(token.get("surface")) != str(token.get("dictionary_form"))
                for token in content_tokens
            ),
        }

    @staticmethod
    def _token_payload(morpheme: object) -> dict[str, object]:
        pos = tuple(str(part) for part in morpheme.part_of_speech())
        return {
            "surface": str(morpheme.surface()),
            "dictionary_form": str(morpheme.dictionary_form()),
            "normalized_form": str(morpheme.normalized_form()),
            "reading_form": str(morpheme.reading_form()),
            "pos": "-".join(part for part in pos if part != "*"),
            "word_id": int(morpheme.word_id()),
            "dictionary_id": int(morpheme.dictionary_id()),
            "is_oov": bool(morpheme.is_oov()),
        }


class WordfreqProbe:
    def __init__(self) -> None:
        try:
            from wordfreq import zipf_frequency
        except Exception as exc:  # pragma: no cover - diagnostic fallback.
            self.available = False
            self.error = f"{type(exc).__name__}: {exc}"
            self._zipf_frequency = None
            return
        self.available = True
        self.error = None
        self._zipf_frequency = zipf_frequency

    def zipf(self, word: str | None, lang: str) -> float | None:
        if not self.available or self._zipf_frequency is None:
            return None
        if word is None or not str(word).strip():
            return None
        try:
            return _finite_or_none(float(self._zipf_frequency(str(word).strip(), lang)))
        except Exception:
            return None


class BccwjProbe:
    def __init__(self, sqlite_path: Path) -> None:
        self.sqlite_path = sqlite_path

    def lookup(self, surface: str, *, family_terms: Sequence[str]) -> dict[str, object]:
        if not self.sqlite_path.exists():
            return {"available": False, "error": f"missing: {self.sqlite_path}"}
        con = sqlite3.connect(self.sqlite_path)
        con.row_factory = sqlite3.Row
        try:
            exact_rows = self._query(con, surface)
            family_rows = [
                {**row, "queried_term": term}
                for term in family_terms
                if term != surface
                for row in self._query(con, term)
            ]
        finally:
            con.close()
        best_exact = _best_ranked(exact_rows)
        best_family = _best_ranked(family_rows)
        return {
            "available": True,
            "exact_match_count": len(exact_rows),
            "best_exact": best_exact,
            "family_match_count": len(family_rows),
            "best_family": best_family,
            "family_terms": list(family_terms),
            "family_rank_gain": _rank_gain(best_exact, best_family),
            "family_pmw_gain": _pmw_gain(best_exact, best_family),
            "sublemma_candidates": sorted(
                {
                    str(row.get("sublemma"))
                    for row in exact_rows
                    if row.get("sublemma") not in (None, "")
                }
            ),
            "wtypes": sorted(
                {str(row.get("wtype")) for row in exact_rows if row.get("wtype") not in (None, "")}
            ),
        }

    @staticmethod
    def _query(con: sqlite3.Connection, term: str) -> list[dict[str, object]]:
        rows = con.execute(
            """
            SELECT rank, lform, lemma, pos, sublemma, wtype, frequency, pmw,
                   core_rank, core_frequency, core_pmw
            FROM frequency
            WHERE lemma = ? OR sublemma = ?
            ORDER BY COALESCE(core_rank, rank, 999999999), COALESCE(rank, 999999999)
            LIMIT 12
            """,
            (term, term),
        ).fetchall()
        return [_sqlite_row(row) for row in rows]


class TubelexProbe:
    def __init__(self, tsv_xz_path: Path, target_terms: set[str]) -> None:
        self.tsv_xz_path = tsv_xz_path
        self.rows_by_word = self._load_rows(target_terms)

    def lookup(self, surface: str, *, family_terms: Sequence[str]) -> dict[str, object]:
        exact_rows = self.rows_by_word.get(surface, [])
        family_rows = [
            {**row, "queried_term": term}
            for term in family_terms
            if term != surface
            for row in self.rows_by_word.get(term, [])
        ]
        best_exact = _best_tubelex(exact_rows)
        best_family = _best_tubelex(family_rows)
        return {
            "available": self.tsv_xz_path.exists(),
            "exact_match_count": len(exact_rows),
            "best_exact": best_exact,
            "family_match_count": len(family_rows),
            "best_family": best_family,
            "family_count_gain": _count_gain(best_exact, best_family),
        }

    def _load_rows(self, target_terms: set[str]) -> dict[str, list[dict[str, object]]]:
        if not self.tsv_xz_path.exists():
            return {}
        csv.field_size_limit(sys.maxsize)
        rows_by_word: dict[str, list[dict[str, object]]] = {}
        with lzma.open(self.tsv_xz_path, "rt", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                word = str(row.get("word") or "")
                if word not in target_terms:
                    continue
                rows_by_word.setdefault(word, []).append(
                    {
                        "word": word,
                        "count": _int_or_none(row.get("count")),
                        "videos": _int_or_none(row.get("videos")),
                        "channels": _int_or_none(row.get("channels")),
                        "pos": row.get("pos"),
                    }
                )
        return rows_by_word


class JmdictProbe:
    def __init__(self, jmdict_path: Path, working_rows: Sequence[Mapping[str, object]]) -> None:
        self.jmdict_path = jmdict_path
        self.target_surfaces = {str(row["lemma"]) for row in working_rows}
        self.target_readings = {_normalize_kana(str(row["reading"])) for row in working_rows}
        self.entries_by_surface: dict[str, list[dict[str, object]]] = {
            surface: [] for surface in self.target_surfaces
        }
        self.entries_by_reading: dict[str, list[dict[str, object]]] = {
            reading: [] for reading in self.target_readings
        }
        self._load()

    def lookup(self, surface: str, reading: str) -> dict[str, object]:
        normalized_reading = _normalize_kana(reading)
        surface_entries = self.entries_by_surface.get(surface, [])
        reading_entries = self.entries_by_reading.get(normalized_reading, [])
        pair_entries = [
            entry
            for entry in surface_entries
            if normalized_reading in entry.get("normalized_readings", ())
        ]
        aggregate = _aggregate_jmdict(pair_entries)
        return {
            "available": self.jmdict_path.exists(),
            "surface_entry_count": len(surface_entries),
            "reading_entry_count": len(reading_entries),
            "pair_entry_count": len(pair_entries),
            "pair_entry_ids": [entry["ent_seq"] for entry in pair_entries],
            **aggregate,
        }

    def _load(self) -> None:
        if not self.jmdict_path.exists():
            return
        for _event, elem in ET.iterparse(self.jmdict_path, events=("end",)):
            if elem.tag != "entry":
                continue
            entry = _jmdict_entry_payload(elem)
            matched_surfaces = set(entry["surfaces"]) & self.target_surfaces
            matched_readings = set(entry["normalized_readings"]) & self.target_readings
            for surface in matched_surfaces:
                self.entries_by_surface.setdefault(surface, []).append(entry)
            for reading in matched_readings:
                self.entries_by_reading.setdefault(reading, []).append(entry)
            elem.clear()


def _jmdict_entry_payload(elem: ET.Element) -> dict[str, object]:
    kebs = [child.text or "" for child in elem.findall("./k_ele/keb")]
    rebs = [child.text or "" for child in elem.findall("./r_ele/reb")]
    surfaces = tuple(dict.fromkeys([*kebs, *rebs]))
    normalized_readings = tuple(dict.fromkeys(_normalize_kana(reading) for reading in rebs))
    priority_tags = [child.text or "" for child in elem.findall("./k_ele/ke_pri") if child.text] + [
        child.text or "" for child in elem.findall("./r_ele/re_pri") if child.text
    ]
    senses = []
    for sense in elem.findall("./sense"):
        glosses = [gloss.text or "" for gloss in sense.findall("gloss") if gloss.text]
        fields = [field.text or "" for field in sense.findall("field") if field.text]
        misc = [misc.text or "" for misc in sense.findall("misc") if misc.text]
        pos = [pos.text or "" for pos in sense.findall("pos") if pos.text]
        sources = []
        for source in sense.findall("lsource"):
            lang = source.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
            source_type = source.attrib.get("ls_type")
            sources.append(
                {
                    "text": source.text,
                    "lang": lang,
                    "type": source_type,
                    "wasei": source.attrib.get("ls_wasei"),
                }
            )
        senses.append(
            {
                "glosses": glosses,
                "fields": fields,
                "misc": misc,
                "pos": pos,
                "sources": sources,
            }
        )
    return {
        "ent_seq": elem.findtext("ent_seq"),
        "kebs": kebs,
        "rebs": rebs,
        "surfaces": surfaces,
        "normalized_readings": normalized_readings,
        "priority_tags": sorted(set(priority_tags)),
        "has_priority": bool(priority_tags),
        "senses": senses,
    }


def _aggregate_jmdict(entries: Sequence[Mapping[str, object]]) -> dict[str, object]:
    senses = [sense for entry in entries for sense in _rows(entry.get("senses"))]
    glosses = [
        str(gloss)
        for sense in senses
        for gloss in _rows(sense.get("glosses"))
        if str(gloss).strip()
    ]
    fields = sorted(
        {
            str(field)
            for sense in senses
            for field in _rows(sense.get("fields"))
            if str(field).strip()
        }
    )
    misc = sorted(
        {str(item) for sense in senses for item in _rows(sense.get("misc")) if str(item).strip()}
    )
    pos = sorted(
        {str(item) for sense in senses for item in _rows(sense.get("pos")) if str(item).strip()}
    )
    sources = [source for sense in senses for source in _rows(sense.get("sources"))]
    source_langs = sorted(
        {str(source.get("lang")) for source in sources if source.get("lang") not in (None, "")}
    )
    source_texts = sorted(
        {str(source.get("text")) for source in sources if source.get("text") not in (None, "")}
    )
    priority_tags = sorted(
        {
            str(tag)
            for entry in entries
            for tag in _rows(entry.get("priority_tags"))
            if str(tag).strip()
        }
    )
    marked_terms = sorted(set(misc) & DOMAIN_OR_MARKED_TERMS)
    technical_fields = sorted(set(fields) & TECHNICAL_FIELDS)
    return {
        "sense_count": len(senses),
        "gloss_count": len(glosses),
        "first_glosses": glosses[:8],
        "pos": pos,
        "fields": fields,
        "misc": misc,
        "source_langs": source_langs,
        "source_texts": source_texts,
        "priority_tags": priority_tags,
        "has_priority": bool(priority_tags),
        "marked_misc_terms": marked_terms,
        "technical_fields": technical_fields,
        "has_domain_or_marked_evidence": bool(marked_terms or technical_fields),
    }


def _english_source_probe(
    *,
    jmdict: Mapping[str, object],
    bccwj: Mapping[str, object],
    wordfreq_probe: WordfreqProbe,
) -> dict[str, object]:
    origin_candidates: list[dict[str, object]] = []
    gloss_candidates: list[dict[str, object]] = []
    for candidate in _rows(bccwj.get("sublemma_candidates")):
        text = str(candidate)
        if ASCIIISH_RE.match(text):
            origin_candidates.append({"source": "bccwj_sublemma", "text": text})
    for source_text in _rows(jmdict.get("source_texts")):
        text = str(source_text)
        if ASCIIISH_RE.match(text):
            origin_candidates.append({"source": "jmdict_lsource", "text": text})
    for gloss in _rows(jmdict.get("first_glosses")):
        gloss_text = str(gloss)
        phrase = _clean_gloss_phrase(gloss_text)
        if phrase:
            gloss_candidates.append({"source": "jmdict_gloss_phrase", "text": phrase})
        for word in WORD_RE.findall(gloss_text):
            if len(word) >= 3 and word.lower() not in ENGLISH_GLOSS_STOPWORDS:
                gloss_candidates.append({"source": "jmdict_gloss_word", "text": word})
    origin_candidates = _zipf_candidates(origin_candidates, wordfreq_probe)
    gloss_candidates = _zipf_candidates(gloss_candidates, wordfreq_probe)
    best_origin = _best_english_candidate(origin_candidates)
    best_gloss = _best_english_candidate(gloss_candidates)
    best = best_origin or best_gloss
    source_langs = set(str(lang) for lang in _rows(jmdict.get("source_langs")))
    non_english_source_langs = sorted(lang for lang in source_langs if lang not in {"eng"})
    return {
        "origin_candidate_count": len(origin_candidates),
        "origin_candidates": origin_candidates[:12],
        "gloss_candidate_count": len(gloss_candidates),
        "gloss_candidates": gloss_candidates[:12],
        "best_origin_candidate": best_origin,
        "best_origin_zipf": None if best_origin is None else best_origin.get("english_zipf"),
        "best_gloss_candidate": best_gloss,
        "best_gloss_zipf": None if best_gloss is None else best_gloss.get("english_zipf"),
        "best_candidate": best,
        "best_zipf": None if best is None else best.get("english_zipf"),
        "jmdict_source_langs": sorted(source_langs),
        "non_english_source_langs": non_english_source_langs,
    }


def _zipf_candidates(
    candidates: Sequence[Mapping[str, object]],
    wordfreq_probe: WordfreqProbe,
) -> list[dict[str, object]]:
    deduped = []
    seen = set()
    for candidate in candidates:
        key = (str(candidate["source"]), str(candidate["text"]).lower())
        if key in seen:
            continue
        seen.add(key)
        zipf = wordfreq_probe.zipf(str(candidate["text"]), "en")
        deduped.append({**candidate, "english_zipf": zipf})
    return sorted(
        deduped,
        key=lambda item: (
            -1.0 if item.get("english_zipf") is None else -float(item["english_zipf"]),
            str(item.get("source") or ""),
            str(item.get("text") or ""),
        ),
    )


def _best_english_candidate(
    candidates: Sequence[Mapping[str, object]],
) -> dict[str, object] | None:
    return dict(candidates[0]) if candidates else None


def _empirical_hints(
    *,
    row: Mapping[str, object],
    sudachi: Mapping[str, object],
    jmdict: Mapping[str, object],
    bccwj: Mapping[str, object],
    tubelex: Mapping[str, object],
    wordfreq: Mapping[str, object],
    english: Mapping[str, object],
) -> dict[str, object]:
    bccwj_rank_gain = _float_or_none(bccwj.get("family_rank_gain"))
    bccwj_pmw_gain = _float_or_none(bccwj.get("family_pmw_gain"))
    tubelex_count_gain = _float_or_none(tubelex.get("family_count_gain"))
    origin_zipf = _float_or_none(english.get("best_origin_zipf"))
    jmdict_domain = bool(jmdict.get("has_domain_or_marked_evidence"))
    exact_bccwj = _mapping(bccwj.get("best_exact"))
    exact_tubelex = _mapping(tubelex.get("best_exact"))
    source_diversity = sum(
        [
            bool(jmdict.get("pair_entry_count")),
            bool(exact_bccwj),
            bool(exact_tubelex),
            _float_or_none(wordfreq.get("surface_zipf")) not in (None, 0.0),
            bool(sudachi.get("available")) and not bool(sudachi.get("has_oov_c")),
        ]
    )
    inflected_or_family_rescue = bool(
        sudachi.get("base_form_differs_c")
        and (
            (bccwj_rank_gain is not None and bccwj_rank_gain >= 2.0)
            or (bccwj_pmw_gain is not None and bccwj_pmw_gain >= 2.0)
            or (tubelex_count_gain is not None and tubelex_count_gain >= 2.0)
        )
    )
    compound_family_hint = bool(
        not sudachi.get("base_form_differs_c")
        and int(sudachi.get("content_token_count_c") or 0) >= 2
        and (
            (bccwj_pmw_gain is not None and bccwj_pmw_gain >= 3.0)
            or (tubelex_count_gain is not None and tubelex_count_gain >= 3.0)
        )
    )
    gairaigo_wtype = "外" in set(str(item) for item in _rows(bccwj.get("wtypes")))
    origin_known = bool(gairaigo_wtype and origin_zipf is not None and origin_zipf > 0.0)
    non_english_source = bool(english.get("non_english_source_langs"))
    english_gairaigo_ease = bool(origin_known and not non_english_source)
    loan_familiarity_clue = bool(origin_known and non_english_source)
    true_tail_candidate = bool(
        not inflected_or_family_rescue
        and not english_gairaigo_ease
        and source_diversity <= 3
        and not bool(jmdict.get("has_priority"))
        and (
            jmdict_domain
            or not exact_tubelex
            or (exact_tubelex and int(exact_tubelex.get("count") or 0) <= 1)
        )
    )
    hints = []
    if inflected_or_family_rescue:
        hints.append("family/base-frequency rescue")
    if compound_family_hint:
        hints.append("compound components are common, but exact word still needs caution")
    if english_gairaigo_ease:
        hints.append("English-source gairaigo clue")
    if loan_familiarity_clue:
        hints.append("non-English loan with English familiarity clue")
    if jmdict_domain:
        hints.append("domain/marked dictionary evidence")
    if true_tail_candidate:
        hints.append("true-tail candidate")
    if not hints:
        hints.append("no strong external discriminator")
    return {
        "source_diversity_count": source_diversity,
        "inflected_or_family_rescue": inflected_or_family_rescue,
        "compound_family_hint": compound_family_hint,
        "gairaigo_wtype": gairaigo_wtype,
        "gairaigo_origin_known": origin_known,
        "non_english_source": non_english_source,
        "english_gairaigo_ease": english_gairaigo_ease,
        "loan_familiarity_clue": loan_familiarity_clue,
        "domain_or_marked_jmdict": jmdict_domain,
        "true_tail_candidate": true_tail_candidate,
        "hints": hints,
        "human_readable": "; ".join(hints),
        "expected_minus_current": _expected_minus_current(row),
    }


def _pattern_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    hint_counts: dict[str, int] = {}
    by_group: dict[str, dict[str, int]] = {}
    examples_by_hint: dict[str, list[str]] = {}
    for row in rows:
        group = str(row.get("group") or "")
        surface = f"{row.get('lemma')}/{row.get('reading')}"
        hints = _mapping(row.get("external_signal_probe")).get("empirical_hints")
        for hint in _rows(_mapping(hints).get("hints")):
            hint_key = str(hint)
            hint_counts[hint_key] = hint_counts.get(hint_key, 0) + 1
            by_group.setdefault(group, {})
            by_group[group][hint_key] = by_group[group].get(hint_key, 0) + 1
            examples_by_hint.setdefault(hint_key, [])
            if len(examples_by_hint[hint_key]) < 6:
                examples_by_hint[hint_key].append(surface)
    return {
        "row_count": len(rows),
        "hint_counts": hint_counts,
        "hint_counts_by_group": by_group,
        "examples_by_hint": examples_by_hint,
        "interpretation": (
            "The useful split is not one more rarity scalar. The new probes identify "
            "separate destinations: inflected/base-frequency rescue, English-source "
            "or loanword familiarity clues, domain/marked advanced terms, and sparse true-tail "
            "candidates."
        ),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    rows = [_mapping(row) for row in _rows(report.get("rows"))]
    lines = [
        "# en-ja Tail External Signal Probe",
        "",
        f"- Generated: `{_escape(str(report.get('generated_at')))}`",
        "- Runtime/model behavior changed: `false`",
        "- Purpose: empirically inspect new raw/external signals on the frozen failure working set before adding another rule.",
        "",
        "## Sources",
        "",
    ]
    inputs = _mapping(report.get("inputs"))
    for key in ("working_set_json", "jmdict", "bccwj_sqlite", "tubelex_tsv_xz"):
        lines.append(f"- `{key}`: `{_escape(str(inputs.get(key)))}`")
    lines.extend(
        [
            f"- `wordfreq_available`: `{_escape(str(inputs.get('wordfreq_available')))}`",
            f"- `sudachi_available`: `{_escape(str(inputs.get('sudachi_available')))}`",
            "",
            "## What The New Signals Say",
            "",
            "| Group | Row | Expected | Current | No cap | JMDict raw | BCCWJ exact/family | Tubelex exact/family | Sudachi | wordfreq ja | English source | Hint |",
            "| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        probe = _mapping(row.get("external_signal_probe"))
        jmdict = _mapping(probe.get("jmdict_raw"))
        bccwj = _mapping(probe.get("bccwj_raw"))
        tubelex = _mapping(probe.get("tubelex_raw"))
        sudachi = _mapping(probe.get("sudachi"))
        wordfreq = _mapping(probe.get("wordfreq"))
        english = _mapping(probe.get("english_source"))
        hints = _mapping(probe.get("empirical_hints"))
        lines.append(
            "| "
            f"{_escape(str(row.get('group')))} | "
            f"`{_escape(str(row.get('lemma')))}/{_escape(str(row.get('reading')))}` | "
            f"{_fmt_expected(row)} | "
            f"{_fmt_score(row, 'current_hard_cap')} | "
            f"{_fmt_score(row, 'no_cap')} | "
            f"{_fmt_jmdict_cell(jmdict)} | "
            f"{_fmt_bccwj_cell(bccwj)} | "
            f"{_fmt_tubelex_cell(tubelex)} | "
            f"{_fmt_sudachi_cell(sudachi)} | "
            f"{_fmt_float(wordfreq.get('surface_zipf'))}/{_fmt_best_family_zipf(wordfreq)} | "
            f"{_fmt_english_cell(english)} | "
            f"{_escape(str(hints.get('human_readable') or ''))} |"
        )
    lines.extend(
        [
            "",
            "## Pattern Summary",
            "",
            "```json",
            json.dumps(report.get("pattern_summary"), ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Immediate Read",
            "",
            "- The family/base probe is strongest for forms like `翻って`: exact surface rarity should not be treated as true lexical-tail evidence when a Sudachi base form has much better corpus support.",
            "- Gairaigo rows need a source-aware split: `デバッグ` and `ワンピ` have BCCWJ sublemma source clues, while `ジェラート`/`キュイジーヌ` are explicitly non-English loans with only an English-familiarity proxy.",
            "- JMDict field/misc evidence is useful for domain or register placement (`dentistry`, `historical term`, etc.), but it is a destination selector, not a monotonic rarity score.",
            "- The remaining hard cases are sparse ordinary words: if they have no family rescue, no English/source ease, no priority, and low corpus diversity, they are better candidates for upper-tail treatment.",
            "",
        ]
    )
    return "\n".join(lines)


def _family_terms(surface: str, sudachi: Mapping[str, object]) -> list[str]:
    terms = [surface]
    for base_form in _rows(sudachi.get("content_dictionary_forms_c")):
        base = str(base_form)
        if base and base not in terms:
            terms.append(base)
    return terms


def _normalize_kana(text: str) -> str:
    chars = []
    for char in text:
        code = ord(char)
        if KATAKANA_START <= code <= KATAKANA_END:
            chars.append(chr(code + HIRAGANA_OFFSET))
        else:
            chars.append(char)
    return "".join(chars)


def _clean_gloss_phrase(text: str) -> str:
    phrase = re.sub(r"\([^)]*\)", "", text).strip()
    phrase = re.split(r"[,;]", phrase, maxsplit=1)[0].strip()
    return phrase if ASCIIISH_RE.match(phrase) else ""


def _best_wordfreq_zipf(
    wordfreq_probe: WordfreqProbe,
    terms: Sequence[str],
    *,
    lang: str,
) -> dict[str, object] | None:
    candidates = [{"term": term, "zipf": wordfreq_probe.zipf(term, lang)} for term in terms if term]
    candidates = [item for item in candidates if item.get("zipf") is not None]
    if not candidates:
        return None
    return max(candidates, key=lambda item: float(item["zipf"]))


def _best_ranked(rows: Sequence[Mapping[str, object]]) -> dict[str, object] | None:
    if not rows:
        return None
    return dict(
        min(
            rows,
            key=lambda row: (
                float(row.get("core_rank") or row.get("rank") or math.inf),
                float(row.get("rank") or math.inf),
            ),
        )
    )


def _best_tubelex(rows: Sequence[Mapping[str, object]]) -> dict[str, object] | None:
    if not rows:
        return None
    return dict(
        max(
            rows,
            key=lambda row: (
                int(row.get("count") or 0),
                int(row.get("videos") or 0),
                int(row.get("channels") or 0),
            ),
        )
    )


def _rank_gain(
    exact: Mapping[str, object] | None,
    family: Mapping[str, object] | None,
) -> float | None:
    if not exact or not family:
        return None
    exact_rank = _float_or_none(exact.get("core_rank")) or _float_or_none(exact.get("rank"))
    family_rank = _float_or_none(family.get("core_rank")) or _float_or_none(family.get("rank"))
    if not exact_rank or not family_rank or family_rank <= 0:
        return None
    return _finite_or_none(exact_rank / family_rank)


def _pmw_gain(
    exact: Mapping[str, object] | None,
    family: Mapping[str, object] | None,
) -> float | None:
    if not exact or not family:
        return None
    exact_pmw = _float_or_none(exact.get("core_pmw")) or _float_or_none(exact.get("pmw")) or 0.0
    family_pmw = _float_or_none(family.get("core_pmw")) or _float_or_none(family.get("pmw")) or 0.0
    if exact_pmw <= 0:
        return None if family_pmw <= 0 else math.inf
    return _finite_or_none(family_pmw / exact_pmw)


def _count_gain(
    exact: Mapping[str, object] | None,
    family: Mapping[str, object] | None,
) -> float | None:
    if not family:
        return None
    exact_count = int(_mapping(exact).get("count") or 0)
    family_count = int(family.get("count") or 0)
    if exact_count <= 0:
        return None
    return _finite_or_none(family_count / exact_count)


def _expected_minus_current(row: Mapping[str, object]) -> float | None:
    expected = _expected_value(row)
    current = _mapping(row.get("scores")).get("current_hard_cap")
    if expected is None or current is None:
        return None
    return _finite_or_none(float(expected) - float(current))


def _fmt_expected(row: Mapping[str, object]) -> str:
    return _fmt_float(_expected_value(row))


def _fmt_score(row: Mapping[str, object], name: str) -> str:
    return _fmt_float(_mapping(row.get("scores")).get(name))


def _fmt_jmdict_cell(jmdict: Mapping[str, object]) -> str:
    parts = [
        f"pair={jmdict.get('pair_entry_count')}",
        f"sense={jmdict.get('sense_count')}",
    ]
    if jmdict.get("has_priority"):
        parts.append("pri")
    marked = [
        *list(_rows(jmdict.get("technical_fields"))),
        *list(_rows(jmdict.get("marked_misc_terms"))),
    ]
    if marked:
        parts.append("+".join(_escape(str(item)) for item in marked[:3]))
    return "<br>".join(parts)


def _fmt_bccwj_cell(bccwj: Mapping[str, object]) -> str:
    exact = _mapping(bccwj.get("best_exact"))
    family = _mapping(bccwj.get("best_family"))
    exact_part = (
        "exact=-"
        if not exact
        else f"exact r{_fmt_int(exact.get('rank'))} pmw{_fmt_float(exact.get('pmw'))}"
    )
    family_part = (
        "family=-"
        if not family
        else f"family {_escape(str(family.get('lemma') or family.get('queried_term')))} r{_fmt_int(family.get('rank'))}"
    )
    gain = bccwj.get("family_pmw_gain")
    return f"{exact_part}<br>{family_part}<br>gain={_fmt_float(gain)}"


def _fmt_tubelex_cell(tubelex: Mapping[str, object]) -> str:
    exact = _mapping(tubelex.get("best_exact"))
    family = _mapping(tubelex.get("best_family"))
    exact_part = (
        "exact=-" if not exact else f"exact c{exact.get('count')}/ch{exact.get('channels')}"
    )
    family_part = (
        "family=-"
        if not family
        else f"family {_escape(str(family.get('word') or family.get('queried_term')))} c{family.get('count')}"
    )
    return f"{exact_part}<br>{family_part}"


def _fmt_sudachi_cell(sudachi: Mapping[str, object]) -> str:
    terms = ",".join(
        _escape(str(term)) for term in _rows(sudachi.get("content_dictionary_forms_c"))
    )
    counts = _mapping(sudachi.get("mode_token_counts"))
    return (
        f"C={counts.get('C')} content={sudachi.get('content_token_count_c')}<br>base={terms or '-'}"
    )


def _fmt_english_cell(english: Mapping[str, object]) -> str:
    origin = _mapping(english.get("best_origin_candidate"))
    gloss = _mapping(english.get("best_gloss_candidate"))
    langs = ",".join(str(lang) for lang in _rows(english.get("jmdict_source_langs")))
    if not origin and not gloss:
        return "-"
    parts = []
    if origin:
        parts.append(
            f"origin {_escape(str(origin.get('text')))} ({_fmt_float(origin.get('english_zipf'))})"
        )
    if gloss:
        parts.append(
            f"gloss {_escape(str(gloss.get('text')))} ({_fmt_float(gloss.get('english_zipf'))})"
        )
    if langs:
        parts.append(f"src={_escape(langs)}")
    return "<br>".join(parts)


def _expected_value(row: Mapping[str, object]) -> object:
    expected = _mapping(row.get("expected_label"))
    return expected.get("expected_learner_difficulty", expected.get("expected"))


def _fmt_best_family_zipf(wordfreq: Mapping[str, object]) -> str:
    best = _mapping(wordfreq.get("best_family_zipf"))
    if not best:
        return "-"
    return f"{_escape(str(best.get('term')))}:{_fmt_float(best.get('zipf'))}"


def _fmt_float(value: object) -> str:
    number = _float_or_none(value)
    if number is None:
        return ""
    if math.isinf(number):
        return "inf"
    return f"{number:.3f}"


def _fmt_int(value: object) -> str:
    number = _float_or_none(value)
    if number is None:
        return "-"
    return str(int(round(number)))


def _sqlite_row(row: sqlite3.Row) -> dict[str, object]:
    return {key: _json_scalar(row[key]) for key in row.keys()}


def _json_scalar(value: object) -> object:
    if isinstance(value, float):
        return _finite_or_none(value)
    return value


def _rows(value: object) -> list:
    return list(value) if isinstance(value, list | tuple) else []


def _mapping(value: object) -> dict:
    return dict(value) if isinstance(value, Mapping) else {}


def _row_key(row: Mapping[str, object]) -> tuple[str, str]:
    return str(row["lemma"]), str(row["reading"])


def _int_or_none(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def _float_or_none(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return _finite_or_none(number)


def _finite_or_none(value: float) -> float | None:
    if not math.isfinite(value):
        return None
    return _rounded(value)


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path.expanduser().resolve()
    return (PROJECT_ROOT / path).expanduser().resolve()


if __name__ == "__main__":
    raise SystemExit(main())
