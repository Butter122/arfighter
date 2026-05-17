"""Core game state machine — manages two fighters and ticks."""

from __future__ import annotations

from fighter import Fighter
from combat import resolve_attack


class GameState:
    """Manages a two-player fighting game round.

    Tracks two fighters, resolves simultaneous actions per tick,
    and exposes serializable state for network broadcast.
    """

    def __init__(self) -> None:
        self.p1: Fighter = Fighter("p1")
        self.p2: Fighter = Fighter("p2")
        self.tick: int = 0

    def update(self, p1_action: str, p2_action: str) -> dict:
        """Advance one tick with the given player actions.

        Both attacks resolve simultaneously — neither player gets
        priority over the other.

        Returns a full game state dict suitable for JSON broadcast.
        """
        self.tick += 1

        # Resolve both attacks simultaneously
        result_p1 = resolve_attack(self.p1, self.p2, p1_action)
        result_p2 = resolve_attack(self.p2, self.p1, p2_action)

        # Advance fighters
        self.p1.update()
        self.p2.update()

        # Reconcile health — if both would die, check hp after resolution
        # (resolve_attack already called take_damage on both sides)

        winner = self.get_winner()

        return {
            "p1": self.p1.to_dict(),
            "p2": self.p2.to_dict(),
            "winner": winner,
            "tick": self.tick,
        }

    def reset(self) -> None:
        """Restart the game with fresh fighters."""
        self.p1 = Fighter("p1")
        self.p2 = Fighter("p2")
        self.tick = 0

    def get_winner(self) -> str | None:
        """Return 'p1', 'p2', or None if the round is still active."""
        p1_alive = self.p1.is_alive()
        p2_alive = self.p2.is_alive()
        if not p1_alive and not p2_alive:
            return "draw"
        if not p1_alive:
            return "p2"
        if not p2_alive:
            return "p1"
        return None
