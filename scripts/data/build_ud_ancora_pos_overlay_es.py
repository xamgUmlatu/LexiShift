#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CORE_ROOT = os.path.join(PROJECT_ROOT, "core")
for path in (PROJECT_ROOT, CORE_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from lexishift_core.pos.ud_ancora import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
