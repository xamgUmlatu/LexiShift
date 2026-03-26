from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class BenchmarkPreset:
    name: str
    description: str
    args: tuple[str, ...]


def load_benchmark_presets(path: Path) -> dict[str, BenchmarkPreset]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Preset payload must be an object: {path}")
    raw_presets = payload.get("presets")
    if not isinstance(raw_presets, Mapping) or not raw_presets:
        raise ValueError(f"Preset payload is missing a non-empty `presets` object: {path}")
    presets: dict[str, BenchmarkPreset] = {}
    for name, raw_preset in raw_presets.items():
        preset_name = str(name or "").strip()
        if not preset_name:
            raise ValueError(f"Preset payload contains an empty preset name: {path}")
        if not isinstance(raw_preset, Mapping):
            raise ValueError(f"Preset `{preset_name}` must be an object: {path}")
        description = str(raw_preset.get("description") or "").strip()
        if not description:
            raise ValueError(f"Preset `{preset_name}` is missing `description`: {path}")
        raw_args = raw_preset.get("args")
        if not isinstance(raw_args, Sequence) or isinstance(raw_args, (str, bytes)):
            raise ValueError(f"Preset `{preset_name}` must define an `args` array: {path}")
        args = tuple(str(item) for item in raw_args)
        if not args:
            raise ValueError(f"Preset `{preset_name}` must provide at least one argv token: {path}")
        presets[preset_name] = BenchmarkPreset(
            name=preset_name,
            description=description,
            args=args,
        )
    return presets


def format_benchmark_presets_listing(presets: Mapping[str, BenchmarkPreset]) -> str:
    lines = ["Rulegen benchmark presets:"]
    for name in sorted(presets):
        preset = presets[name]
        lines.append(f"- {preset.name}: {preset.description}")
    return "\n".join(lines)
