from __future__ import annotations

from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree

from lexishift_core.resources.japanese_script import (
    contains_kana,
    contains_kanji,
    kana_to_romaji,
)


XML_LANG_KEY = "{http://www.w3.org/XML/1998/namespace}lang"
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def load_jmdict_glosses(
    path: Path,
    *,
    languages: Iterable[str] = ("eng", "en"),
    include_kana: bool = True,
    include_kanji: bool = True,
) -> dict[str, set[str]]:
    ordered, _forms = load_jmdict_glosses_and_script_forms(
        path,
        languages=languages,
        include_kana=include_kana,
        include_kanji=include_kanji,
    )
    return {key: set(values) for key, values in ordered.items()}


def load_jmdict_glosses_ordered(
    path: Path,
    *,
    languages: Iterable[str] = ("eng", "en"),
    include_kana: bool = True,
    include_kanji: bool = True,
) -> dict[str, list[str]]:
    mapping, _forms = load_jmdict_glosses_and_script_forms(
        path,
        languages=languages,
        include_kana=include_kana,
        include_kanji=include_kanji,
    )
    return mapping


def _collect_glosses(
    *,
    elem: ElementTree.Element,
    allowed_languages: set[str],
) -> list[str]:
    glosses: list[str] = []
    for gloss in elem.findall("sense/gloss"):
        text = (gloss.text or "").strip()
        if not text:
            continue
        lang = gloss.get(XML_LANG_KEY)
        if lang and allowed_languages and lang.lower() not in allowed_languages:
            continue
        glosses.append(text)
    return glosses


def _collect_forms(*, elem: ElementTree.Element, tag_path: str) -> list[str]:
    forms: list[str] = []
    for entry in elem.findall(tag_path):
        text = (entry.text or "").strip()
        if not text:
            continue
        if text not in forms:
            forms.append(text)
    return forms


def _build_script_forms(
    *,
    term: str,
    canonical_kanji: str,
    canonical_kana: str,
) -> dict[str, str]:
    forms: dict[str, str] = {}
    if canonical_kanji:
        forms["kanji"] = canonical_kanji
    if canonical_kana:
        forms["kana"] = canonical_kana
    if not forms.get("kanji") and contains_kanji(term):
        forms["kanji"] = term
    if not forms.get("kana") and contains_kana(term):
        forms["kana"] = term
    kana_value = forms.get("kana", "")
    if kana_value:
        romaji = kana_to_romaji(kana_value)
        if romaji:
            forms["romaji"] = romaji
    return forms


def load_jmdict_glosses_and_script_forms(
    path: Path,
    *,
    languages: Iterable[str] = ("eng", "en"),
    include_kana: bool = True,
    include_kanji: bool = True,
) -> tuple[dict[str, list[str]], dict[str, dict[str, str]]]:
    mapping: dict[str, list[str]] = {}
    forms_by_term: dict[str, dict[str, str]] = {}
    if not path.exists():
        return mapping, forms_by_term
    allowed = {lang.lower() for lang in languages} if languages else set()
    try:
        context = ElementTree.iterparse(path, events=("end",))
    except (ElementTree.ParseError, OSError):
        return mapping, forms_by_term
    for _event, elem in context:
        if elem.tag != "entry":
            continue
        glosses = _collect_glosses(elem=elem, allowed_languages=allowed)
        if not glosses:
            elem.clear()
            continue
        kanji_forms = _collect_forms(elem=elem, tag_path="k_ele/keb")
        kana_forms = _collect_forms(elem=elem, tag_path="r_ele/reb")
        canonical_kanji = kanji_forms[0] if kanji_forms else ""
        canonical_kana = kana_forms[0] if kana_forms else ""
        terms: list[str] = []
        if include_kanji:
            terms.extend(kanji_forms)
        if include_kana:
            terms.extend(kana_forms)
        for term in terms:
            bucket = mapping.setdefault(term, [])
            for gloss in glosses:
                if gloss not in bucket:
                    bucket.append(gloss)
            entry_forms = _build_script_forms(
                term=term,
                canonical_kanji=canonical_kanji,
                canonical_kana=canonical_kana,
            )
            existing = forms_by_term.setdefault(term, {})
            for script, value in entry_forms.items():
                if script not in existing and value:
                    existing[script] = value
        elem.clear()
    return mapping, forms_by_term


def load_jmdict_lemmas(
    path: Path,
    *,
    include_kana: bool = True,
    include_kanji: bool = True,
) -> set[str]:
    lemmas: set[str] = set()
    if not path.exists():
        return lemmas
    try:
        context = ElementTree.iterparse(path, events=("end",))
    except (ElementTree.ParseError, OSError):
        return lemmas
    for _event, elem in context:
        if elem.tag != "entry":
            continue
        if include_kanji:
            for keb in elem.findall("k_ele/keb"):
                if keb.text and keb.text.strip():
                    lemmas.add(keb.text.strip())
        if include_kana:
            for reb in elem.findall("r_ele/reb"):
                if reb.text and reb.text.strip():
                    lemmas.add(reb.text.strip())
        elem.clear()
    return lemmas


def load_freedict_tei_glosses_ordered(
    path: Path,
    *,
    target_lang: str,
) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    if not path.exists():
        return mapping
    try:
        context = ElementTree.iterparse(path, events=("end",))
    except (ElementTree.ParseError, OSError):
        return mapping
    for _event, elem in context:
        if elem.tag != f"{{{TEI_NS['tei']}}}entry":
            continue
        headwords: list[str] = []
        for orth in elem.findall("tei:form/tei:orth", TEI_NS):
            text = (orth.text or "").strip()
            if text and text not in headwords:
                headwords.append(text)
        if not headwords:
            elem.clear()
            continue
        translations: list[str] = []
        for quote in elem.findall(".//tei:cit[@type='trans']/tei:quote", TEI_NS):
            text = (quote.text or "").strip()
            if not text:
                continue
            lang = (quote.get(XML_LANG_KEY) or "").strip().lower()
            if lang and lang != target_lang.lower():
                continue
            if text not in translations:
                translations.append(text)
        if translations:
            for headword in headwords:
                bucket = mapping.setdefault(headword, [])
                for translation in translations:
                    if translation not in bucket:
                        bucket.append(translation)
        elem.clear()
    return mapping
