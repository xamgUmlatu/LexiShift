from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

CORE_ROOT = Path(__file__).resolve().parents[3] / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs.admission_suppression import (  # noqa: E402
    active_suppressed_lemmas,
    load_admission_suppression_store,
)
from lexishift_core.srs.browsing_admission import load_browsing_signal_store  # noqa: E402


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


class TestHelperBrowsingAdmissionEntrypoints(unittest.TestCase):
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
