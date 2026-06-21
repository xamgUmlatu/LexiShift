from __future__ import annotations

from settings_pair_resource_plan import available_pair_resource_plans, pair_resource_plan


def test_en_es_pair_requires_wiktionary_and_frequency_resources() -> None:
    plan = pair_resource_plan("en-es")

    assert plan is not None
    pack_ids = [resource.pack_id for resource in plan.resources]
    assert pack_ids == [
        "freq-es-spalex-v1",
        "pos-es-ud-ancora-v1",
        "wiktionary-es-en",
        "freedict-es-en",
        "en-es-active-only-combined-full-v1-tranche-011",
    ]
    optional_pack_ids = [resource.pack_id for resource in plan.resources if resource.optional]
    assert optional_pack_ids == [
        "pos-es-ud-ancora-v1",
        "en-es-active-only-combined-full-v1-tranche-011",
    ]
    required_pack_ids = [resource.pack_id for resource in plan.required_resources]
    assert required_pack_ids == ["freq-es-spalex-v1", "wiktionary-es-en", "freedict-es-en"]


def test_en_de_pair_requires_frequency_and_bidirectional_freedict_resources() -> None:
    plan = pair_resource_plan("en-de")

    assert plan is not None
    pack_ids = [resource.pack_id for resource in plan.resources]
    assert pack_ids == [
        "freq-de-default",
        "freq-en-leipzig-default",
        "freedict-de-en",
        "freedict-en-de",
        "en-de-semantic-reference-pending",
    ]
    required_pack_ids = [resource.pack_id for resource in plan.required_resources]
    assert required_pack_ids == [
        "freq-de-default",
        "freq-en-leipzig-default",
        "freedict-de-en",
        "freedict-en-de",
    ]
    pending = next(resource for resource in plan.resources if resource.kind == "semantic_pack")
    assert pending.optional
    assert not pending.available


def test_en_ja_pair_requires_bccwj_and_jmdict_resources() -> None:
    plan = pair_resource_plan("en-ja")

    assert plan is not None
    pack_ids = [resource.pack_id for resource in plan.resources]
    assert pack_ids == [
        "freq-ja-bccwj",
        "jmdict-ja-en",
        "kanjidic2-ja",
        "jmnedict-ja",
        "kanjivg-ja",
        "jlpt-tanos-vocab-ja",
        "sbsjapanese1-ja",
    ]
    optional_pack_ids = [resource.pack_id for resource in plan.resources if resource.optional]
    assert optional_pack_ids == [
        "kanjidic2-ja",
        "jmnedict-ja",
        "kanjivg-ja",
        "jlpt-tanos-vocab-ja",
        "sbsjapanese1-ja",
    ]
    required_pack_ids = [resource.pack_id for resource in plan.required_resources]
    assert required_pack_ids == [
        "freq-ja-bccwj",
        "jmdict-ja-en",
    ]


def test_available_learning_pair_plans_include_en_de_en_es_and_en_ja() -> None:
    pairs = [plan.pair for plan in available_pair_resource_plans()]

    assert pairs == ["en-de", "en-es", "en-ja"]
