from typing import TYPE_CHECKING

from pygame import Color
from pygame.math import Vector2 as Vec2

from ship import BulletEnemy, PlayerShip, ShipInput
from universe import Asteroid, Planet, Universe

if TYPE_CHECKING:
    from physics import Disk


def test_planet_gravitation():
    world = Vec2(3000, 3000)
    planet = Planet(world / 2, 1000, Color(0, 0, 0), 1)
    player = PlayerShip(
        world / 4,
        Vec2(100, -200),
        1,
        17,
        Color(0, 0, 0),
        Color(0, 0, 0),
        ShipInput.arrows(),
        "assets/player_ship.png",
    )
    enemy = BulletEnemy(3 * world / 4, Vec2(100, -200), player, world)

    universe = Universe(world, [planet], [player], [enemy], [])
    asteroid = Asteroid(world / 2 + world.rotate(90) / 2, Vec2(100, -200), 1, 10)
    universe.asteroids.append(asteroid)

    for _ in range(60 * 100):
        universe.step(0.01)

    epsilon = 1e-2
    disks: list[Disk] = [player, enemy, asteroid]
    for disk in disks:
        assert abs(1 - (disk.radius + planet.radius) / disk.pos.distance_to(planet.pos)) < epsilon, (
            "Gravity should have pulled the object to the planet's surface within a minute"
        )


def test_mutual_bounce():
    start_y = 15
    start_vel = 5
    asteroid_moving_rightward = Asteroid(Vec2(10, start_y), Vec2(start_vel, 0), 1, 1)
    asteroid_moving_leftward = Asteroid(Vec2(20, start_y), Vec2(-start_vel, 0), 2, 0.9)

    universe = Universe(Vec2(30, 30), [], [], [], [])
    universe.asteroids.append(asteroid_moving_rightward)
    universe.asteroids.append(asteroid_moving_leftward)

    for _ in range(150):
        universe.step(0.01)

    assert asteroid_moving_rightward.pos.x < asteroid_moving_leftward.pos.x, (
        "The asteroids shouldn't fly past each other"
    )
    assert asteroid_moving_rightward.pos.y == asteroid_moving_leftward.pos.y == start_y, (
        "The asteroid shouldn't move vertically at all"
    )
    assert asteroid_moving_rightward.vel.y == asteroid_moving_leftward.vel.y == 0, (
        "The asteroid shouldn't move vertically at all"
    )
    # Test related to https://github.com/Tim2othy/spacegame/issues/9
    assert 0 < asteroid_moving_rightward.vel.x < start_vel * 0.99, (
        "The right asteroid should be moving to the right with less speed"
    )
    assert 0 > asteroid_moving_rightward.vel.x > -start_vel * 0.99, (
        "The left asteroid should be moving to the left with less speed"
    )
