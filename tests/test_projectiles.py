from pygame import Color
from pygame.math import Vector2 as Vec2

from projectiles import Bullet, Missile, Rocket
from ship import Ship

# TODO: More class defaults.


def test_homing():
    ship = Ship(Vec2(512, -1024), Vec2(), 10)

    def hits_ship(projectile: Bullet) -> bool:
        """Simulate projectile for a while and return if it ever hits `ship`"""
        for _ in range(2000):
            projectile.step(0.01)
            ship.step(0.01)
            if ship.intersects_point(projectile.pos):
                return True
        return False

    missile = Missile(Vec2(0, 0), Vec2(500, 0), Color(0, 0, 0), ship)
    rocket = Rocket(Vec2(0, 0), Vec2(0, 0), Color(0, 0, 0), ship)

    assert hits_ship(missile), "Missile should have hit the ship"
    assert hits_ship(rocket), "Rocket should have hit the ship"
