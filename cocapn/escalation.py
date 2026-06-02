"""Tier escalation chain."""

from dataclasses import dataclass
from .device import Tier


@dataclass
class EscalationChain:
    current_tier: Tier = Tier.REFLEX
    escalation_count: int = 0

    def escalate(self) -> Tier:
        if self.current_tier.value < Tier.CLOUD.value:
            self.current_tier = Tier(self.current_tier.value + 1)
            self.escalation_count += 1
        return self.current_tier

    def deescalate(self) -> Tier:
        if self.current_tier.value > Tier.REFLEX.value:
            self.current_tier = Tier(self.current_tier.value - 1)
        return self.current_tier
