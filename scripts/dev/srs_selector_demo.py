from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.srs.selector import SelectorCandidate, SelectorConfig, filter_candidates, rank_candidates


def _load_candidates(path: Path) -> list[SelectorCandidate]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items", [])
    candidates: list[SelectorCandidate] = []
    for item in items:
        candidates.append(
            SelectorCandidate(
                lemma=str(item.get("lemma", "")),
                language_pair=str(item.get("language_pair", "")),
                base_freq=float(item.get("base_freq", 0.0)),
                topic_bias=float(item.get("topic_bias", 0.0)),
                user_pref=float(item.get("user_pref", 0.0)),
                confidence=float(item.get("confidence", 0.0)),
                difficulty_target=float(item.get("difficulty_target", 0.0)),
                recency=item.get("recency"),
                source_type=item.get("source_type"),
                pos=item.get("pos"),
            )
        )
    return candidates


def main() -> None:
    dataset_path = PROJECT_ROOT / "docs" / "srs" / "srs_selector_test_dataset.json"
    candidates = _load_candidates(dataset_path)
    filtered = filter_candidates(candidates)
    ranked = rank_candidates(filtered, config=SelectorConfig(top_n=10))

    print(f"Loaded {len(candidates)} candidates.")
    print("Top 10 candidates:")
    for idx, entry in enumerate(ranked[:10], start=1):
        lemma = entry.candidate.lemma
        pair = entry.candidate.language_pair
        score = entry.breakdown.final_score
        components = entry.breakdown.components
        dominant = max(components, key=components.get)
        print(f"{idx:02d}. {lemma:<12} [{pair}] score={score:.4f} dominant={dominant}")


if __name__ == "__main__":
    main()
