from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Mapping, Sequence

from semantic_veto_difficulty_stratification_common import _optional_float, _round4
from semantic_veto_product_quality_en_es import _repo_path


@dataclass(frozen=True)
class FrequencyRecord:
    lemma: str
    rank: float | None
    frequency: float | None


@dataclass(frozen=True)
class FrequencyMatch:
    input_lemma: str
    matched_lemma: str
    rank: float | None
    frequency: float | None
    match_kind: str


@dataclass(frozen=True)
class FrequencyLookup:
    language: str
    path: Path | None
    records_by_key: Mapping[str, FrequencyRecord]
    status: str = "ok"
    issue: str = ""
    lemma_column: str = ""
    rank_column: str = ""
    frequency_column: str = ""

    @classmethod
    def from_records(
        cls,
        *,
        language: str,
        rows: Mapping[str, Mapping[str, object]],
        path: Path | None = None,
    ) -> "FrequencyLookup":
        records: dict[str, FrequencyRecord] = {}
        for lemma, row in rows.items():
            normalized = _normalize_lemma_key(lemma)
            if not normalized:
                continue
            records[normalized] = FrequencyRecord(
                lemma=str(lemma),
                rank=_optional_float(row.get("rank")),
                frequency=_optional_float(row.get("frequency") or row.get("freq")),
            )
        return cls(language=language, path=path, records_by_key=records)

    @classmethod
    def from_sqlite(cls, *, path: Path, language: str) -> "FrequencyLookup":
        candidate = Path(path)
        if not candidate.exists():
            return cls(
                language=language,
                path=candidate,
                records_by_key={},
                status="missing",
                issue="frequency_db_missing",
            )
        try:
            with sqlite3.connect(candidate) as conn:
                columns = _sqlite_columns(conn, "frequency")
                lemma_column = _resolve_column(columns, ("lemma", "word", "surface", "form"))
                rank_column = _resolve_column(
                    columns,
                    ("core_rank", "rank", "row_rank", "id", "index"),
                )
                frequency_column = _resolve_column(
                    columns,
                    (
                        "pmw",
                        "core_pmw",
                        "frequency",
                        "core_frequency",
                        "freq",
                        "freq_per_million",
                        "count",
                        "ipm",
                    ),
                )
                if not lemma_column:
                    return cls(
                        language=language,
                        path=candidate,
                        records_by_key={},
                        status="review",
                        issue="frequency_db_missing_lemma_column",
                    )
                select_columns = [_quote_identifier(lemma_column)]
                if rank_column:
                    select_columns.append(_quote_identifier(rank_column))
                if frequency_column:
                    select_columns.append(_quote_identifier(frequency_column))
                query = f"SELECT {', '.join(select_columns)} FROM frequency;"
                records = {}
                for row in conn.execute(query):
                    lemma = str(row[0] or "").strip()
                    if not lemma:
                        continue
                    rank = _optional_float(row[1]) if rank_column and len(row) > 1 else None
                    frequency_index = 2 if rank_column else 1
                    frequency = (
                        _optional_float(row[frequency_index])
                        if frequency_column and len(row) > frequency_index
                        else None
                    )
                    _merge_frequency_record(
                        records,
                        FrequencyRecord(lemma=lemma, rank=rank, frequency=frequency),
                    )
                return cls(
                    language=language,
                    path=candidate,
                    records_by_key=records,
                    lemma_column=lemma_column,
                    rank_column=rank_column or "",
                    frequency_column=frequency_column or "",
                )
        except sqlite3.Error as exc:
            return cls(
                language=language,
                path=candidate,
                records_by_key={},
                status="review",
                issue=f"frequency_db_read_failed:{exc}",
            )

    def lookup(self, lemma: object) -> FrequencyMatch:
        text = str(lemma or "").strip()
        if not text:
            return FrequencyMatch("", "", None, None, "missing_input")
        candidates = [(text, "exact")]
        if self.language == "es":
            candidates.extend(
                (value, "spanish_plural_fallback") for value in _spanish_fallbacks(text)
            )
        for candidate, match_kind in candidates:
            record = self.records_by_key.get(_normalize_lemma_key(candidate))
            if record is not None:
                return FrequencyMatch(
                    input_lemma=text,
                    matched_lemma=record.lemma,
                    rank=record.rank,
                    frequency=record.frequency,
                    match_kind=match_kind,
                )
        return FrequencyMatch(text, "", None, None, "missing")


