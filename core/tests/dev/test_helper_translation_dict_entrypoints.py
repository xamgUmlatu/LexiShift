from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from lexishift_core.helper.paths import build_helper_paths


REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER_SCRIPT = REPO_ROOT / "scripts" / "helper" / "lexishift_helper.py"
NATIVE_HOST_SCRIPT = REPO_ROOT / "scripts" / "helper" / "lexishift_native_host.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestHelperTranslationDictEntrypoints(unittest.TestCase):
    def test_helper_cli_translation_dict_help_describes_installed_pack_defaults(self) -> None:
        commands = (
            "run_rulegen",
            "init_srs_set",
            "refresh_srs_set",
            "plan_srs_rebalance",
            "apply_srs_rebalance",
        )

        for command in commands:
            with self.subTest(command=command):
                result = subprocess.run(
                    [sys.executable, str(HELPER_SCRIPT), command, "--help"],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 0, msg=result.stderr)
                help_text = result.stdout
                normalized_help = " ".join(help_text.split())
                self.assertIn("--translation-dict", help_text)
                self.assertNotIn("--freedict-de-en", help_text)
                self.assertIn(
                    "Installed language packs are used by default.",
                    normalized_help,
                )
                self.assertIn(
                    "manual translation dictionary override",
                    normalized_help,
                )
                self.assertIn(
                    "manual compatibility",
                    normalized_help,
                )

    def test_helper_cli_exposes_admission_preview_and_rebalance_commands(self) -> None:
        result = subprocess.run(
            [sys.executable, str(HELPER_SCRIPT), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        help_text = result.stdout
        self.assertIn("preview_srs_admission", help_text)
        self.assertIn("plan_srs_rebalance", help_text)
        self.assertIn("apply_srs_rebalance", help_text)
        self.assertIn("install_semantic_pack", help_text)

    def test_helper_cli_preview_admission_help_lists_profile_preview_flags(self) -> None:
        result = subprocess.run(
            [sys.executable, str(HELPER_SCRIPT), "preview_srs_admission", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        help_text = result.stdout
        self.assertIn("--preview-count", help_text)
        self.assertIn("--preview-sampling-mode", help_text)
        self.assertIn("--profile-context-json", help_text)

    def test_helper_cli_install_semantic_pack_help_lists_safety_flags(self) -> None:
        result = subprocess.run(
            [sys.executable, str(HELPER_SCRIPT), "install_semantic_pack", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        help_text = result.stdout
        self.assertIn("--semantic-inventory", help_text)
        self.assertIn("--data-root", help_text)
        self.assertIn("--allow-default-data-root", help_text)
        self.assertIn("--dry-run", help_text)
        self.assertIn("--copy-only", help_text)

    def test_helper_cli_install_semantic_pack_requires_explicit_data_root(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(HELPER_SCRIPT),
                "install_semantic_pack",
                "--semantic-inventory",
                "missing.json",
                "--dry-run",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("requires --data-root", result.stderr)

    def test_native_host_install_semantic_pack_requires_explicit_data_root(self) -> None:
        module = _load_module("lexishift_native_host_install_safety_test", NATIVE_HOST_SCRIPT)

        with patch.object(module, "build_helper_paths", side_effect=AssertionError):
            with self.assertRaisesRegex(ValueError, "requires payload.data_root"):
                module._handle_request(
                    "install_semantic_pack",
                    {
                        "pair": "en-es",
                        "profile_id": "semantic alpha",
                        "semantic_inventory_path": "missing.json",
                    },
                )

    def test_native_host_installs_semantic_pack_into_profile_publication_family(self) -> None:
        module = _load_module(
            "lexishift_native_host_install_semantic_pack_test", NATIVE_HOST_SCRIPT
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_inventory = root / "source_inventory.json"
            source_inventory.write_text(
                json.dumps(_sample_semantic_inventory(), ensure_ascii=False),
                encoding="utf-8",
            )
            data_root = root / "data-root"

            response = module._handle_request(
                "install_semantic_pack",
                {
                    "pair": "en-es",
                    "profile_id": "semantic alpha",
                    "semantic_inventory_path": str(source_inventory),
                    "pack_id": "en-es-active-only-native-v1",
                    "data_root": str(data_root),
                    "generated_at": "2026-05-10T00:00:00Z",
                },
            )
            paths = build_helper_paths(data_root)

            self.assertEqual(response["status"], "ok")
            self.assertEqual(response["profile_id"], "semantic_alpha")
            self.assertEqual(response["summary"]["rule_count"], 1)
            self.assertTrue(paths.ruleset_path("en-es", profile_id="semantic_alpha").exists())
            self.assertTrue(
                paths.semantic_inventory_path("en-es", profile_id="semantic_alpha").exists()
            )
            self.assertTrue(
                (
                    paths.language_packs_dir
                    / "en-es"
                    / "semantic_packs"
                    / "en-es-active-only-native-v1"
                    / "semantic_inventory.json"
                ).exists()
            )

    def test_native_host_installs_named_semantic_pack_without_source_path(self) -> None:
        module = _load_module("lexishift_native_host_named_semantic_pack_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data-root"
            paths = build_helper_paths(data_root)
            pack_inventory = (
                paths.language_packs_dir
                / "en-es"
                / "semantic_packs"
                / "en-es-installed-native-v1"
                / "semantic_inventory.json"
            )
            pack_inventory.parent.mkdir(parents=True, exist_ok=True)
            pack_inventory.write_text(
                json.dumps(_sample_semantic_inventory(), ensure_ascii=False),
                encoding="utf-8",
            )

            response = module._handle_request(
                "install_semantic_pack",
                {
                    "pair": "en-es",
                    "profile_id": "semantic alpha",
                    "pack_id": "en-es-installed-native-v1",
                    "data_root": str(data_root),
                    "generated_at": "2026-05-10T00:00:00Z",
                    "no_pack_copy": True,
                },
            )

            self.assertEqual(response["status"], "ok")
            self.assertEqual(response["profile_id"], "semantic_alpha")
            self.assertEqual(response["summary"]["rule_count"], 1)
            self.assertEqual(
                response["source"]["semantic_inventory_path"],
                str(pack_inventory),
            )

    def test_native_host_ignores_legacy_translation_dict_payload_key(self) -> None:
        module = _load_module("lexishift_native_host_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            legacy_path = Path(tmp) / "legacy.sqlite"
            resolved_jmdict, resolved_translation_dict, resolved_frequency_db = (
                module._resolve_pair_resource_paths(
                    paths,
                    pair="en-de",
                    payload={"freedict_de_en_path": str(legacy_path)},
                )
            )

        self.assertIsNone(resolved_jmdict)
        self.assertIsNotNone(resolved_translation_dict)
        self.assertIsNotNone(resolved_frequency_db)
        self.assertNotEqual(resolved_translation_dict, legacy_path)
        self.assertTrue(str(resolved_translation_dict).endswith("freedict-de-en.sqlite"))

    def test_native_host_serves_semantic_inventory_payload(self) -> None:
        module = _load_module("lexishift_native_host_semantic_inventory_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            payload = {
                "schema_version": 1,
                "pair": "en-es",
                "profile_id": "default",
                "generated_at": "2026-04-13T00:00:00Z",
                "triggers": {},
                "senses": {},
                "competition_sets": {},
                "phrase_sets": {},
            }
            paths.semantic_inventory_path("en-es").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            with patch.object(module, "build_helper_paths", return_value=paths):
                response = module._handle_request(
                    "get_semantic_inventory",
                    {"pair": "en-es", "profile_id": "default"},
                )

        self.assertEqual(response["pair"], "en-es")
        self.assertEqual(response["schema_version"], 1)

    def test_native_host_routes_srs_preview_admission(self) -> None:
        module = _load_module("lexishift_native_host_preview_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            with (
                patch.object(module, "build_helper_paths", return_value=paths),
                patch.object(
                    module,
                    "preview_srs_admission",
                    return_value={"kind": "preview", "pair": "en-ja"},
                ) as preview,
            ):
                response = module._handle_request(
                    "srs_preview_admission",
                    {
                        "pair": "en-ja",
                        "profile_id": "default",
                        "strategy": "profile_bootstrap",
                        "objective": "bootstrap",
                        "preview_count": 3,
                        "profile_context": {"interests": ["animals"]},
                    },
                )

        self.assertEqual(response["kind"], "preview")
        config = preview.call_args.kwargs["config"]
        self.assertEqual(config.pair, "en-ja")
        self.assertEqual(config.profile_id, "default")
        self.assertEqual(config.strategy, "profile_bootstrap")
        self.assertEqual(config.preview_count, 3)
        self.assertEqual(config.profile_context, {"interests": ["animals"]})

    def test_native_host_routes_srs_refresh_profile_growth(self) -> None:
        module = _load_module("lexishift_native_host_refresh_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            with (
                patch.object(module, "build_helper_paths", return_value=paths),
                patch.object(
                    module,
                    "refresh_srs_set",
                    return_value={"kind": "refresh", "pair": "en-ja"},
                ) as refresh,
            ):
                response = module._handle_request(
                    "srs_refresh",
                    {
                        "pair": "en-ja",
                        "profile_id": "default",
                        "strategy": "profile_growth",
                        "profile_context": {"interests": ["animals"]},
                    },
                )

        self.assertEqual(response["kind"], "refresh")
        config = refresh.call_args.kwargs["config"]
        self.assertEqual(config.pair, "en-ja")
        self.assertEqual(config.profile_id, "default")
        self.assertEqual(config.strategy, "profile_growth")
        self.assertEqual(config.profile_context, {"interests": ["animals"]})

    def test_native_host_routes_srs_auto_refresh_policy(self) -> None:
        module = _load_module("lexishift_native_host_auto_refresh_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            with (
                patch.object(module, "build_helper_paths", return_value=paths),
                patch.object(
                    module,
                    "maybe_auto_refresh_srs_set",
                    return_value={"kind": "auto_refresh", "pair": "en-ja"},
                ) as auto_refresh,
            ):
                response = module._handle_request(
                    "srs_auto_refresh",
                    {
                        "pair": "en-ja",
                        "profile_id": "default",
                        "strategy": "profile_growth",
                        "profile_context": {"interests": ["animals"]},
                        "auto_refresh_min_feedback_events": 9,
                        "auto_refresh_min_good_easy": 7,
                        "auto_refresh_repeat_min_good_easy": 13,
                        "auto_refresh_cooldown_minutes": 45,
                    },
                )

        self.assertEqual(response["kind"], "auto_refresh")
        config = auto_refresh.call_args.kwargs["config"]
        self.assertEqual(config.pair, "en-ja")
        self.assertEqual(config.profile_id, "default")
        self.assertEqual(config.strategy, "profile_growth")
        self.assertEqual(config.profile_context, {"interests": ["animals"]})
        self.assertEqual(config.auto_refresh_min_feedback_events, 9)
        self.assertEqual(config.auto_refresh_min_good_easy, 7)
        self.assertEqual(config.auto_refresh_repeat_min_good_easy, 13)
        self.assertEqual(config.auto_refresh_cooldown_minutes, 45)

    def test_native_host_routes_semantic_admit_batch(self) -> None:
        module = _load_module("lexishift_native_host_semantic_admit_batch_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            with patch.object(module, "build_helper_paths", return_value=paths):
                response = module._handle_request(
                    "semantic_admit_batch",
                    {
                        "pair": "en-es",
                        "profile_id": "default",
                        "fallback_policy": "abstain_on_unavailable",
                        "matches": [
                            {
                                "match_id": "m1",
                                "source_phrase": "bank",
                                "context_text": "You can bank on her support.",
                                "match_start": 8,
                                "match_end": 12,
                                "semantic_admission": {
                                    "schema_version": 1,
                                    "status": "ready",
                                    "trigger_id": "en-es:trigger:bank",
                                    "sense_id": "sense:banco",
                                    "competition_set_id": "comp:bank",
                                },
                            }
                        ],
                    },
                )

        self.assertEqual(response["pair"], "en-es")
        self.assertEqual(response["decisions"][0]["decision_source"], "fallback_policy")
        self.assertIn("semantic_inventory_missing", response["decisions"][0]["reason_codes"])

    def test_native_host_routes_srs_rebalance_plan_and_apply(self) -> None:
        module = _load_module("lexishift_native_host_rebalance_test", NATIVE_HOST_SCRIPT)

        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            with (
                patch.object(module, "build_helper_paths", return_value=paths),
                patch.object(
                    module,
                    "plan_srs_rebalance",
                    return_value={"kind": "plan", "pair": "en-ja"},
                ) as plan_rebalance,
                patch.object(
                    module,
                    "apply_srs_rebalance",
                    return_value={"kind": "apply", "pair": "en-ja"},
                ) as apply_rebalance,
            ):
                preview_response = module._handle_request(
                    "srs_rebalance_plan",
                    {
                        "pair": "en-ja",
                        "profile_id": "default",
                        "strategy": "profile_growth",
                        "objective": "rebalance",
                        "max_active_items": 12,
                        "profile_context": {"interests": ["animals"]},
                    },
                )
                apply_response = module._handle_request(
                    "srs_rebalance_apply",
                    {
                        "pair": "en-ja",
                        "profile_id": "default",
                        "strategy": "profile_growth",
                        "objective": "rebalance",
                        "max_active_items": 12,
                        "profile_context": {"interests": ["animals"]},
                    },
                )

        self.assertEqual(preview_response["kind"], "plan")
        self.assertEqual(apply_response["kind"], "apply")

        preview_config = plan_rebalance.call_args.kwargs["config"]
        self.assertEqual(preview_config.pair, "en-ja")
        self.assertEqual(preview_config.profile_id, "default")
        self.assertEqual(preview_config.strategy, "profile_growth")
        self.assertEqual(preview_config.max_active_items, 12)
        self.assertEqual(preview_config.profile_context, {"interests": ["animals"]})

        apply_config = apply_rebalance.call_args.kwargs["config"]
        self.assertEqual(apply_config.pair, "en-ja")
        self.assertEqual(apply_config.profile_id, "default")
        self.assertEqual(apply_config.strategy, "profile_growth")
        self.assertEqual(apply_config.max_active_items, 12)
        self.assertEqual(apply_config.profile_context, {"interests": ["animals"]})


def _sample_semantic_inventory() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "triggers": {
            "family:bank:trigger": {
                "trigger_id": "family:bank:trigger",
                "source_phrase": "bank",
            }
        },
        "senses": {
            "family:bank:active": {
                "sense_id": "family:bank:active",
                "target_lemma": "banco",
                "evidence_views": {
                    "sense_label": "financial institution",
                    "all_evidence_text": "The bank approved the loan.",
                },
            },
            "family:bank:shadow": {
                "sense_id": "family:bank:shadow",
                "target_lemma": "orilla",
                "evidence_views": {
                    "sense_label": "river edge",
                    "all_evidence_text": "They sat on the bank of the river.",
                },
            },
        },
        "competition_sets": {
            "family:bank:banco:v1": {
                "competition_set_id": "family:bank:banco:v1",
                "trigger_id": "family:bank:trigger",
                "active_sense_id": "family:bank:active",
                "shadow_sense_ids": ["family:bank:shadow"],
            }
        },
        "phrase_sets": {},
    }


if __name__ == "__main__":
    unittest.main()
