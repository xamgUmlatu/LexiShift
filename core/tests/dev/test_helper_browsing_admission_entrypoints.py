from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

CORE_ROOT = Path(__file__).resolve().parents[3] / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))
HELPER_ROOT = Path(__file__).resolve().parents[3] / "scripts" / "helper"
if str(HELPER_ROOT) not in sys.path:
    sys.path.insert(0, str(HELPER_ROOT))

from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.persistence.storage import VocabDataset, save_vocab_dataset  # noqa: E402
from lexishift_core.replacement.core import VocabRule  # noqa: E402
from lexishift_core.srs import SrsItem, SrsStore, save_srs_store  # noqa: E402
from lexishift_core.srs.admission_suppression import (  # noqa: E402
    active_suppressed_lemmas,
    load_admission_suppression_store,
)
from lexishift_core.srs.browsing_admission import load_browsing_signal_store  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER_SCRIPT = REPO_ROOT / "scripts" / "helper" / "lexishift_helper.py"
NATIVE_HOST_SCRIPT = REPO_ROOT / "scripts" / "helper" / "lexishift_native_host.py"


def _write_translation_pack(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE entries (
                headword TEXT,
                headword_lc TEXT,
                translation TEXT,
                pos TEXT,
                rank INTEGER
            )
            """
        )
        conn.execute(
            """
            INSERT INTO entries (headword, headword_lc, translation, pos, rank)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("perro", "perro", "dog", "noun", 1),
        )
        conn.commit()
    finally:
        conn.close()


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestHelperBrowsingAdmissionEntrypoints(unittest.TestCase):
    def test_native_host_routes_srs_items_list(self) -> None:
        module = _load_module("lexishift_native_host_srs_items_list_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-es:perro",
                            lemma="perro",
                            language_pair="en-es",
                            source_type="initial_set",
                        ),
                    ),
                    version=2,
                ),
                paths.srs_store_path_for("default"),
            )
            with patch.object(module, "build_helper_paths", return_value=paths):
                response = module._handle_request(
                    "srs_items_list",
                    {
                        "pair": "en-es",
                        "profile_id": "default",
                    },
                )

            self.assertEqual(response["status"], "ok")
            self.assertEqual(response["summary"]["total"], 1)
            self.assertEqual(response["items"][0]["lemma"], "perro")

    def test_native_host_routes_srs_item_rule_details(self) -> None:
        module = _load_module("lexishift_native_host_srs_rule_details_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            save_vocab_dataset(
                VocabDataset(
                    rules=(
                        VocabRule(source_phrase="dog", replacement="perro"),
                        VocabRule(source_phrase="hound", replacement="perro"),
                    ),
                ),
                paths.ruleset_path("en-es", profile_id="default"),
            )
            with patch.object(module, "build_helper_paths", return_value=paths):
                response = module._handle_request(
                    "srs_item_rule_details",
                    {
                        "pair": "en-es",
                        "profile_id": "default",
                        "lemma": "perro",
                        "limit": 1,
                    },
                )

            self.assertEqual(response["status"], "ok")
            self.assertEqual(response["rule_count"], 2)
            self.assertEqual(response["returned_rule_count"], 1)
            self.assertTrue(response["truncated"])
            self.assertEqual(response["rules"][0]["replacement"], "perro")

    def test_native_host_routes_word_info_lookup(self) -> None:
        module = _load_module("lexishift_native_host_word_info_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            _write_translation_pack(paths.language_packs_dir / "wiktionary-es-en.sqlite")
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-es:perro",
                            lemma="perro",
                            language_pair="en-es",
                            source_type="initial_set",
                        ),
                    ),
                    version=2,
                ),
                paths.srs_store_path_for("default"),
            )
            save_vocab_dataset(
                VocabDataset(rules=(VocabRule(source_phrase="dog", replacement="perro"),)),
                paths.ruleset_path("en-es", profile_id="default"),
            )
            with patch.object(module, "build_helper_paths", return_value=paths):
                response = module._handle_request(
                    "word_info_lookup",
                    {
                        "pair": "en-es",
                        "profile_id": "default",
                        "lemma": "perro",
                        "display": "perro",
                        "origin": "srs",
                        "source_phrase": "dog",
                    },
                )

            self.assertEqual(response["status"], "ok")
            self.assertEqual(response["glosses"][0]["text"], "dog")
            self.assertTrue(response["srs"]["present"])
            self.assertEqual(response["source_phrases"], ["dog"])

    def test_native_host_routes_srs_admission_suppression(self) -> None:
        module = _load_module("lexishift_native_host_admission_suppress_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            with patch.object(module, "build_helper_paths", return_value=paths):
                response = module._handle_request(
                    "srs_admission_suppress",
                    {
                        "pair": "en-es",
                        "profile_id": "default",
                        "lemma": "perro",
                        "reason": "user_blocked",
                    },
                )

            self.assertEqual(response["status"], "ok")
            self.assertEqual(response["reason"], "user_blocked")
            self.assertFalse(response["runtime_srs_mutation"])
            store = load_admission_suppression_store(
                paths.srs_admission_suppression_store_path_for("default")
            )
            self.assertEqual(
                active_suppressed_lemmas(store, pair="en-es"),
                {"perro": "user_blocked"},
            )
            self.assertFalse(paths.srs_store_path_for("default").exists())

    def test_native_host_routes_opt_in_browsing_signal_ingest(self) -> None:
        module = _load_module("lexishift_native_host_browsing_ingest_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            with patch.object(module, "build_helper_paths", return_value=paths):
                response = module._handle_request(
                    "srs_browsing_signal_ingest",
                    {
                        "pair": "en-es",
                        "profile_id": "default",
                        "captured_at": "2026-05-23T00:00:00Z",
                        "opt_in": True,
                        "signals": [
                            {
                                "target_lemma": "hipoteca",
                                "side": "source",
                                "count": 4,
                                "source_mapping_confidence": 0.75,
                            }
                        ],
                    },
                )

            self.assertEqual(response["status"], "ok")
            self.assertFalse(response["runtime_srs_mutation"])
            store = load_browsing_signal_store(
                paths.srs_browsing_signal_store_path_for("default", "en-es")
            )
            self.assertIn("hipoteca", store.items)
            self.assertFalse(paths.srs_store_path_for("default").exists())

    def test_helper_cli_browsing_signal_ingest_requires_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload_path = root / "signals.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "pair": "en-es",
                        "signals": [{"target_lemma": "salud", "side": "target", "count": 2}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["LEXISHIFT_DATA_DIR"] = str(root / "data")

            skipped = subprocess.run(
                [
                    sys.executable,
                    str(HELPER_SCRIPT),
                    "ingest_browsing_admission_signals",
                    "--signals-json",
                    str(payload_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            accepted = subprocess.run(
                [
                    sys.executable,
                    str(HELPER_SCRIPT),
                    "ingest_browsing_admission_signals",
                    "--signals-json",
                    str(payload_path),
                    "--opt-in",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )

            self.assertEqual(skipped.returncode, 0, msg=skipped.stderr)
            self.assertEqual(accepted.returncode, 0, msg=accepted.stderr)
            self.assertEqual(json.loads(skipped.stdout)["status"], "skipped")
            self.assertEqual(json.loads(accepted.stdout)["status"], "ok")
            paths = build_helper_paths(root / "data")
            store = load_browsing_signal_store(
                paths.srs_browsing_signal_store_path_for("default", "en-es")
            )
            self.assertIn("salud", store.items)


if __name__ == "__main__":
    unittest.main()
