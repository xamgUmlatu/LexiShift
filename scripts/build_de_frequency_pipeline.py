#!/usr/bin/env python3
from __future__ import annotations

import os
import sys


def _ensure_core_on_path() -> None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    core_root = os.path.join(repo_root, "core")
    if core_root not in sys.path:
        sys.path.insert(0, core_root)


def main() -> None:
    _ensure_core_on_path()
    from lexishift_core.de_frequency_pipeline import main as core_main

    core_main()


if __name__ == "__main__":
    main()
