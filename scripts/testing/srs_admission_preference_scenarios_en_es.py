#!/usr/bin/env python3
from __future__ import annotations


def scenario(
    name: str,
    description: str,
    profile_context: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "name": name,
        "description": description,
        "profile_context": dict(profile_context or {}),
    }


def topic_scenario(
    name: str,
    topic: str,
    label: str,
    source: str = "source-backed topics",
    code: str | None = None,
) -> tuple[str, str, str, str]:
    description = f"Strong explicit {label} interest from {source}."
    admission_code = code if code is not None else f"{topic.upper()}_INTEREST_MOVES_ADMISSION"
    return (name, topic, description, admission_code)


TOPIC_INTEREST_SCENARIOS: tuple[tuple[str, str, str, str], ...] = (
    topic_scenario("animals_interest", "animals", "animals", "the UX chip"),
    topic_scenario("plants_nature_interest", "plants_nature", "plants/nature", "the UX chip"),
    topic_scenario("food_cooking_interest", "food_cooking", "food/cooking", "the UX chip"),
    topic_scenario("medicine_health_interest", "medicine_health", "medicine/health"),
    topic_scenario("finance_business_interest", "finance_business", "finance/business"),
    topic_scenario("sports_fitness_interest", "sports_fitness", "sports/fitness"),
    topic_scenario("games_interest", "games", "games"),
    topic_scenario(
        "music_media_entertainment_interest",
        "music_media_entertainment",
        "music/media/entertainment",
    ),
    topic_scenario(
        "law_politics_civics_interest",
        "law_politics_civics",
        "law/politics/civics",
    ),
    topic_scenario("science_technology_interest", "science_technology", "science/technology"),
    topic_scenario(
        "travel_places_transport_interest",
        "travel_places_transport",
        "travel/place/transport",
        "the beta coverage path",
        code="",
    ),
)

SCENARIOS: tuple[dict[str, object], ...] = (
    scenario("neutral", "No user preference signals."),
    scenario(
        "animals_interest",
        "Strong explicit animals interest from the UX chip.",
        {"interests": ["animals"]},
    ),
    scenario(
        "animals_light_weight",
        "Low scalar animals preference below the full chip weight.",
        {"topic_weights": {"animals": 0.10}},
    ),
    *(
        scenario(name, description, {"interests": [topic]})
        for name, topic, description, _code in TOPIC_INTEREST_SCENARIOS[1:]
    ),
    scenario(
        "animals_high_proficiency",
        "Animals preference with high proficiency should suppress too-easy animals.",
        {
            "topic_weights": {"animals": 1.0},
            "proficiency": {"estimated_value": 0.8},
            "difficulty_preferences": {
                "target_challenge_center": 0.8,
                "target_challenge_spread": 0.12,
            },
        },
    ),
    scenario(
        "animals_plants_interest",
        "Combined animals plus plants/nature interests.",
        {"interests": ["animals", "plants_nature"]},
    ),
    scenario(
        "weighted_plants_over_animals",
        "Scalar topic weights preferring plants/nature over animals.",
        {"topic_weights": {"plants_nature": 1.0, "animals": 0.25}},
    ),
)

EXPECTED_TOPIC_SCENARIOS: tuple[tuple[str, str, str], ...] = tuple(
    (name, topic, code) for name, topic, _description, code in TOPIC_INTEREST_SCENARIOS if code
)
