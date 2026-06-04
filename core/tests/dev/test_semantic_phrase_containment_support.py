from __future__ import annotations

from pathlib import Path
import sys
import unittest

CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_phrase_containment_support import match_phrase_containment_examples  # noqa: E402


class SemanticPhraseContainmentSupportTests(unittest.TestCase):
    def test_phrase_containment_matches_singular_and_plural_marker_tokens(self) -> None:
        match = match_phrase_containment_examples(
            sentence="The end table held a small lamp.",
            source_phrase="end",
            trigger="end",
            phrase_examples=["end tables placed conveniently"],
        )

        self.assertTrue(match.hit)
        self.assertEqual(match.pattern_text, "end tables")
        self.assertEqual(match.reason_code, "example_phrase_right_containment")


if __name__ == "__main__":
    unittest.main()
