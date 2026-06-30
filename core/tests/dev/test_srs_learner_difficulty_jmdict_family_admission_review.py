from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_jmdict_family_admission_review_en_ja import (  # noqa: E402
    build_pair_lookup,
    load_jmdict_families,
    pair_key,
)


class TestSrsLearnerDifficultyJmdictFamilyAdmissionReview(unittest.TestCase):
    def test_entry_family_uses_jmdict_ent_seq_for_alt_forms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            path.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<JMdict>
  <entry>
    <ent_seq>1000001</ent_seq>
    <k_ele><keb>始め</keb></k_ele>
    <k_ele><keb>初め</keb></k_ele>
    <r_ele><reb>はじめ</reb></r_ele>
    <sense><gloss>beginning</gloss></sense>
  </entry>
</JMdict>
""",
                encoding="utf-8",
            )

            families = load_jmdict_families(path)
            lookup = build_pair_lookup(families)

        self.assertEqual(len(families), 1)
        self.assertEqual(lookup[pair_key("始め", "はじめ")][0].ent_seq, "1000001")
        self.assertEqual(lookup[pair_key("初め", "はじめ")][0].ent_seq, "1000001")

    def test_reading_restriction_prevents_cross_form_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            path.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<JMdict>
  <entry>
    <ent_seq>1000002</ent_seq>
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

            lookup = build_pair_lookup(load_jmdict_families(path))

        self.assertIn(pair_key("上手", "じょうず"), lookup)
        self.assertNotIn(pair_key("下手", "じょうず"), lookup)

    def test_ambiguous_reading_form_keeps_multiple_entries_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            path.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<JMdict>
  <entry>
    <ent_seq>1000003</ent_seq>
    <k_ele><keb>橋</keb></k_ele>
    <r_ele><reb>はし</reb></r_ele>
    <sense><gloss>bridge</gloss></sense>
  </entry>
  <entry>
    <ent_seq>1000004</ent_seq>
    <k_ele><keb>箸</keb></k_ele>
    <r_ele><reb>はし</reb></r_ele>
    <sense><gloss>chopsticks</gloss></sense>
  </entry>
</JMdict>
""",
                encoding="utf-8",
            )

            lookup = build_pair_lookup(load_jmdict_families(path))

        self.assertEqual(
            sorted(match.ent_seq for match in lookup[pair_key("はし", "はし")]),
            ["1000003", "1000004"],
        )


if __name__ == "__main__":
    unittest.main()
