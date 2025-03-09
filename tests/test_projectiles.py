import pytest
from pygame import Color
from pygame.math import Vector2 as Vec2

from physics import PosVelObj
from projectiles import Missile, Rocket
from ship import Ship

ORIGIN = PosVelObj._new_origin_and_only_use_this_if_you_really_know_what_you_are_doing()


@pytest.mark.parametrize("bullet_type", [Missile, Rocket])
def test_homing(bullet_type: type[Missile | Rocket]) -> None:
    ship = Ship(ORIGIN, Vec2(), Vec2(), 10)
    projectile = bullet_type(ship, Vec2(-500, -500), Vec2(100, 0), Color(0, 0, 0), ship)

    for _ in range(2000):
        projectile.step(0.01)
        ship.step(0.01)
        if ship.contains_center_of(projectile):
            return
    pytest.fail("The projectile should have hit the ship.")
