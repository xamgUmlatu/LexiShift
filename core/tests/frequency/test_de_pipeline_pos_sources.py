from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.frequency.de.pipeline import (  # noqa: E402
    DE_POS_SOURCE_AUTO,
    DE_POS_SOURCE_EIG_SONSTIGE,
    DE_POS_SOURCE_GERMAN_DICT,
    _convert_morfologik_decompiled_to_tsv,
    _normalize_de_pos_source,
    _resolve_de_pos_source_order,
)


class TestDePipelinePosSources(unittest.TestCase):
    def test_normalize_de_pos_source_aliases(self) -> None:
        self.assertEqual(_normalize_de_pos_source("auto"), DE_POS_SOURCE_AUTO)
        self.assertEqual(_normalize_de_pos_source(""), DE_POS_SOURCE_AUTO)
        self.assertEqual(_normalize_de_pos_source("GERMAN-DICT"), DE_POS_SOURCE_GERMAN_DICT)
        self.assertEqual(_normalize_de_pos_source("dict"), DE_POS_SOURCE_GERMAN_DICT)
        self.assertEqual(_normalize_de_pos_source("legacy"), DE_POS_SOURCE_EIG_SONSTIGE)
        self.assertEqual(_normalize_de_pos_source("eig_sonstige"), DE_POS_SOURCE_EIG_SONSTIGE)
        with self.assertRaises(ValueError):
            _normalize_de_pos_source("unknown")

    def test_resolve_de_pos_source_order(self) -> None:
        self.assertEqual(
            _resolve_de_pos_source_order(DE_POS_SOURCE_AUTO),
            [DE_POS_SOURCE_GERMAN_DICT, DE_POS_SOURCE_EIG_SONSTIGE],
        )
        self.assertEqual(
            _resolve_de_pos_source_order(DE_POS_SOURCE_GERMAN_DICT),
            [DE_POS_SOURCE_GERMAN_DICT],
        )
        self.assertEqual(
            _resolve_de_pos_source_order(DE_POS_SOURCE_EIG_SONSTIGE),
            [DE_POS_SOURCE_EIG_SONSTIGE],
        )

    def test_convert_morfologik_decompiled_to_tsv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "decompiled.txt"
            output_path = Path(tmp) / "decompiled.tsv"
            input_path.write_text(
                "\n".join(
                    (
                        "bleichen_#bleich_VER:1:SIN:PRÄ:NON -- inline comment",
                        "Hehl_-_SUB:DAT:SIN:MAS",
                        "foo_bar_baz_SUB:NOM:SIN:NEU",
                        "malformed",
                        "",
                    )
                ),
                encoding="utf-8",
            )

            rows = _convert_morfologik_decompiled_to_tsv(
                input_path=input_path,
                output_path=output_path,
            )

            self.assertEqual(rows, 3)
            lines = output_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "bleichen\t#bleich\tVER:1:SIN:PRÄ:NON")
            self.assertEqual(lines[1], "Hehl\t-\tSUB:DAT:SIN:MAS")
            self.assertEqual(lines[2], "foo_bar\tbaz\tSUB:NOM:SIN:NEU")

    def test_convert_morfologik_raises_when_no_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "empty.txt"
            output_path = Path(tmp) / "out.tsv"
            input_path.write_text("not_valid\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                _convert_morfologik_decompiled_to_tsv(
                    input_path=input_path,
                    output_path=output_path,
                )


if __name__ == "__main__":
    unittest.main()
