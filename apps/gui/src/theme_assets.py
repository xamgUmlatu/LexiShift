from __future__ import annotations

import os
import shutil

from theme_loader import theme_dir
from utils_paths import resource_path


def ensure_sample_images() -> None:
    src_dir = resource_path("sample_images")
    if not os.path.isdir(src_dir):
        return
    dest_dir = os.path.join(theme_dir(), "sample_images")
    os.makedirs(dest_dir, exist_ok=True)
    for entry in os.listdir(src_dir):
        if entry.startswith("."):
            continue
        src_path = os.path.join(src_dir, entry)
        if not os.path.isfile(src_path):
            continue
        dest_path = os.path.join(dest_dir, entry)
        if os.path.exists(dest_path):
            continue
        try:
            shutil.copy2(src_path, dest_path)
        except OSError:
            continue


def ensure_sample_themes() -> None:
    src_dir = resource_path("themes")
    if not os.path.isdir(src_dir):
        return
    dest_dir = theme_dir()
    os.makedirs(dest_dir, exist_ok=True)
    for entry in os.listdir(src_dir):
        if entry.startswith("."):
            continue
        src_path = os.path.join(src_dir, entry)
        if not os.path.isfile(src_path):
            continue
        dest_path = os.path.join(dest_dir, entry)
        if os.path.exists(dest_path):
            continue
        try:
            shutil.copy2(src_path, dest_path)
        except OSError:
            continue
