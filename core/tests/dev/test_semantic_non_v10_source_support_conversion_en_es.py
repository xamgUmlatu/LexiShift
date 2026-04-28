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

from semantic_non_v10_source_support_conversion_en_es import (  # noqa: E402
    build_source_support_conversion_report,
    render_source_support_conversion_markdown,
)


class SemanticNonV10SourceSupportConversionTests(unittest.TestCase):
    def test_conversion_audit_classifies_supported_and_review_needed_rows(self) -> None:
        report = build_source_support_conversion_report(
            dataset_payload=_dataset_payload(),
            generated_at="2026-04-28T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "support_conversion_needed")
        self.assertEqual(report["summary"]["family_count"], 2)
        self.assertEqual(report["summary"]["fully_supported_family_count"], 1)
        self.assertEqual(report["summary"]["needs_reviewed_source_support_family_count"], 1)
        self.assertEqual(report["summary"]["unsupported_sense_count"], 1)
        unsupported = report["families"][1]["unsupported_senses"][0]
        self.assertEqual(unsupported["target_lemma"], "feria")
        self.assertEqual(unsupported["conversion_state"], "needs_reviewed_source_support")

    def test_conversion_audit_surfaces_same_pos_supported_alternatives(self) -> None:
        payload = _dataset_payload()
        family = payload["families"][1]
        family["metadata"]["translation_candidates"].append(
            {
                "translation": "cambio",
                "canonical_pos": "noun",
                "rank": 2,
                "sense_text": "act of changing",
                "reverse_support": True,
                "freedict_support": False,
                "wordnet_linked": True,
                "best_wordnet_link_score": 0.42,
                "support_sources": ["wiktionary_en_es", "wiktionary_es_en"],
            }
        )

        report = build_source_support_conversion_report(
            dataset_payload=payload,
            generated_at="2026-04-28T00:00:00Z",
        )

        self.assertEqual(report["summary"]["candidate_swap_review_family_count"], 1)
        unsupported = report["families"][1]["unsupported_senses"][0]
        self.assertEqual(unsupported["conversion_state"], "candidate_swap_review_available")
        self.assertEqual(
            unsupported["same_pos_supported_alternatives"][0]["translation"],
            "cambio",
        )

    def test_conversion_audit_rejects_alternative_that_duplicates_family_target(self) -> None:
        payload = _dataset_payload()
        family = payload["families"][1]
        family["metadata"]["translation_candidates"].append(
            {
                "translation": "cambiar",
                "canonical_pos": "noun",
                "rank": 2,
                "sense_text": "duplicate of an existing family target",
                "reverse_support": True,
                "freedict_support": False,
                "wordnet_linked": True,
                "best_wordnet_link_score": 0.42,
                "support_sources": ["wiktionary_en_es", "wiktionary_es_en"],
            }
        )

        report = build_source_support_conversion_report(
            dataset_payload=payload,
            generated_at="2026-04-28T00:00:00Z",
        )

        unsupported = report["families"][1]["unsupported_senses"][0]
        self.assertEqual(unsupported["conversion_state"], "needs_reviewed_source_support")
        self.assertEqual(unsupported["same_pos_supported_alternatives"], [])

    def test_render_conversion_markdown_includes_upper_bound_label(self) -> None:
        report = build_source_support_conversion_report(
            dataset_payload=_dataset_payload(),
            generated_at="2026-04-28T00:00:00Z",
        )

        markdown = render_source_support_conversion_markdown(report)

        self.assertIn("Source Support Conversion Audit", markdown)
        self.assertIn("Translation support mode: `forward_only_upper_bound`", markdown)
        self.assertIn("`change`", markdown)
        self.assertIn("`needs_reviewed_source_support`", markdown)


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "upper_bound_selected",
        "translation_support_mode": "forward_only_upper_bound",
        "families": [
            _family(
                trigger="look",
                active=_sense(
                    target="aspecto",
                    pos="noun",
                    reverse=False,
                    freedict=True,
                ),
                shadows=[
                    _sense(
                        target="parecer",
                        pos="verb",
                        reverse=False,
                        freedict=True,
                    )
                ],
                candidates=[],
            ),
            _family(
                trigger="change",
                active=_sense(
                    target="feria",
                    pos="noun",
                    reverse=False,
                    freedict=False,
                ),
                shadows=[
                    _sense(
                        target="cambiar",
                        pos="verb",
                        reverse=False,
                        freedict=True,
                    )
                ],
                candidates=[
                    {
                        "translation": "modificar",
                        "canonical_pos": "verb",
                        "rank": 3,
                        "sense_text": "make different",
                        "reverse_support": True,
                        "freedict_support": False,
                        "wordnet_linked": True,
                        "best_wordnet_link_score": 0.4,
                    }
                ],
            ),
        ],
    }


def _family(
    *,
    trigger: str,
    active: dict[str, object],
    shadows: list[dict[str, object]],
    candidates: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "family_id": f"en-es:sentence-veto:{trigger}:{active['target_lemma']}",
        "trigger": trigger,
        "active": active,
        "shadows": shadows,
        "metadata": {"translation_candidates": candidates},
    }


def _sense(
    *,
    target: str,
    pos: str,
    reverse: bool,
    freedict: bool,
) -> dict[str, object]:
    return {
        "sense_id": f"sense:{target}",
        "target_lemma": target,
        "canonical_pos": pos,
        "metadata": {
            "reverse_support": reverse,
            "freedict_support": freedict,
            "translation_rank": 1,
            "translation_sense_text": "test sense",
            "wordnet_linked": True,
            "best_wordnet_link_score": 0.4,
            "support_sources": ["wiktionary_en_es"],
        },
    }


if __name__ == "__main__":
    unittest.main()
