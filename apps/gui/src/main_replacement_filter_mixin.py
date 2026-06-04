from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem

from i18n import t
from lexishift_core import SynonymSourceSettings, VocabRule
from lexishift_core.helper.embedding_packs import resolve_embedding_pack_artifact
from lexishift_core.resources.synonyms import EmbeddingIndex
from main_embedding_loader import EmbeddingLoaderThread
from main_paths import _app_data_dir


class MainWindowReplacementFilterMixin:
    def _refresh_embedding_index(self) -> None:
        self._embedding_indices.clear()
        self._embedding_load_error = None
        self._embedding_loading = False
        self._embedding_loading_pair = None
        self._update_replacement_filter_state()
        self._ensure_embedding_loaded_for_selection()

    def _ensure_embedding_loaded_for_selection(self) -> None:
        pair_key = self._embedding_pair_for_replacement(self._selected_replacement())
        if not pair_key:
            self._update_replacement_filter_state()
            return
        self._ensure_embedding_loaded(pair_key)

    def _ensure_embedding_loaded(self, pair_key: str) -> None:
        if pair_key in self._embedding_indices:
            self._update_replacement_filter_state()
            return
        settings = self.state.settings.synonyms
        paths = self._embedding_paths_for_pair(settings, pair_key)
        if not settings or not settings.use_embeddings or not paths:
            self._embedding_load_error = t("replacement.embeddings_missing")
            self._update_replacement_filter_state()
            return
        self._embedding_loading = True
        self._embedding_loading_pair = pair_key
        self._embedding_load_id += 1
        load_id = self._embedding_load_id
        self._embedding_thread = EmbeddingLoaderThread(
            pair_key,
            paths,
            lower_case=settings.lower_case,
            parent=self,
        )
        self._embedding_thread.loaded.connect(
            lambda loaded_pair, index, error, load_id=load_id: self._on_embeddings_loaded(
                load_id, loaded_pair, index, error
            )
        )
        self._embedding_thread.start()
        self._update_replacement_filter_state()

    def _update_replacement_filter_state(self) -> None:
        replacement = self._selected_replacement()
        has_selection = replacement is not None
        pair_key = self._embedding_pair_for_replacement(replacement)
        has_embeddings = bool(pair_key and pair_key in self._embedding_indices)
        scope = self._replacement_filter_scope(replacement)
        enabled = (
            has_embeddings and has_selection and scope != "none" and not self._embedding_loading
        )
        self.replacement_threshold_slider.setEnabled(enabled)
        self.replacement_threshold_value.setEnabled(enabled)
        self.embedding_progress.setVisible(self._embedding_loading)
        if self._embedding_loading:
            self.replacement_hint_label.setText(t("replacement.loading_embeddings"))
            self.replacement_hint_label.setVisible(True)
        elif self._embedding_load_error:
            self.replacement_hint_label.setText(self._embedding_load_error)
            self.replacement_hint_label.setVisible(True)
        elif not has_embeddings:
            self.replacement_hint_label.setText(t("replacement.enable_embeddings_hint"))
            self.replacement_hint_label.setVisible(True)
        elif scope == "all":
            self.replacement_hint_label.setText(t("replacement.no_synonym_tags"))
            self.replacement_hint_label.setVisible(True)
        else:
            self.replacement_hint_label.setVisible(False)

    def _refresh_replacement_list(self) -> None:
        selected = self._selected_replacement()
        replacement_counts: dict[str, tuple[int, int, int]] = {}
        for rule in self.rules_model.rules():
            replacement = rule.replacement.strip()
            if not replacement:
                continue
            syn_total, syn_enabled, total = replacement_counts.get(replacement, (0, 0, 0))
            total += 1
            if "synonym" in rule.tags:
                syn_total += 1
                if rule.enabled:
                    syn_enabled += 1
            replacement_counts[replacement] = (syn_total, syn_enabled, total)
        self.replacement_list.blockSignals(True)
        self.replacement_list.clear()
        for replacement in sorted(replacement_counts.keys(), key=str.lower):
            syn_total, syn_enabled, total = replacement_counts[replacement]
            if syn_total:
                label = t(
                    "replacement.list_label",
                    replacement=replacement,
                    enabled=syn_enabled,
                    total=syn_total,
                )
            else:
                label = replacement
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, replacement)
            if syn_total:
                item.setToolTip(
                    t(
                        "replacement.tooltip_counts",
                        enabled=syn_enabled,
                        total=syn_total,
                        overall=total,
                    )
                )
            self.replacement_list.addItem(item)
        restored = False
        if selected:
            for row in range(self.replacement_list.count()):
                item = self.replacement_list.item(row)
                if item and item.data(Qt.UserRole) == selected:
                    self.replacement_list.setCurrentRow(row)
                    restored = True
                    break
        self.replacement_list.blockSignals(False)
        if selected and not restored:
            self.replacement_selected_label.setText(t("replacement.select_hint"))
        self._update_replacement_filter_state()

    def _selected_replacement(self) -> Optional[str]:
        item = self.replacement_list.currentItem()
        if not item:
            return None
        return item.data(Qt.UserRole)

    def _normalize_pair(self, lang_a: str, lang_b: str) -> str:
        if lang_a == lang_b:
            return f"{lang_a}-{lang_b}"
        return "-".join(sorted([lang_a, lang_b]))

    def _embedding_pair_for_replacement(self, replacement: Optional[str]) -> Optional[str]:
        if not replacement:
            return None
        counts: dict[str, int] = {}
        for rule in self.rules_model.rules():
            if rule.replacement != replacement:
                continue
            pair = rule.metadata.language_pair if rule.metadata else None
            if not pair:
                continue
            counts[pair] = counts.get(pair, 0) + 1
        if not counts:
            return None
        return max(counts.items(), key=lambda item: item[1])[0]

    def _embedding_paths_for_pair(
        self,
        settings: Optional[SynonymSourceSettings],
        pair_key: Optional[str],
    ) -> list[Path]:
        if not settings or not settings.use_embeddings or not pair_key:
            return []
        enabled = dict(settings.embedding_pair_enabled or {})
        if pair_key in enabled and not enabled[pair_key]:
            return []
        resolved_paths: list[Path] = []
        seen: set[Path] = set()
        embedding_pack_paths = dict(settings.embedding_pack_paths or {})
        pair_pack_ids = dict(getattr(settings, "embedding_pair_pack_ids", {}) or {}).get(pair_key)
        if isinstance(pair_pack_ids, (list, tuple)):
            base_dir = _app_data_dir() / "embedding_packs"
            for pack_id in pair_pack_ids:
                pack_key = str(pack_id or "").strip()
                if not pack_key:
                    continue
                configured_path = embedding_pack_paths.get(pack_key)
                resolved = resolve_embedding_pack_artifact(
                    base_dir,
                    pack_id=pack_key,
                    configured_path=Path(configured_path) if configured_path else None,
                )
                if resolved is None or not resolved.exists():
                    continue
                if resolved in seen:
                    continue
                seen.add(resolved)
                resolved_paths.append(resolved)
        pair_paths = dict(settings.embedding_pair_paths or {}).get(pair_key)
        if isinstance(pair_paths, (list, tuple)):
            for raw_path in pair_paths:
                candidate = Path(raw_path) if raw_path else None
                if candidate is None or not candidate.exists():
                    continue
                if candidate in seen:
                    continue
                seen.add(candidate)
                resolved_paths.append(candidate)
        return resolved_paths

    def _replacement_filter_scope(self, replacement: Optional[str]) -> str:
        if not replacement:
            return "none"
        has_any = False
        for rule in self.rules_model.rules():
            if rule.replacement != replacement:
                continue
            has_any = True
            if "synonym" in rule.tags:
                return "synonyms"
        return "all" if has_any else "none"

    def _default_embedding_threshold(self) -> float:
        settings = self.state.settings.synonyms
        if settings:
            return settings.embedding_threshold
        return 0.0

    def _on_replacement_selected(
        self, current: Optional[QListWidgetItem], _previous: Optional[QListWidgetItem]
    ) -> None:
        replacement = current.data(Qt.UserRole) if current else None
        if replacement:
            threshold = self._replacement_thresholds.get(
                replacement, self._default_embedding_threshold()
            )
            self._replacement_slider_updating = True
            self.replacement_threshold_slider.setValue(int(round(threshold * 100)))
            self.replacement_threshold_value.setText(f"{threshold:.2f}")
            self._replacement_slider_updating = False
            scope = self._replacement_filter_scope(replacement)
            if scope == "all":
                self.replacement_selected_label.setText(
                    t("replacement.filter_rules", replacement=replacement)
                )
            else:
                self.replacement_selected_label.setText(
                    t("replacement.filter_synonyms", replacement=replacement)
                )
        else:
            self.replacement_selected_label.setText(t("replacement.select_hint"))
        self._ensure_embedding_loaded_for_selection()
        self._update_replacement_filter_state()

    def _on_replacement_threshold_changed(self, value: int) -> None:
        if self._replacement_slider_updating:
            return
        replacement = self._selected_replacement()
        if not replacement:
            return
        threshold = value / 100.0
        self.replacement_threshold_value.setText(f"{threshold:.2f}")
        self._replacement_thresholds[replacement] = threshold
        self._apply_replacement_threshold(replacement, threshold)

    def _on_embeddings_loaded(
        self, load_id: int, pair_key: str, index: Optional[EmbeddingIndex], error: str
    ) -> None:
        if load_id != self._embedding_load_id:
            return
        self._embedding_loading = False
        if index is not None:
            self._embedding_indices[pair_key] = index
        self._embedding_load_error = error or None
        self._embedding_loading_pair = None
        if self._embedding_thread:
            self._embedding_thread.quit()
            self._embedding_thread = None
        self._update_replacement_filter_state()

    def _apply_replacement_threshold(self, replacement: str, threshold: float) -> None:
        pair_key = self._embedding_pair_for_replacement(replacement)
        if not pair_key:
            return
        index = self._embedding_indices.get(pair_key)
        if index is None:
            return
        scope = self._replacement_filter_scope(replacement)
        if scope == "none":
            return
        updates: list[tuple[int, VocabRule]] = []
        for row, rule in enumerate(self.rules_model.rules()):
            if rule.replacement != replacement:
                continue
            if scope == "synonyms" and "synonym" not in rule.tags:
                continue
            score = index.similarity(rule.source_phrase, replacement)
            if score is None:
                enabled = threshold <= 0.0
            else:
                enabled = score >= threshold
            if rule.enabled != enabled:
                updates.append((row, replace(rule, enabled=enabled)))
        if updates:
            self.rules_model.update_rules_bulk(updates)
