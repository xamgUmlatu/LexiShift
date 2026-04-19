from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import TranslationGlossRecord  # noqa: E402
from lexishift_core.rulegen.semantic_shadow_record_clusters import (  # noqa: E402
    cluster_shadow_records,
)


def _record(
    *,
    translation: str,
    pos_raw: str = "noun",
    gloss_ord: int | None = None,
) -> TranslationGlossRecord:
    metadata: dict[str, object] = {}
    if gloss_ord is not None:
        metadata["gloss_ord"] = gloss_ord
    return TranslationGlossRecord(
        translation=translation,
        pos_raw=pos_raw,
        metadata=metadata,
    )


class TestSemanticShadowRecordClusters(unittest.TestCase):
    def test_cluster_shadow_records_uses_translation_gloss_locator_for_ordered_glosses(
        self,
    ) -> None:
        clusters = cluster_shadow_records(
            target_override=None,
            records=(_record(translation="house", gloss_ord=2),),
            provider="custom_translation_pack",
        )

        self.assertEqual(len(clusters), 1)
        locator = clusters[0]["locator"]
        self.assertEqual(locator["provider"], "custom_translation_pack")
        self.assertEqual(locator["locator_kind"], "translation_gloss")
        self.assertEqual(locator["target_key"], "house")
        self.assertEqual(locator["gloss_ord"], 2)

    def test_cluster_shadow_records_falls_back_to_opaque_locator_without_gloss_order(self) -> None:
        clusters = cluster_shadow_records(
            target_override=None,
            records=(_record(translation="house"),),
            provider="custom_translation_pack",
        )

        self.assertEqual(len(clusters), 1)
        locator = clusters[0]["locator"]
        self.assertEqual(locator["provider"], "custom_translation_pack")
        self.assertEqual(locator["locator_kind"], "opaque")


if __name__ == "__main__":
    unittest.main()
