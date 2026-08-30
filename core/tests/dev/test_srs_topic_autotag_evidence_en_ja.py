from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_autotag_evidence_en_ja import build_report, render_markdown  # noqa: E402


class SrsTopicAutotagEvidenceEnJaTests(unittest.TestCase):
    def test_jmdict_field_and_gloss_sources_preserve_exact_item_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            jmdict_path = root / "JMdict_e"
            taxonomy_json = root / "taxonomy.json"
            policy_json = REPO_ROOT / "docs" / "test_inputs" / "srs_topic_autotag_policy_en_ja.json"
            _write_candidates(
                candidates_csv,
                [
                    ("1", "鮭", "さけ", "0.32"),
                    ("2", "県", "けん", "0.10"),
                    ("3", "漫画", "まんが", "0.28"),
                ],
            )
            _write_jmdict(
                jmdict_path,
                """<?xml version="1.0" encoding="UTF-8"?>
<JMdict>
  <entry>
    <ent_seq>1</ent_seq>
    <k_ele><keb>鮭</keb></k_ele>
    <r_ele><reb>さけ</reb></r_ele>
    <sense><field>zoology</field><gloss>salmon</gloss><gloss>fish</gloss></sense>
  </entry>
  <entry>
    <ent_seq>2</ent_seq>
    <k_ele><keb>犬</keb></k_ele>
    <r_ele><reb>けん</reb></r_ele>
    <sense><field>zoology</field><gloss>dog</gloss></sense>
  </entry>
  <entry>
    <ent_seq>3</ent_seq>
    <k_ele><keb>漫画</keb></k_ele>
    <r_ele><reb>まんが</reb></r_ele>
    <sense><field>manga</field><gloss>manga</gloss><gloss>comic</gloss></sense>
  </entry>
</JMdict>
""",
            )
            _write_taxonomy(taxonomy_json)

            report = build_report(
                candidates_csv=candidates_csv,
                jmdict_path=jmdict_path,
                taxonomy_json=taxonomy_json,
                policy_json=policy_json,
                sources=("jmdict_field_direct", "jmdict_gloss_keyword"),
                top_n=10,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "ok")
        rows = report["evidence_rows"]
        row_keys = {(row["lemma"], row["source"], row["topic"]) for row in rows}
        self.assertIn(("鮭", "jmdict_field_direct", "animals"), row_keys)
        self.assertIn(("鮭", "jmdict_gloss_keyword", "animals"), row_keys)
        self.assertIn(("漫画", "jmdict_field_direct", "anime_manga_pop_culture"), row_keys)
        self.assertNotIn(("県", "jmdict_field_direct", "animals"), row_keys)
        self.assertTrue(all(row["lemma"] != "県" for row in rows))

        markdown = render_markdown(report)
        self.assertIn("en-ja SRS Topic Autotag Evidence", markdown)
        self.assertIn("鮭", markdown)

    def test_kana_only_jmdict_matches_preserve_kana_surface_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            jmdict_path = root / "JMdict_e"
            taxonomy_json = root / "taxonomy.json"
            policy_json = REPO_ROOT / "docs" / "test_inputs" / "srs_topic_autotag_policy_en_ja.json"
            _write_candidates(
                candidates_csv,
                [
                    ("1", "ちゃんと", "ちゃんと", "0.18"),
                    ("2", "チャント", "ちゃんと", "0.42"),
                    ("3", "デモ", "でも", "0.30"),
                    ("4", "でも", "でも", "0.02"),
                ],
            )
            _write_jmdict(
                jmdict_path,
                """<?xml version="1.0" encoding="UTF-8"?>
<JMdict>
  <entry>
    <ent_seq>10</ent_seq>
    <r_ele><reb>チャント</reb></r_ele>
    <sense><gloss>chant (in a sports game, etc.)</gloss><gloss>cheer</gloss></sense>
  </entry>
  <entry>
    <ent_seq>11</ent_seq>
    <r_ele><reb>デモ</reb></r_ele>
    <sense><field>law</field><gloss>demonstration</gloss><gloss>protest</gloss></sense>
  </entry>
  <entry>
    <ent_seq>12</ent_seq>
    <r_ele><reb>でも</reb></r_ele>
    <sense><gloss>but</gloss><gloss>however</gloss></sense>
  </entry>
</JMdict>
""",
            )
            _write_taxonomy(taxonomy_json)

            report = build_report(
                candidates_csv=candidates_csv,
                jmdict_path=jmdict_path,
                taxonomy_json=taxonomy_json,
                policy_json=policy_json,
                sources=("jmdict_field_direct", "jmdict_gloss_keyword"),
                top_n=10,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        row_keys = {(row["lemma"], row["source"], row["topic"]) for row in report["evidence_rows"]}
        self.assertNotIn(("ちゃんと", "jmdict_gloss_keyword", "games"), row_keys)
        self.assertIn(("チャント", "jmdict_gloss_keyword", "games"), row_keys)
        self.assertIn(("デモ", "jmdict_field_direct", "law_politics_civics"), row_keys)
        self.assertNotIn(("でも", "jmdict_field_direct", "law_politics_civics"), row_keys)

    def test_wordnet_gloss_bridge_uses_installed_lexname_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            jmdict_path = root / "JMdict_e"
            taxonomy_json = root / "taxonomy.json"
            wordnet_root = root / "wordnet"
            policy_json = REPO_ROOT / "docs" / "test_inputs" / "srs_topic_autotag_policy_en_ja.json"
            wordnet_root.mkdir()
            _write_candidates(candidates_csv, [("1", "サーモン", "さーもん", "0.42")])
            _write_jmdict(
                jmdict_path,
                """<?xml version="1.0" encoding="UTF-8"?>
<JMdict>
  <entry>
    <ent_seq>10</ent_seq>
    <k_ele><keb>サーモン</keb></k_ele>
    <r_ele><reb>サーモン</reb></r_ele>
    <sense><gloss>salmon</gloss></sense>
  </entry>
</JMdict>
""",
            )
            _write_taxonomy(taxonomy_json)
            (wordnet_root / "noun.food.json").write_text(
                json.dumps({"00000001-n": {"members": ["salmon"], "partOfSpeech": "n"}}),
                encoding="utf-8",
            )
            (wordnet_root / "entries-s.json").write_text(
                json.dumps(
                    {
                        "salmon": {
                            "n": {
                                "sense": [
                                    {
                                        "id": "salmon%1:13:00::",
                                        "synset": "00000001-n",
                                    }
                                ]
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(
                candidates_csv=candidates_csv,
                jmdict_path=jmdict_path,
                taxonomy_json=taxonomy_json,
                policy_json=policy_json,
                wordnet_root=wordnet_root,
                sources=("english_wordnet_gloss_bridge",),
                top_n=10,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["source_summary"]["english_wordnet_gloss_bridge"]["row_count"], 1)
        row = report["evidence_rows"][0]
        self.assertEqual(row["lemma"], "サーモン")
        self.assertEqual(row["topic"], "food_cooking")
        self.assertEqual(row["extra"]["wordnet_gloss_key"], "salmon")

    def test_wikipedia_dump_rejects_surface_only_multi_reading_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            taxonomy_json = root / "taxonomy.json"
            policy_json = REPO_ROOT / "docs" / "test_inputs" / "srs_topic_autotag_policy_en_ja.json"
            page_sql = root / "page.sql.gz"
            redirect_sql = root / "redirect.sql.gz"
            categorylinks_sql = root / "categorylinks.sql.gz"
            category_sql = root / "category.sql.gz"
            linktarget_sql = root / "linktarget.sql.gz"
            _write_candidates(
                candidates_csv,
                [
                    ("1", "今日", "きょう", "0.04"),
                    ("2", "今日", "こんにち", "0.24"),
                    ("3", "漫画", "まんが", "0.12"),
                ],
            )
            _write_taxonomy(taxonomy_json)
            _write_gzip_text(
                page_sql,
                "INSERT INTO `page` VALUES (1,0,'今日',0),(2,0,'漫画',0);\n",
            )
            _write_gzip_text(redirect_sql, "")
            _write_gzip_text(category_sql, "")
            _write_gzip_text(
                categorylinks_sql,
                (
                    "INSERT INTO `categorylinks` VALUES "
                    "(1,'漫画','',0,0,'page',100),(2,'漫画','',0,0,'page',100);\n"
                ),
            )
            _write_gzip_text(linktarget_sql, "INSERT INTO `linktarget` VALUES (100,14,'漫画');\n")

            report = build_report(
                candidates_csv=candidates_csv,
                taxonomy_json=taxonomy_json,
                policy_json=policy_json,
                sources=("jawikipedia_dump_category",),
                jawiki_page_sql_gz=page_sql,
                jawiki_redirect_sql_gz=redirect_sql,
                jawiki_categorylinks_sql_gz=categorylinks_sql,
                jawiki_category_sql_gz=category_sql,
                jawiki_linktarget_sql_gz=linktarget_sql,
                top_n=10,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        row_keys = {(row["lemma"], row["reading"], row["topic"]) for row in report["evidence_rows"]}
        self.assertNotIn(("今日", "きょう", "anime_manga_pop_culture"), row_keys)
        self.assertNotIn(("今日", "こんにち", "anime_manga_pop_culture"), row_keys)
        self.assertIn(("漫画", "まんが", "anime_manga_pop_culture"), row_keys)
        self.assertTrue(
            any(
                "rejected_ambiguous_surface_only" in str(finding.get("message") or "")
                for finding in report["findings"]
            )
        )

    def test_wikipedia_dump_rejects_low_score_uncorroborated_category_topics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            taxonomy_json = root / "taxonomy.json"
            policy_json = REPO_ROOT / "docs" / "test_inputs" / "srs_topic_autotag_policy_en_ja.json"
            page_sql = root / "page.sql.gz"
            redirect_sql = root / "redirect.sql.gz"
            categorylinks_sql = root / "categorylinks.sql.gz"
            category_sql = root / "category.sql.gz"
            linktarget_sql = root / "linktarget.sql.gz"
            _write_candidates(
                candidates_csv,
                [
                    ("1", "大勢", "おおぜい", "0.10"),
                    ("2", "例えば", "たとえば", "0.13"),
                    ("3", "スポーツ", "すぽーつ", "0.06"),
                    ("4", "漫画", "まんが", "0.12"),
                    ("5", "茶色", "ちゃいろ", "0.11"),
                    ("6", "食べる", "たべる", "0.03"),
                ],
            )
            _write_taxonomy(taxonomy_json)
            _write_gzip_text(
                page_sql,
                "INSERT INTO `page` VALUES "
                "(1,0,'大勢',0),(2,0,'例えば',0),(3,0,'スポーツ',0),(4,0,'漫画',0),"
                "(5,0,'茶色',0),(6,0,'食べる',0);\n",
            )
            _write_gzip_text(redirect_sql, "")
            _write_gzip_text(category_sql, "")
            _write_gzip_text(
                categorylinks_sql,
                (
                    "INSERT INTO `categorylinks` VALUES "
                    "(1,'日本の野球選手','',0,0,'page',100),"
                    "(1,'兵庫県出身のスポーツ選手','',0,0,'page',101),"
                    "(2,'アニメ映画挿入歌','',0,0,'page',102),"
                    "(2,'花譜の楽曲','',0,0,'page',103),"
                    "(3,'スポーツ','',0,0,'page',104),"
                    "(3,'ゲーム','',0,0,'page',105),"
                    "(4,'漫画','',0,0,'page',106),"
                    "(5,'茶','',0,0,'page',107),"
                    "(6,'飲食','',0,0,'page',108);\n"
                ),
            )
            _write_gzip_text(
                linktarget_sql,
                "INSERT INTO `linktarget` VALUES "
                "(100,14,'日本の野球選手'),"
                "(101,14,'兵庫県出身のスポーツ選手'),"
                "(102,14,'アニメ映画挿入歌'),"
                "(103,14,'花譜の楽曲'),"
                "(104,14,'スポーツ'),"
                "(105,14,'ゲーム'),"
                "(106,14,'漫画'),"
                "(107,14,'茶'),"
                "(108,14,'飲食');\n",
            )

            report = build_report(
                candidates_csv=candidates_csv,
                taxonomy_json=taxonomy_json,
                policy_json=policy_json,
                sources=("jawikipedia_dump_category",),
                jawiki_page_sql_gz=page_sql,
                jawiki_redirect_sql_gz=redirect_sql,
                jawiki_categorylinks_sql_gz=categorylinks_sql,
                jawiki_category_sql_gz=category_sql,
                jawiki_linktarget_sql_gz=linktarget_sql,
                top_n=10,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        row_keys = {
            (row["lemma"], row["reading"], row["topic"], row["source_label"])
            for row in report["evidence_rows"]
        }
        self.assertNotIn(("大勢", "おおぜい", "sports_fitness", "スポーツ"), row_keys)
        self.assertNotIn(("例えば", "たとえば", "anime_manga_pop_culture", "アニメ"), row_keys)
        self.assertNotIn(("例えば", "たとえば", "plants_nature", "花"), row_keys)
        self.assertNotIn(("スポーツ", "すぽーつ", "games", "ゲーム"), row_keys)
        self.assertNotIn(("茶色", "ちゃいろ", "food_cooking", "茶"), row_keys)
        self.assertIn(("スポーツ", "すぽーつ", "sports_fitness", "スポーツ"), row_keys)
        self.assertIn(("漫画", "まんが", "anime_manga_pop_culture", "漫画"), row_keys)
        self.assertIn(("食べる", "たべる", "food_cooking", "飲食"), row_keys)

    def test_kaikki_topic_uses_entry_reading_to_rescue_one_multi_reading_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            taxonomy_json = root / "taxonomy.json"
            policy_json = REPO_ROOT / "docs" / "test_inputs" / "srs_topic_autotag_policy_en_ja.json"
            kaikki_jsonl = root / "kaikki.jsonl.gz"
            _write_candidates(
                candidates_csv,
                [
                    ("1", "今日", "きょう", "0.04"),
                    ("2", "今日", "こんにち", "0.24"),
                    ("3", "漫画", "まんが", "0.12"),
                ],
            )
            _write_taxonomy(taxonomy_json)
            _write_gzip_text(
                kaikki_jsonl,
                "\n".join(
                    [
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "今日",
                                "pos": "noun",
                                "forms": [{"form": "今日", "ruby": [["今日", "きょう"]]}],
                                "senses": [{"topics": ["medicine"], "glosses": ["today"]}],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "今日",
                                "pos": "noun",
                                "senses": [{"topics": ["sports"], "glosses": ["today"]}],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "漫画",
                                "pos": "noun",
                                "forms": [{"form": "漫画", "ruby": [["漫", "まん"], ["画", "が"]]}],
                                "senses": [{"topics": ["manga"], "glosses": ["manga"]}],
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
            )

            report = build_report(
                candidates_csv=candidates_csv,
                taxonomy_json=taxonomy_json,
                policy_json=policy_json,
                sources=("kaikki_wiktionary_topic",),
                kaikki_ja_jsonl_gz=kaikki_jsonl,
                top_n=10,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        rows = report["evidence_rows"]
        row_keys = {(row["lemma"], row["reading"], row["topic"]) for row in rows}
        self.assertIn(("今日", "きょう", "medicine_health"), row_keys)
        self.assertNotIn(("今日", "こんにち", "medicine_health"), row_keys)
        self.assertNotIn(("今日", "きょう", "sports_fitness"), row_keys)
        self.assertNotIn(("今日", "こんにち", "sports_fitness"), row_keys)
        self.assertIn(("漫画", "まんが", "anime_manga_pop_culture"), row_keys)
        today_rows = [row for row in rows if row["lemma"] == "今日"]
        self.assertTrue(
            all(
                row["extra"]["reading_identity"] == "external_exact_source_reading"
                for row in today_rows
            )
        )

    def test_kaikki_generic_late_sense_topics_are_rejected_but_primary_topics_remain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            taxonomy_json = root / "taxonomy.json"
            policy_json = REPO_ROOT / "docs" / "test_inputs" / "srs_topic_autotag_policy_en_ja.json"
            kaikki_jsonl = root / "kaikki.jsonl.gz"
            _write_candidates(
                candidates_csv,
                [
                    ("1", "水", "みず", "0.04"),
                    ("2", "山", "やま", "0.05"),
                    ("3", "法律", "ほうりつ", "0.14"),
                    ("4", "旅行", "りょこう", "0.06"),
                    ("5", "漫画", "まんが", "0.12"),
                    ("6", "戦争", "せんそう", "0.13"),
                    ("7", "パン", "パン", "0.12"),
                ],
            )
            _write_taxonomy(taxonomy_json)
            _write_gzip_text(
                kaikki_jsonl,
                "\n".join(
                    [
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "水",
                                "pos": "noun",
                                "forms": [{"form": "水", "ruby": [["水", "みず"]]}],
                                "senses": [
                                    {"glosses": ["water"]},
                                    {"glosses": ["liquid"]},
                                    {
                                        "glosses": ["short for 水入り (mizuiri): halting"],
                                        "topics": ["sumo", "sports"],
                                    },
                                ],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "山",
                                "pos": "noun",
                                "forms": [{"form": "山", "ruby": [["山", "やま"]]}],
                                "senses": [
                                    {
                                        "glosses": ["a mountain"],
                                        "categories": [{"name": "Geography"}],
                                    },
                                    {"glosses": ["a pile"]},
                                    {
                                        "glosses": ["a wall, wall tile"],
                                        "topics": ["mahjong", "games"],
                                    },
                                ],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "法律",
                                "pos": "noun",
                                "forms": [
                                    {"form": "法律", "ruby": [["法", "ほう"], ["律", "りつ"]]}
                                ],
                                "senses": [{"glosses": ["law"], "categories": [{"name": "Law"}]}],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "旅行",
                                "pos": "noun",
                                "forms": [
                                    {"form": "旅行", "ruby": [["旅", "りょ"], ["行", "こう"]]}
                                ],
                                "senses": [
                                    {"glosses": ["travel"], "categories": [{"name": "Travel"}]}
                                ],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "漫画",
                                "pos": "noun",
                                "forms": [{"form": "漫画", "ruby": [["漫", "まん"], ["画", "が"]]}],
                                "senses": [
                                    {"glosses": ["drawing"]},
                                    {"glosses": ["caricature"]},
                                    {"glosses": ["a comic"], "categories": [{"name": "Comics"}]},
                                ],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "戦争",
                                "pos": "noun",
                                "forms": [
                                    {"form": "戦争", "ruby": [["戦", "せん"], ["争", "そう"]]}
                                ],
                                "senses": [
                                    {"glosses": ["war"]},
                                    {"glosses": ["war"], "topics": ["card-games", "games"]},
                                ],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "パン",
                                "pos": "name",
                                "forms": [{"form": "パン"}],
                                "senses": [{"glosses": ["Pan"], "topics": ["philosophy"]}],
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
            )

            report = build_report(
                candidates_csv=candidates_csv,
                taxonomy_json=taxonomy_json,
                policy_json=policy_json,
                sources=("kaikki_wiktionary_topic",),
                kaikki_ja_jsonl_gz=kaikki_jsonl,
                top_n=10,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        row_keys = {
            (row["lemma"], row["reading"], row["topic"], row["source_label"])
            for row in report["evidence_rows"]
        }
        self.assertNotIn(("水", "みず", "sports_fitness", "sumo"), row_keys)
        self.assertNotIn(("水", "みず", "sports_fitness", "sports"), row_keys)
        self.assertNotIn(("山", "やま", "games", "mahjong"), row_keys)
        self.assertNotIn(("山", "やま", "games", "games"), row_keys)
        self.assertNotIn(("戦争", "せんそう", "games", "card games"), row_keys)
        self.assertNotIn(("戦争", "せんそう", "games", "games"), row_keys)
        self.assertNotIn(("パン", "パン", "arts_literature_humanities", "philosophy"), row_keys)
        self.assertIn(("山", "やま", "travel_places_transport", "Geography"), row_keys)
        self.assertIn(("法律", "ほうりつ", "law_politics_civics", "Law"), row_keys)
        self.assertIn(("旅行", "りょこう", "travel_places_transport", "Travel"), row_keys)
        self.assertIn(("漫画", "まんが", "anime_manga_pop_culture", "Comics"), row_keys)
        self.assertTrue(
            any(
                finding.get("code") == "topic_evidence_quality_guards_applied"
                for finding in report["findings"]
            )
        )

    def test_kaikki_weak_broad_labels_require_topic_anchor_for_low_score_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            taxonomy_json = root / "taxonomy.json"
            policy_json = REPO_ROOT / "docs" / "test_inputs" / "srs_topic_autotag_policy_en_ja.json"
            kaikki_jsonl = root / "kaikki.jsonl.gz"
            _write_candidates(
                candidates_csv,
                [
                    ("1", "ポケット", "ポケット", "0.10"),
                    ("2", "売り場", "うりば", "0.15"),
                    ("3", "もしもし", "もしもし", "0.13"),
                    ("4", "エンジニア", "エンジニア", "0.12"),
                    ("5", "科学", "かがく", "0.13"),
                    ("6", "身体", "しんたい", "0.15"),
                    ("7", "布団", "ふとん", "0.15"),
                ],
            )
            _write_taxonomy(taxonomy_json)
            _write_gzip_text(
                kaikki_jsonl,
                "\n".join(
                    [
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "ポケット",
                                "pos": "noun",
                                "forms": [{"form": "ポケット"}],
                                "senses": [{"glosses": ["pocket"], "topics": ["business"]}],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "売り場",
                                "pos": "noun",
                                "forms": [
                                    {
                                        "form": "売り場",
                                        "ruby": [["売", "う"], ["り", "り"], ["場", "ば"]],
                                    }
                                ],
                                "senses": [
                                    {
                                        "glosses": [
                                            "place where things are sold; point of sale; counter in a shop"
                                        ],
                                        "topics": ["business"],
                                    }
                                ],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "もしもし",
                                "pos": "interjection",
                                "senses": [
                                    {
                                        "glosses": ["telephone greeting; hello"],
                                        "topics": ["engineering"],
                                    }
                                ],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "エンジニア",
                                "pos": "noun",
                                "forms": [{"form": "エンジニア"}],
                                "senses": [{"glosses": ["engineer"], "topics": ["engineering"]}],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "科学",
                                "pos": "noun",
                                "forms": [{"form": "科学", "ruby": [["科", "か"], ["学", "がく"]]}],
                                "senses": [{"glosses": ["science"], "topics": ["sciences"]}],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "身体",
                                "pos": "noun",
                                "forms": [
                                    {"form": "身体", "ruby": [["身", "しん"], ["体", "たい"]]}
                                ],
                                "senses": [
                                    {"glosses": ["body"], "topics": ["sciences", "medicine"]}
                                ],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "lang_code": "ja",
                                "word": "布団",
                                "pos": "noun",
                                "forms": [{"form": "布団", "ruby": [["布", "ふ"], ["団", "とん"]]}],
                                "senses": [
                                    {
                                        "glosses": ["zazen cushion used in Zen meditation"],
                                        "topics": ["religion"],
                                    }
                                ],
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
            )

            report = build_report(
                candidates_csv=candidates_csv,
                taxonomy_json=taxonomy_json,
                policy_json=policy_json,
                sources=("kaikki_wiktionary_topic",),
                kaikki_ja_jsonl_gz=kaikki_jsonl,
                top_n=10,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        row_keys = {
            (row["lemma"], row["reading"], row["topic"], row["source_label"])
            for row in report["evidence_rows"]
        }
        self.assertNotIn(("ポケット", "ポケット", "work_office", "business"), row_keys)
        self.assertIn(("売り場", "うりば", "work_office", "business"), row_keys)
        self.assertNotIn(("もしもし", "もしもし", "computing_internet", "engineering"), row_keys)
        self.assertIn(("エンジニア", "エンジニア", "computing_internet", "engineering"), row_keys)
        self.assertIn(("科学", "かがく", "science_math", "sciences"), row_keys)
        self.assertNotIn(("身体", "しんたい", "science_math", "sciences"), row_keys)
        self.assertIn(("身体", "しんたい", "medicine_health", "medicine"), row_keys)
        self.assertNotIn(("布団", "ふとん", "arts_literature_humanities", "religion"), row_keys)


def _write_candidates(path: Path, rows: list[tuple[str, str, str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "rank",
                "lemma",
                "reading",
                "score",
                "band",
                "core_rank",
                "candidate_state",
                "admission_override",
                "topic_stretch_allowed",
                "correction_types",
            ],
        )
        writer.writeheader()
        for rank, lemma, reading, score in rows:
            writer.writerow(
                {
                    "rank": rank,
                    "lemma": lemma,
                    "reading": reading,
                    "score": score,
                    "band": "0.30-0.35",
                    "core_rank": rank,
                    "candidate_state": "normal_vocab",
                    "topic_stretch_allowed": "True",
                }
            )


def _write_jmdict(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_gzip_text(path: Path, text: str) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(text)


def _write_taxonomy(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_label_mappings": [
                    {
                        "source_channel": "jmdict_field",
                        "source_label": "zoology",
                        "target_family": "animals",
                        "weight": 0.9,
                        "confidence": 0.9,
                    },
                    {
                        "source_channel": "jmdict_field",
                        "source_label": "manga",
                        "target_family": "anime_manga_pop_culture",
                        "weight": 0.75,
                        "confidence": 0.75,
                    },
                    {
                        "source_channel": "jmdict_field",
                        "source_label": "law",
                        "target_family": "law_politics_civics",
                        "weight": 0.9,
                        "confidence": 0.9,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
