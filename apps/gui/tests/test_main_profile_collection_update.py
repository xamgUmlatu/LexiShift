from __future__ import annotations

from types import SimpleNamespace

from lexishift_core import AppSettings, Profile
from main import MainWindow


def test_apply_profile_collection_update_keeps_active_id_and_refreshes() -> None:
    old_profile = Profile(
        profile_id="p1",
        name="Old",
        dataset_path="/tmp/old.json",
        rulesets=("/tmp/old.json",),
        active_ruleset="/tmp/old.json",
    )
    new_profile = Profile(
        profile_id="p1",
        name="New",
        dataset_path="/tmp/new.json",
        rulesets=("/tmp/new.json",),
        active_ruleset="/tmp/new.json",
    )
    calls: list[tuple[str, object]] = []

    dummy = SimpleNamespace(
        state=SimpleNamespace(
            settings=AppSettings(
                profiles=(old_profile,),
                active_profile_id="p1",
            ),
            set_profiles=lambda profiles, active_profile_id: calls.append(
                ("set_profiles", (profiles, active_profile_id))
            ),
        ),
        _load_active_profile=lambda: calls.append(("load_active", None)),
        _refresh_profiles_ui=lambda: calls.append(("refresh_profiles_ui", None)),
    )

    MainWindow._apply_profile_collection_update(dummy, (new_profile,))

    assert calls[0][0] == "set_profiles"
    profiles_arg, active_id_arg = calls[0][1]
    assert profiles_arg == (new_profile,)
    assert active_id_arg == "p1"
    assert calls[1:] == [("load_active", None), ("refresh_profiles_ui", None)]
