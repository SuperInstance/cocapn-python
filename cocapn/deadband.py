"""Deadband trigger with relative tolerance and directional awareness."""

from enum import Enum
from dataclasses import dataclass, field


class Direction(Enum):
    BOTH = "both"
    ABOVE_ONLY = "above"
    BELOW_ONLY = "below"


class State(Enum):
    NORMAL = 0
    APPROACHING = 1
    EXCEEDED = 2


@dataclass
class Deadband:
    center: float
    tolerance: float  # relative, e.g. 0.05 = 5%
    direction: Direction = Direction.BOTH

    def _rel_tol(self) -> float:
        if abs(self.center) < 1e-12:
            return self.tolerance
        return abs(self.center) * self.tolerance

    def check(self, value: float) -> State:
        diff = value - self.center
        tol = self._rel_tol()

        if self.direction == Direction.ABOVE_ONLY:
            if diff > tol:
                return State.EXCEEDED
            if diff > tol * 0.8:
                return State.APPROACHING
            return State.NORMAL

        if self.direction == Direction.BELOW_ONLY:
            if diff < -tol:
                return State.EXCEEDED
            if diff < -tol * 0.8:
                return State.APPROACHING
            return State.NORMAL

        # Both
        adiff = abs(diff)
        if adiff > tol:
            return State.EXCEEDED
        if adiff > tol * 0.8:
            return State.APPROACHING
        return State.NORMAL


@dataclass
class DeadbandMonitor:
    deadbands: dict[str, Deadband] = field(default_factory=dict)

    def check_all(self, values: dict[str, float]) -> dict[str, State]:
        return {name: db.check(values.get(name, db.center)) for name, db in self.deadbands.items()}

    def triggered(self, values: dict[str, float]) -> list[str]:
        return [name for name, state in self.check_all(values).items() if state == State.EXCEEDED]
