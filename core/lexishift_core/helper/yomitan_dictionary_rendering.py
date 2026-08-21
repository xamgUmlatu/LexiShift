from __future__ import annotations

from collections.abc import Iterable, Mapping


MAX_PLAIN_DEFINITION_CHARS = 8_000
MAX_STRUCTURED_CONTENT_CHARS = 24_000
MAX_STRUCTURED_CONTENT_NODES = 1_500
_STRUCTURED_CONTENT_TAGS = {
    "a",
    "br",
    "div",
    "li",
    "ol",
    "rp",
    "rt",
    "ruby",
    "span",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}
_STRUCTURED_CONTENT_ROLES = {
    "見出部": "headword",
    "見出仮名": "headword-reading",
    "漢字見出G": "headword",
    "漢字見出": "headword-written",
    "表記G": "headword-writing",
    "標準表記": "headword-written",
    "解説部": "explanation",
    "大語義": "major-section",
    "準大語義": "section",
    "中語義": "sense-group",
    "語義G": "sense",
    "語義Gnum": "sense-number",
    "副義": "subsense",
    "副義num": "subsense-number",
    "語釈": "definition",
    "品詞G": "part-of-speech-group",
    "品詞subG": "part-of-speech-group",
    "品詞": "part-of-speech",
    "用例": "example",
    "補説G": "note",
    "補説": "note",
    "参照G": "reference",
    "参照": "reference",
    "ref": "reference",
    "出典": "source",
    "書名": "source-title",
    "付記": "source-note",
    "アクセントG": "accent",
    "アクセント": "accent",
    "accent": "accent",
    "漢字音G": "reading-list",
    "漢字音": "reading",
    "熟語例G": "related-terms",
    "熟語": "related-term",
    "ルビG": "reading-note",
}


