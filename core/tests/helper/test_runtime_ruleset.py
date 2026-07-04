from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.engine import load_ruleset  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.persistence.storage import VocabDataset, save_vocab_dataset  # noqa: E402
from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402


class RuntimeRulesetTests(unittest.TestCase):
    def test_load_ruleset_expands_english_source_noun_plurals_for_browser_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            save_vocab_dataset(
                VocabDataset(
                    rules=(
                        VocabRule(
                            source_phrase="company",
                            replacement="会社",
                            metadata=RuleMetadata(
                                pos={"target": {"canonical": "noun"}},
                            ),
                        ),
                        VocabRule(
                            source_phrase="country",
                            replacement="国",
                            metadata=RuleMetadata(
                                pos={"target": {"canonical": "noun"}},
                            ),
                        ),
                        VocabRule(
                            source_phrase="go",
                            replacement="行く",
                            metadata=RuleMetadata(word_package={"pos_canonical": "verb"}),
                        ),
                    )
                ),
                paths.ruleset_path("en-ja", profile_id="suisui"),
            )

            payload = load_ruleset(paths, pair="en-ja", profile_id="suisui")
            rules_by_source = {
                str(rule["source_phrase"]): rule for rule in payload.get("rules", [])
            }

            self.assertIn("company", rules_by_source)
            self.assertIn("companies", rules_by_source)
            self.assertEqual(rules_by_source["companies"]["replacement"], "会社")
            self.assertIn("generated_source_plural", rules_by_source["companies"]["tags"])
            self.assertIn("countries", rules_by_source)
            self.assertNotIn("goes", rules_by_source)

            persisted = json.loads(
                paths.ruleset_path("en-ja", profile_id="suisui").read_text(encoding="utf-8")
            )
            self.assertEqual(
                [rule["source_phrase"] for rule in persisted["rules"]],
                ["company", "country", "go"],
            )

    def test_load_ruleset_does_not_expand_non_english_source_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            save_vocab_dataset(
                VocabDataset(
                    rules=(
                        VocabRule(
                            source_phrase="会社",
                            replacement="company",
                            metadata=RuleMetadata(word_package={"pos_canonical": "noun"}),
                        ),
                    )
                ),
                paths.ruleset_path("ja-en", profile_id="suisui"),
            )

            payload = load_ruleset(paths, pair="ja-en", profile_id="suisui")

            self.assertEqual(
                [rule["source_phrase"] for rule in payload.get("rules", [])],
                ["会社"],
            )


if __name__ == "__main__":
    unittest.main()
