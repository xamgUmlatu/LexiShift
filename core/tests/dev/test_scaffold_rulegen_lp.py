from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scaffold_rulegen_lp import (  # noqa: E402
    build_benchmark_case_payload,
    build_profile_payload,
    infer_record_shape,
    render_benchmark_preset_starter,
    render_integration_handoff,
    render_pair_module_stub,
    render_pair_test_stub,
    render_workstream_roadmap,
    scaffold_rulegen_lp,
)


class TestScaffoldRulegenLp(unittest.TestCase):
    def test_infer_record_shape_maps_known_families(self) -> None:
        self.assertEqual(
            infer_record_shape(family="freedict", reverse=False),
            "freedict_gloss_ordered",
        )
        self.assertEqual(
            infer_record_shape(family="kaikki", reverse=False),
            "wiktionary_kaikki_gloss_ordered",
        )
        self.assertEqual(
            infer_record_shape(family="kaikki", reverse=True),
            "wiktionary_kaikki_translation_ordered",
        )

    def test_build_profile_payload_uses_pair_scaffold_conventions(self) -> None:
        payload = build_profile_payload(
            pair="en-fr",
            translation_family="freedict",
            translation_pack_id="freedict-fr-en",
            reverse_family="freedict",
            reverse_pack_id="freedict-en-fr",
        )

        self.assertEqual(payload["pair"], "en-fr")
        self.assertEqual(payload["languages"]["target"], "fr")
        self.assertEqual(payload["translation_lanes"][0]["pack_id"], "freedict-fr-en")
        self.assertEqual(payload["reverse_lanes"][0]["pack_id"], "freedict-en-fr")
        self.assertEqual(
            payload["benchmark_profile"]["case_file"],
            "docs/test_inputs/rulegen_benchmark_cases/en_fr.json",
        )
        self.assertEqual(
            payload["benchmark_profile"]["preset_name"],
            "en_fr_canonical_matrix",
        )

    def test_build_benchmark_case_payload_starts_empty(self) -> None:
        payload = build_benchmark_case_payload(pair="ja-en")

        self.assertEqual(payload["pair"], "ja-en")
        self.assertEqual(payload["cases"], [])

    def test_render_workstream_roadmap_substitutes_pair_identity(self) -> None:
        template = (
            "# Rulegen LP Onboarding Checklist Template\n\n"
            "## Copy Rules\n\n"
            "## Pair Identity\n\n"
            "- Pair key: `<source-target>`\n"
            "- Primary target language: `<target>`\n"
        )

        rendered = render_workstream_roadmap(pair="en-fr", template_text=template)

        self.assertIn("# `en-fr` Workstream Roadmap", rendered)
        self.assertIn("`en-fr`", rendered)
        self.assertIn("`fr`", rendered)

    def test_render_pair_module_stub_mentions_profile_and_sources(self) -> None:
        rendered = render_pair_module_stub(
            pair="en-fr",
            translation_family="freedict",
            translation_pack_id="freedict-fr-en",
            reverse_family="freedict",
            reverse_pack_id="freedict-en-fr",
        )

        self.assertIn("class EnFrRulegenConfig", rendered)
        self.assertIn("generate_en_fr_results", rendered)
        self.assertIn("`freedict` / `freedict-fr-en`", rendered)
        self.assertIn("docs/test_inputs/rulegen_lp_profiles/en_fr.json", rendered)

    def test_render_pair_test_stub_uses_pair_module_import(self) -> None:
        rendered = render_pair_test_stub(pair="en-fr")

        self.assertIn("from lexishift_core.rulegen.pairs.en_fr import EnFrRulegenConfig", rendered)
        self.assertIn("run_rules_with_adapter", rendered)
        self.assertIn("generate_en_fr_results", rendered)
        self.assertIn("replace with pair-specific adapter/generation tests", rendered)
        self.assertIn('self.assertEqual(config.language_pair, "en-fr")', rendered)

    def test_render_benchmark_preset_starter_uses_pair_conventions(self) -> None:
        rendered = render_benchmark_preset_starter(pair="en-fr", reverse_pack_id="freedict-fr-en")

        self.assertIn("# `en-fr` Benchmark Preset Starter", rendered)
        self.assertIn('"en_fr_canonical_matrix"', rendered)
        self.assertIn('"--pairs"', rendered)
        self.assertIn('"en-fr"', rendered)
        self.assertIn('"false,true"', rendered)

    def test_render_integration_handoff_lists_central_follow_ups(self) -> None:
        rendered = render_integration_handoff(
            pair="en-fr",
            translation_family="freedict",
            translation_pack_id="freedict-fr-en",
            reverse_family="freedict",
            reverse_pack_id="freedict-en-fr",
            with_roadmap=True,
        )

        self.assertIn("# `en-fr` Integration Handoff", rendered)
        self.assertIn("core/lexishift_core/rulegen/pairs/__init__.py", rendered)
        self.assertIn("core/lexishift_core/rulegen/adapters.py", rendered)
        self.assertIn("docs/test_inputs/rulegen_benchmark_presets.json", rendered)
        self.assertIn("en_fr_canonical_matrix", rendered)
        self.assertIn("docs/language_pairs/en_fr_workstream_roadmap.md", rendered)

    def test_scaffold_rulegen_lp_writes_profile_cases_and_optional_roadmap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "rulegen").mkdir(parents=True)
            (root / "docs" / "rulegen" / "lp_onboarding_checklist_template.md").write_text(
                "# Rulegen LP Onboarding Checklist Template\n\n## Copy Rules\n\n## Pair Identity\n\n- Pair key: `<source-target>`\n",
                encoding="utf-8",
            )
            created = scaffold_rulegen_lp(
                project_root=root,
                pair="en-fr",
                translation_family="freedict",
                translation_pack_id="freedict-fr-en",
                reverse_family="freedict",
                reverse_pack_id="freedict-en-fr",
                with_roadmap=True,
            )

            self.assertEqual(
                created["profile"],
                "docs/test_inputs/rulegen_lp_profiles/en_fr.json",
            )
            self.assertEqual(
                created["benchmark_cases"],
                "docs/test_inputs/rulegen_benchmark_cases/en_fr.json",
            )
            self.assertEqual(
                created["roadmap"],
                "docs/language_pairs/en_fr_workstream_roadmap.md",
            )

            profile_payload = json.loads((root / created["profile"]).read_text(encoding="utf-8"))
            self.assertEqual(profile_payload["pair"], "en-fr")
            self.assertEqual(
                json.loads((root / created["benchmark_cases"]).read_text(encoding="utf-8"))[
                    "cases"
                ],
                [],
            )
            self.assertIn(
                "# `en-fr` Workstream Roadmap",
                (root / created["roadmap"]).read_text(encoding="utf-8"),
            )

    def test_scaffold_rulegen_lp_writes_code_stubs_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            created = scaffold_rulegen_lp(
                project_root=root,
                pair="en-fr",
                translation_family="freedict",
                translation_pack_id="freedict-fr-en",
                reverse_family="freedict",
                reverse_pack_id="freedict-en-fr",
                with_code_stubs=True,
            )

            self.assertEqual(
                created["pair_module"],
                "core/lexishift_core/rulegen/pairs/en_fr.py",
            )
            self.assertEqual(
                created["pair_test"],
                "core/tests/rulegen/test_rulegen_en_fr_scaffold.py",
            )
            self.assertIn(
                "class EnFrRulegenConfig",
                (root / created["pair_module"]).read_text(encoding="utf-8"),
            )
            self.assertIn(
                "@unittest.skip",
                (root / created["pair_test"]).read_text(encoding="utf-8"),
            )

    def test_scaffold_rulegen_lp_writes_integration_handoff_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            created = scaffold_rulegen_lp(
                project_root=root,
                pair="en-fr",
                translation_family="freedict",
                translation_pack_id="freedict-fr-en",
                reverse_family="freedict",
                reverse_pack_id="freedict-en-fr",
                with_integration_handoff=True,
            )

            self.assertEqual(
                created["integration_handoff"],
                "docs/language_pairs/en_fr_integration_handoff.md",
            )
            rendered = (root / created["integration_handoff"]).read_text(encoding="utf-8")
            self.assertIn("core/lexishift_core/rulegen/adapters.py", rendered)
            self.assertIn("en_fr_canonical_matrix", rendered)

    def test_scaffold_rulegen_lp_writes_benchmark_preset_starter_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            created = scaffold_rulegen_lp(
                project_root=root,
                pair="en-fr",
                translation_family="freedict",
                translation_pack_id="freedict-fr-en",
                reverse_family="freedict",
                reverse_pack_id="freedict-en-fr",
                with_benchmark_preset_starter=True,
            )

            self.assertEqual(
                created["benchmark_preset_starter"],
                "docs/language_pairs/en_fr_benchmark_preset_starter.md",
            )
            rendered = (root / created["benchmark_preset_starter"]).read_text(encoding="utf-8")
            self.assertIn('"en_fr_canonical_matrix"', rendered)
            self.assertIn('"--pairs"', rendered)


if __name__ == "__main__":
    unittest.main()
