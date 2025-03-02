import pytest
from pygame import Color
from pygame.math import Vector2 as Vec2

from projectiles import Bullet, Missile, Rocket
from ship import Ship


@pytest.mark.parametrize("bullet_type", [Missile, Rocket])
def test_homing(bullet_type: type[Bullet]):
    ship = Ship(Vec2(512, -1024), Vec2(4,8), 10)
    projectile = bullet_type(Vec2(10, -15), Vec2(8, 29), Color(0, 0, 0), ship)

    for _ in range(2000):
        projectile.step(0.01)
        ship.step(0.01)
        if ship.intersects_point(projectile.pos):
            return
    pytest.fail("The projectile should have hit the ship.")
