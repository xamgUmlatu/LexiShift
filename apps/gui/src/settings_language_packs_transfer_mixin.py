from __future__ import annotations

from i18n import t
from language_packs import (
    FrequencyPackDownloadThread,
    LanguagePackDownloadThread,
    download_log_path,
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
        if message == "cancelled" and self._closing:
            row.status_item.setText(t("language_packs.status.cancelled"))
            self._set_status_item_tone(row.status_item, "muted")
            row.download_button.setEnabled(True)
            row.download_button.setText(t("buttons.download"))
            return
        row.status_item.setText(t("language_packs.status.failed"))
        self._set_status_item_tone(row.status_item, "error")
        row.download_button.setEnabled(True)
        row.download_button.setText(t("buttons.retry"))
        link = pack.wayback_url
        log_path = download_log_path()
        row.status_item.setToolTip(log_path)
        self._set_status_message(
            t("language_packs.download_failed", name=pack.display_name(), error=message, link=link),
            tone="error",
            tooltip=log_path,
        )

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
