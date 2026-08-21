from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_ROOT = REPO_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.srs.topic_overlay import (  # noqa: E402
    resolve_preview_profile_topic_overlay,
)


class TestSrsTopicPackagedOverlayResources(unittest.TestCase):
    def test_preview_resolver_falls_back_to_packaged_topic_overlays(self) -> None:
        cases = (
            ("en-ja", "computing_internet", "en_ja"),
            ("en-es", "animals", "en_es"),
            ("en-de", "animals", "en_de"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = SimpleNamespace(srs_dir=root / "srs", data_root=root / "data")
            for pair, topic, resource_dir in cases:
                with self.subTest(pair=pair):
                    payload, diagnostics = resolve_preview_profile_topic_overlay(
                        paths,
                        pair=pair,
                        profile_context={"interests": [topic]},
                    )

                    self.assertIsNotNone(payload)
                    self.assertEqual(diagnostics["status"], "active")
                    self.assertEqual(diagnostics["active_topics"], [topic])
                    self.assertIn(
                        f"core/lexishift_core/resources/srs/{resource_dir}/topic_overlays/",
                        str(diagnostics["source_path"]),
                    )

    def test_packaged_overlay_wins_over_unmarked_local_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = SimpleNamespace(srs_dir=root / "srs", data_root=root / "data")
            local_overlay = paths.srs_dir / "topic_overlays" / "stale-en-de-games.json"
            _write_topic_overlay(
                local_overlay,
                pair="en-de",
                topic="games",
                lemma="Altbestand",
                overlay_id="stale_local_overlay",
            )

            _payload, diagnostics = resolve_preview_profile_topic_overlay(
                paths,
                pair="en-de",
                profile_context={"interests": ["games"]},
            )

        self.assertEqual(diagnostics["status"], "active")
        self.assertIn(
            "core/lexishift_core/resources/srs/en_de/topic_overlays/",
            str(diagnostics["source_path"]),
        )

    def test_explicit_local_overlay_override_wins_over_packaged_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = SimpleNamespace(srs_dir=root / "srs", data_root=root / "data")
            local_overlay = paths.srs_dir / "topic_overlays" / "override-en-de-games.json"
            _write_topic_overlay(
                local_overlay,
                pair="en-de",
                topic="games",
                lemma="OverrideSpiel",
                overlay_id="explicit_local_override",
                runtime_precedence="override",
            )

            _payload, diagnostics = resolve_preview_profile_topic_overlay(
                paths,
                pair="en-de",
                profile_context={"interests": ["games"]},
            )

        self.assertEqual(diagnostics["status"], "active")
        self.assertEqual(diagnostics["source_path"], str(local_overlay))
        self.assertEqual(diagnostics["overlay_id"], "explicit_local_override")


def _write_topic_overlay(
    path: Path,
    *,
    pair: str,
    topic: str,
    lemma: str,
    overlay_id: str,
    runtime_precedence: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "ok",
        "overlay_id": overlay_id,
        "rows": [
            {
                "language_pair": pair,
                "lemma": lemma,
                "topic": topic,
                "membership": 1.0,
                "review_id": "unit",
                "confidence_label": "unit",
            }
        ],
    }
    if runtime_precedence:
        payload["overlay_policy"] = {"runtime_precedence": runtime_precedence}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
