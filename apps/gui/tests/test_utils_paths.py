from __future__ import annotations

import os

import utils_paths


def test_reveal_path_selects_file_on_windows(monkeypatch) -> None:
    calls: list[tuple[list[str], bool]] = []
    path = "/tmp/lexishift/freq-es-cde.sqlite"
    target = os.path.abspath(path)

    monkeypatch.setattr(utils_paths.sys, "platform", "win32")
    monkeypatch.setattr(utils_paths.os.path, "isdir", lambda _value: False)
    monkeypatch.setattr(
        utils_paths.subprocess,
        "run",
        lambda command, check: calls.append((command, check)),
    )

    utils_paths.reveal_path(path)

    assert calls == [(["explorer", f"/select,{target}"], False)]


def test_reveal_path_opens_directory_on_windows(monkeypatch) -> None:
    calls: list[tuple[list[str], bool]] = []
    path = "/tmp/lexishift/language_packs"
    target = os.path.abspath(path)

    monkeypatch.setattr(utils_paths.sys, "platform", "win32")
    monkeypatch.setattr(utils_paths.os.path, "isdir", lambda _value: True)
    monkeypatch.setattr(
        utils_paths.subprocess,
        "run",
        lambda command, check: calls.append((command, check)),
    )

    utils_paths.reveal_path(path)

    assert calls == [(["explorer", target], False)]
