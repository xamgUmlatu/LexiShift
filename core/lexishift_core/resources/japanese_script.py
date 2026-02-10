from __future__ import annotations

from typing import Optional

_HIRAGANA_MAP = {
    "あ": "a",
    "い": "i",
    "う": "u",
    "え": "e",
    "お": "o",
    "か": "ka",
    "き": "ki",
    "く": "ku",
    "け": "ke",
    "こ": "ko",
    "さ": "sa",
    "し": "shi",
    "す": "su",
    "せ": "se",
    "そ": "so",
    "た": "ta",
    "ち": "chi",
    "つ": "tsu",
    "て": "te",
    "と": "to",
    "な": "na",
    "に": "ni",
    "ぬ": "nu",
    "ね": "ne",
    "の": "no",
    "は": "ha",
    "ひ": "hi",
    "ふ": "fu",
    "へ": "he",
    "ほ": "ho",
    "ま": "ma",
    "み": "mi",
    "む": "mu",
    "め": "me",
    "も": "mo",
    "や": "ya",
    "ゆ": "yu",
    "よ": "yo",
    "ら": "ra",
    "り": "ri",
    "る": "ru",
    "れ": "re",
    "ろ": "ro",
    "わ": "wa",
    "を": "o",
    "ん": "n",
    "が": "ga",
    "ぎ": "gi",
    "ぐ": "gu",
    "げ": "ge",
    "ご": "go",
    "ざ": "za",
    "じ": "ji",
    "ず": "zu",
    "ぜ": "ze",
    "ぞ": "zo",
    "だ": "da",
    "ぢ": "ji",
    "づ": "zu",
    "で": "de",
    "ど": "do",
    "ば": "ba",
    "び": "bi",
    "ぶ": "bu",
    "べ": "be",
    "ぼ": "bo",
    "ぱ": "pa",
    "ぴ": "pi",
    "ぷ": "pu",
    "ぺ": "pe",
    "ぽ": "po",
    "ゔ": "vu",
    "ぁ": "a",
    "ぃ": "i",
    "ぅ": "u",
    "ぇ": "e",
    "ぉ": "o",
    "ゎ": "wa",
}

_DIGRAPH_MAP = {
    "きゃ": "kya",
    "きゅ": "kyu",
    "きょ": "kyo",
    "しゃ": "sha",
    "しゅ": "shu",
    "しょ": "sho",
    "ちゃ": "cha",
    "ちゅ": "chu",
    "ちょ": "cho",
    "にゃ": "nya",
    "にゅ": "nyu",
    "にょ": "nyo",
    "ひゃ": "hya",
    "ひゅ": "hyu",
    "ひょ": "hyo",
    "みゃ": "mya",
    "みゅ": "myu",
    "みょ": "myo",
    "りゃ": "rya",
    "りゅ": "ryu",
    "りょ": "ryo",
    "ぎゃ": "gya",
    "ぎゅ": "gyu",
    "ぎょ": "gyo",
    "じゃ": "ja",
    "じゅ": "ju",
    "じょ": "jo",
    "びゃ": "bya",
    "びゅ": "byu",
    "びょ": "byo",
    "ぴゃ": "pya",
    "ぴゅ": "pyu",
    "ぴょ": "pyo",
    "ゔぁ": "va",
    "ゔぃ": "vi",
    "ゔぇ": "ve",
    "ゔぉ": "vo",
    "てぃ": "ti",
    "でぃ": "di",
    "とぅ": "tu",
    "どぅ": "du",
    "ふぁ": "fa",
    "ふぃ": "fi",
    "ふぇ": "fe",
    "ふぉ": "fo",
    "うぃ": "wi",
    "うぇ": "we",
    "うぉ": "wo",
    "つぁ": "tsa",
    "つぃ": "tsi",
    "つぇ": "tse",
    "つぉ": "tso",
    "しぇ": "she",
    "じぇ": "je",
    "ちぇ": "che",
}

_SMALL_TSU = "っ"
_LONG_VOWEL_MARK = "ー"
_VOWELS = frozenset({"a", "e", "i", "o", "u"})


def is_hiragana_char(ch: str) -> bool:
    code = ord(ch)
    return 0x3040 <= code <= 0x309F


def is_katakana_char(ch: str) -> bool:
    code = ord(ch)
    return 0x30A0 <= code <= 0x30FF


def contains_kana(text: str) -> bool:
    return any(is_hiragana_char(ch) or is_katakana_char(ch) for ch in str(text or ""))


def contains_kanji(text: str) -> bool:
    for ch in str(text or ""):
        code = ord(ch)
        if (0x4E00 <= code <= 0x9FFF) or (0x3400 <= code <= 0x4DBF):
            return True
    return False


def _katakana_to_hiragana(text: str) -> str:
    out: list[str] = []
    for ch in text:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            out.append(chr(code - 0x60))
            continue
        if ch == "ヵ":
            out.append("か")
            continue
        if ch == "ヶ":
            out.append("け")
            continue
        out.append(ch)
    return "".join(out)


def _last_vowel(text: str) -> Optional[str]:
    for ch in reversed(text):
        if ch.lower() in _VOWELS:
            return ch.lower()
    return None


def _apply_geminate(romaji: str) -> str:
    if not romaji:
        return romaji
    first = romaji[0].lower()
    if first in _VOWELS or first == "n":
        return romaji
    return first + romaji


def kana_to_romaji(text: str) -> str:
    source = _katakana_to_hiragana(str(text or ""))
    if not source:
        return ""
    out: list[str] = []
    idx = 0
    geminate_next = False
    while idx < len(source):
        ch = source[idx]
        if ch == _SMALL_TSU:
            geminate_next = True
            idx += 1
            continue
        if ch == _LONG_VOWEL_MARK:
            vowel = _last_vowel("".join(out))
            if vowel:
                out.append(vowel)
            idx += 1
            continue
        pair = source[idx: idx + 2]
        mapped = _DIGRAPH_MAP.get(pair)
        consumed = 2
        if mapped is None:
            mapped = _HIRAGANA_MAP.get(ch)
            consumed = 1
        if mapped is None:
            out.append(ch)
            idx += 1
            continue
        if geminate_next:
            mapped = _apply_geminate(mapped)
            geminate_next = False
        out.append(mapped)
        idx += consumed
    return "".join(out)


__all__ = [
    "contains_kana",
    "contains_kanji",
    "is_hiragana_char",
    "is_katakana_char",
    "kana_to_romaji",
]
