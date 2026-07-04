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
from lexishift_core.helper.rulegen_outputs import RulegenOutput  # noqa: E402
from lexishift_core.helper.use_cases.browsing_source_index import (  # noqa: E402
    build_srs_browsing_source_index,
)
from lexishift_core.persistence.storage import VocabDataset, save_vocab_dataset  # noqa: E402
from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402
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
    def test_browsing_source_index_use_case_builds_compact_candidate_rules(self) -> None:
        class FakeReport:
            selected_unique_count = 2
            admitted_count = 2
            selected_preview = ("発酵", "血圧")

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            frequency_db = Path(tmp) / "freq.sqlite"
            jmdict_path = Path(tmp) / "JMdict_e"
            frequency_db.write_text("", encoding="utf-8")
            jmdict_path.write_text("", encoding="utf-8")
            captured: dict[str, object] = {}

            def fake_init(store, *, config):
                captured["init_config"] = config
                return (
                    SrsStore(
                        items=(
                            SrsItem(
                                item_id="en-ja:発酵",
                                lemma="発酵",
                                language_pair="en-ja",
                                source_type="initial_set",
                                word_package={
                                    "version": 1,
                                    "language_tag": "ja",
                                    "surface": "発酵",
                                    "reading": "はっこう",
                                    "script_forms": {"kanji": "発酵", "kana": "はっこう"},
                                    "source": {"source_frequency_profile": "x" * 1000},
                                },
                            ),
                            SrsItem(
                                item_id="en-ja:血圧",
                                lemma="血圧",
                                language_pair="en-ja",
                                source_type="initial_set",
                                word_package={
                                    "version": 1,
                                    "language_tag": "ja",
                                    "surface": "血圧",
                                    "reading": "けつあつ",
                                    "script_forms": {"kanji": "血圧", "kana": "けつあつ"},
                                },
                            ),
                        )
                    ),
                    FakeReport(),
                )

            def fake_rulegen(**kwargs):
                captured["rulegen"] = kwargs
                rules = (
                    VocabRule(
                        source_phrase="fermentation",
                        replacement="発酵",
                        metadata=RuleMetadata(
                            language_pair="en-ja",
                            word_package={
                                "version": 1,
                                "language_tag": "ja",
                                "surface": "発酵",
                                "reading": "はっこう",
                                "script_forms": {
                                    "kanji": "発酵",
                                    "kana": "はっこう",
                                    "romaji": "hakkou",
                                },
                                "source": {"source_frequency_profile": "x" * 1000},
                            },
                            pos={"source": {"raw": "noun", "matched_rule": "x" * 1000}},
                            semantic_admission={"competition_set_id": "x" * 1000},
                        ),
                    ),
                    VocabRule(
                        source_phrase="blood pressure",
                        replacement="血圧",
                        metadata=RuleMetadata(
                            language_pair="en-ja",
                            word_package={
                                "version": 1,
                                "language_tag": "ja",
                                "surface": "血圧",
                                "reading": "けつあつ",
                            },
                        ),
                    ),
                )
                return kwargs["store"], RulegenOutput(rules=rules, snapshot={}, target_count=2)

            payload = build_srs_browsing_source_index(
                paths,
                pair="en-ja",
                profile_id="default",
                top_n=12,
                max_targets=2,
                max_rules=5,
                resolve_pair_set_top_n_fn=lambda **_kwargs: 2000,
                resolve_pair_resources_fn=lambda *_args, **_kwargs: (
                    jmdict_path,
                    None,
                    frequency_db,
                ),
                ensure_pair_requirements_fn=lambda **_kwargs: None,
                resolve_profile_id_fn=lambda _paths, *, profile_id: profile_id or "default",
                resolve_stopwords_path_fn=lambda *_args, **_kwargs: None,
                initialize_store_from_frequency_list_with_report_fn=fake_init,
                run_rulegen_for_pair_fn=fake_rulegen,
            )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["pair"], "en-ja")
            self.assertEqual(payload["rule_count"], 2)
            self.assertEqual(payload["target_count"], 2)
            self.assertEqual(payload["frontier"]["top_n"], 12)
            init_config = captured["init_config"]
            self.assertEqual(init_config.initial_active_count, 2)
            self.assertEqual(init_config.top_n, 12)
            rulegen_kwargs = captured["rulegen"]
            self.assertEqual(rulegen_kwargs["targets_override"], ("発酵", "血圧"))
            self.assertEqual(rulegen_kwargs["active_item_ids"], ("en-ja:発酵", "en-ja:血圧"))
            self.assertFalse(paths.srs_store_path_for("default").exists())
            self.assertEqual(payload["rules"][0]["source_phrase"], "fermentation")
            self.assertEqual(payload["rules"][0]["metadata"]["lexishift_origin"], "srs")
            self.assertEqual(payload["rules"][0]["metadata"]["source_index"], "candidate_frontier")
            self.assertNotIn("semantic_admission", payload["rules"][0]["metadata"])
            self.assertNotIn("pos", payload["rules"][0]["metadata"])
            self.assertNotIn(
                "source",
                payload["rules"][0]["metadata"]["word_package"],
            )
            self.assertEqual(
                payload["rules"][0]["metadata"]["word_package"]["reading"],
                "はっこう",
            )
            self.assertEqual(
                payload["rules"][0]["metadata"]["word_package"]["script_forms"]["romaji"],
                "hakkou",
            )
            self.assertLess(len(json.dumps(payload["rules"][0])), 500)
            self.assertEqual(payload["source_index_cache"]["source"], "generated")

            def fail_init(*_args, **_kwargs):
                raise AssertionError("cached source index should not rebuild frontier")

            def fail_rulegen(**_kwargs):
                raise AssertionError("cached source index should not rerun rulegen")

            def fail_requirements(**_kwargs):
                raise AssertionError("stale cache should not validate missing resources")

            cached_payload = build_srs_browsing_source_index(
                paths,
                pair="en-ja",
                profile_id="default",
                top_n=12,
                max_targets=2,
                max_rules=5,
                resolve_pair_set_top_n_fn=lambda **_kwargs: 2000,
                resolve_pair_resources_fn=lambda *_args, **_kwargs: (
                    jmdict_path,
                    None,
                    frequency_db,
                ),
                ensure_pair_requirements_fn=lambda **_kwargs: None,
                resolve_profile_id_fn=lambda _paths, *, profile_id: profile_id or "default",
                resolve_stopwords_path_fn=lambda *_args, **_kwargs: None,
                initialize_store_from_frequency_list_with_report_fn=fail_init,
                run_rulegen_for_pair_fn=fail_rulegen,
            )
            self.assertEqual(cached_payload["status"], "ok")
            self.assertEqual(cached_payload["source_index_cache"]["source"], "helper-cache")
            self.assertEqual(cached_payload["rules"][0]["source_phrase"], "fermentation")

            jmdict_path.unlink()
            stale_payload = build_srs_browsing_source_index(
                paths,
                pair="en-ja",
                profile_id="default",
                top_n=12,
                max_targets=2,
                max_rules=5,
                resolve_pair_set_top_n_fn=lambda **_kwargs: 2000,
                resolve_pair_resources_fn=lambda *_args, **_kwargs: (
                    jmdict_path,
                    None,
                    frequency_db,
                ),
                ensure_pair_requirements_fn=fail_requirements,
                resolve_profile_id_fn=lambda _paths, *, profile_id: profile_id or "default",
                resolve_stopwords_path_fn=lambda *_args, **_kwargs: None,
                initialize_store_from_frequency_list_with_report_fn=fail_init,
                run_rulegen_for_pair_fn=fail_rulegen,
            )
            self.assertEqual(stale_payload["status"], "ok")
            self.assertEqual(stale_payload["source_index_cache"]["source"], "helper-cache-stale")
            self.assertEqual(stale_payload["resource_status"], "missing_required_resources")
            self.assertEqual(stale_payload["missing_inputs"][0]["type"], "jmdict_path")
            self.assertEqual(stale_payload["rules"][0]["source_phrase"], "fermentation")

    def test_browsing_source_index_reports_missing_resources_without_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            frequency_db = Path(tmp) / "missing-freq.sqlite"
            jmdict_path = Path(tmp) / "missing-JMdict_e"

            def fail_requirements(**_kwargs):
                raise AssertionError("missing-resource preflight should not validate later")

            def fail_init(*_args, **_kwargs):
                raise AssertionError("missing resources should not initialize frontier")

            def fail_rulegen(**_kwargs):
                raise AssertionError("missing resources should not run rulegen")

            payload = build_srs_browsing_source_index(
                paths,
                pair="en-ja",
                profile_id="default",
                top_n=12,
                max_targets=2,
                max_rules=5,
                resolve_pair_set_top_n_fn=lambda **_kwargs: 2000,
                resolve_pair_resources_fn=lambda *_args, **_kwargs: (
                    jmdict_path,
                    None,
                    frequency_db,
                ),
                ensure_pair_requirements_fn=fail_requirements,
                resolve_profile_id_fn=lambda _paths, *, profile_id: profile_id or "default",
                resolve_stopwords_path_fn=lambda *_args, **_kwargs: None,
                initialize_store_from_frequency_list_with_report_fn=fail_init,
                run_rulegen_for_pair_fn=fail_rulegen,
            )

            self.assertEqual(payload["status"], "not_ready")
            self.assertEqual(payload["reason"], "missing_required_resources")
            self.assertEqual(payload["rule_count"], 0)
            self.assertEqual(
                {item["type"] for item in payload["missing_inputs"]},
                {"jmdict_path", "set_source_db"},
            )
            self.assertEqual(payload["source_index_cache"]["source"], "miss")

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

    def test_native_host_routes_browsing_source_index(self) -> None:
        module = _load_module(
            "lexishift_native_host_browsing_source_index_test", NATIVE_HOST_SCRIPT
        )

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            with (
                patch.object(module, "build_helper_paths", return_value=paths),
                patch.object(
                    module,
                    "build_srs_browsing_source_index",
                    return_value={"status": "ok", "rules": []},
                ) as mocked,
            ):
                response = module._handle_request(
                    "srs_browsing_source_index",
                    {
                        "pair": "en-ja",
                        "profile_id": "default",
                        "top_n": 10,
                        "max_targets": 3,
                        "max_rules": 4,
                        "allow_generate": False,
                        "force_refresh": True,
                    },
                )

            self.assertEqual(response["status"], "ok")
            mocked.assert_called_once()
            self.assertEqual(mocked.call_args.kwargs["pair"], "en-ja")
            self.assertEqual(mocked.call_args.kwargs["profile_id"], "default")
            self.assertEqual(mocked.call_args.kwargs["top_n"], 10)
            self.assertEqual(mocked.call_args.kwargs["max_targets"], 3)
            self.assertEqual(mocked.call_args.kwargs["max_rules"], 4)
            self.assertIs(mocked.call_args.kwargs["allow_generate"], False)
            self.assertIs(mocked.call_args.kwargs["force_refresh"], True)

    def test_native_host_browsing_source_index_reports_missing_resources(self) -> None:
        module = _load_module(
            "lexishift_native_host_browsing_source_index_missing_test",
            NATIVE_HOST_SCRIPT,
        )

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            with patch.object(module, "build_helper_paths", return_value=paths):
                response = module._handle_request(
                    "srs_browsing_source_index",
                    {"pair": "en-ja", "profile_id": "default"},
                )

            self.assertEqual(response["status"], "not_ready")
            self.assertEqual(response["reason"], "missing_required_resources")
            self.assertEqual(response["rule_count"], 0)
            self.assertEqual(
                {item["type"] for item in response["missing_inputs"]},
                {"jmdict_path", "set_source_db"},
            )

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
