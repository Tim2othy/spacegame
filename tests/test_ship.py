from math import tau

import pytest
from pygame.math import Vector2 as Vec2

from physics import PosVel
from ship import Ship, ShipConfig

EPSILON = 1e-8

ORIGIN = PosVel._new_origin_and_only_use_this_if_you_really_know_what_you_are_doing()


def test_cooldown() -> None:
    Ship(ORIGIN, ShipConfig(relative_pos=Vec2(0, 0), gun_cooldown=1))
    with pytest.raises(ValueError):
        Ship(ORIGIN, ShipConfig(relative_pos=Vec2(0, 0), gun_cooldown=-1))
    with pytest.raises(ValueError):
        Ship(ORIGIN, ShipConfig(relative_pos=Vec2(0, 0), gun_cooldown=0))
    with pytest.raises(ValueError):
        Ship(ORIGIN, ShipConfig(relative_pos=Vec2(0, 0), gun_cooldown=float("inf")))
    with pytest.raises(ValueError):
        Ship(ORIGIN, ShipConfig(relative_pos=Vec2(0, 0), gun_cooldown=float("-inf")))
    with pytest.raises(ValueError):
        Ship(ORIGIN, ShipConfig(relative_pos=Vec2(0, 0), gun_cooldown=float("nan")))


def test_shooting() -> None:
    gun_cooldown = 0.123
    bullet_count = 10
    ship = Ship(ORIGIN, ShipConfig(relative_pos=Vec2(0, 0), gun_cooldown=gun_cooldown))

    ship.angle = tau / 8
    ship.shooting = True
    ship.handle_shooting(bullet_count * gun_cooldown)

    assert len(ship.projectiles) == bullet_count, "Ship should have shot 10 bullets"

    assert all(abs(p.pos_relative_to(ship).angle_to(ship.get_faced_direction())) < EPSILON for p in ship.projectiles), (
        "Bullets should be shot in the direction of the ship"
    )

    reference_delta = ship.projectiles[1].pos_relative_to(ship.projectiles[0])
    for i in range(2, len(ship.projectiles)):
        delta = ship.projectiles[i].pos_relative_to(ship.projectiles[i - 1])
        assert (reference_delta - delta).length_squared() < EPSILON, "Bullets should be evenly spaced"


def test_movement() -> None:
    ship = Ship(ORIGIN, ShipConfig(relative_pos=Vec2(0, 0)))
    ship.thruster_rot_left = True
    ship.step(0.01)
    ship.thruster_rot_left = False
    ship.thruster_forward = True
    ship.step(0.01)
    assert ship.vel_relative_to(ORIGIN).x > 0, "Ship should be moving forward"
    assert ship.vel_relative_to(ORIGIN).y > 0, "Ship should be moving upward"