def definition_payloads(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    payloads: list[dict[str, object]] = []
    for definition in value:
        text = _definition_text(definition)
        if not text:
            continue
        text = _limit_definition_text(text)
        if text.casefold() in {str(item.get("text") or "").casefold() for item in payloads}:
            continue
        payload: dict[str, object] = {"text": text}
        structured_content, truncated = _structured_content_payload(definition)
        if structured_content:
            payload["structured_content"] = structured_content
            if truncated:
                payload["structured_content_truncated"] = True
        payloads.append(payload)
    return payloads


def is_cross_reference_only_glossary(value: object) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for definition in value:
        if not isinstance(definition, Mapping):
            return False
        if str(definition.get("type") or "") != "structured-content":
            return False
        content = definition.get("content")
        if isinstance(content, list) and len(content) == 1:
            content = content[0]
        if not isinstance(content, Mapping) or str(content.get("tag") or "").lower() != "a":
            return False
    return True


def _definition_text(value: object, *, depth: int = 0) -> str:
    if depth > 32:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        if len(value) == 2 and isinstance(value[0], str) and isinstance(value[1], list):
            return value[0].strip()
        return _join_content(_definition_text(item, depth=depth + 1) for item in value)
    if not isinstance(value, Mapping):
        return ""
    value_type = str(value.get("type") or "").strip()
    if value_type == "text":
        return str(value.get("text") or "").strip()
    if value_type == "structured-content":
        return _definition_text(value.get("content"), depth=depth + 1)
    if value_type == "image":
        return _first_text(value.get("alt"), value.get("description"), value.get("title"))
    tag = str(value.get("tag") or "").strip().lower()
    if tag == "br":
        return "\n"
    if tag == "img":
        return _first_text(value.get("alt"), value.get("description"), value.get("title"))
    content = _definition_text(value.get("content"), depth=depth + 1)
    if tag == "rt" and content:
        return f"({content})"
    if tag == "li" and content:
        return f"• {content}\n"
    if (
        tag
        in {
            "div",
            "ol",
            "ul",
            "table",
            "thead",
            "tbody",
            "tfoot",
            "tr",
            "details",
            "summary",
        }
        and content
    ):
        return f"{content}\n"
    return content


def _join_content(values: Iterable[str]) -> str:
    chunks: list[str] = []
    for value in values:
        if not value:
            continue
        if chunks and _content_needs_space(chunks[-1], value):
            chunks.append(" ")
        chunks.append(value)
    return "".join(chunks).strip()


def _content_needs_space(left: str, right: str) -> bool:
    if not left or not right or left.endswith(("\n", " ")) or right.startswith(("\n", " ")):
        return False
    left_char = left[-1]
    right_char = right[0]
    if _is_cjk_or_kana(left_char) or _is_cjk_or_kana(right_char):
        return False
    if (
        left_char in "([{（［｛〈《「『【“‘"
        or right_char in ")]},.!?;:）］｝〉》」』】、。！？；：”’"
    ):
        return False
    return left_char.isalnum() and right_char.isalnum()


def _is_cjk_or_kana(value: str) -> bool:
    if not value:
        return False
    codepoint = ord(value[0])
    return (
        0x3040 <= codepoint <= 0x30FF
        or 0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
    )


def _structured_content_payload(value: object) -> tuple[list[dict[str, object]], bool]:
    if not isinstance(value, Mapping) or str(value.get("type") or "") != "structured-content":
        return [], False
    budget = {"nodes": 0, "chars": 0, "truncated": False}
    nodes = _structured_nodes(value.get("content"), budget=budget, depth=0)
    return nodes, bool(budget["truncated"])


def _structured_nodes(
    value: object,
    *,
    budget: dict[str, int | bool],
    depth: int,
) -> list[dict[str, object]]:
    if depth > 32 or bool(budget["truncated"]):
        budget["truncated"] = True
        return []
    if isinstance(value, str):
        text = _take_structured_text(value, budget)
        return [{"type": "text", "text": text}] if text else []
    if isinstance(value, list):
        nodes: list[dict[str, object]] = []
        for item in value:
            nodes.extend(_structured_nodes(item, budget=budget, depth=depth + 1))
            if bool(budget["truncated"]):
                break
        return nodes
    if not isinstance(value, Mapping):
        return []

    value_type = str(value.get("type") or "").strip()
    if value_type == "text":
        return _structured_nodes(value.get("text"), budget=budget, depth=depth + 1)
    if value_type == "structured-content":
        return _structured_nodes(value.get("content"), budget=budget, depth=depth + 1)
    if value_type == "image":
        return _structured_image_fallback(value, budget)

    tag = str(value.get("tag") or "").strip().lower()
    if tag == "img":
        return _structured_image_fallback(value, budget)
    if tag == "br":
        return [_structured_node({"type": "break"}, budget)]

    children = _structured_nodes(value.get("content"), budget=budget, depth=depth + 1)
    if not children:
        return []
    if tag not in _STRUCTURED_CONTENT_TAGS:
        return children
    node: dict[str, object] = {
        "type": "element",
        "tag": tag,
        "children": children,
    }
    role = _structured_content_role(value.get("data"))
    if role:
        node["role"] = role
    styles = _structured_content_styles(value.get("style"))
    if styles:
        node["styles"] = styles
    query = _structured_content_query(value.get("href")) if tag == "a" else ""
    if query:
        node["query"] = query
    return [_structured_node(node, budget)]


def _structured_node(
    value: dict[str, object],
    budget: dict[str, int | bool],
) -> dict[str, object]:
    budget["nodes"] = int(budget["nodes"]) + 1
    if int(budget["nodes"]) > MAX_STRUCTURED_CONTENT_NODES:
        budget["truncated"] = True
        return {"type": "text", "text": "…"}
    return value


def _take_structured_text(value: object, budget: dict[str, int | bool]) -> str:
    text = str(value or "")
    remaining = MAX_STRUCTURED_CONTENT_CHARS - int(budget["chars"])
    if remaining <= 0:
        budget["truncated"] = True
        return ""
    if len(text) > remaining:
        budget["chars"] = MAX_STRUCTURED_CONTENT_CHARS
        budget["truncated"] = True
        return text[: max(0, remaining - 1)].rstrip() + "…"
    budget["chars"] = int(budget["chars"]) + len(text)
    return text


def _structured_image_fallback(
    value: Mapping[str, object],
    budget: dict[str, int | bool],
) -> list[dict[str, object]]:
    text = _take_structured_text(
        _first_text(value.get("alt"), value.get("description"), value.get("title")),
        budget,
    )
    if not text:
        return []
    return [_structured_node({"type": "image-fallback", "text": text}, budget)]


def _structured_content_role(value: object) -> str:
    if not isinstance(value, Mapping):
        return ""
    name = str(value.get("name") or "").strip()
    return _STRUCTURED_CONTENT_ROLES.get(name, "")


def _structured_content_styles(value: object) -> list[str]:
    if not isinstance(value, Mapping):
        return []
    styles: list[str] = []
    weight = str(value.get("fontWeight") or "").strip().lower()
    try:
        numeric_weight = int(float(weight))
    except (TypeError, ValueError):
        numeric_weight = 0
    if weight in {"bold", "bolder"} or numeric_weight >= 600:
        styles.append("bold")
    if str(value.get("fontStyle") or "").strip().lower() in {"italic", "oblique"}:
        styles.append("italic")
    vertical_align = str(value.get("verticalAlign") or "").strip().lower()
    if vertical_align in {"super", "sub"}:
        styles.append(vertical_align)
    decoration = str(value.get("textDecorationLine") or "").strip().lower()
    if "underline" in decoration:
        styles.append("underline")
    return styles


def _structured_content_query(value: object) -> str:
    href = str(value or "").strip()
    if not href.startswith("?query="):
        return ""
    query = href[len("?query=") :].split("&", 1)[0]
    return query[:200]


def _limit_definition_text(value: str) -> str:
    lines = [line.rstrip() for line in str(value or "").replace("\r\n", "\n").split("\n")]
    text = "\n".join(lines).strip()
    if len(text) <= MAX_PLAIN_DEFINITION_CHARS:
        return text
    return text[: MAX_PLAIN_DEFINITION_CHARS - 1].rstrip() + "…"


def _first_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


__all__ = ["definition_payloads", "is_cross_reference_only_glossary"]
