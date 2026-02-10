from __future__ import annotations

from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


XML_LANG_KEY = "{http://www.w3.org/XML/1998/namespace}lang"
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def load_jmdict_glosses(
    path: Path,
    *,
    languages: Iterable[str] = ("eng", "en"),
    include_kana: bool = True,
    include_kanji: bool = True,
) -> dict[str, set[str]]:
    ordered = load_jmdict_glosses_ordered(
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
    mapping: dict[str, list[str]] = {}
    if not path.exists():
        return mapping
    allowed = {lang.lower() for lang in languages} if languages else set()
    try:
        context = ElementTree.iterparse(path, events=("end",))
    except (ElementTree.ParseError, OSError):
        return mapping
    for _event, elem in context:
        if elem.tag != "entry":
            continue
        glosses: list[str] = []
        for gloss in elem.findall("sense/gloss"):
            text = (gloss.text or "").strip()
            if not text:
                continue
            lang = gloss.get(XML_LANG_KEY)
            if lang and allowed and lang.lower() not in allowed:
                continue
            glosses.append(text)
        if glosses:
            jp_terms = []
            if include_kanji:
                for keb in elem.findall("k_ele/keb"):
                    if keb.text and keb.text.strip():
                        jp_terms.append(keb.text.strip())
            if include_kana:
                for reb in elem.findall("r_ele/reb"):
                    if reb.text and reb.text.strip():
                        jp_terms.append(reb.text.strip())
            for jp_term in jp_terms:
                bucket = mapping.setdefault(jp_term, [])
                for gloss in glosses:
                    if gloss not in bucket:
                        bucket.append(gloss)
        elem.clear()
    return mapping


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
