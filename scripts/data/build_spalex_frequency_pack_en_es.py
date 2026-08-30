#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.frequency.es.spalex import (  # noqa: E402,F401
    DEFAULT_DATA_ROOT,
    DEFAULT_CURRENT_FREQUENCY_DB,
    DEFAULT_KAIKKI_FORWARD_DB,
    DEFAULT_PACK_ID,
    DEFAULT_PROVIDER,
    DEFAULT_SOURCE_MODE,
    DEFAULT_SPALEX_DOI,
    DEFAULT_SPALEX_LICENSE,
    DEFAULT_SPALEX_SOURCE_URL,
    SOURCE_MODE_CDE_UNION,
    SOURCE_MODE_SPALEX_ONLY,
    SOURCE_MODES,
    build_spalex_frequency_pack,
    main,
)


if __name__ == "__main__":
    raise SystemExit(main())
