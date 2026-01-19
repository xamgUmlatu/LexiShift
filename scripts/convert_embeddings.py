import argparse
import math
import os
import sqlite3
import sys
import time
from array import array
from pathlib import Path

CORE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core"))
if CORE_ROOT not in sys.path:
    sys.path.insert(0, CORE_ROOT)

from lexishift_core.synonyms import _read_binary_vector, _read_binary_word


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert embeddings to SQLite for fast lookup.")
    parser.add_argument("--input", required=True, help="Path to .vec/.txt/.bin embeddings file.")
    parser.add_argument("--output", required=True, help="Path to output .db/.sqlite file.")
    parser.add_argument("--lowercase-words", action="store_true", help="Store words lowercased.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if it exists.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of rows (debug).")
    parser.add_argument("--batch", type=int, default=5000, help="Batch size for inserts.")
    parser.add_argument("--progress", type=int, default=50000, help="Progress print interval.")
    return parser.parse_args()


def _init_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS vectors ("
        "word TEXT PRIMARY KEY, "
        "word_lc TEXT NOT NULL, "
        "dim INTEGER NOT NULL, "
        "norm REAL NOT NULL, "
        "vector BLOB NOT NULL"
        ")"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vectors_word_lc ON vectors(word_lc)")
    return conn


def _is_header(parts: list[str]) -> bool:
    if len(parts) != 2:
        return False
    return parts[0].isdigit() and parts[1].isdigit()


def _pack_vector(values: list[float]) -> bytes:
    arr = array("f", values)
    return arr.tobytes()


def _insert_batch(conn: sqlite3.Connection, batch: list[tuple]) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO vectors (word, word_lc, dim, norm, vector) VALUES (?, ?, ?, ?, ?)",
        batch,
    )


def _convert_text(
    conn: sqlite3.Connection,
    path: Path,
    *,
    lowercase_words: bool,
    limit: int,
    batch_size: int,
    progress_every: int,
) -> None:
    dim = None
    batch = []
    count = 0
    start = time.time()
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        first = handle.readline()
        if not first:
            return
        parts = first.strip().split()
        if _is_header(parts):
            dim = int(parts[1])
        else:
            dim = len(parts) - 1
            _process_vector_line(
                conn,
                parts,
                dim,
                batch,
                lowercase_words=lowercase_words,
            )
            count += 1
        for line in handle:
            parts = line.strip().split()
            if not parts:
                continue
            if dim is None:
                dim = len(parts) - 1
            if len(parts) != dim + 1:
                continue
            _process_vector_line(
                conn,
                parts,
                dim,
                batch,
                lowercase_words=lowercase_words,
            )
            count += 1
            if limit and count >= limit:
                break
            if len(batch) >= batch_size:
                _insert_batch(conn, batch)
                conn.commit()
                batch.clear()
            if progress_every and count % progress_every == 0:
                elapsed = time.time() - start
                print(f"Processed {count} rows in {elapsed:.1f}s")
    if batch:
        _insert_batch(conn, batch)
        conn.commit()
        batch.clear()
    if dim is not None:
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", ("dim", str(dim)))
        conn.commit()


def _process_vector_line(
    conn: sqlite3.Connection,
    parts: list[str],
    dim: int,
    batch: list[tuple],
    *,
    lowercase_words: bool,
) -> None:
    word = parts[0]
    if lowercase_words:
        word = word.lower()
    word_lc = word.lower()
    try:
        values = [float(value) for value in parts[1:]]
    except ValueError:
        return
    if len(values) != dim:
        return
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 0.0:
        return
    blob = _pack_vector(values)
    batch.append((word, word_lc, dim, norm, blob))


def _convert_binary(
    conn: sqlite3.Connection,
    path: Path,
    *,
    lowercase_words: bool,
    limit: int,
    batch_size: int,
    progress_every: int,
) -> None:
    batch = []
    count = 0
    start = time.time()
    with path.open("rb") as handle:
        header = handle.readline()
        if not header:
            return
        parts = header.split()
        if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
            return
        vocab_size = int(parts[0])
        dim = int(parts[1])
        for _ in range(vocab_size):
            word = _read_binary_word(handle)
            if not word:
                break
            vector = _read_binary_vector(handle, dim)
            if vector is None:
                break
            if lowercase_words:
                word = word.lower()
            word_lc = word.lower()
            norm = math.sqrt(sum(value * value for value in vector))
            if norm <= 0.0:
                continue
            blob = _pack_vector(vector)
            batch.append((word, word_lc, dim, norm, blob))
            count += 1
            if limit and count >= limit:
                break
            if len(batch) >= batch_size:
                _insert_batch(conn, batch)
                conn.commit()
                batch.clear()
            if progress_every and count % progress_every == 0:
                elapsed = time.time() - start
                print(f"Processed {count} rows in {elapsed:.1f}s")
    if batch:
        _insert_batch(conn, batch)
        conn.commit()
        batch.clear()
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", ("dim", str(dim)))
    conn.commit()


def main() -> int:
    args = _parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 1
    if output_path.exists() and not args.overwrite:
        print(f"Output already exists: {output_path}")
        print("Re-run with --overwrite to replace it.")
        return 1
    if output_path.exists() and args.overwrite:
        output_path.unlink()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    conn = _init_db(output_path)
    if input_path.suffix.lower() == ".bin":
        _convert_binary(
            conn,
            input_path,
            lowercase_words=args.lowercase_words,
            limit=args.limit,
            batch_size=args.batch,
            progress_every=args.progress,
        )
    else:
        _convert_text(
            conn,
            input_path,
            lowercase_words=args.lowercase_words,
            limit=args.limit,
            batch_size=args.batch,
            progress_every=args.progress,
        )
    conn.close()
    print(f"Saved SQLite embeddings: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
