from pygame import Color
from pygame.math import Vector2 as Vec2

from projectiles import Missile, Rocket
from ship import Ship


def test_homing():
    ship = Ship(
        Vec2(1000, -500),
        vel=Vec2(0, 0),
        density=1,
        size=10,
        color=Color(0, 0, 0),
        bullet_color=Color(0, 0, 0),
        gun_cooldown=0.1,
        bullet_speed=100,
    )

    for projectile in [
        Missile(Vec2(0, 0), Vec2(0, 0), Color(0, 0, 0), ship, "assets/missile.png"),
        Rocket(Vec2(0, 0), Vec2(0, 0), Color(0, 0, 0), ship),
    ]:
        min_dist = 1e9
        for _ in range(200):
            projectile.step(0.1)
            ship.step(0.1)
            min_dist = min(min_dist, projectile.pos.distance_to(ship.pos))

        assert min_dist < ship.size, "Projectile should have hit the ship"
