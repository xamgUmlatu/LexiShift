from __future__ import annotations

from typing import Mapping


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# SRS Browsing Admission Offline Page Mining",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Scope: `{report.get('scope', '')}`",
        f"- Config: `{report.get('config_path', '')}`",
        f"- Live user data touched: `{report.get('live_user_data_touched')}`",
        "",
    ]
    for case in _list_of_mappings(report.get("cases")):
        lines.extend(render_case_markdown(case))
    return "\n".join(lines)


def render_case_markdown(case: Mapping[str, object]) -> list[str]:
    lines = [
        f"## {case.get('name')}",
        "",
        f"- Status: `{case.get('status')}`",
        f"- Pair: `{case.get('pair')}`",
        f"- Profile: `{case.get('profile_id')}`",
        "",
        "### Checks",
        "",
    ]
    for check in _list_of_mappings(case.get("checks")):
        lines.append(f"- `{check.get('status')}` `{check.get('name')}`: {check.get('detail')}")
    _append_documents(lines, case)
    _append_extension_signals(lines, case)
    _append_aggregate_store(lines, case)
    _append_admission_simulations(lines, case)
    lines.append("")
    return lines


def _append_documents(lines: list[str], case: Mapping[str, object]) -> None:
    lines.extend(["", "### Documents", ""])
    lines.extend(
        [
            "| document | side | text chars | ruby pairs | sha256 |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for document in _list_of_mappings(case.get("documents")):
        lines.append(
            "| "
            f"`{document.get('document_id')}` | "
            f"`{document.get('side')}` | "
            f"{document.get('visible_text_char_count')} | "
            f"{document.get('ruby_pair_count')} | "
            f"`{str(document.get('sha256') or '')[:12]}` |"
        )


def _append_extension_signals(lines: list[str], case: Mapping[str, object]) -> None:
    lines.extend(["", "### Extension Signals", ""])
    extension = _as_mapping(case.get("extension_payload"))
    lines.extend(
        [
            f"- Packet count: `{extension.get('packet_count')}`",
            f"- Signal count: `{extension.get('signal_count')}`",
            f"- Source signal count: `{extension.get('source_signal_count')}`",
            f"- Target signal count: `{extension.get('target_signal_count')}`",
            "",
            "| target | side | source | count | confidence | context |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in _list_of_mappings(extension.get("signals")):
        lines.append(
            "| "
            f"`{row.get('target_key')}` | "
            f"`{row.get('side')}` | "
            f"`{row.get('observation_source')}` | "
            f"{row.get('count')} | "
            f"{row.get('source_mapping_confidence')} | "
            f"`{row.get('context_key_prefix')}` |"
        )


def _append_aggregate_store(lines: list[str], case: Mapping[str, object]) -> None:
    lines.extend(["", "### Aggregate Store", ""])
    lines.extend(
        [
            "| target | reading | source | target | contexts | evidence | signal | sources |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    store = _as_mapping(case.get("aggregate_store"))
    for row in _list_of_mappings(store.get("items")):
        lines.append(
            "| "
            f"`{row.get('target_lemma')}` | "
            f"`{row.get('target_reading') or ''}` | "
            f"{row.get('source_hit_count')} | "
            f"{row.get('target_hit_count')} | "
            f"{row.get('browsing_context_count')} | "
            f"{row.get('browsing_evidence')} | "
            f"{row.get('browsing_signal')} | "
            f"`{', '.join(map(str, row.get('observation_sources') or []))}` |"
        )


def _append_admission_simulations(lines: list[str], case: Mapping[str, object]) -> None:
    simulations = _as_mapping(case.get("admission_simulations"))
    if not simulations:
        return
    lines.extend(["", "### Admission Simulation", ""])
    for strength, simulation_value in simulations.items():
        simulation = _as_mapping(simulation_value)
        lines.extend(
            [
                f"#### {strength}",
                "",
                f"- Selected: `{', '.join(map(str, simulation.get('selected_lemmas', [])))}`",
                f"- Browsing driven count: `{simulation.get('browsing_driven_count')}`",
                "",
                "| target | lane | selected | neutral rank | final rank | signal | boost |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in _list_of_mappings(simulation.get("rows")):
            if row.get("browsing_signal") or row.get("selected"):
                lines.append(
                    "| "
                    f"`{row.get('target_key')}` | "
                    f"`{row.get('selected_lane')}` | "
                    f"{row.get('selected')} | "
                    f"{row.get('neutral_rank')} | "
                    f"{row.get('final_rank')} | "
                    f"{row.get('effective_browsing_signal')} | "
                    f"{row.get('browsing_boost')} |"
                )
        lines.append("")


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _list_of_mappings(value: object) -> list[Mapping[str, object]]:
    return [item for item in _list(value) if isinstance(item, Mapping)]
