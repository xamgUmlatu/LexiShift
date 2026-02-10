import argparse
import os
import sys
import time
from pathlib import Path

CORE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core"))
if CORE_ROOT not in sys.path:
    sys.path.insert(0, CORE_ROOT)

from lexishift_core.resources.synonyms import EmbeddingIndex


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test embedding similarity rankings.")
    parser.add_argument(
        "--embeddings",
        required=True,
        help="Path to .vec/.txt/.bin/.db/.sqlite embeddings file.",
    )
    parser.add_argument("--target", default="scabrous", help="Target word to compare against.")
    parser.add_argument(
        "--candidates",
        default="salty,rough,scaly,coarse,harsh,abrasive,gritty,raspy",
        help="Comma-separated candidate words.",
    )
    parser.add_argument("--lowercase", action="store_true", help="Lowercase lookup keys.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    path = Path(args.embeddings)
    if not path.exists():
        print(f"Embeddings file not found: {path}")
        return 1

    start = time.time()
    index = EmbeddingIndex(path, lower_case=args.lowercase)
    elapsed = time.time() - start
    print(f"Loaded embeddings in {elapsed:.2f}s")

    target = args.target.strip()
    candidates = [part.strip() for part in args.candidates.split(",") if part.strip()]
    if not target or not candidates:
        print("Provide a target word and at least one candidate.")
        return 1

    scores = []
    for candidate in candidates:
        score = index.similarity(target, candidate)
        scores.append((candidate, score))

    scores.sort(key=lambda item: (-1 if item[1] is None else -item[1], item[0]))
    print(f"Target: {target}")
    for candidate, score in scores:
        if score is None:
            print(f"- {candidate}: (missing vector)")
        else:
            print(f"- {candidate}: {score:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
