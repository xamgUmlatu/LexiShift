from __future__ import annotations

from html.parser import HTMLParser
import re
from typing import Mapping


class SavedPageTextExtractor(HTMLParser):
    SKIP_TAGS = {
        "script",
        "style",
        "noscript",
        "textarea",
        "select",
        "option",
        "template",
        "svg",
        "canvas",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[tuple[str, bool]] = []
        self._skip_depth = 0
        self._ruby_depth = 0
        self._rt_depth = 0
        self._rp_depth = 0
        self._ruby_surface: list[str] = []
        self._ruby_reading: list[str] = []
        self._visible_parts: list[str] = []
        self.ruby_pairs: list[dict[str, str]] = []

    @property
    def visible_text(self) -> str:
        return _collapse_spaces(" ".join(self._visible_parts))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        attrs_map = {key.lower(): value or "" for key, value in attrs}
        starts_skip = self._skip_depth > 0 or self._starts_skip(normalized_tag, attrs_map)
        self._stack.append((normalized_tag, starts_skip))
        if starts_skip:
            self._skip_depth += 1
            return
        if normalized_tag == "ruby":
            self._ruby_depth += 1
            if self._ruby_depth == 1:
                self._ruby_surface = []
                self._ruby_reading = []
        elif self._ruby_depth and normalized_tag == "rt":
            self._rt_depth += 1
        elif self._ruby_depth and normalized_tag == "rp":
            self._rp_depth += 1

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        stack_tag, started_skip = self._pop_stack(normalized_tag)
        _ = stack_tag
        if started_skip:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._ruby_depth and normalized_tag == "rt":
            self._rt_depth = max(0, self._rt_depth - 1)
        elif self._ruby_depth and normalized_tag == "rp":
            self._rp_depth = max(0, self._rp_depth - 1)
        elif normalized_tag == "ruby" and self._ruby_depth:
            if self._ruby_depth == 1:
                pair = _normalize_ruby_pair(
                    "".join(self._ruby_surface),
                    "".join(self._ruby_reading),
                )
                if pair:
                    self.ruby_pairs.append(pair)
                self._ruby_surface = []
                self._ruby_reading = []
            self._ruby_depth = max(0, self._ruby_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = str(data or "")
        if not text.strip():
            return
        if self._ruby_depth:
            if self._rt_depth:
                self._ruby_reading.append(text)
                return
            if self._rp_depth:
                return
            self._ruby_surface.append(text)
        self._visible_parts.append(text)

    def _starts_skip(self, tag: str, attrs: Mapping[str, str]) -> bool:
        if tag in self.SKIP_TAGS:
            return True
        if attrs.get("data-lexishift-scan-skip", "").strip().lower() == "true":
            return True
        class_names = {part.strip() for part in attrs.get("class", "").split()}
        return bool({"lexishift-replacement", "lexishift-popup"} & class_names)

    def _pop_stack(self, tag: str) -> tuple[str, bool]:
        if not self._stack:
            return tag, False
        if self._stack[-1][0] == tag:
            return self._stack.pop()
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                _, started_skip = self._stack.pop(index)
                return tag, started_skip
        return tag, False


def _normalize_ruby_pair(surface: str, reading: str) -> dict[str, str] | None:
    clean_surface = re.sub(r"\s+", "", surface or "").strip()
    clean_reading = re.sub(r"\s+", "", reading or "").strip()
    if not clean_surface or not clean_reading:
        return None
    return {"surface": clean_surface, "reading": clean_reading}


def _collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
