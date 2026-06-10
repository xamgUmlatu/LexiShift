from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.source_stacks import source_stack_for_pair  # noqa: E402


class TestSourceStacks(unittest.TestCase):
    def test_en_ja_stack_declares_quality_preferred_default_resources(self) -> None:
        stack = source_stack_for_pair("en-ja")

        assert stack is not None
        self.assertEqual(stack.stack_id, "en-ja-default-v1")
        setup_pack_ids = [resource.pack_id for resource in stack.pair_setup_resources()]
        self.assertEqual(
            setup_pack_ids,
            [
                "freq-ja-bccwj",
                "jmdict-ja-en",
            ],
        )
        target_frequency = next(
            resource for resource in stack.resources if resource.role == "target_frequency"
        )
        self.assertEqual(target_frequency.required_for, ("srs_admission", "srs_bootstrap"))
        self.assertIn("manual_supply_quality_preferred", target_frequency.notes)
        source_frequency = next(
            resource for resource in stack.resources if resource.role == "source_frequency_prior"
        )
        self.assertFalse(source_frequency.wired)
        self.assertEqual(
            source_frequency.optional_for,
            ("rulegen_source_frequency_prior_experiment",),
        )
        wordnet = next(
            resource
            for resource in stack.resources
            if resource.role == "target_monolingual_wordnet"
        )
        self.assertFalse(wordnet.wired)
        self.assertEqual(
            wordnet.optional_for,
            ("semantic_evidence_enrichment_experiment",),
        )

    def test_en_de_stack_declares_downloadable_default_resources(self) -> None:
        stack = source_stack_for_pair("en-de")

        assert stack is not None
        self.assertEqual(stack.stack_id, "en-de-default-v1")
        setup_pack_ids = [resource.pack_id for resource in stack.pair_setup_resources()]
        self.assertEqual(
            setup_pack_ids,
            [
                "freq-de-default",
                "freq-en-leipzig-default",
                "freedict-de-en",
                "freedict-en-de",
                "en-de-semantic-reference-pending",
            ],
        )
        semantic = next(resource for resource in stack.pair_setup_resources() if not resource.wired)
        self.assertEqual(semantic.family, "semantic_pack")
        self.assertEqual(semantic.optional_for, ("semantic_admission_reference",))
        source_frequency = next(
            resource for resource in stack.resources if resource.role == "source_frequency_prior"
        )
        self.assertEqual(source_frequency.pack_id, "freq-en-leipzig-default")
        self.assertEqual(source_frequency.required_for, ("rulegen_source_frequency_prior",))

    def test_en_es_setup_resources_preserve_existing_download_shape(self) -> None:
        stack = source_stack_for_pair("en-es")

        assert stack is not None
        setup_pack_ids = [resource.pack_id for resource in stack.pair_setup_resources()]
        self.assertEqual(
            setup_pack_ids,
            [
                "freq-es-spalex-v1",
                "pos-es-ud-ancora-v1",
                "wiktionary-es-en",
                "freedict-es-en",
                "en-es-active-only-combined-full-v1-tranche-011",
            ],
        )

    def test_en_es_stack_tracks_pos_overlay_as_recommended_enrichment(self) -> None:
        stack = source_stack_for_pair("en-es")

        assert stack is not None
        overlay = next(resource for resource in stack.resources if resource.family == "pos_overlay")
        self.assertEqual(overlay.pack_id, "pos-es-ud-ancora-v1")
        self.assertTrue(overlay.pair_setup)
        self.assertEqual(overlay.optional_for, ("srs_admission_pos_recovery",))

    def test_en_es_stack_tracks_semantic_reference_as_recommended_enrichment(self) -> None:
        stack = source_stack_for_pair("en-es")

        assert stack is not None
        semantic = next(
            resource for resource in stack.resources if resource.family == "semantic_pack"
        )
        self.assertEqual(semantic.pack_id, "en-es-active-only-combined-full-v1-tranche-011")
        self.assertTrue(semantic.pair_setup)
        self.assertTrue(semantic.wired)
        self.assertEqual(semantic.optional_for, ("semantic_admission_reference",))
