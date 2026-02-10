from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs.signal_queue import (  # noqa: E402
    SIGNAL_EXPOSURE,
    SIGNAL_FEEDBACK,
    SrsSignalEvent,
    append_signal_event,
    load_signal_events,
    summarize_signal_events,
)


class TestSrsSignalQueue(unittest.TestCase):
    def test_append_and_load_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "srs_signal_queue.json"
            append_signal_event(
                path,
                SrsSignalEvent(
                    event_type=SIGNAL_FEEDBACK,
                    pair="en-ja",
                    lemma="cat",
                    source_type="extension",
                    rating="good",
                ),
            )
            events = load_signal_events(path)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].event_type, SIGNAL_FEEDBACK)
            self.assertEqual(events[0].pair, "en-ja")
            self.assertEqual(events[0].lemma, "cat")

    def test_summary_scopes_by_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "srs_signal_queue.json"
            append_signal_event(
                path,
                SrsSignalEvent(
                    event_type=SIGNAL_FEEDBACK,
                    pair="en-ja",
                    lemma="cat",
                    source_type="extension",
                    rating="good",
                ),
            )
            append_signal_event(
                path,
                SrsSignalEvent(
                    event_type=SIGNAL_EXPOSURE,
                    pair="en-ja",
                    lemma="dog",
                    source_type="extension",
                ),
            )
            append_signal_event(
                path,
                SrsSignalEvent(
                    event_type=SIGNAL_EXPOSURE,
                    pair="en-en",
                    lemma="bird",
                    source_type="extension",
                ),
            )

            scoped = summarize_signal_events(path, pair="en-ja")
            self.assertEqual(scoped["event_count"], 2)
            self.assertEqual(scoped["event_types"].get(SIGNAL_FEEDBACK), 1)
            self.assertEqual(scoped["event_types"].get(SIGNAL_EXPOSURE), 1)
            self.assertEqual(scoped["unique_lemmas"], 2)


if __name__ == "__main__":
    unittest.main()
