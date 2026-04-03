from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_benchmark_bundle import (  # noqa: E402
    build_bundle_run_argv,
    export_bundle,
    validate_bundle,
)


class TestRulegenBenchmarkBundle(unittest.TestCase):
    def test_export_bundle_copies_resources_and_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "rulegen_benchmark_cases.json"
            dataset.write_text('{"cases":[]}', encoding="utf-8")
            preset_file = root / "rulegen_benchmark_presets.json"
            preset_file.write_text('{"presets":{}}', encoding="utf-8")
            benchmark_json = root / "benchmark.json"
            forward = root / "wiktionary-es-en.sqlite"
            reverse = root / "wiktionary-en-es.sqlite"
            forward.write_text("forward", encoding="utf-8")
            reverse.write_text("reverse", encoding="utf-8")
            benchmark_json.write_text(
                json.dumps(
                    {
                        "dataset_path": str(dataset),
                        "profile_id": "default",
                        "sweep": {
                            "preset": {
                                "name": "en_es_canonical_matrix",
                                "description": "test preset",
                                "preset_file": str(preset_file),
                                "args": ["--pairs", "en-es", "--max-configurations", "16"],
                            }
                        },
                        "pairs": {
                            "en-es": {
                                "case_count": 2,
                                "resources": {
                                    "translation_dict_path": str(forward),
                                    "reverse_translation_dict_path": str(reverse),
                                    "checksums": {
                                        "translation_dict_sha256": None,
                                        "reverse_translation_dict_sha256": None,
                                        "jmdict_sha256": None,
                                    },
                                },
                                "word_package_snapshot": {
                                    "casa": None,
                                    "madre": {
                                        "version": 1,
                                        "language_tag": "es",
                                        "surface": "madre",
                                        "reading": "madre",
                                        "script_forms": {"default": "madre"},
                                        "source": {"provider": "bundle"},
                                    },
                                },
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            manifest_path = export_bundle(
                benchmark_json=benchmark_json,
                output_dir=root / "bundle",
                pair_filter=None,
                force=False,
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["pair_names"], ["en-es"])
            self.assertTrue((root / "bundle" / manifest["dataset_path"]).exists())
            self.assertTrue((root / "bundle" / manifest["word_package_snapshot_path"]).exists())
            pair_resources = manifest["pairs"]["en-es"]["resources"]
            self.assertTrue((root / "bundle" / pair_resources["translation_dict_path"]).exists())
            self.assertTrue(
                (root / "bundle" / pair_resources["reverse_translation_dict_path"]).exists()
            )
            self.assertTrue((root / "bundle" / "README.md").exists())

    def test_export_bundle_accepts_non_preset_benchmark_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "rulegen_benchmark_cases.json"
            dataset.write_text('{"cases":[]}', encoding="utf-8")
            benchmark_json = root / "benchmark.json"
            forward = root / "wiktionary-es-en.sqlite"
            reverse = root / "wiktionary-en-es.sqlite"
            forward.write_text("forward", encoding="utf-8")
            reverse.write_text("reverse", encoding="utf-8")
            benchmark_json.write_text(
                json.dumps(
                    {
                        "dataset_path": str(dataset),
                        "profile_id": "default",
                        "sweep": {
                            "preset": None,
                            "pair_filter": ["en-es"],
                            "configuration_count": 144,
                        },
                        "pairs": {
                            "en-es": {
                                "case_count": 2,
                                "resources": {
                                    "translation_dict_path": str(forward),
                                    "reverse_translation_dict_path": str(reverse),
                                    "checksums": {
                                        "translation_dict_sha256": None,
                                        "reverse_translation_dict_sha256": None,
                                        "jmdict_sha256": None,
                                    },
                                },
                                "word_package_snapshot": {"casa": None},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            manifest_path = export_bundle(
                benchmark_json=benchmark_json,
                output_dir=root / "bundle",
                pair_filter=None,
                force=False,
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["preset"]["name"], "canonical_cli_defaults")
            self.assertEqual(manifest["preset"]["args"], [])
            readme_text = (root / "bundle" / "README.md").read_text(encoding="utf-8")
            self.assertIn("canonical_cli_defaults", readme_text)
            self.assertIn("wiktionary-es-en.sqlite", readme_text)

    def test_validate_bundle_accepts_exported_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "dataset.json"
            dataset.write_text('{"cases":[]}', encoding="utf-8")
            benchmark_json = root / "benchmark.json"
            forward = root / "forward.sqlite"
            forward.write_text("forward", encoding="utf-8")
            checksum = "sha256:" + __import__("hashlib").sha256(b"forward").hexdigest()
            benchmark_json.write_text(
                json.dumps(
                    {
                        "dataset_path": str(dataset),
                        "profile_id": "default",
                        "sweep": {
                            "preset": {
                                "name": "tiny",
                                "description": "tiny preset",
                                "args": ["--pairs", "en-es"],
                            }
                        },
                        "pairs": {
                            "en-es": {
                                "case_count": 1,
                                "resources": {
                                    "translation_dict_path": str(forward),
                                    "reverse_translation_dict_path": None,
                                    "checksums": {
                                        "translation_dict_sha256": checksum,
                                        "reverse_translation_dict_sha256": None,
                                        "jmdict_sha256": None,
                                    },
                                },
                                "word_package_snapshot": {"casa": None},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            export_bundle(
                benchmark_json=benchmark_json,
                output_dir=root / "bundle",
                pair_filter=None,
                force=False,
            )

            manifest = validate_bundle(root / "bundle")

            self.assertEqual(manifest["bundle_version"], 1)

    def test_export_bundle_materializes_directory_backed_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset_dir = root / "rulegen_benchmark_cases"
            dataset_dir.mkdir()
            (dataset_dir / "en_de.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "pair": "en-de",
                        "cases": [
                            {
                                "case_id": "en-de:Haus",
                                "target": "Haus",
                                "expected_any": ["house"],
                                "expected_top1_any": ["house"],
                                "forbidden_top1": [],
                                "forbidden_any": [],
                                "tier": "smoke",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (dataset_dir / "en_es.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "pair": "en-es",
                        "cases": [
                            {
                                "case_id": "en-es:casa",
                                "target": "casa",
                                "expected_any": ["house"],
                                "expected_top1_any": ["house"],
                                "forbidden_top1": [],
                                "forbidden_any": [],
                                "tier": "smoke",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            benchmark_json = root / "benchmark.json"
            forward = root / "freedict-de-en.sqlite"
            reverse = root / "freedict-en-de.sqlite"
            forward.write_text("forward", encoding="utf-8")
            reverse.write_text("reverse", encoding="utf-8")
            benchmark_json.write_text(
                json.dumps(
                    {
                        "dataset_path": str(dataset_dir),
                        "profile_id": "default",
                        "sweep": {
                            "preset": {
                                "name": "en_de_canonical_matrix",
                                "description": "test preset",
                                "args": ["--pairs", "en-de"],
                            }
                        },
                        "pairs": {
                            "en-de": {
                                "case_count": 1,
                                "resources": {
                                    "translation_dict_path": str(forward),
                                    "reverse_translation_dict_path": str(reverse),
                                    "checksums": {
                                        "translation_dict_sha256": None,
                                        "reverse_translation_dict_sha256": None,
                                        "jmdict_sha256": None,
                                    },
                                },
                                "word_package_snapshot": {"Haus": None},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            manifest_path = export_bundle(
                benchmark_json=benchmark_json,
                output_dir=root / "bundle",
                pair_filter=None,
                force=False,
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            dataset_bundle_path = root / "bundle" / str(manifest["dataset_path"])
            dataset_payload = json.loads(dataset_bundle_path.read_text(encoding="utf-8"))
            self.assertEqual(dataset_payload["pairs"], ["en-de"])
            self.assertEqual(len(dataset_payload["cases"]), 1)
            self.assertEqual(dataset_payload["cases"][0]["pair"], "en-de")

    def test_build_bundle_run_argv_uses_bundle_relative_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp)
            manifest = {
                "dataset_path": "inputs/rulegen_benchmark_cases.json",
                "word_package_snapshot_path": "inputs/word_package_snapshots.json",
                "pair_names": ["en-es"],
                "preset": {
                    "name": "tiny",
                    "description": "tiny preset",
                    "args": ["--max-configurations", "8"],
                },
                "pairs": {
                    "en-es": {
                        "resources": {
                            "translation_dict_path": "resources/en-es/wiktionary-es-en.sqlite",
                            "reverse_translation_dict_path": "resources/en-es/wiktionary-en-es.sqlite",
                            "checksums": {},
                        }
                    }
                },
            }

            argv = build_bundle_run_argv(
                bundle_dir=bundle_dir,
                manifest=manifest,
                selected_pairs=["en-es"],
                json_output=bundle_dir / "out.json",
                markdown_output=bundle_dir / "out.md",
                html_output=bundle_dir / "out.html",
            )

            argv_text = " ".join(argv)
            self.assertIn("--word-package-snapshot-json", argv_text)
            self.assertIn("--translation-dict-en-es", argv_text)
            self.assertIn("--translation-dict-es-en", argv_text)
            self.assertIn("--pairs en-es", argv_text)

    def test_build_bundle_run_argv_accepts_empty_default_args(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp)
            manifest = {
                "dataset_path": "inputs/rulegen_benchmark_cases.json",
                "word_package_snapshot_path": "inputs/word_package_snapshots.json",
                "pair_names": ["en-es"],
                "preset": {
                    "name": "canonical_cli_defaults",
                    "description": "default replay",
                    "args": [],
                    "mode": "cli_defaults",
                },
                "pairs": {
                    "en-es": {
                        "resources": {
                            "translation_dict_path": "resources/en-es/wiktionary-es-en.sqlite",
                            "reverse_translation_dict_path": "resources/en-es/wiktionary-en-es.sqlite",
                            "checksums": {},
                        }
                    }
                },
            }

            argv = build_bundle_run_argv(
                bundle_dir=bundle_dir,
                manifest=manifest,
                selected_pairs=["en-es"],
                json_output=bundle_dir / "out.json",
                markdown_output=bundle_dir / "out.md",
                html_output=bundle_dir / "out.html",
            )

            self.assertIn("--dataset", argv)
            self.assertIn("--word-package-snapshot-json", argv)
            self.assertIn("--pairs", argv)


if __name__ == "__main__":
    unittest.main()
