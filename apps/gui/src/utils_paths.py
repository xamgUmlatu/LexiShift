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
    if getattr(sys, "frozen", False):
        # One-file uses _MEIPASS; One-dir uses executable dir
        base = getattr(sys, "_MEIPASS", None)
        if base:
            return os.path.join(base, "resources", *parts)
        exe_dir = os.path.dirname(sys.executable)
        if sys.platform == "darwin":
            # .../Contents/MacOS -> .../Contents/Resources
            macos_dir = os.path.normpath(exe_dir)
            if macos_dir.endswith(os.path.join("Contents", "MacOS")):
                resources_dir = os.path.abspath(os.path.join(macos_dir, "..", "Resources"))
                return os.path.join(resources_dir, "resources", *parts)
        return os.path.join(exe_dir, "resources", *parts)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.abspath(os.path.join(current_dir, "..", "resources"))
    return os.path.join(resources_dir, *parts)
