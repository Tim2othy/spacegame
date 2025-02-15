from math import tau
from pygame import Color
from pygame.math import Vector2 as Vec2

from ship import Ship


EPSILON = 1e-8


def test_shooting():
    gun_cooldown = 0.123
    bullet_speed = 0.456
    bullet_count = 10
    ship = Ship(
        Vec2(0, 0),
        Vec2(0, 0),
        1,
        1,
        Color(0, 0, 0),
        Color(0, 0, 0),
        gun_cooldown=gun_cooldown,
        bullet_speed=bullet_speed,
    )
    ship.angle = tau / 8
    ship.shooting = True
    ship.shoot(bullet_count * gun_cooldown)

    assert len(ship.projectiles) == bullet_count, "Ship should have shot 10 bullets"

    assert all(
        abs((p.pos - ship.pos).angle_to(ship.get_faced_direction())) < EPSILON for p in ship.projectiles
    ), "Bullets should be shot in the direction of the ship"

    reference_delta = ship.projectiles[1].pos - ship.projectiles[0].pos
    previous_projectile_pos = ship.projectiles[1].pos
    for p in ship.projectiles[2:]:
        delta = p.pos - previous_projectile_pos
        assert (reference_delta - delta).length() < EPSILON, "Bullets should be evenly spaced"
        previous_projectile_pos = p.pos


def test_movement():
    ship = Ship(Vec2(0, 0), Vec2(0, 0), 1, 1, Color(0, 0, 0), Color(0, 0, 0), 1, 1)
    ship.thruster_rot_left = True
    ship.step(0.01)
    ship.thruster_rot_left = False
    ship.thruster_forward = True
    ship.step(0.01)
    assert ship.vel.x > 0, "Ship should be moving forward"
    assert ship.vel.y > 0, "Ship should be moving forward"
