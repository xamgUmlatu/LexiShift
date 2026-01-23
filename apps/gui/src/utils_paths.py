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


def resource_path(*parts: str) -> str:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, "resources", *parts)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.abspath(os.path.join(current_dir, "..", "resources"))
    return os.path.join(resources_dir, *parts)
