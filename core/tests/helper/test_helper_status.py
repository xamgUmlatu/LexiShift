from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lexishift_core.helper.status import HelperStatus, load_status, save_status


class TestHelperStatus(unittest.TestCase):
    def test_load_status_returns_default_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status = load_status(Path(tmp) / "missing.json")

        self.assertEqual(status, HelperStatus())

    def test_load_status_returns_default_for_empty_or_corrupt_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "srs_status.json"

            status_path.write_text("", encoding="utf-8")
            self.assertEqual(load_status(status_path), HelperStatus())

            status_path.write_text("{", encoding="utf-8")
            self.assertEqual(load_status(status_path), HelperStatus())

    def test_load_status_returns_default_for_invalid_status_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "srs_status.json"
            status_path.write_text('{"last_rule_count": "not-an-int"}', encoding="utf-8")

            status = load_status(status_path)

        self.assertEqual(status, HelperStatus())

    def test_save_status_writes_atomically_and_cleans_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "nested" / "srs_status.json"
            save_status(
                HelperStatus(last_pair="en-de", last_rule_count=117, last_target_count=40),
                status_path,
            )

            status = load_status(status_path)
            temp_files = list(status_path.parent.glob(".srs_status.json.*.tmp"))

        self.assertEqual(status.last_pair, "en-de")
        self.assertEqual(status.last_rule_count, 117)
        self.assertEqual(status.last_target_count, 40)
        self.assertEqual(temp_files, [])


if __name__ == "__main__":
    unittest.main()
