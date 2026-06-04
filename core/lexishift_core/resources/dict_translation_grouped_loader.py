from __future__ import annotations

import sqlite3
from typing import Sequence

from lexishift_core.resources.dict_sqlite_support import (
    load_auxiliary_sqlite_gloss_records_by_translation_ordered,
)
from lexishift_core.resources.dict_loaders import TranslationGlossRecord


def load_sqlite_gloss_records_by_translation_ordered(
    conn: sqlite3.Connection,
    *,
    translations: Sequence[str] | None = None,
) -> dict[str, list[TranslationGlossRecord]]:
    from lexishift_core.resources.dict_loaders import (
        FreedictGlossRecord,
    )
    from lexishift_core.resources.dict_gloss_metadata import build_auxiliary_gloss_metadata

    return load_auxiliary_sqlite_gloss_records_by_translation_ordered(
        conn,
        translations=translations,
        record_factory=FreedictGlossRecord,
        metadata_builder=build_auxiliary_gloss_metadata,
    )
