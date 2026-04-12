from __future__ import annotations

from typing import Mapping, Sequence


def _render_rate(value: object) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _render_metric_ci(metric_view: Mapping[str, object]) -> str:
    bootstrap = metric_view.get("bootstrap_interval")
    if not isinstance(bootstrap, Mapping):
        return "n/a"
    lower = bootstrap.get("lower")
    upper = bootstrap.get("upper")
    if not isinstance(lower, (int, float)) or not isinstance(upper, (int, float)):
        return "n/a"
    return f"{_render_rate(lower)} to {_render_rate(upper)}"


def _render_metric_bound(metric_view: Mapping[str, object]) -> str:
    direction = str(metric_view.get("direction") or "")
    if direction == "lower":
        return _render_rate(metric_view.get("conservative_ceiling"))
    return _render_rate(metric_view.get("conservative_floor"))


def _render_surface_markdown(
    *,
    surface: Mapping[str, object],
    metric_order: Sequence[str],
    show_cluster_table: bool,
) -> list[str]:
    lines = [
        f"### {surface.get('label', '')}",
        "",
        f"- Cluster key: `{surface.get('cluster_key_name', '')}`",
        f"- Cluster count: `{surface.get('cluster_count', 0)}`",
    ]
    config = surface.get("config")
    if isinstance(config, Mapping) and config:
        config_parts = []
        for key in (
            "scorer_id",
            "context_view",
            "evidence_view",
            "min_active_score",
            "min_margin",
            "phrase_control_mode",
            "active_rescue_mode",
            "source_id",
        ):
            if key in config:
                config_parts.append(f"{key}={config.get(key)!r}")
        if config_parts:
            lines.append(f"- Config: `{', '.join(config_parts)}`")
    metric_views = surface.get("metric_views")
    if isinstance(metric_views, Mapping):
        lines.extend(
            [
                "",
                "| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for metric_name in metric_order:
            metric_view = metric_views.get(metric_name)
            if not isinstance(metric_view, Mapping):
                continue
            leave_one_cluster_out = metric_view.get("leave_one_cluster_out")
            held_out_worst = (
                leave_one_cluster_out.get("worst_case")
                if isinstance(leave_one_cluster_out, Mapping)
                else None
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        metric_name,
                        _render_rate(metric_view.get("point_estimate")),
                        _render_metric_ci(metric_view),
                        _render_rate(held_out_worst),
                        _render_metric_bound(metric_view),
                    ]
                )
                + " |"
            )
    if show_cluster_table:
        cluster_summaries = surface.get("cluster_summaries")
        if isinstance(cluster_summaries, Sequence) and not isinstance(
            cluster_summaries, (str, bytes)
        ):
            lines.extend(
                [
                    "",
                    "#### Cluster Breakdown",
                    "",
                    "| Cluster | Rows | Primary Read | Risk Read |",
                    "| --- | ---: | ---: | ---: |",
                ]
            )
            for row in cluster_summaries[:12]:
                if not isinstance(row, Mapping):
                    continue
                summary = row.get("summary")
                if not isinstance(summary, Mapping):
                    continue
                if "decision_accuracy" in summary:
                    primary = _render_rate(summary.get("replace_recall"))
                    risk = _render_rate(summary.get("harmful_replace_rate"))
                else:
                    primary = _render_rate(summary.get("abstain_recall"))
                    risk = _render_rate(summary.get("harmful_allow_rate"))
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            str(row.get("cluster_id") or ""),
                            str(int(row.get("row_count") or 0)),
                            primary,
                            risk,
                        ]
                    )
                    + " |"
                )
    return lines


def render_generalization_bound_markdown(
    report: Mapping[str, object],
    *,
    fixed_shadow_metric_order: Sequence[str],
    veto_proxy_metric_order: Sequence[str],
) -> str:
    lines = [
        "# en-es Semantic Veto Generalization Bound",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Pair: `{report.get('pair', '')}`",
    ]
    methodology = report.get("methodology")
    if isinstance(methodology, Mapping):
        lines.extend(
            [
                f"- Confidence method: `{methodology.get('bootstrap_kind', '')}`",
                f"- Bootstrap iterations: `{methodology.get('bootstrap_iterations', 0)}`",
                f"- Confidence level: `{methodology.get('confidence_level', 0.0)}`",
                f"- Random seed: `{methodology.get('random_seed', 0)}`",
                "- Important caveat: fixed-shadow and veto-proxy rows are different evaluation surfaces. "
                "This report estimates a corridor, not one single deploy KPI.",
            ]
        )

    corridor = report.get("confidence_corridor")
    if isinstance(corridor, Mapping):
        lines.extend(
            [
                "",
                "## Current Corridor",
                "",
                f"- Best current source-only blocker lane: `{corridor.get('source_only_source_id', '')}`",
                f"- Source-only abstain-recall conservative floor: `{_render_rate(corridor.get('source_only_abstain_recall_conservative_floor'))}`",
                f"- Source-only harmful-allow conservative ceiling: `{_render_rate(corridor.get('source_only_harmful_allow_conservative_ceiling'))}`",
                f"- Fixed-shadow replace-recall conservative floor: `{_render_rate(corridor.get('fixed_shadow_replace_recall_conservative_floor'))}`",
                f"- Fixed-shadow harmful-replace conservative ceiling: `{_render_rate(corridor.get('fixed_shadow_harmful_replace_conservative_ceiling'))}`",
            ]
        )

    fixed_shadow_bounds = report.get("fixed_shadow_bounds")
    if isinstance(fixed_shadow_bounds, Sequence) and not isinstance(
        fixed_shadow_bounds, (str, bytes)
    ):
        lines.extend(["", "## Fixed-Shadow Bounds"])
        for surface in fixed_shadow_bounds:
            if not isinstance(surface, Mapping):
                continue
            lines.extend(
                [""]
                + _render_surface_markdown(
                    surface=surface,
                    metric_order=fixed_shadow_metric_order,
                    show_cluster_table=True,
                )
            )

    veto_proxy_bounds = report.get("veto_proxy_bounds")
    if isinstance(veto_proxy_bounds, Sequence) and not isinstance(veto_proxy_bounds, (str, bytes)):
        lines.extend(["", "## Blocker-Generation Bounds"])
        for surface in veto_proxy_bounds:
            if not isinstance(surface, Mapping):
                continue
            lines.extend(
                [""]
                + _render_surface_markdown(
                    surface=surface,
                    metric_order=veto_proxy_metric_order,
                    show_cluster_table=False,
                )
            )

    return "\n".join(lines) + "\n"
