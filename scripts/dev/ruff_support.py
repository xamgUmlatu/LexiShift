#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import shutil
import subprocess
import sys


@dataclass(frozen=True)
class RuffResolution:
    available: bool
    prefix: tuple[str, ...]
    source: str
    detail: str

    def command(self, *args: str) -> list[str]:
        if not self.available:
            raise RuntimeError("Ruff is unavailable in the current environment")
        return [*self.prefix, *args]


def _probe(prefix: list[str]) -> bool:
    try:
        result = subprocess.run(
            [*prefix, "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0


def resolve_ruff() -> RuffResolution:
    module_prefix = [sys.executable, "-m", "ruff"]
    if _probe(module_prefix):
        return RuffResolution(
            available=True,
            prefix=tuple(module_prefix),
            source="python-module",
            detail=sys.executable,
        )

    path_executable = shutil.which("ruff")
    if path_executable and _probe([path_executable]):
        return RuffResolution(
            available=True,
            prefix=(path_executable,),
            source="path",
            detail=path_executable,
        )

    return RuffResolution(
        available=False,
        prefix=(),
        source="unavailable",
        detail=f"Tried {sys.executable} -m ruff and ruff on PATH",
    )
