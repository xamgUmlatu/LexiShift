from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_ROOT = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from srs_browsing_admission_saved_page_pack_en_ja import build_report  # noqa: E402


class TestSrsBrowsingAdmissionSavedPagePackEnJa(unittest.TestCase):
    def test_saved_pages_become_reading_aware_aggregate_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_json = root / "source.json"
            target_html = root / "target.html"
            manifest_json = root / "manifest.json"
            jmdict_path = root / "JMdict_e"

            source_json.write_text(
                json.dumps(
                    {
                        "title": "Rabbit",
                        "description": "Small mammal.",
                        "extract": "This field is intentionally unused.",
                    }
                ),
                encoding="utf-8",
            )
            target_html.write_text(
                (
                    "<html><body>"
                    "<ruby><rb>注文</rb><rp>（</rp><rt>ちゅうもん</rt><rp>）</rp></ruby>"
                    "の多い"
                    "<ruby><rb>料理店</rb><rp>（</rp><rt>りょうりてん</rt><rp>）</rp></ruby>"
                    "</body></html>"
                ),
                encoding="utf-8",
            )
            jmdict_path.write_text(
                """<JMdict>
<entry><k_ele><keb>兎</keb></k_ele><r_ele><reb>うさぎ</reb></r_ele><sense><gloss>rabbit</gloss></sense></entry>
<entry><k_ele><keb>哺乳類</keb></k_ele><r_ele><reb>ほにゅうるい</reb></r_ele><sense><gloss>mammal</gloss></sense></entry>
<entry><k_ele><keb>注文</keb></k_ele><r_ele><reb>ちゅうもん</reb></r_ele><sense><gloss>order</gloss></sense></entry>
<entry><k_ele><keb>料理店</keb></k_ele><r_ele><reb>りょうりてん</reb></r_ele><sense><gloss>restaurant</gloss></sense></entry>
</JMdict>
""",
                encoding="utf-8",
            )
            manifest_json.write_text(
                json.dumps(
                    {
                        "pair": "en-ja",
                        "documents": [
                            {
                                "document_id": "source",
                                "side": "source",
                                "format": "json",
                                "path": str(source_json),
                                "encoding": "utf-8",
                                "text_fields": ["title", "description"],
                            },
                            {
                                "document_id": "target",
                                "side": "target",
                                "format": "html",
                                "path": str(target_html),
                                "encoding": "utf-8",
                            },
                        ],
                        "expectations": {
                            "min_source_mapping_signals": 1,
                            "min_target_surface_signals": 1,
                            "required_observation_sources": [
                                "source_mapping",
                                "target_surface",
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(
                manifest_json=manifest_json,
                jmdict_path=jmdict_path,
                generated_at="2026-07-03T00:00:00Z",
            )

        self.assertEqual(report["status"], "pass")
        target_keys = {row["target_key"] for row in report["signals"]["top"]}
        self.assertIn("兎|うさぎ", target_keys)
        self.assertIn("注文|ちゅうもん", target_keys)
        self.assertIn("料理店|りょうりてん", target_keys)
        aggregate_rows = report["helper_ingest"]["aggregate_store"]["top_items"]
        aggregate_keys = {row["target_key"] for row in aggregate_rows}
        self.assertIn("注文|ちゅうもん", aggregate_keys)
        self.assertFalse(report["privacy"]["aggregate_report_stores_raw_text"])
        self.assertFalse(report["helper_ingest"]["runtime_srs_mutation"])


if __name__ == "__main__":
    unittest.main()
