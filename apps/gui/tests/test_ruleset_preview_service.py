from __future__ import annotations

from lexishift_core import VocabRule
from ruleset_preview_service import build_ruleset_preview_lines


def test_build_ruleset_preview_lines_formats_disabled_and_overflow() -> None:
    rules = [
        VocabRule(source_phrase="a", replacement="x", enabled=True),
        VocabRule(source_phrase="b", replacement="y", enabled=False),
        VocabRule(source_phrase="c", replacement="z", enabled=True),
    ]
    lines = build_ruleset_preview_lines(
        rules,
        max_rows=2,
        disabled_label="Disabled",
        overflow_template="... +{count} more",
    )
    assert lines == [
        "1. a -> x",
        "2. b -> y [Disabled]",
        "... +1 more",
    ]


def test_build_ruleset_preview_lines_fallback_when_overflow_template_invalid() -> None:
    rules = [
        VocabRule(source_phrase="a", replacement="x"),
        VocabRule(source_phrase="b", replacement="y"),
    ]
    lines = build_ruleset_preview_lines(
        rules,
        max_rows=1,
        disabled_label="Disabled",
        overflow_template="{bad_key}",
    )
    assert lines == [
        "1. a -> x",
        "... +1 more",
    ]