def _source_zipf_status(source_zipf_by_trigger: Mapping[str, float] | None) -> str:
    if source_zipf_by_trigger is not None:
        return "injected"
    try:
        from wordfreq import zipf_frequency as _zipf_frequency  # noqa: F401
    except ImportError:
        return "wordfreq_package_unavailable"
    return "wordfreq"


def _source_zipf_frequency(
    *,
    trigger: str,
    source_zipf_by_trigger: Mapping[str, float] | None,
    source_zipf_status: str,
) -> float | None:
    normalized = _normalize_lemma_key(trigger)
    if not normalized:
        return None
    if source_zipf_by_trigger is not None:
        raw = source_zipf_by_trigger.get(trigger)
        if raw is None:
            raw = source_zipf_by_trigger.get(normalized)
        value = _optional_float(raw)
        return _round4(value) if value and value > 0 else None
    if source_zipf_status != "wordfreq":
        return None
    from wordfreq import zipf_frequency

    value = _optional_float(zipf_frequency(trigger, "en"))
    return _round4(value) if value and value > 0 else None


def _source_zipf_match_kind(*, source_zipf: float | None, source_zipf_status: str) -> str:
    if source_zipf is None:
        return "missing"
    return source_zipf_status


def _source_zipf_band(zipf: object) -> str:
    value = _optional_float(zipf)
    if value is None or value <= 0:
        return "missing"
    if value >= 5.0:
        return "zipf_5_plus_very_common"
    if value >= 4.0:
        return "zipf_4_to_5_common"
    if value >= 3.0:
        return "zipf_3_to_4_mid"
    return "zipf_below_3_rare"


def _sqlite_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({_quote_identifier(table)});").fetchall()
    return [str(row[1]) for row in rows if len(row) > 1]


def _resolve_column(columns: Sequence[str], candidates: Sequence[str]) -> str:
    lowered = {column.lower(): column for column in columns}
    for candidate in candidates:
        resolved = lowered.get(candidate.lower())
        if resolved:
            return resolved
    return ""


def _quote_identifier(value: str) -> str:
    return '"' + str(value).replace('"', '""') + '"'


def _merge_frequency_record(
    records: dict[str, FrequencyRecord],
    record: FrequencyRecord,
) -> None:
    key = _normalize_lemma_key(record.lemma)
    current = records.get(key)
    if current is None:
        records[key] = record
        return
    current_rank = current.rank if current.rank is not None else 999999999.0
    incoming_rank = record.rank if record.rank is not None else 999999999.0
    current_freq = current.frequency if current.frequency is not None else -1.0
    incoming_freq = record.frequency if record.frequency is not None else -1.0
    if incoming_rank < current_rank or (
        incoming_rank == current_rank and incoming_freq > current_freq
    ):
        records[key] = record


def _spanish_fallbacks(lemma: str) -> list[str]:
    text = str(lemma or "").strip()
    fallbacks = []
    if len(text) > 4 and text.endswith("ces"):
        fallbacks.append(text[:-3] + "z")
    if len(text) > 4 and text.endswith("es"):
        fallbacks.append(text[:-2])
    if len(text) > 3 and text.endswith("s"):
        fallbacks.append(text[:-1])
    return [item for item in fallbacks if item and item != text]


def _frequency_public(lookup: FrequencyLookup) -> dict[str, object]:
    return {
        "language": lookup.language,
        "path": _repo_path(lookup.path),
        "status": lookup.status,
        "issue": lookup.issue,
        "record_count": len(lookup.records_by_key),
        "lemma_column": lookup.lemma_column,
        "rank_column": lookup.rank_column,
        "frequency_column": lookup.frequency_column,
    }


def _normalize_lemma_key(value: object) -> str:
    return str(value or "").strip().casefold()
