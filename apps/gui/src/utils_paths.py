from __future__ import annotations

import os
import subprocess
import sys


def reveal_path(path: str) -> None:
    if not path:
        return
    target = os.path.abspath(os.path.expanduser(path))
    if sys.platform == "darwin":
        subprocess.run(["open", "-R", target], check=False)
        return
    if sys.platform.startswith("win"):
        subprocess.run(["explorer", "/select,", target], check=False)
        return
    directory = target if os.path.isdir(target) else os.path.dirname(target)
    subprocess.run(["xdg-open", directory], check=False)
