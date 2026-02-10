import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core import (  # noqa: E402
    BuildOptions,
    FORM_PLURAL,
    InflectionSpec,
    VocabRule,
    expand_vocab_rules,
)


class BuilderTests(unittest.TestCase):
    def test_expand_vocab_rules_tags_generated(self) -> None:
        rules = [VocabRule(source_phrase="twilight", replacement="gloaming")]
        options = BuildOptions(
            inflection_spec=InflectionSpec(forms=frozenset({FORM_PLURAL})),
            include_generated_tag=True,
        )
        expanded = expand_vocab_rules(rules, options=options)
        sources = {rule.source_phrase for rule in expanded}
        self.assertIn("twilight", sources)
        self.assertIn("twilights", sources)
        generated = [rule for rule in expanded if rule.source_phrase == "twilights"][0]
        self.assertIn("generated", generated.tags)


if __name__ == "__main__":
    unittest.main()
