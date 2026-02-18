from __future__ import annotations

from typing import Sequence

from lexishift_core import VocabRule


def build_ruleset_preview_lines(
    rules: Sequence[VocabRule],
    *,
    max_rows: int = 140,
    disabled_label: str = "Disabled",
    overflow_template: str = "... +{count} more",
) -> list[str]:
    lines: list[str] = []
    for index, rule in enumerate(rules[:max_rows], start=1):
        source = str(rule.source_phrase or "").strip()
        replacement = str(rule.replacement or "").strip()
        disabled_suffix = f" [{disabled_label}]" if not bool(rule.enabled) else ""
        lines.append(f"{index}. {source} -> {replacement}{disabled_suffix}")
    if len(rules) > max_rows:
        remaining = len(rules) - max_rows
        try:
            lines.append(str(overflow_template).format(count=remaining))
        except Exception:  # noqa: BLE001
            lines.append(f"... +{remaining} more")
    return lines
