#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import tempfile
from typing import Callable, Mapping, Optional

from lexishift_core.frequency.de.build import BuildResult, build_de_frequency_sqlite
from lexishift_core.frequency.de.pipeline import (
    _check_cancel,
    _download_file,
    _emit_progress,
    _extract_member_from_tar,
    _stage_download_progress,
)

LEIPZIG_EN_CORPUS_URL = "https://downloads.wortschatz-leipzig.de/corpora/eng_news_2025_1M.tar.gz"

ProgressCallback = Callable[[int, int], None]
CancelCallback = Callable[[], bool]
SourceBundleComponentPathsCallback = Callable[[Mapping[str, Path]], None]


def default_data_root() -> Path:
    return Path.home() / "Library/Application Support/LexiShift/LexiShift"


def default_frequency_output() -> Path:
    return default_data_root() / "frequency_packs" / "freq-en-leipzig-default" / "main.sqlite"


def default_language_packs_dir() -> Path:
    return default_data_root() / "language_packs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the managed freq-en-leipzig-default SQLite artifact end-to-end by "
            "downloading the Leipzig English news corpus and compiling lemma frequency ranks."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_frequency_output(),
        help="Output frequency SQLite path",
    )
    parser.add_argument(
        "--language-packs-dir",
        type=Path,
        default=default_language_packs_dir(),
        help="Language packs directory retained for builder interface parity",
    )
    parser.add_argument(
        "--corpus-url",
        default=LEIPZIG_EN_CORPUS_URL,
        help="Leipzig English corpus archive URL",
    )
    parser.add_argument(
        "--min-lemma-count",
        type=int,
        default=2,
        help="Drop aggregated lemmas below this count (default: 2)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output DB if it already exists",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary download/build files for debugging",
    )
    return parser.parse_args()


def _component_paths(*, archive_path: Path, words_file: Path) -> dict[str, Path]:
    return {
        archive_path.name: archive_path,
        words_file.name: words_file,
    }


def run_en_frequency_pipeline(
    *,
    output_sqlite: Path,
    language_packs_dir: Path,
    overwrite: bool = True,
    corpus_url: str = LEIPZIG_EN_CORPUS_URL,
    min_lemma_count: int = 2,
    keep_temp: bool = False,
    progress_cb: Optional[ProgressCallback] = None,
    cancel_cb: Optional[CancelCallback] = None,
    source_bundle_component_paths_cb: Optional[SourceBundleComponentPathsCallback] = None,
) -> BuildResult:
    output_sqlite = output_sqlite.expanduser().resolve()
    language_packs_dir = language_packs_dir.expanduser().resolve()
    frequency_packs_dir = output_sqlite.parent
    frequency_packs_dir.mkdir(parents=True, exist_ok=True)
    language_packs_dir.mkdir(parents=True, exist_ok=True)

    archive_name = Path(str(corpus_url or LEIPZIG_EN_CORPUS_URL)).name or "eng_news_1M.tar.gz"
    words_name = archive_name.removesuffix(".tar.gz") + "-words.txt"
    workspace = Path(tempfile.mkdtemp(prefix="freq-en-build-", dir=str(frequency_packs_dir)))
    try:
        _check_cancel(cancel_cb)
        _emit_progress(progress_cb, 1, 100)

        leipzig_archive = workspace / archive_name
        words_file = workspace / words_name
        _download_file(
            url=str(corpus_url or LEIPZIG_EN_CORPUS_URL),
            dest=leipzig_archive,
            progress=_stage_download_progress(base=1, span=70, callback=progress_cb),
            cancel_cb=cancel_cb,
        )
        _check_cancel(cancel_cb)
        _emit_progress(progress_cb, 74, 100)
        _extract_member_from_tar(
            archive_path=leipzig_archive,
            member_suffix="-words.txt",
            output_path=words_file,
        )
        _check_cancel(cancel_cb)

        if source_bundle_component_paths_cb is not None:
            source_bundle_component_paths_cb(
                _component_paths(archive_path=leipzig_archive, words_file=words_file)
            )
        _emit_progress(progress_cb, 86, 100)

        result = build_de_frequency_sqlite(
            input_path=words_file,
            output_path=output_sqlite,
            lang="en",
            min_lemma_count=max(1, int(min_lemma_count)),
            disable_lexicon_whitelist=True,
            no_lemmatize=False,
            overwrite=bool(overwrite),
        )
        _emit_progress(progress_cb, 99, 100)
        return result
    finally:
        if not keep_temp and workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)
        _emit_progress(progress_cb, 100, 100)


def main() -> None:
    args = parse_args()
    result = run_en_frequency_pipeline(
        output_sqlite=args.output,
        language_packs_dir=args.language_packs_dir,
        overwrite=bool(args.overwrite),
        corpus_url=str(args.corpus_url or LEIPZIG_EN_CORPUS_URL),
        min_lemma_count=max(1, int(args.min_lemma_count)),
        keep_temp=bool(args.keep_temp),
    )
    print(f"Built: {result.output_path}")
    print(f"Rows: {result.row_count:,}")
    print(f"Unique lemmas: {result.stats.unique_lemmas:,}")
    print(f"Kept lemmas: {result.stats.kept_lemmas:,}")


if __name__ == "__main__":
    main()
