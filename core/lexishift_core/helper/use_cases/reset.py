from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.status import HelperStatus, load_status, save_status
from lexishift_core.srs import (
    SrsStore,
    load_srs_inventory,
    load_srs_store,
    remove_pair_inventory,
    save_srs_inventory,
    save_srs_store,
)
from lexishift_core.srs.time import now_utc


def _remove_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    path.unlink()
    return True


def reset_srs_data(
    paths: HelperPaths,
    *,
    pair: Optional[str] = None,
    profile_id: str = "default",
    resolve_profile_id_fn: Callable[..., str],
) -> dict:
    normalized_profile_id = resolve_profile_id_fn(paths, profile_id=profile_id)
    scoped_pair = str(pair or "").strip() or None
    profile_store_path = paths.srs_store_path_for(normalized_profile_id)
    profile_srs_dir = paths.profile_srs_dir(normalized_profile_id)
    profile_status_path = paths.srs_status_path_for(normalized_profile_id)
    inventory_path = paths.srs_inventory_path_for(normalized_profile_id)

    removed_items = 0
    remaining_items = 0
    if profile_store_path.exists():
        store = load_srs_store(profile_store_path)
        if scoped_pair:
            kept_items = tuple(item for item in store.items if item.language_pair != scoped_pair)
        else:
            kept_items = tuple()
        removed_items = len(store.items) - len(kept_items)
        remaining_items = len(kept_items)
        save_srs_store(SrsStore(items=kept_items, version=store.version), profile_store_path)
    else:
        save_srs_store(SrsStore(), profile_store_path)

    removed_snapshots = 0
    removed_rulesets = 0
    removed_inventory_entries = 0
    if scoped_pair:
        if _remove_file(paths.snapshot_path(scoped_pair, profile_id=normalized_profile_id)):
            removed_snapshots += 1
        if _remove_file(paths.ruleset_path(scoped_pair, profile_id=normalized_profile_id)):
            removed_rulesets += 1
        if inventory_path.exists():
            inventory = load_srs_inventory(inventory_path)
            pair_exists = scoped_pair in dict(inventory.pairs or {})
            if pair_exists:
                updated_inventory = remove_pair_inventory(inventory, scoped_pair)
                removed_inventory_entries = 1
                if updated_inventory.pairs:
                    save_srs_inventory(updated_inventory, inventory_path)
                else:
                    _remove_file(inventory_path)
    else:
        for snapshot in profile_srs_dir.glob("srs_rulegen_snapshot_*.json"):
            if _remove_file(snapshot):
                removed_snapshots += 1
        for ruleset in profile_srs_dir.glob("srs_ruleset_*.json"):
            if _remove_file(ruleset):
                removed_rulesets += 1
        if inventory_path.exists():
            inventory = load_srs_inventory(inventory_path)
            removed_inventory_entries = len(dict(inventory.pairs or {}))
            _remove_file(inventory_path)

    status = load_status(profile_status_path)
    save_status(
        HelperStatus(
            version=status.version,
            helper_version=status.helper_version,
            last_run_at=now_utc().isoformat(),
            last_error=None,
            last_pair=scoped_pair,
            last_rule_count=0,
            last_target_count=0,
        ),
        profile_status_path,
    )

    return {
        "pair": scoped_pair or "all",
        "profile_id": normalized_profile_id,
        "removed_items": removed_items,
        "remaining_items": remaining_items,
        "removed_snapshots": removed_snapshots,
        "removed_rulesets": removed_rulesets,
        "removed_inventory_entries": removed_inventory_entries,
        "inventory_path": str(inventory_path),
    }
