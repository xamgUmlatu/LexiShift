from __future__ import annotations

from pathlib import Path
from typing import Optional

from i18n import t
from lexishift_core import (
    SeedSelectionConfig,
    SrsGrowthConfig,
    build_seed_candidates,
    grow_srs_store,
    resolve_allowed_pairs,
    seed_to_selector_candidates,
)
from lexishift_core.helper.frequency_packs import (
    FrequencyPackRef,
    resolve_configured_frequency_pack,
)
from lexishift_core.helper.lp_capabilities import (
    default_jmdict_path,
    resolve_pair_capability,
)
from main_paths import _app_data_dir


class MainWindowSrsMixin:
    def _refresh_srs_growth(self) -> None:
        settings = self.state.settings.srs
        if not settings or not settings.enabled:
            return
        synonym_settings = self.state.settings.synonyms
        if not synonym_settings:
            return
        language_pack_paths = synonym_settings.language_pack_paths or {}
        frequency_pack_paths = synonym_settings.frequency_pack_paths or {}
        managed_frequency_pack_ids = tuple(
            getattr(synonym_settings, "managed_frequency_pack_ids", ()) or ()
        )
        allowed_pairs = tuple(resolve_allowed_pairs(settings))
        if not allowed_pairs:
            return
        try:
            candidates = []
            for pair in allowed_pairs:
                capability = resolve_pair_capability(pair)
                frequency_pack = self._resolve_frequency_pack_for_pair(
                    pair,
                    frequency_pack_paths=frequency_pack_paths,
                    managed_frequency_pack_ids=managed_frequency_pack_ids,
                )
                if not frequency_pack or not frequency_pack.path.exists():
                    continue
                jmdict_path = self._resolve_jmdict_for_pair(
                    pair,
                    language_pack_paths=language_pack_paths,
                )
                if capability.requires_jmdict_for_seed and (
                    not jmdict_path or not jmdict_path.exists()
                ):
                    continue
                seed_config = SeedSelectionConfig(
                    language_pair=pair,
                    top_n=2000,
                    jmdict_path=jmdict_path,
                    require_jmdict=capability.requires_jmdict_for_seed,
                )
                seeds = build_seed_candidates(
                    frequency_db=frequency_pack.path,
                    config=seed_config,
                )
                candidates.extend(seed_to_selector_candidates(seeds))
            if not candidates:
                self._append_log(t("logs.srs_seed_missing"))
                return
            growth_config = SrsGrowthConfig(
                coverage_scalar=settings.coverage_scalar,
                max_new_items=settings.max_new_items_per_day,
            )
            updated_store, plan = grow_srs_store(
                candidates,
                store=self.state.srs_store,
                settings=settings,
                config=growth_config,
                allowed_pairs=allowed_pairs,
            )
            if plan.add_count > 0:
                self.state.update_srs_store(updated_store)
                self._append_log(
                    t(
                        "logs.srs_seed_updated",
                        added=plan.add_count,
                        total=len(updated_store.items),
                        pool=plan.pool_size,
                    )
                )
            else:
                self._append_log(
                    t(
                        "logs.srs_seed_noop",
                        total=len(updated_store.items),
                        pool=plan.pool_size,
                    )
                )
        except Exception as exc:
            self._append_log(t("logs.srs_seed_failed", error=str(exc)))

    def _resolve_frequency_pack_for_pair(
        self,
        pair: str,
        *,
        frequency_pack_paths: dict[str, str],
        managed_frequency_pack_ids: tuple[str, ...] = (),
    ) -> Optional[FrequencyPackRef]:
        frequency_dir = _app_data_dir() / "frequency_packs"
        resolved, _resolution = resolve_configured_frequency_pack(
            pair,
            frequency_packs_dir=frequency_dir,
            settings_frequency_pack_paths=frequency_pack_paths,
            managed_frequency_pack_ids=managed_frequency_pack_ids,
        )
        return resolved

    def _resolve_jmdict_for_pair(
        self,
        pair: str,
        *,
        language_pack_paths: dict[str, str],
    ) -> Optional[Path]:
        default_jmdict = default_jmdict_path(pair, language_packs_dir=Path("."))
        if default_jmdict is None:
            return None
        lookup_keys = ("jmdict-ja-en", default_jmdict.name)
        for key in lookup_keys:
            raw_path = str(language_pack_paths.get(key, "")).strip()
            if not raw_path:
                continue
            candidate = Path(raw_path)
            if candidate.is_file():
                return candidate
            if candidate.is_dir():
                nested = candidate / default_jmdict.name
                if nested.is_file():
                    return nested
        return None
