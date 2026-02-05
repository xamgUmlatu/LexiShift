from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def open_path(path: Path) -> None:
    target = Path(path).expanduser().resolve()
    if sys.platform == "darwin":
        subprocess.run(["open", str(target)], check=False)
        return
    if sys.platform.startswith("win"):
        os.startfile(str(target))  # type: ignore[attr-defined]
        return
    subprocess.run(["xdg-open", str(target)], check=False)
