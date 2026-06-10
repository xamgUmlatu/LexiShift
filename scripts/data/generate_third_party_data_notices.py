#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps" / "gui" / "src"))
sys.path.insert(0, str(REPO_ROOT / "core"))

from i18n import set_locale  # noqa: E402
from language_packs_catalog import build_pack_catalogs  # noqa: E402


DEFAULT_OUTPUT = REPO_ROOT / "docs" / "language_pairs" / "THIRD_PARTY_DATA_NOTICES.md"


def _cell(value: object) -> str:
    text = str(value or "Not recorded")
    text = text.replace("\n", "<br>")
    return text.replace("|", "\\|")


def _source_urls(pack) -> str:
    urls = [str(getattr(pack, "url", "") or "").strip()]
    urls.extend(str(url).strip() for url in getattr(pack, "source_urls", ()) or ())
    result: list[str] = []
    for url in urls:
        if url and url not in result:
            result.append(url)
    return "<br>".join(result)


def _notes(pack) -> str:
    notes = tuple(str(note) for note in getattr(pack, "license_notes", ()) or () if str(note))
    return "<br>".join(notes)


def _pack_row(pack) -> str:
    return (
        "| "
        + " | ".join(
            (
                _cell(getattr(pack, "pack_id", "")),
                _cell(pack.display_name()),
                _cell(pack.display_source()),
                _cell(getattr(pack, "license_name", "")),
                _cell(getattr(pack, "distribution_mode", "")),
                _cell(getattr(pack, "license_status", "")),
                _cell(_source_urls(pack)),
                _cell(getattr(pack, "license_url", "")),
                _cell(_notes(pack)),
            )
        )
        + " |"
    )


def _section(title: str, packs: tuple[object, ...]) -> list[str]:
    lines = [f"## {title}", ""]
    lines.extend(
        (
            "| Pack ID | Name | Source | License | Distribution mode | Status | Source URL | License URL | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        )
    )
    lines.extend(_pack_row(pack) for pack in sorted(packs, key=lambda item: item.pack_id))
    lines.append("")
    return lines


def render_notices(*, as_of: str | None = None) -> str:
    set_locale("en")
    catalogs = build_pack_catalogs(source_overrides={})
    lines = [
        "# Third-Party Data Notices",
        "",
        f"Generated: {as_of or date.today().isoformat()}",
        "",
        "This notice lists the source and license metadata recorded in the LexiShift resource catalog.",
        "It is not legal advice, and it does not by itself approve bundled or hosted redistribution of converted artifacts.",
        "",
    ]
    lines.extend(_section("Language Packs", catalogs.language_packs))
    lines.extend(_section("Frequency Packs", catalogs.frequency_packs))
    lines.extend(_section("POS Overlay Packs", catalogs.pos_overlay_packs))
    lines.extend(_section("Semantic Packs", catalogs.semantic_packs))
    lines.extend(_section("Embedding Packs", catalogs.embedding_packs))
    lines.extend(_section("Cross-Lingual Embedding Packs", catalogs.cross_embedding_packs))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Markdown output path.")
    parser.add_argument(
        "--as-of", default=None, help="Override generated date for reproducible docs."
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_notices(as_of=args.as_of), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
