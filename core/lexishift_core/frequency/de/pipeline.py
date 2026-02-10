#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import ssl
import tarfile
import tempfile
from typing import Callable, Optional
import urllib.request

from lexishift_core.frequency.de.build import BuildResult, build_de_frequency_sqlite
from lexishift_core.frequency.de.pos_compile import write_compact_pos_lexicon

LEIPZIG_CORPUS_URL = "https://downloads.wortschatz-leipzig.de/corpora/deu_news_2023_1M.tar.gz"
FREEDICT_DE_EN_URL = (
    "https://download.freedict.org/dictionaries/deu-eng/1.9-fd1/"
    "freedict-deu-eng-1.9-fd1.src.tar.xz"
)
ODENET_URL = (
    "https://raw.githubusercontent.com/hdaSprachtechnologie/odenet/"
    "refs/heads/master/odenet_oneline.xml"
)
OPENTHESAURUS_URL = (
    "https://gitlab.htl-perg.ac.at/20180016/hue_junit/-/raw/master/Thesaurus/src/"
    "openthesaurus.txt?inline=false"
)
GERMAN_POS_EIG_URL = (
    "https://raw.githubusercontent.com/languagetool-org/german-pos-dict/"
    "master/src/main/resources/org/languagetool/resource/de/EIG.txt"
)
GERMAN_POS_SONSTIGE_URL = (
    "https://raw.githubusercontent.com/languagetool-org/german-pos-dict/"
    "master/src/main/resources/org/languagetool/resource/de/sonstige.txt"
)

ProgressCallback = Callable[[int, int], None]
CancelCallback = Callable[[], bool]


def default_data_root() -> Path:
    return Path.home() / "Library/Application Support/LexiShift/LexiShift"


def default_frequency_output() -> Path:
    return default_data_root() / "frequency_packs" / "freq-de-default.sqlite"


def default_language_packs_dir() -> Path:
    return default_data_root() / "language_packs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build freq-de-default.sqlite end-to-end by downloading Leipzig corpus + "
            "required DE lexicon resources and compiling POS hints."
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
        help="Language packs directory used for dictionary whitelist resources",
    )
    parser.add_argument(
        "--min-lemma-count",
        type=int,
        default=2,
        help="Drop aggregated lemmas below this count (default: 2)",
    )
    parser.add_argument(
        "--whitelist-min-count",
        type=int,
        default=20,
        help="Keep non-whitelist lemmas only if count >= this threshold (default: 20)",
    )
    parser.add_argument(
        "--disable-lexicon-whitelist",
        action="store_true",
        help="Disable whitelist filtering from FreeDict/OdeNet/OpenThesaurus",
    )
    parser.add_argument(
        "--disable-pos",
        action="store_true",
        help="Disable POS enrichment/filtering",
    )
    parser.add_argument(
        "--drop-proper-nouns",
        action="store_true",
        help="Drop proper nouns when POS enrichment is enabled",
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
    parser.add_argument(
        "--report-top",
        type=int,
        default=15,
        help="How many top lemmas to print",
    )
    return parser.parse_args()


def _should_retry_insecure(exc: Exception) -> bool:
    text = str(exc)
    return (
        isinstance(exc, FileNotFoundError)
        or "base_library.zip" in text
        or "CERTIFICATE_VERIFY_FAILED" in text
        or "SSL" in text
    )


def _open_request(request: urllib.request.Request, timeout: int) -> urllib.request.addinfourl:
    try:
        return urllib.request.urlopen(request, timeout=timeout)
    except Exception as exc:
        if _should_retry_insecure(exc):
            ctx = ssl._create_unverified_context()
            return urllib.request.urlopen(request, timeout=timeout, context=ctx)
        raise


def _emit_progress(callback: Optional[ProgressCallback], value: int, total: int = 100) -> None:
    if callback is None:
        return
    callback(max(0, min(value, total)), total)


def _check_cancel(cancel_cb: Optional[CancelCallback]) -> None:
    if cancel_cb and cancel_cb():
        raise RuntimeError("cancelled")


def _download_file(
    *,
    url: str,
    dest: Path,
    timeout: int = 45,
    progress: Optional[Callable[[int, int], None]] = None,
    cancel_cb: Optional[CancelCallback] = None,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "LexiShift/1.0"})
    with _open_request(request, timeout=timeout) as response:
        total = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        with dest.open("wb") as handle:
            while True:
                _check_cancel(cancel_cb)
                chunk = response.read(1024 * 128)
                if not chunk:
                    break
                handle.write(chunk)
                downloaded += len(chunk)
                if progress:
                    progress(downloaded, total)


