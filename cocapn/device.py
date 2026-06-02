"""Device tiers and capabilities."""

from enum import Enum, Flag, auto
from dataclasses import dataclass


class Tier(Enum):
    REFLEX = 0
    BACKBONE = 1
    CORTEX = 2
    CLOUD = 3


class Capability(Flag):
    SENSE = auto()
    ACT = auto()
    ROUTE = auto()
    PREDICT = auto()
    TRAIN = auto()
    COMMUNICATE = auto()


@dataclass
class Device:
    id: int
    name: str
    tier: Tier
    capabilities: Capability = Capability(0)
    online: bool = True

    def can(self, cap: Capability) -> bool:
        return self.online and (cap in self.capabilities)
