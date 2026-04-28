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

from semantic_llm_surface_pos_support import surface_pos_signal  # noqa: E402


class SemanticLlmSurfacePosSupportTests(unittest.TestCase):
    def test_modified_noun_followed_by_predicate_is_active_frame(self) -> None:
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_noun(),
                shadow_examples=[(_shadow_verb(), "act in a manner such that one has fun")],
                preceding_token="comedy",
                following_token="opened",
            ),
            "active_noun_frame",
        )
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_noun(),
                shadow_examples=[(_shadow_verb(), "announce information")],
                preceding_token="quarterly",
                following_token="summarized",
            ),
            "active_noun_frame",
        )
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_noun(),
                shadow_examples=[(_shadow_verb(), "act in a manner such that one has fun")],
                preceding_token="school",
                following_token="won",
            ),
            "active_noun_frame",
        )
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_noun(),
                shadow_examples=[(_shadow_verb(), "inspect a place")],
                preceding_token="fraud",
                following_token="drew",
            ),
            "active_noun_frame",
        )
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_noun(),
                shadow_examples=[(_shadow_verb(), "sound loudly")],
                preceding_token="gold",
                following_token="lay",
            ),
            "active_noun_frame",
        )
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_noun(),
                shadow_examples=[(_shadow_verb(), "create by training and teaching")],
                preceding_token="morning",
                following_token="left",
            ),
            "active_noun_frame",
        )

    def test_adjective_modifier_frames_are_active_frames(self) -> None:
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_adjective(),
                shadow_examples=[(_shadow_verb(), "remove moisture from clothes")],
                preceding_token="the",
                following_token="towel",
            ),
            "active_modifier_frame",
        )
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_adjective(),
                shadow_examples=[(_shadow_noun(), "the period happening now")],
                preceding_token="the",
                following_token="policy",
            ),
            "active_modifier_frame",
        )

    def test_non_verb_active_in_clear_verb_frames_is_shadow_frame(self) -> None:
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_adjective(),
                shadow_examples=[(_shadow_noun(), "the current moment")],
                preceding_token="will",
                following_token="the",
            ),
            "shadow_verb_frame",
        )
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_noun(),
                shadow_examples=[(_shadow_noun(), "a pause for relaxation")],
                preceding_token="workers",
                following_token="after",
            ),
            "shadow_verb_frame",
        )
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_adjective(),
                shadow_examples=[(_shadow_verb(), "abstain from food")],
                preceding_token="held",
                following_token="to",
            ),
            "shadow_verb_frame",
        )

    def test_subject_verb_frames_remain_shadow_frames(self) -> None:
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_noun(),
                shadow_examples=[(_shadow_verb(), "inspect verify")],
                preceding_token="auditors",
                following_token="the",
            ),
            "shadow_verb_frame",
        )
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_noun(),
                shadow_examples=[(_shadow_verb(), "act in a manner such that one has fun")],
                preceding_token="children",
                following_token="soccer",
            ),
            "shadow_verb_frame",
        )

    def test_of_complement_frames_are_active_noun_frames(self) -> None:
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_noun(),
                shadow_examples=[(_shadow_verb(), "apply something practically")],
                preceding_token="safe",
                following_token="of",
            ),
            "active_noun_frame",
        )
        self.assertEqual(
            surface_pos_signal(
                active_sense=_active_noun(),
                shadow_examples=[(_shadow_verb(), "cease activity recover")],
                preceding_token="of",
                following_token="",
            ),
            "active_noun_frame",
        )


def _active_noun() -> dict[str, object]:
    return {"sense_id": "active", "canonical_pos": "noun"}


def _active_adjective() -> dict[str, object]:
    return {"sense_id": "active", "canonical_pos": "adjective"}


def _shadow_noun() -> dict[str, object]:
    return {"sense_id": "shadow", "canonical_pos": "noun"}


def _shadow_verb() -> dict[str, object]:
    return {"sense_id": "shadow", "canonical_pos": "verb"}


if __name__ == "__main__":
    unittest.main()
