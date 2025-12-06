import random

import pytest
from pygame import Color
from pygame.math import Vector2 as Vec2

from src.physics import PosVel
from src.projectiles import Missile, Rocket
from src.ship import Ship, ShipConfig

ORIGIN = PosVel._new_origin_and_only_use_this_if_you_really_know_what_you_are_doing()


@pytest.mark.parametrize("bullet_type", [Missile, Rocket])
def test_homing(bullet_type: type[Missile | Rocket]) -> None:
    ship = Ship(ORIGIN, ShipConfig(relative_pos=Vec2(0, 0)))
    num_projectiles = 10
    projectiles = []
    for _ in range(num_projectiles):
        start_pos = Vec2((random.random() - 0.5) * 200, (random.random() - 0.5) * 200)
        start_vel = Vec2((random.random() - 0.5) * 200, (random.random() - 0.5) * 200)
        projectiles.append(bullet_type(ship, start_pos, start_vel, Color(0, 0, 0), ship))

    for _ in range(2000):
        for projectile in projectiles:
            projectile.step(0.01)
            ship.step(0.01)
            if ship.intersects_disk(projectile):
                return
    pytest.fail("None of the projectiles hit the ship. At least one should have hit.")
