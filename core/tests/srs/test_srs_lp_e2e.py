from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from xml.sax.saxutils import escape

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.engine import (  # noqa: E402
    SrsRefreshJobConfig,
    SetInitializationJobConfig,
    get_srs_runtime_diagnostics,
    initialize_srs_set,
    refresh_srs_set,
)
from lexishift_core.helper.paths import HelperPaths, build_helper_paths  # noqa: E402
from lexishift_core.srs import SrsSettings, save_srs_settings  # noqa: E402


def _alpha_suffix(index: int) -> str:
    value = max(0, int(index))
    chars = []
    for _ in range(3):
        chars.append(chr(ord("a") + (value % 26)))
        value //= 26
    return "".join(reversed(chars))


def _build_tokens(prefix: str, count: int) -> list[str]:
    return [f"{prefix}{_alpha_suffix(i)}" for i in range(max(0, int(count)))]


def _write_frequency_db(
    *,
    path: Path,
    lemmas: list[str],
    pos: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("DROP TABLE IF EXISTS frequency;")
    conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL, pos TEXT);")
    rows = [
        (lemma, float(index + 1), float(len(lemmas) - index), pos)
        for index, lemma in enumerate(lemmas)
    ]
    conn.executemany(
        "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?);",
        rows,
    )
    conn.commit()
    conn.close()


def _write_jmdict(path: Path, *, targets: list[str], sources: list[str]) -> None:
    entries: list[str] = []
    for target, source in zip(targets, sources):
        entries.append(
            "<entry>"
            f"<k_ele><keb>{escape(target)}</keb></k_ele>"
            f"<r_ele><reb>{escape(target)}</reb></r_ele>"
            f"<sense><gloss>{escape(source)}</gloss></sense>"
            "</entry>"
        )
    payload = "<JMdict>" + "".join(entries) + "</JMdict>"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _write_freedict_de_en(path: Path, *, targets: list[str], sources: list[str]) -> None:
    entries: list[str] = []
    for target, source in zip(targets, sources):
        entries.append(
            "<entry>"
            f"<form><orth>{escape(target)}</orth></form>"
            "<sense>"
            f"<cit type='trans'><quote xml:lang='en'>{escape(source)}</quote></cit>"
            "</sense>"
            "</entry>"
        )
    payload = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<TEI xmlns='http://www.tei-c.org/ns/1.0'>"
        "<text><body>"
        + "".join(entries)
        + "</body></text>"
        "</TEI>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


class TestSrsLpE2E(unittest.TestCase):
    def _run_e2e_for_pair(
        self,
        *,
        pair: str,
        configure_resources,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            save_srs_settings(
                SrsSettings(max_active_items=100, max_new_items_per_day=8),
                paths.srs_settings_path,
            )
            configure_resources(paths)

            init = initialize_srs_set(
                paths,
                config=SetInitializationJobConfig(
                    pair=pair,
                    profile_id="default",
                    set_top_n=200,
                    replace_pair=True,
                ),
            )
            self.assertTrue(init["applied"])
            self.assertTrue(init["rulegen"]["published"])
            self.assertGreater(init["rulegen"]["targets"], 0)
            self.assertGreater(init["rulegen"]["rules"], 0)
            self.assertTrue(Path(init["rulegen"]["snapshot_path"]).exists())
            self.assertTrue(Path(init["rulegen"]["ruleset_path"]).exists())

            refresh = refresh_srs_set(
                paths,
                config=SrsRefreshJobConfig(
                    pair=pair,
                    profile_id="default",
                    set_top_n=200,
                    feedback_window_size=40,
                ),
            )
            self.assertTrue(refresh["applied"])
            self.assertGreater(refresh["added_items"], 0)
            self.assertIsNotNone(refresh["rulegen"])
            self.assertTrue(refresh["rulegen"]["published"])
            self.assertGreater(refresh["rulegen"]["targets"], 0)
            self.assertGreater(refresh["rulegen"]["rules"], 0)
            self.assertTrue(Path(refresh["rulegen"]["snapshot_path"]).exists())
            self.assertTrue(Path(refresh["rulegen"]["ruleset_path"]).exists())

            diagnostics = get_srs_runtime_diagnostics(paths, pair=pair)
            self.assertTrue(diagnostics["store_exists"])
            self.assertTrue(diagnostics["ruleset_exists"])
            self.assertTrue(diagnostics["snapshot_exists"])
            self.assertEqual(diagnostics["missing_inputs"], [])
            self.assertIn("pair_policy", diagnostics)
            self.assertEqual(diagnostics["pair_policy"]["pair"], pair)
            self.assertGreater(int(diagnostics["store_items_for_pair"]), 0)
            self.assertGreater(int(diagnostics["ruleset_rules_count"]), 0)
            self.assertGreater(int(diagnostics["snapshot_target_count"]), 0)

    def test_en_ja_e2e_initialize_and_refresh_publish_outputs(self) -> None:
        def _configure(paths: HelperPaths) -> None:
            targets = _build_tokens("ja", 70)
            sources = _build_tokens("eng", 70)
            _write_frequency_db(
                path=paths.frequency_packs_dir / "freq-ja-bccwj.sqlite",
                lemmas=targets,
                pos="名詞-普通名詞-一般",
            )
            _write_jmdict(
                paths.language_packs_dir / "JMdict_e",
                targets=targets,
                sources=sources,
            )

        self._run_e2e_for_pair(pair="en-ja", configure_resources=_configure)

    def test_en_de_e2e_initialize_and_refresh_publish_outputs(self) -> None:
        def _configure(paths: HelperPaths) -> None:
            targets = _build_tokens("de", 70)
            sources = _build_tokens("eng", 70)
            _write_frequency_db(
                path=paths.frequency_packs_dir / "freq-de-default.sqlite",
                lemmas=targets,
                pos="SUB:NOM:SIN:NEU",
            )
            _write_freedict_de_en(
                paths.language_packs_dir / "deu-eng.tei",
                targets=targets,
                sources=sources,
            )

        self._run_e2e_for_pair(pair="en-de", configure_resources=_configure)


if __name__ == "__main__":
    unittest.main()
