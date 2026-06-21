from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_source_pair_validation_en_ja import (  # noqa: E402
    PairKey,
    collect_source_evidence,
    evaluate_label_row,
    normalize_reading,
)


class TestSrsLearnerDifficultySourcePairValidation(unittest.TestCase):
    def test_collect_source_evidence_respects_reading_restrictions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "JMdict_e"
            xml_path.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<JMdict>
  <entry>
    <k_ele><keb>上手</keb></k_ele>
    <k_ele><keb>下手</keb></k_ele>
    <r_ele><reb>じょうず</reb><re_restr>上手</re_restr></r_ele>
    <r_ele><reb>へた</reb><re_restr>下手</re_restr></r_ele>
    <sense><gloss>skillful</gloss></sense>
  </entry>
</JMdict>
""",
                encoding="utf-8",
            )
            exact = PairKey("上手", "じょうず", normalize_reading("じょうず"))
            restricted = PairKey("下手", "じょうず", normalize_reading("じょうず"))

            evidence = collect_source_evidence(
                xml_path,
                pairs=(exact, restricted),
                source="jmdict",
                include_name_types=False,
            )

            self.assertEqual(evidence[exact].status(), "exact")
            self.assertEqual(evidence[restricted].status(), "restriction_mismatch")

    def test_collect_source_evidence_accepts_katakana_surface_with_hiragana_reading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "JMdict_e"
            xml_path.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<JMdict>
  <entry>
    <r_ele><reb>ダウン</reb></r_ele>
    <sense><gloss>down</gloss></sense>
  </entry>
</JMdict>
""",
                encoding="utf-8",
            )
            pair = PairKey("ダウン", "だうん", normalize_reading("だうん"))

            evidence = collect_source_evidence(
                xml_path,
                pairs=(pair,),
                source="jmdict",
                include_name_types=False,
            )

            self.assertEqual(evidence[pair].status(), "exact")

    def test_evaluate_label_row_routes_name_exact_separately_from_vocab_exact(self) -> None:
        pair = PairKey("山田", "やまだ", normalize_reading("やまだ"))
        with tempfile.TemporaryDirectory() as tmp:
            empty_jmdict = Path(tmp) / "JMdict_e"
            jmnedict = Path(tmp) / "JMnedict.xml"
            empty_jmdict.write_text("<JMdict></JMdict>\n", encoding="utf-8")
            jmnedict.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<JMnedict>
  <entry>
    <k_ele><keb>山田</keb></k_ele>
    <r_ele><reb>やまだ</reb></r_ele>
    <trans><name_type>surname</name_type><trans_det>Yamada</trans_det></trans>
  </entry>
</JMnedict>
""",
                encoding="utf-8",
            )
            jmdict_evidence = collect_source_evidence(
                empty_jmdict,
                pairs=(pair,),
                source="jmdict",
                include_name_types=False,
            )
            jmnedict_evidence = collect_source_evidence(
                jmnedict,
                pairs=(pair,),
                source="jmnedict",
                include_name_types=True,
            )

        row = evaluate_label_row(
            {
                "lemma": "山田",
                "reading": "やまだ",
                "label": "山田/やまだ",
                "has_reading": True,
                "target": "scalar_vocab",
            },
            jmdict_evidence=jmdict_evidence,
            jmnedict_evidence=jmnedict_evidence,
        )

        self.assertEqual(row["primary_pair_status"], "jmnedict_exact_name")
        self.assertEqual(row["gate_recommendation"], "name_or_entity_lane_review")


if __name__ == "__main__":
    unittest.main()
