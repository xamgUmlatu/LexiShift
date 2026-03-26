from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.pos.normalization import (  # noqa: E402
    canonical_pos_to_bucket,
    normalize_pos,
    resolve_pos_source_profile,
)


class TestPosNormalization(unittest.TestCase):
    def test_resolve_profile_from_context(self) -> None:
        self.assertEqual(
            resolve_pos_source_profile(source_provider="freq-ja-bccwj"),
            "bccwj",
        )
        self.assertEqual(
            resolve_pos_source_profile(source_provider="freq-es-cde"),
            "freq-es-cde",
        )
        self.assertEqual(
            resolve_pos_source_profile(source_provider="freq-de-default"),
            "freq-de-default",
        )
        self.assertEqual(
            resolve_pos_source_profile(source_provider="freedict-es-en"),
            "freedict",
        )
        self.assertEqual(
            resolve_pos_source_profile(source_provider="wiktionary-es-en"),
            "wiktionary",
        )
        self.assertEqual(
            resolve_pos_source_profile(language_pair="en-en", source_kind="frequency"),
            "compact-latin",
        )
        self.assertEqual(
            resolve_pos_source_profile(language_pair="en-es", source_kind="frequency"),
            "freq-es-cde",
        )
        self.assertEqual(
            resolve_pos_source_profile(language_pair="en-xx", source_kind="frequency"),
            "generic",
        )

    def test_bccwj_known_and_unknown(self) -> None:
        noun = normalize_pos(
            "名詞-普通名詞-一般",
            language_pair="en-ja",
            source_provider="freq-ja-bccwj",
            source_kind="frequency",
        )
        self.assertEqual(noun.source_profile, "bccwj")
        self.assertEqual(noun.canonical, "noun")
        self.assertEqual(noun.bucket, "noun")
        self.assertTrue(noun.mapped)

        numeral = normalize_pos(
            "名詞-数詞",
            language_pair="en-ja",
            source_provider="freq-ja-bccwj",
        )
        self.assertEqual(numeral.canonical, "numeral")
        self.assertEqual(numeral.bucket, "other")
        self.assertTrue(numeral.mapped)

        suffix = normalize_pos(
            "接尾辞-名詞的-一般",
            language_pair="en-ja",
            source_provider="freq-ja-bccwj",
        )
        self.assertEqual(suffix.canonical, "other")
        self.assertEqual(suffix.bucket, "other")
        self.assertTrue(suffix.mapped)

        unknown = normalize_pos(
            "未知カテゴリ-テスト",
            language_pair="en-ja",
            source_provider="freq-ja-bccwj",
        )
        self.assertEqual(unknown.canonical, "other")
        self.assertEqual(unknown.bucket, "other")
        self.assertFalse(unknown.mapped)

    def test_compact_spanish_tags(self) -> None:
        noun = normalize_pos(
            "n",
            language_pair="en-es",
            source_provider="freq-es-cde",
            source_kind="frequency",
        )
        self.assertEqual(noun.canonical, "noun")
        self.assertEqual(noun.bucket, "noun")
        self.assertTrue(noun.mapped)

        verb = normalize_pos(
            "v",
            language_pair="es-en",
            source_provider="freq-en-coca",
            source_kind="frequency",
        )
        self.assertEqual(verb.canonical, "verb")
        self.assertEqual(verb.bucket, "verb")
        self.assertTrue(verb.mapped)

        unknown = normalize_pos(
            "u",
            language_pair="es-en",
            source_provider="freq-en-coca",
            source_kind="frequency",
        )
        self.assertEqual(unknown.canonical, "other")
        self.assertEqual(unknown.bucket, "other")
        self.assertTrue(unknown.mapped)

    def test_german_profile_tags(self) -> None:
        noun = normalize_pos(
            "SUB:NOM:SIN:NEU",
            language_pair="en-de",
            source_provider="freq-de-default",
            source_kind="frequency",
        )
        self.assertEqual(noun.canonical, "noun")
        self.assertEqual(noun.bucket, "noun")
        self.assertTrue(noun.mapped)

        adverb = normalize_pos(
            "ADV:MOD|PRO:DEM",
            language_pair="en-de",
            source_provider="freq-de-default",
            source_kind="frequency",
        )
        self.assertEqual(adverb.canonical, "adverb")
        self.assertEqual(adverb.bucket, "adverb")
        self.assertTrue(adverb.mapped)

        unknown = normalize_pos(
            "ZUS",
            language_pair="en-de",
            source_provider="freq-de-default",
            source_kind="frequency",
        )
        self.assertEqual(unknown.canonical, "other")
        self.assertFalse(unknown.mapped)

    def test_freedict_multi_tag_uses_lexical_priority(self) -> None:
        pos = normalize_pos(
            "verb|noun",
            language_pair="en-de",
            source_provider="freedict-de-en",
            source_kind="dictionary",
        )
        self.assertEqual(pos.source_profile, "freedict")
        self.assertEqual(pos.canonical, "noun")
        self.assertEqual(pos.bucket, "noun")
        self.assertTrue(pos.mapped)

    def test_wiktionary_pos_uses_generic_and_compact_hits(self) -> None:
        adjective = normalize_pos(
            "adj",
            language_pair="en-es",
            source_provider="wiktionary-es-en",
            source_kind="dictionary",
        )
        self.assertEqual(adjective.source_profile, "wiktionary")
        self.assertEqual(adjective.canonical, "adjective")
        self.assertEqual(adjective.bucket, "adjective")
        self.assertTrue(adjective.mapped)

        noun = normalize_pos(
            "noun",
            language_pair="en-es",
            source_provider="wiktionary-es-en",
            source_kind="dictionary",
        )
        self.assertEqual(noun.canonical, "noun")
        self.assertEqual(noun.bucket, "noun")
        self.assertTrue(noun.mapped)

        adverb = normalize_pos(
            "adv",
            language_pair="en-es",
            source_provider="wiktionary-es-en",
            source_kind="dictionary",
        )
        self.assertEqual(adverb.canonical, "adverb")
        self.assertEqual(adverb.bucket, "adverb")
        self.assertTrue(adverb.mapped)

    def test_empty_and_bucket_helper(self) -> None:
        empty = normalize_pos(
            "",
            language_pair="en-es",
            source_provider="freq-es-cde",
        )
        self.assertEqual(empty.canonical, "other")
        self.assertEqual(empty.bucket, "other")
        self.assertFalse(empty.mapped)
        self.assertEqual(empty.matched_rule, "empty")
        self.assertEqual(canonical_pos_to_bucket("numeral"), "other")


if __name__ == "__main__":
    unittest.main()