def _extract_member_from_tar(
    *,
    archive_path: Path,
    member_suffix: str,
    output_path: Path,
) -> None:
    with tarfile.open(archive_path, "r:*") as archive:
        target_member = None
        for member in archive.getmembers():
            if member.isfile() and member.name.endswith(member_suffix):
                target_member = member
                break
        if target_member is None:
            raise FileNotFoundError(
                f"Could not find member ending with '{member_suffix}' in archive: {archive_path}"
            )
        extracted = archive.extractfile(target_member)
        if extracted is None:
            raise FileNotFoundError(f"Unable to read archive member: {target_member.name}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as handle:
            shutil.copyfileobj(extracted, handle)


def _ensure_plain_resource(
    *,
    target_path: Path,
    url: str,
    cancel_cb: Optional[CancelCallback] = None,
) -> Path:
    if target_path.exists() and target_path.is_file():
        return target_path
    _download_file(url=url, dest=target_path, cancel_cb=cancel_cb)
    return target_path


def _ensure_freedict_de_en(
    *,
    language_packs_dir: Path,
    workspace_dir: Path,
    cancel_cb: Optional[CancelCallback] = None,
) -> Path:
    target_path = language_packs_dir / "deu-eng.tei"
    if target_path.exists() and target_path.is_file():
        return target_path

    archive_path = workspace_dir / "freedict-deu-eng-1.9-fd1.src.tar.xz"
    _download_file(url=FREEDICT_DE_EN_URL, dest=archive_path, cancel_cb=cancel_cb)
    _extract_member_from_tar(
        archive_path=archive_path,
        member_suffix="/deu-eng.tei",
        output_path=target_path,
    )
    return target_path


def _combine_pos_sources(*, eig_path: Path, sonstige_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out:
        for source_path in (eig_path, sonstige_path):
            with source_path.open("r", encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    out.write(line)


def _stage_download_progress(
    *,
    base: int,
    span: int,
    callback: Optional[ProgressCallback],
) -> Callable[[int, int], None]:
    def _inner(downloaded: int, total: int) -> None:
        if total <= 0:
            return
        pct = base + int((downloaded / total) * span)
        _emit_progress(callback, pct, 100)

    return _inner


def run_de_frequency_pipeline(
    *,
    output_sqlite: Path,
    language_packs_dir: Path,
    overwrite: bool = True,
    min_lemma_count: int = 2,
    whitelist_min_count: int = 20,
    disable_lexicon_whitelist: bool = False,
    disable_pos: bool = False,
    drop_proper_nouns: bool = True,
    keep_temp: bool = False,
    progress_cb: Optional[ProgressCallback] = None,
    cancel_cb: Optional[CancelCallback] = None,
) -> BuildResult:
    output_sqlite = output_sqlite.expanduser().resolve()
    language_packs_dir = language_packs_dir.expanduser().resolve()
    frequency_packs_dir = output_sqlite.parent
    frequency_packs_dir.mkdir(parents=True, exist_ok=True)
    language_packs_dir.mkdir(parents=True, exist_ok=True)

    workspace = Path(tempfile.mkdtemp(prefix="freq-de-build-", dir=str(frequency_packs_dir)))
    try:
        _check_cancel(cancel_cb)
        _emit_progress(progress_cb, 1, 100)

        leipzig_archive = workspace / "deu_news_2023_1M.tar.gz"
        words_file = workspace / "deu_news_2023_1M-words.txt"
        _download_file(
            url=LEIPZIG_CORPUS_URL,
            dest=leipzig_archive,
            progress=_stage_download_progress(base=1, span=54, callback=progress_cb),
            cancel_cb=cancel_cb,
        )
        _check_cancel(cancel_cb)
        _emit_progress(progress_cb, 56, 100)
        _extract_member_from_tar(
            archive_path=leipzig_archive,
            member_suffix="-words.txt",
            output_path=words_file,
        )
        _check_cancel(cancel_cb)

        _ensure_plain_resource(
            target_path=language_packs_dir / "odenet_oneline.xml",
            url=ODENET_URL,
            cancel_cb=cancel_cb,
        )
        _ensure_plain_resource(
            target_path=language_packs_dir / "openthesaurus.txt",
            url=OPENTHESAURUS_URL,
            cancel_cb=cancel_cb,
        )
        _ensure_freedict_de_en(
            language_packs_dir=language_packs_dir,
            workspace_dir=workspace,
            cancel_cb=cancel_cb,
        )
        _check_cancel(cancel_cb)
        _emit_progress(progress_cb, 76, 100)

        pos_compact_path: Optional[Path] = None
        if not disable_pos:
            eig_path = workspace / "EIG.txt"
            sonstige_path = workspace / "sonstige.txt"
            merged_pos_path = workspace / "german_pos_merged.txt"
            pos_compact_path = workspace / "de-pos-compact.tsv"
            _download_file(url=GERMAN_POS_EIG_URL, dest=eig_path, cancel_cb=cancel_cb)
            _download_file(url=GERMAN_POS_SONSTIGE_URL, dest=sonstige_path, cancel_cb=cancel_cb)
            _combine_pos_sources(
                eig_path=eig_path,
                sonstige_path=sonstige_path,
                output_path=merged_pos_path,
            )
            write_compact_pos_lexicon(
                input_path=merged_pos_path,
                output_path=pos_compact_path,
                overwrite=True,
            )
            _check_cancel(cancel_cb)
        _emit_progress(progress_cb, 88, 100)

        result = build_de_frequency_sqlite(
            input_path=words_file,
            output_path=output_sqlite,
            language_packs_dir=language_packs_dir,
            min_lemma_count=max(1, int(min_lemma_count)),
            whitelist_min_count=max(1, int(whitelist_min_count)),
            disable_lexicon_whitelist=bool(disable_lexicon_whitelist),
            pos_lexicon_path=pos_compact_path,
            pos_format="generic_compact" if pos_compact_path else "auto",
            drop_proper_nouns=bool(drop_proper_nouns and pos_compact_path is not None),
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
    result = run_de_frequency_pipeline(
        output_sqlite=args.output,
        language_packs_dir=args.language_packs_dir,
        overwrite=bool(args.overwrite),
        min_lemma_count=max(1, int(args.min_lemma_count)),
        whitelist_min_count=max(1, int(args.whitelist_min_count)),
        disable_lexicon_whitelist=bool(args.disable_lexicon_whitelist),
        disable_pos=bool(args.disable_pos),
        drop_proper_nouns=bool(args.drop_proper_nouns),
        keep_temp=bool(args.keep_temp),
    )

    print(f"Built: {result.output_path}")
    print(
        "Parse stats:"
        f" input_rows={result.stats.input_rows:,}, malformed_rows={result.stats.malformed_rows:,},"
        f" dropped_non_numeric={result.stats.dropped_non_numeric:,},"
        f" dropped_non_positive={result.stats.dropped_non_positive:,},"
        f" dropped_invalid_surface={result.stats.dropped_invalid_surface:,},"
        f" kept_rows={result.stats.kept_rows:,}"
    )
    print(
        "Lexicon stats:"
        f" freedict_headwords={result.lexicon_stats.freedict_headwords:,},"
        f" odenet_lemmas={result.lexicon_stats.odenet_lemmas:,},"
        f" openthesaurus_lemmas={result.lexicon_stats.openthesaurus_lemmas:,},"
        f" whitelist_lemmas={result.lexicon_stats.whitelist_lemmas:,},"
        f" whitelist_enabled={result.filter_config.whitelist_enabled}"
    )
    if result.requested_whitelist_enabled and not result.filter_config.whitelist_enabled:
        print("Note: whitelist filtering was requested but no whitelist lemmas were available; disabled.")
    print(
        "Filter stats:"
        f" dropped_min_lemma_count={result.stats.dropped_min_lemma_count:,},"
        f" dropped_not_in_whitelist={result.stats.dropped_not_in_whitelist:,},"
        f" dropped_proper_noun={result.stats.dropped_proper_noun:,},"
        f" kept_lemmas={result.stats.kept_lemmas:,}"
    )
    print(
        "Shape:"
        f" unique_surfaces={result.stats.unique_surfaces:,},"
        f" unique_lemmas_pre_filter={result.stats.unique_lemmas:,},"
        f" total_tokens_pre_filter={result.stats.total_tokens_pre_filter:,},"
        f" db_rows={result.row_count:,},"
        f" total_tokens_post_filter={result.stats.total_tokens_post_filter:,},"
        f" total_pmw={result.total_pmw:.2f}"
    )
    print(
        "Paths:"
        f" language_packs_dir={result.language_packs_dir},"
        f" freedict_de_en_path={result.discovered_paths['freedict_de_en_path']},"
        f" odenet_path={result.discovered_paths['odenet_path']},"
        f" openthesaurus_path={result.discovered_paths['openthesaurus_path']},"
        f" pos_lexicon_path={str(result.pos_lexicon_path) if result.pos_lexicon_path else None}"
    )
    report_top = max(0, int(args.report_top))
    print(f"Top {report_top} lemmas:")
    for lemma, count in result.ranked[:report_top]:
        print(f"  {lemma}\t{count}")


if __name__ == "__main__":
    main()
