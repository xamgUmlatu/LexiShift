from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


def clamp(value: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(value, max_value))


@dataclass(frozen=True)
class PmwWeighting:
    mode: str = "log1p"  # log1p, linear
    min_value: float = 0.0

    def normalize(self, value: Optional[float], *, max_value: Optional[float]) -> float:
        if value is None or max_value is None or max_value <= 0:
            return 0.0
        if value < self.min_value:
            return 0.0
        if self.mode == "linear":
            return clamp(value / max_value)
        # default: log1p
        return clamp(math.log1p(value) / math.log1p(max_value))


@dataclass(frozen=True)
class RankWeighting:
    def normalize(self, value: Optional[float], *, max_value: Optional[float]) -> float:
        if value is None or max_value is None or max_value <= 1:
            return 0.0
        return clamp(1.0 - ((value - 1.0) / (max_value - 1.0)))


@dataclass(frozen=True)
class GlossDecay:
    schedule: tuple[float, ...] = (1.0, 0.7, 0.5)

    def multiplier(self, index: Optional[int]) -> float:
        if index is None or index < 0:
            return 1.0
        if index < len(self.schedule):
            return self.schedule[index]
        return self.schedule[-1]
