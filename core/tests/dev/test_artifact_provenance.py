from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import (  # noqa: E402
    attach_provenance_to_npz_metadata,
    build_artifact_provenance,
    validate_artifact_freshness,
)


class TestArtifactProvenance(unittest.TestCase):
    def test_fresh_json_artifact_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            producer = _write(root / "producer.py", "print('producer')\n")
            dependency = _write(root / "dependency.py", "VALUE = 1\n")
            source_input = _write(root / "input.json", '{"ok": true}\n')
            artifact = root / "docs" / "test_outputs" / "artifact.json"
            provenance = build_artifact_provenance(
                producer_script=producer,
                code_paths={"dependency": dependency},
                input_paths={"source_input": source_input},
                argv=("producer.py", "--flag"),
                project_root=root,
            )
            _write_json(artifact, {"schema_version": 1, "provenance": provenance})

            result = validate_artifact_freshness(artifact, project_root=root)

            self.assertTrue(result["fresh"])
            self.assertEqual(result["status"], "fresh")

    def test_input_mutation_marks_artifact_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            producer = _write(root / "producer.py", "print('producer')\n")
            source_input = _write(root / "input.json", '{"ok": true}\n')
            artifact = root / "docs" / "test_outputs" / "artifact.json"
            provenance = build_artifact_provenance(
                producer_script=producer,
                input_paths={"source_input": source_input},
                argv=("producer.py",),
                project_root=root,
            )
            _write_json(artifact, {"schema_version": 1, "provenance": provenance})
            source_input.write_text('{"ok": false}\n', encoding="utf-8")

            result = validate_artifact_freshness(artifact, project_root=root)

            self.assertFalse(result["fresh"])
            self.assertIn("source_input:sha256_changed", result["failures"])

    def test_missing_provenance_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "docs" / "test_outputs" / "artifact.json"
            _write_json(artifact, {"schema_version": 1})

            result = validate_artifact_freshness(artifact, project_root=root)

            self.assertFalse(result["fresh"])
            self.assertIn("missing_provenance", result["failures"])

    def test_generated_input_without_provenance_marks_parent_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            producer = _write(root / "producer.py", "print('producer')\n")
            generated_input = root / "docs" / "test_outputs" / "upstream.json"
            _write_json(generated_input, {"schema_version": 1})
            artifact = root / "docs" / "test_outputs" / "artifact.json"
            provenance = build_artifact_provenance(
                producer_script=producer,
                input_paths={"upstream": generated_input},
                argv=("producer.py",),
                project_root=root,
            )
            _write_json(artifact, {"schema_version": 1, "provenance": provenance})

            result = validate_artifact_freshness(artifact, project_root=root)

            self.assertFalse(result["fresh"])
            self.assertTrue(
                any("upstream:input_artifact_stale" in item for item in result["failures"])
            )

    def test_npz_metadata_provenance_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            producer = _write(root / "producer.py", "print('producer')\n")
            provenance = build_artifact_provenance(
                producer_script=producer,
                argv=("producer.py",),
                project_root=root,
            )
            npz_path = root / "docs" / "test_outputs" / "matrix.npz"
            npz_path.parent.mkdir(parents=True, exist_ok=True)
            arrays = attach_provenance_to_npz_metadata(
                {"metadata_json": json.dumps({"schema_version": 1}), "values": [1, 2, 3]},
                provenance,
            )
            np.savez_compressed(npz_path, **arrays)

            result = validate_artifact_freshness(npz_path, project_root=root)

            self.assertTrue(result["fresh"])


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _write_json(path: Path, payload: object) -> Path:
    return _write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    unittest.main()
