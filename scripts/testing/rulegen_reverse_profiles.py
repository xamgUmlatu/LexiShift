from __future__ import annotations


REVERSE_CHECK_PROFILES: dict[str, dict[str, str]] = {
    "default": {
        "enabled_values": "false",
        "match_bonus_values": "0.2",
        "near_bonus_values": "0.1",
        "near_rank_max_values": "2",
        "far_hit_penalty_values": "0.0",
        "miss_penalty_values": "0.2",
    },
    "experiment": {
        "enabled_values": "false,true",
        "match_bonus_values": "0.2",
        "near_bonus_values": "0.1",
        "near_rank_max_values": "2",
        "far_hit_penalty_values": "0.0",
        "miss_penalty_values": "0.2",
    },
    "force-on": {
        "enabled_values": "true",
        "match_bonus_values": "0.2",
        "near_bonus_values": "0.1",
        "near_rank_max_values": "2",
        "far_hit_penalty_values": "0.0",
        "miss_penalty_values": "0.2",
    },
    "far-hit-experiment": {
        "enabled_values": "false,true",
        "match_bonus_values": "0.6",
        "near_bonus_values": "0.1",
        "near_rank_max_values": "2",
        "far_hit_penalty_values": "0.05",
        "miss_penalty_values": "0.8",
    },
}
