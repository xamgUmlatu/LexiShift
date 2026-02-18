from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from lexishift_core import Profile
from profile_ruleset_migration_service import migrate_profile_ruleset_paths


def test_migrate_profile_ruleset_paths_moves_paths_under_base_dir() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        base_dir = root / "app_data"
        rulesets_dir = base_dir / "rulesets"
        legacy_dir = base_dir / "legacy"
        legacy_dir.mkdir(parents=True, exist_ok=True)
        legacy_file = legacy_dir / "alpha.json"
        legacy_file.write_text("{}", encoding="utf-8")

        profile = Profile(
            profile_id="p1",
            name="P1",
            dataset_path=str(legacy_file),
            rulesets=(str(legacy_file),),
            active_ruleset=str(legacy_file),
        )

        updated_profiles, changed = migrate_profile_ruleset_paths(
            (profile,),
            base_dir=base_dir,
            rulesets_dir=rulesets_dir,
        )

        expected = str(rulesets_dir / "alpha.json")
        assert changed is True
        assert updated_profiles[0].dataset_path == expected
        # Preserve legacy behavior: once dataset_path migrates, subsequent checks for the same
        # original path see the old file as missing and keep the old string values unchanged.
        assert updated_profiles[0].active_ruleset == str(legacy_file)
        assert updated_profiles[0].rulesets == (str(legacy_file),)
        assert not legacy_file.exists()
        assert (rulesets_dir / "alpha.json").exists()


def test_migrate_profile_ruleset_paths_ignores_paths_outside_base_dir() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        base_dir = root / "app_data"
        rulesets_dir = base_dir / "rulesets"
        outside_dir = root / "outside"
        outside_dir.mkdir(parents=True, exist_ok=True)
        outside_file = outside_dir / "beta.json"
        outside_file.write_text("{}", encoding="utf-8")

        profile = Profile(
            profile_id="p1",
            name="P1",
            dataset_path=str(outside_file),
            rulesets=(str(outside_file),),
            active_ruleset=str(outside_file),
        )

        updated_profiles, changed = migrate_profile_ruleset_paths(
            (profile,),
            base_dir=base_dir,
            rulesets_dir=rulesets_dir,
        )

        assert changed is False
        assert updated_profiles[0] == profile
        assert outside_file.exists()


def test_migrate_profile_ruleset_paths_updates_when_target_already_exists() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        base_dir = root / "app_data"
        rulesets_dir = base_dir / "rulesets"
        legacy_dir = base_dir / "legacy"
        legacy_dir.mkdir(parents=True, exist_ok=True)
        rulesets_dir.mkdir(parents=True, exist_ok=True)
        legacy_file = legacy_dir / "gamma.json"
        legacy_file.write_text("{legacy}", encoding="utf-8")
        target_file = rulesets_dir / "gamma.json"
        target_file.write_text("{new}", encoding="utf-8")

        profile = Profile(
            profile_id="p1",
            name="P1",
            dataset_path=str(legacy_file),
            rulesets=(str(legacy_file),),
            active_ruleset=str(legacy_file),
        )

        updated_profiles, changed = migrate_profile_ruleset_paths(
            (profile,),
            base_dir=base_dir,
            rulesets_dir=rulesets_dir,
        )

        expected = str(target_file)
        assert changed is True
        assert updated_profiles[0].dataset_path == expected
        assert legacy_file.exists()
        assert target_file.read_text(encoding="utf-8") == "{new}"


def test_migrate_profile_ruleset_paths_keeps_original_when_replace_fails() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        base_dir = root / "app_data"
        rulesets_dir = base_dir / "rulesets"
        legacy_dir = base_dir / "legacy"
        legacy_dir.mkdir(parents=True, exist_ok=True)
        legacy_file = legacy_dir / "delta.json"
        legacy_file.write_text("{}", encoding="utf-8")

        profile = Profile(
            profile_id="p1",
            name="P1",
            dataset_path=str(legacy_file),
            rulesets=(str(legacy_file),),
            active_ruleset=str(legacy_file),
        )

        with patch("profile_ruleset_migration_service.os.replace", side_effect=OSError("fail")):
            updated_profiles, changed = migrate_profile_ruleset_paths(
                (profile,),
                base_dir=base_dir,
                rulesets_dir=rulesets_dir,
            )

        assert changed is False
        assert updated_profiles[0] == profile
        assert legacy_file.exists()
