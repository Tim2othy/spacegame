from math import tau

from pygame.math import Vector2 as Vec2

from physics import PosVel
from ship import PlayerConfig, PlayerShip, RotationState, Ship, ShipConfig, ThrustState

EPSILON = 1e-8

ORIGIN = PosVel._new_origin_and_only_use_this_if_you_really_know_what_you_are_doing()


def test_shooting() -> None:
    bullet_count = 10
    ship = Ship(ORIGIN, ShipConfig(relative_pos=Vec2(0, 0)))
    ship._SHIP_GUN_COOLDOWN = 0.123
    ship.angle = tau / 8
    ship.shooting = True
    ship.handle_shooting(bullet_count * ship._SHIP_GUN_COOLDOWN)

    assert len(ship.projectiles) == bullet_count, "Ship should have shot 10 bullets"

    assert all(
        abs(p.pos_relative_to(ship).angle_to(ship.get_faced_direction())) < EPSILON for p in ship.projectiles
    ), "Bullets should be shot in the direction of the ship"

    reference_delta = ship.projectiles[1].pos_relative_to(ship.projectiles[0])
    for i in range(2, len(ship.projectiles)):
        delta = ship.projectiles[i].pos_relative_to(ship.projectiles[i - 1])
        assert (reference_delta - delta).length_squared() < EPSILON, "Bullets should be evenly spaced"


def test_movement() -> None:
    ship = PlayerShip(ORIGIN, PlayerConfig(relative_pos=Vec2(0, 0)))
    ship.increment_rot_counters(RotationState.LEFT)
    ship.step(0.01)
    ship.thrust_state = ThrustState.FORWARD
    ship.step(0.01)
    assert ship.vel_relative_to(ORIGIN).x > 0, "Ship should be moving forward"
    assert ship.vel_relative_to(ORIGIN).y > 0, "Ship should be moving upward"


def test_ship_rotation() -> None:
    """
    Rotate ship by calling rotating(True, False) until
    ship.angle reaches ~70. Then release the input, allow the ship to decelerate,
    and verify that the final angle settles near 140°.
    """
    ship = PlayerShip(ORIGIN, PlayerConfig(relative_pos=Vec2(0, 0)))

    for _ in range(5000):
        if ship.angle < 70:
            ship.increment_rot_counters(RotationState.LEFT)

        ship.step(0.01)
        if abs(ship.angular_velocity) < 0.01 and ship.rotation_state == RotationState.NONE:
            break

    tol_final = 4.0
    assert abs(ship.angle - 140) < tol_final, f"Final angle {ship.angle} should be close to 140°"
