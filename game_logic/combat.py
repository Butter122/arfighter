"""Attack resolution and damage calculation."""

from __future__ import annotations

from fighter import Fighter
from config import ATTACK_ACTIONS, CHIP_DAMAGE, DAMAGE_TABLE


def resolve_attack(attacker: Fighter, defender: Fighter, action: str) -> dict:
    """Resolve a single attack. Called simultaneously for both players.

    Args:
        attacker: The fighter performing the action.
        defender: The opposing fighter.
        action: The action string (punch_left, kick, block, etc.).

    Returns:
        Dict with hit (bool), damage (int), and action (str).
    """
    hit, dmg = False, 0

    if action in ATTACK_ACTIONS:
        attacker.state = "attacking"
        base_dmg = DAMAGE_TABLE.get(action, 0)

        if defender.state == "blocking":
            dmg = CHIP_DAMAGE
            hit = True
        elif defender.invincible_frames == 0:
            dmg = base_dmg
            hit = True

        if hit:
            defender.take_damage(dmg)

    elif action == "block":
        attacker.state = "blocking"

    else:
        attacker.state = action if action in ("idle",) else action

    return {"hit": hit, "damage": dmg, "action": action}
