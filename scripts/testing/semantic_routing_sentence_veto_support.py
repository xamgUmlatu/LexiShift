#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for candidate in (str(SCRIPT_ROOT), str(CORE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_routing_sentence_veto_common import (  # noqa: E402,F401
    DEFAULT_SENTENCE_VETO_DATASET,
    DEFAULT_SENTENCE_VETO_JSON_OUT,
    DEFAULT_SENTENCE_VETO_LADDER_JSON_OUT,
    DEFAULT_SENTENCE_VETO_LADDER_MARKDOWN_OUT,
    DEFAULT_SENTENCE_VETO_MARKDOWN_OUT,
    DEFAULT_SENTENCE_VETO_PHRASE_LEAK_JSON_OUT,
    DEFAULT_SENTENCE_VETO_PHRASE_LEAK_MARKDOWN_OUT,
    DEFAULT_SENTENCE_VETO_SWEEP_JSON_OUT,
    DEFAULT_SENTENCE_VETO_SWEEP_MARKDOWN_OUT,
    DEFAULT_SENTENCE_VETO_WEAK_ACTIVE_JSON_OUT,
    DEFAULT_SENTENCE_VETO_WEAK_ACTIVE_MARKDOWN_OUT,
    SENTENCE_VETO_PHRASE_GUARD_POS_SCOPES,
    _resolve_sentence_veto_phrase_guard_pos_tags,
    build_sentence_veto_report,
    load_sentence_veto_dataset,
)
from semantic_routing_sentence_veto_ladder_support import (  # noqa: E402,F401
    build_sentence_veto_ladder_case_rows,
    build_sentence_veto_ladder_report,
    select_best_sentence_veto_ladder_row,
    sentence_veto_ladder_rank_key,
)
from semantic_routing_sentence_veto_overlay_support import (  # noqa: E402,F401
    build_sentence_veto_phrase_leak_probe_report,
    build_sentence_veto_rescue_overlay_case_rows,
    build_sentence_veto_weak_active_probe_report,
    sentence_veto_overlay_rank_key,
)
from semantic_routing_sentence_veto_reporting import (  # noqa: E402,F401
    render_sentence_veto_ladder_markdown,
    render_sentence_veto_markdown,
    render_sentence_veto_phrase_leak_probe_markdown,
    render_sentence_veto_sweep_markdown,
    render_sentence_veto_weak_active_probe_markdown,
)
from semantic_routing_sentence_veto_sweep_support import (  # noqa: E402,F401
    build_sentence_veto_sweep_report,
)

__all__ = [
    "DEFAULT_SENTENCE_VETO_DATASET",
    "DEFAULT_SENTENCE_VETO_JSON_OUT",
    "DEFAULT_SENTENCE_VETO_MARKDOWN_OUT",
    "DEFAULT_SENTENCE_VETO_SWEEP_JSON_OUT",
    "DEFAULT_SENTENCE_VETO_SWEEP_MARKDOWN_OUT",
    "DEFAULT_SENTENCE_VETO_LADDER_JSON_OUT",
    "DEFAULT_SENTENCE_VETO_LADDER_MARKDOWN_OUT",
    "DEFAULT_SENTENCE_VETO_WEAK_ACTIVE_JSON_OUT",
    "DEFAULT_SENTENCE_VETO_WEAK_ACTIVE_MARKDOWN_OUT",
    "DEFAULT_SENTENCE_VETO_PHRASE_LEAK_JSON_OUT",
    "DEFAULT_SENTENCE_VETO_PHRASE_LEAK_MARKDOWN_OUT",
    "SENTENCE_VETO_PHRASE_GUARD_POS_SCOPES",
    "_resolve_sentence_veto_phrase_guard_pos_tags",
    "load_sentence_veto_dataset",
    "build_sentence_veto_report",
    "build_sentence_veto_sweep_report",
    "build_sentence_veto_ladder_report",
    "select_best_sentence_veto_ladder_row",
    "sentence_veto_ladder_rank_key",
    "build_sentence_veto_ladder_case_rows",
    "build_sentence_veto_weak_active_probe_report",
    "sentence_veto_overlay_rank_key",
    "build_sentence_veto_phrase_leak_probe_report",
    "build_sentence_veto_rescue_overlay_case_rows",
    "render_sentence_veto_markdown",
    "render_sentence_veto_sweep_markdown",
    "render_sentence_veto_ladder_markdown",
    "render_sentence_veto_weak_active_probe_markdown",
    "render_sentence_veto_phrase_leak_probe_markdown",
]
