from __future__ import annotations

from settings_pair_resource_plan import pair_resource_plan


def test_en_es_pair_requires_wiktionary_and_frequency_resources() -> None:
    plan = pair_resource_plan("en-es")

    assert plan is not None
    pack_ids = [resource.pack_id for resource in plan.resources]
    assert pack_ids == ["freq-es-cde", "wiktionary-es-en", "freedict-es-en"]
