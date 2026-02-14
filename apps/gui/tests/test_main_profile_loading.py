from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from lexishift_core import AppSettings, Profile
from main import MainWindow


def test_load_active_profile_falls_back_to_first_profile_when_id_is_stale() -> None:
    loaded: list[str] = []
    profile = Profile(
        profile_id="p1",
        name="Profile 1",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json",),
        active_ruleset="/tmp/a.json",
    )

    dummy = SimpleNamespace(
        state=SimpleNamespace(
            settings=AppSettings(
                profiles=(profile,),
                active_profile_id="missing-profile",
            )
        ),
        _load_profile=lambda selected: loaded.append(selected.profile_id),
    )

    MainWindow._load_active_profile(dummy)
    assert loaded == ["p1"]


def test_load_profile_recovers_from_missing_active_ruleset_path() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        existing = root / "existing.json"
        existing.write_text("{}", encoding="utf-8")
        missing = root / "missing.json"
        profile = Profile(
            profile_id="p1",
            name="Profile 1",
            dataset_path=str(existing),
            rulesets=(str(existing),),
            active_ruleset=str(missing),
        )
        loaded: list[str] = []
        activated: list[str] = []
        dummy = SimpleNamespace(
            state=SimpleNamespace(
                settings=AppSettings(
                    profiles=(profile,),
                    active_profile_id="p1",
                ),
                load_dataset=lambda path: loaded.append(str(path)),
                set_profiles=lambda profiles, active_profile_id: None,
            ),
            _current_profile=lambda: profile,
            _active_ruleset_path=lambda selected: MainWindow._active_ruleset_path(dummy, selected),
            _resolve_profile_dataset_path=lambda selected: MainWindow._resolve_profile_dataset_path(dummy, selected),
            _set_active_ruleset_path=lambda path: activated.append(os.path.abspath(str(path))),
        )

        MainWindow._load_profile(dummy, profile)

        expected = os.path.abspath(str(existing))
        assert loaded == [expected]
        assert activated == [expected]
