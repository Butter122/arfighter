"""Fighter entity with HP, state machine, and damage handling."""

from __future__ import annotations

from typing import Literal

from config import INVINCIBLE_FRAMES, MAX_HP

FighterState = Literal["idle", "attacking", "blocking", "hit", "dead"]


class Fighter:
    """A single player in the fighting game.

    Attributes:
        player_id: "p1" or "p2".
        hp: Current health points.
        max_hp: Maximum health points.
        state: Current fighter state.
        invincible_frames: Remaining invincibility ticks.
    """

    def __init__(self, player_id: str) -> None:
        self.player_id: str = player_id
        self.hp: int = MAX_HP
        self.max_hp: int = MAX_HP
        self.state: FighterState = "idle"
        self.invincible_frames: int = 0

    def take_damage(self, amount: int) -> None:
        """Apply damage and grant invincibility frames.

        No effect if already invincible or dead.
        """
        if self.invincible_frames > 0 or self.state == "dead":
            return
        self.hp = max(0, self.hp - amount)
        self.invincible_frames = INVINCIBLE_FRAMES
        self.state = "hit" if self.hp > 0 else "dead"

    def update(self) -> None:
        """Advance one tick — decrement invincibility frames."""
        if self.invincible_frames > 0:
            self.invincible_frames -= 1

    def is_alive(self) -> bool:
        """Return True if the fighter still has HP."""
        return self.hp > 0

    def to_dict(self) -> dict:
        """Serialize for network broadcast."""
        return {
            "player_id": self.player_id,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "state": self.state,
        }
