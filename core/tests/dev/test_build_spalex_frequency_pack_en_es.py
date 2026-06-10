from __future__ import annotations

import csv
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_DATA_ROOT = REPO_ROOT / "scripts" / "data"
for candidate in (CORE_ROOT, SCRIPTS_DATA_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from build_spalex_frequency_pack_en_es import build_spalex_frequency_pack  # noqa: E402
from lexishift_core.helper.installed_packs import load_installed_pack_manifest  # noqa: E402
from lexishift_core.helper.pack_provenance import validate_pack_provenance_file  # noqa: E402


class BuildSpalexFrequencyPackTests(unittest.TestCase):
    def test_builds_cde_seed_plus_spalex_additions_with_compact_pos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current_db = root / "freq-es-cde.sqlite"
            spalex_csv = root / "word_info.csv"
            kaikki_db = root / "wiktionary-es-en.sqlite"
            output = root / "freq-es-spalex-expanded-v1" / "main.sqlite"
            _write_current_frequency_db(
                current_db,
                [("el", 1, 1000.0, "l"), ("de", 2, 900.0, "e"), ("casa", 3, 800.0, "n")],
            )
            _write_spalex_csv(
                spalex_csv,
                [
                    ("que", 7.4, 2.1, 28628.0, 98.8),
                    ("casa", 6.0, 1.8, 1000.0, 99.0),
                    ("medicina", 4.5, 1.1, 22.0, 88.0),
                ],
            )
            _write_kaikki_forward_db(
                kaikki_db,
                {
                    "que": ("conj", []),
                    "medicina": ("noun", ["medicine", "sciences"]),
                },
            )

            metadata = build_spalex_frequency_pack(
                spalex_csv=spalex_csv,
                current_frequency_db=current_db,
                kaikki_forward_db=kaikki_db,
                output_sqlite=output,
                pack_id="freq-es-spalex-expanded-v1",
                provider="freq-es-spalex-expanded-v1",
                source_mode="spalex_cde_union",
                overwrite=True,
                write_sidecars=True,
            )

            self.assertEqual(metadata["metrics"]["row_count"], 5)
            self.assertEqual(metadata["source_mode"], "spalex_cde_union")
            self.assertTrue(metadata["sidecars_written"])
            with sqlite3.connect(output) as conn:
                rows = conn.execute(
                    "SELECT id, pmw, freq, lemma, pos, source_family, topics "
                    "FROM frequency ORDER BY id"
                ).fetchall()
                meta = json.loads(
                    conn.execute("SELECT value FROM meta WHERE key='metadata'").fetchone()[0]
                )
            self.assertEqual([row[3] for row in rows], ["el", "de", "casa", "que", "medicina"])
            self.assertEqual([row[4] for row in rows], ["l", "e", "n", "c", "n"])
            self.assertEqual(rows[0][1], 5.0)
            self.assertEqual(rows[-1][1], 1.0)
            self.assertEqual(rows[4][6], "medicine,sciences")
            self.assertEqual(
                meta["frequency_column_semantics"]["pmw"], "rank_descending_commonness_score"
            )
            self.assertEqual(
                meta["frequency_column_semantics"]["freq"], "original_source_frequency"
            )
            self.assertEqual(metadata["source_counts"]["spalex_added"], 2)
            self.assertEqual(metadata["source_counts"]["cde_included"], 3)

            manifest = load_installed_pack_manifest(root, "freq-es-spalex-expanded-v1")
            self.assertIsNotNone(manifest)
            self.assertEqual(manifest.artifact_relpath, "main.sqlite")
            provenance_errors = validate_pack_provenance_file(output.parent / "provenance.json")
            self.assertEqual(provenance_errors, ())

    def test_target_size_caps_after_seed_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current_db = root / "freq-es-cde.sqlite"
            spalex_csv = root / "word_info.csv"
            output = root / "main.sqlite"
            _write_current_frequency_db(current_db, [("el", 1, 1000.0, "l")])
            _write_spalex_csv(
                spalex_csv,
                [
                    ("que", 7.4, 2.1, 100.0, 98.8),
                    ("casa", 6.0, 1.8, 90.0, 99.0),
                    ("medicina", 4.5, 1.1, 22.0, 88.0),
                ],
            )

            metadata = build_spalex_frequency_pack(
                spalex_csv=spalex_csv,
                current_frequency_db=current_db,
                output_sqlite=output,
                pack_id="freq-es-spalex-expanded-v1",
                provider="freq-es-spalex-expanded-v1",
                source_mode="spalex_cde_union",
                target_size=2,
                overwrite=True,
            )

            self.assertEqual(metadata["metrics"]["row_count"], 2)
            with sqlite3.connect(output) as conn:
                lemmas = [row[0] for row in conn.execute("SELECT lemma FROM frequency ORDER BY id")]
            self.assertEqual(lemmas, ["el", "que"])

    def test_kaikki_legacy_flat_path_falls_back_to_managed_main_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spalex_csv = root / "word_info.csv"
            managed_kaikki_db = root / "wiktionary-es-en" / "main.sqlite"
            output = root / "main.sqlite"
            _write_spalex_csv(spalex_csv, [("medicina", 4.5, 1.1, 22.0, 88.0)])
            managed_kaikki_db.parent.mkdir(parents=True)
            _write_kaikki_forward_db(
                managed_kaikki_db,
                {"medicina": ("noun", ["medicine", "sciences"])},
            )

            metadata = build_spalex_frequency_pack(
                spalex_csv=spalex_csv,
                current_frequency_db=root / "missing-cde.sqlite",
                output_sqlite=output,
                kaikki_forward_db=root / "wiktionary-es-en.sqlite",
                overwrite=True,
            )

            self.assertEqual(metadata["metrics"]["pos_rows"], 1)
            self.assertEqual(metadata["metrics"]["topic_domain_rows"], 1)
            with sqlite3.connect(output) as conn:
                pos, topics = conn.execute(
                    "SELECT pos, topics FROM frequency WHERE lemma = 'medicina'"
                ).fetchone()
                meta = json.loads(
                    conn.execute("SELECT value FROM meta WHERE key='metadata'").fetchone()[0]
                )
            self.assertEqual(pos, "n")
            self.assertEqual(topics, "medicine,sciences")
            self.assertTrue(str(meta["sources"]["kaikki_forward_db"]).endswith("main.sqlite"))

    def test_default_builds_spalex_only_without_cde_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spalex_csv = root / "word_info.csv"
            output = root / "freq-es-spalex-v1" / "main.sqlite"
            missing_cde = root / "missing-freq-es-cde.sqlite"
            _write_spalex_csv(
                spalex_csv,
                [
                    ("que", 7.4, 2.1, 28628.0, 98.8),
                    ("casa", 6.0, 1.8, 1000.0, 99.0),
                    ("medicina", 4.5, 1.1, 22.0, 88.0),
                ],
            )

            metadata = build_spalex_frequency_pack(
                spalex_csv=spalex_csv,
                current_frequency_db=missing_cde,
                output_sqlite=output,
                kaikki_forward_db=None,
                overwrite=True,
                write_sidecars=True,
            )

            self.assertEqual(metadata["source_mode"], "spalex_only")
            self.assertEqual(metadata["metrics"]["row_count"], 3)
            self.assertEqual(metadata["source_counts"]["current_cde_distinct"], 0)
            self.assertEqual(metadata["source_counts"]["cde_included"], 0)
            self.assertEqual(metadata["source_counts"]["spalex_included"], 3)
            with sqlite3.connect(output) as conn:
                rows = conn.execute(
                    "SELECT lemma, source_family, pos FROM frequency ORDER BY id"
                ).fetchall()
                meta = json.loads(
                    conn.execute("SELECT value FROM meta WHERE key='metadata'").fetchone()[0]
                )
            self.assertEqual([row[0] for row in rows], ["que", "casa", "medicina"])
            self.assertEqual({row[1] for row in rows}, {"spalex"})
            self.assertEqual([row[2] for row in rows], ["", "", ""])
            self.assertEqual(meta["source_profile"], "spalex_only_v1")
            self.assertEqual(meta["pos_policy"], "none")

            manifest = load_installed_pack_manifest(root, "freq-es-spalex-v1")
            self.assertIsNotNone(manifest)
            self.assertEqual(manifest.artifact_relpath, "main.sqlite")
            provenance_path = output.parent / "provenance.json"
            provenance_errors = validate_pack_provenance_file(provenance_path)
            self.assertEqual(provenance_errors, ())
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            self.assertEqual(provenance["source"]["license_status"], "confirmed")
            self.assertEqual(provenance["build"]["required_files"], ["word_info.csv"])
            component_roles = {
                component["role"]
                for component in provenance["source"]["source_bundle"]["components"]
            }
            self.assertEqual(component_roles, {"primary_frequency"})


def _write_current_frequency_db(path: Path, rows: list[tuple[str, int, float, str]]) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE frequency (id REAL, freq REAL, lemma TEXT, pos TEXT)")
        conn.executemany(
            "INSERT INTO frequency (id, freq, lemma, pos) VALUES (?, ?, ?, ?)",
            [(rank, freq, lemma, pos) for lemma, rank, freq, pos in rows],
        )
        conn.commit()
    finally:
        conn.close()


def _write_spalex_csv(path: Path, rows: list[tuple[str, float, float, float, float]]) -> None:
    fieldnames = [
        "spelling",
        "count_total",
        "percent_total",
        "prevalence_total",
        "count_nts",
        "percent_nts",
        "prevalence_nts",
        "count_ntl",
        "percent_ntl",
        "prevalence_ntl",
        "freq",
        "zipf",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for spelling, zipf, prevalence, freq, percent in rows:
            writer.writerow(
                {
                    "spelling": spelling,
                    "count_total": 100,
                    "percent_total": percent,
                    "prevalence_total": prevalence,
                    "count_nts": 50,
                    "percent_nts": percent,
                    "prevalence_nts": prevalence,
                    "count_ntl": 50,
                    "percent_ntl": percent,
                    "prevalence_ntl": prevalence,
                    "freq": freq,
                    "zipf": zipf,
                }
            )


def _write_kaikki_forward_db(path: Path, rows: dict[str, tuple[str, list[str]]]) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE entry_meta ("
            "entry_ord INTEGER, headword TEXT, headword_lc TEXT, lang TEXT, lang_code TEXT, "
            "pos TEXT, pos_title TEXT, categories_json TEXT, forms_json TEXT, sounds_json TEXT, "
            "synonyms_json TEXT, tags_json TEXT, etymology_text TEXT)"
        )
        conn.execute(
            "CREATE TABLE sense_glosses ("
            "entry_ord INTEGER, sense_ord INTEGER, gloss_ord INTEGER, headword TEXT, "
            "headword_lc TEXT, translation TEXT, translation_lc TEXT, pos TEXT, "
            "raw_glosses_json TEXT, tags_json TEXT, topics_json TEXT, categories_json TEXT, "
            "form_of_json TEXT, alt_of_json TEXT)"
        )
        for index, (lemma, (pos, topics)) in enumerate(rows.items(), 1):
            topics_json = json.dumps(topics)
            conn.execute(
                "INSERT INTO entry_meta VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (index, lemma, lemma, "Spanish", "es", pos, pos, "[]", "[]", "[]", "[]", "[]", ""),
            )
            conn.execute(
                "INSERT INTO sense_glosses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    index,
                    1,
                    1,
                    lemma,
                    lemma,
                    f"{lemma} gloss",
                    f"{lemma} gloss",
                    pos,
                    "[]",
                    "[]",
                    topics_json,
                    "[]",
                    "[]",
                    "[]",
                ),
            )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
