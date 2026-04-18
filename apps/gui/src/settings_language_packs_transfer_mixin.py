from __future__ import annotations

import os
from pathlib import Path

from i18n import t
from language_packs import (
    FrequencyPackDownloadThread,
    LanguagePackDownloadThread,
    download_log_path,
)
from lexishift_core.helper.installed_packs import write_installed_pack_manifest
from pack_download_failures import (
    PACK_DOWNLOAD_FAILURE_BLOCKED,
    PACK_DOWNLOAD_FAILURE_CANCELLED,
    PACK_DOWNLOAD_FAILURE_NOT_FOUND,
    PACK_DOWNLOAD_FAILURE_OFFLINE,
    PACK_DOWNLOAD_FAILURE_PROCESSING_FAILED,
    PACK_DOWNLOAD_FAILURE_SOURCE_UNAVAILABLE,
    PACK_DOWNLOAD_FAILURE_TIMEOUT,
    PACK_DOWNLOAD_FAILURE_WRITE_FAILED,
    PackDownloadFailure,
    pack_download_failure_supports_archive_mirror,
    parse_pack_download_failure,
)
from settings_language_packs_support import EmbeddingConversionThread


class LanguagePackPanelTransferMixin:
    def _on_language_pack_progress(self, pack_id: str, downloaded: int, total: int) -> None:
        row = self._language_pack_rows.get(pack_id)
        if not row:
            return
        self._set_status_item_tone(row.status_item, "info")
        if total > 0:
            pct = int((downloaded / total) * 100)
            row.status_item.setText(t("language_packs.status.downloading_pct", percent=pct))
        else:
            row.status_item.setText(t("language_packs.status.downloading"))

    def _on_frequency_pack_progress(self, pack_id: str, downloaded: int, total: int) -> None:
        row = self._frequency_pack_rows.get(pack_id)
        if not row:
            return
        self._set_status_item_tone(row.status_item, "info")
        if total > 0:
            pct = int((downloaded / total) * 100)
            row.status_item.setText(t("language_packs.status.downloading_pct", percent=pct))
        else:
            row.status_item.setText(t("language_packs.status.downloading"))

    def _on_embedding_pack_progress(self, pack_id: str, downloaded: int, total: int) -> None:
        row = self._embedding_row_for(pack_id)
        if not row:
            return
        self._set_status_item_tone(row.status_item, "info")
        if total > 0:
            pct = int((downloaded / total) * 100)
            row.status_item.setText(t("language_packs.status.downloading_pct", percent=pct))
        else:
            row.status_item.setText(t("language_packs.status.downloading"))

    def _set_download_failed_status(self, *, pack, row, message: str) -> None:
        failure = parse_pack_download_failure(message)
        if failure.kind == PACK_DOWNLOAD_FAILURE_CANCELLED and self._closing:
            row.status_item.setText(t("language_packs.status.cancelled"))
            self._set_status_item_tone(row.status_item, "muted")
            row.download_button.setEnabled(True)
            row.download_button.setText(t("buttons.download"))
            return
        row.status_item.setText(t("language_packs.status.failed"))
        self._set_status_item_tone(row.status_item, "error")
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.retry"))
        log_path = download_log_path()
        tooltip = self._download_failure_tooltip(log_path=log_path, failure=failure)
        row.status_item.setToolTip(tooltip)
        self._set_status_message(
            self._download_failure_message(pack=pack, failure=failure),
            tone="error",
            tooltip=tooltip,
        )

    def _download_failure_message(self, *, pack, failure: PackDownloadFailure) -> str:
        name = pack.display_name()
        if failure.kind == PACK_DOWNLOAD_FAILURE_OFFLINE:
            message = t("language_packs.download_failed_offline", name=name)
        elif failure.kind == PACK_DOWNLOAD_FAILURE_TIMEOUT:
            message = t("language_packs.download_failed_timeout", name=name)
        elif failure.kind == PACK_DOWNLOAD_FAILURE_NOT_FOUND:
            message = t("language_packs.download_failed_not_found", name=name)
        elif failure.kind == PACK_DOWNLOAD_FAILURE_BLOCKED:
            message = t("language_packs.download_failed_blocked", name=name)
        elif failure.kind == PACK_DOWNLOAD_FAILURE_SOURCE_UNAVAILABLE:
            message = t("language_packs.download_failed_source_unavailable", name=name)
        elif failure.kind == PACK_DOWNLOAD_FAILURE_WRITE_FAILED:
            message = t(
                "language_packs.download_failed_write_failure",
                name=name,
                error=failure.detail,
            )
        elif failure.kind == PACK_DOWNLOAD_FAILURE_PROCESSING_FAILED:
            message = t(
                "language_packs.download_failed_processing_failure",
                name=name,
                error=failure.detail,
            )
        else:
            message = t("language_packs.download_failed_unknown", name=name, error=failure.detail)
        if pack_download_failure_supports_archive_mirror(failure) and pack.wayback_url:
            message = (
                f"{message} "
                f"{t('language_packs.download_failed_try_archive', link=pack.wayback_url)}"
            )
        return message

    def _download_failure_tooltip(self, *, log_path: str, failure: PackDownloadFailure) -> str:
        detail = str(failure.detail or "").strip()
        if not detail or failure.kind == PACK_DOWNLOAD_FAILURE_CANCELLED:
            return log_path
        return f"{log_path}\n\n{detail}"

    def _on_language_pack_failed(self, pack_id: str, message: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        self._set_download_failed_status(pack=pack, row=row, message=message)

    def _on_frequency_pack_failed(self, pack_id: str, message: str) -> None:
        pack = self._frequency_pack_info.get(pack_id)
        row = self._frequency_pack_rows.get(pack_id)
        if not pack or not row:
            return
        self._set_download_failed_status(pack=pack, row=row, message=message)

    def _on_embedding_pack_failed(self, pack_id: str, message: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        self._set_download_failed_status(pack=pack, row=row, message=message)

    def _cleanup_language_pack_thread(self, thread: LanguagePackDownloadThread) -> None:
        if thread in self._language_pack_threads:
            self._language_pack_threads.remove(thread)
        thread.deleteLater()

    def _cleanup_frequency_pack_thread(self, thread: FrequencyPackDownloadThread) -> None:
        if thread in self._frequency_pack_threads:
            self._frequency_pack_threads.remove(thread)
        thread.deleteLater()

    def _cleanup_embedding_conversion_thread(self, thread: EmbeddingConversionThread) -> None:
        if thread in self._embedding_conversion_threads:
            self._embedding_conversion_threads.remove(thread)
        thread.deleteLater()

    def _auto_link_downloaded_packs(self) -> None:
        for pack_id, pack in self._language_pack_info.items():
            if self._language_resource_binding(pack_id):
                continue
            candidate = self._resolve_downloaded_path(pack)
            if not candidate:
                continue
            valid, _message = self._validate_language_pack_path(pack, candidate)
            if valid:
                if self._is_pack_id_first_translation_pack(pack):
                    self._set_managed_language_pack_entry(pack_id, effective_path=candidate)
                else:
                    self._set_manual_language_pack_entry(pack_id, candidate)

    def _auto_link_downloaded_frequency_packs(self) -> None:
        for pack_id, pack in self._frequency_pack_info.items():
            if pack_id in self._frequency_pack_paths or pack_id in self._managed_frequency_pack_ids:
                continue
            candidate = self._resolve_frequency_pack_path(pack)
            if not candidate:
                continue
            valid, _message = self._validate_frequency_pack_path(pack, candidate)
            if valid:
                self._set_managed_frequency_pack_entry(pack_id)

    def _auto_link_downloaded_embeddings(self) -> None:
        for pack_id, pack in self._embedding_pack_info.items():
            if pack_id in self._embedding_pack_paths:
                continue
            candidate = self._resolve_downloaded_path(pack, embeddings=True)
            if candidate:
                if self._embedding_pack_pair_key(
                    pack_id
                ) and self._is_installed_embedding_pack_entry(pack_id, candidate):
                    continue
                self._embedding_pack_paths[pack_id] = candidate

    def _on_language_pack_completed(self, pack_id: str, dest_path: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        if pack.pack_id == "wordnet-en":
            dest_path = self._normalize_wordnet_path(dest_path)
        valid, message = self._validate_language_pack_path(pack, dest_path)
        if valid:
            if self._is_pack_id_first_translation_pack(pack):
                self._set_managed_language_pack_entry(pack_id, effective_path=dest_path)
            else:
                self._set_manual_language_pack_entry(pack_id, dest_path)
            row.status_item.setText(t("language_packs.status.installed"))
            self._set_status_item_tone(row.status_item, "success")
            row.status_item.setToolTip(dest_path)
            self._set_status_message(
                t("language_packs.installed_linked", name=pack.display_name(), path=dest_path),
                tone="success",
            )
        else:
            self._clear_language_pack_entry(pack_id)
            row.status_item.setText(t("language_packs.status.invalid"))
            self._set_status_item_tone(row.status_item, "error")
            row.status_item.setToolTip(dest_path)
            self._set_status_message(
                t("language_packs.installed_invalid", name=pack.display_name(), message=message),
                tone="error",
            )
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.redownload"))
        self._refresh_language_pack_table()

    def _on_frequency_pack_completed(self, pack_id: str, dest_path: str) -> None:
        pack = self._frequency_pack_info.get(pack_id)
        row = self._frequency_pack_rows.get(pack_id)
        if not pack or not row:
            return
        valid, message = self._validate_frequency_pack_path(pack, dest_path)
        if valid:
            self._set_managed_frequency_pack_entry(pack_id)
            row.status_item.setText(t("language_packs.status.installed"))
            self._set_status_item_tone(row.status_item, "success")
            row.status_item.setToolTip(dest_path)
            self._set_status_message(
                t("language_packs.installed_linked", name=pack.display_name(), path=dest_path),
                tone="success",
            )
        else:
            self._clear_frequency_pack_entry(pack_id)
            row.status_item.setText(t("language_packs.status.invalid"))
            self._set_status_item_tone(row.status_item, "error")
            row.status_item.setToolTip(dest_path)
            self._set_status_message(
                t("language_packs.installed_invalid", name=pack.display_name(), message=message),
                tone="error",
            )
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.redownload"))
        self._refresh_frequency_pack_table()

    def _on_embedding_pack_completed(self, pack_id: str, dest_path: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        if self._is_sqlite_db(dest_path):
            self._finalize_embedding_pack(pack_id=pack_id, resolved_path=dest_path)
            return
        optimized_path = self._embedding_pack_sqlite_path(pack)
        if self._is_sqlite_db(optimized_path):
            self._finalize_embedding_pack(pack_id=pack_id, resolved_path=optimized_path)
            return
        self._embedding_pack_paths[pack_id] = dest_path
        row.status_item.setText(t("language_packs.status.converting"))
        self._set_status_item_tone(row.status_item, "info")
        row.status_item.setToolTip(dest_path)
        row.download_button.setEnabled(False)
        row.use_button.setEnabled(False)
        self._set_status_message(
            t("language_packs.converting_for_optimized_use", name=pack.display_name()),
            tone="info",
        )
        thread = EmbeddingConversionThread(
            pack_id=pack_id,
            source_path=dest_path,
            output_path=optimized_path,
            parent=self,
        )
        thread.completed.connect(self._on_embedding_conversion_completed)
        thread.failed.connect(self._on_embedding_conversion_failed)
        thread.finished.connect(lambda: self._cleanup_embedding_conversion_thread(thread))
        self._embedding_conversion_threads.append(thread)
        thread.start()

    def _on_embedding_conversion_completed(self, pack_id: str, sqlite_path: str) -> None:
        self._finalize_embedding_pack(pack_id=pack_id, resolved_path=sqlite_path)

    def _on_embedding_conversion_failed(self, pack_id: str, message: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        self._embedding_pack_paths.pop(pack_id, None)
        row.status_item.setText(t("language_packs.status.failed"))
        self._set_status_item_tone(row.status_item, "error")
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.retry"))
        row.use_button.setEnabled(False)
        self._set_status_message(
            t(
                "language_packs.download_completed_but_conversion_failed",
                name=pack.display_name(),
                message=message,
            ),
            tone="error",
            tooltip=message,
        )
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()

    def _finalize_embedding_pack(self, *, pack_id: str, resolved_path: str) -> None:
        pack = self._embedding_pack_info.get(pack_id)
        row = self._embedding_row_for(pack_id)
        if not pack or not row:
            return
        prior_path = self._embedding_pack_paths.get(pack_id)
        if self._is_sqlite_db(resolved_path) and self._is_app_data_path(
            resolved_path, embeddings=True
        ):
            write_installed_pack_manifest(
                Path(self._embedding_pack_dir),
                pack_id=pack_id,
                pack_kind="embedding",
                provider=str(pack.source or "").strip().lower(),
                local_kind="file",
                build_mode="convert_to_sqlite",
                artifact_path=Path(resolved_path),
                source_filename=pack.filename,
                sqlite_filename=os.path.basename(resolved_path),
                raw_retained=False,
            )
            if (
                prior_path
                and prior_path != resolved_path
                and os.path.exists(prior_path)
                and self._is_app_data_path(prior_path, embeddings=True)
            ):
                self._remove_path(prior_path)
        if self._embedding_pack_pair_key(pack_id) and self._is_installed_embedding_pack_entry(
            pack_id, resolved_path
        ):
            self._embedding_pack_paths.pop(pack_id, None)
        else:
            self._embedding_pack_paths[pack_id] = resolved_path
        row.status_item.setText(t("language_packs.status.installed"))
        self._set_status_item_tone(row.status_item, "success")
        row.status_item.setToolTip(resolved_path)
        self._set_status_message(
            t("language_packs.installed_linked", name=pack.display_name(), path=resolved_path),
            tone="success",
        )
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.redownload"))
        row.use_button.setEnabled(True)
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()
