import math
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

    universe = Universe(world, [planet], [player], [enemy])
    asteroid = Asteroid(world / 2 + world.rotate(90) / 2, Vec2(100, -200), 1, 10)
    universe.add_asteroids(asteroid)

    for _ in range(60 * 100):
        universe.step(0.01)

    epsilon = 1e-2
    disks: list[Disk] = [player, enemy, asteroid]
    for disk in disks:
        assert abs(1 - (disk.radius + planet.radius) / disk.pos.distance_to(planet.pos)) < epsilon, (
            "Gravity should have pulled the object to the planet's surface within a minute"
        )


def test_mutual_bounce():
    # Two asteroids
    #  o   →               ←   O
    #  asteroid_a     asteroid_b

    # Bounces should be relative to the two asteroids' velocities:
    for absolute_vel in [30 * Vec2(i, j) for i in range(-1, 2) for j in range(-1, 2)]:
        start_y = 15
        relative_vel = Vec2(5, 0)
        # Boost both asteroids by absolute_vel
        asteroid_a = Asteroid(Vec2(10, start_y), absolute_vel + relative_vel, 1, 1)
        asteroid_b = Asteroid(Vec2(20, start_y), absolute_vel - relative_vel, 2, 0.9)

        universe = Universe(Vec2(30, 30), [], [], [])
        universe.add_asteroids(asteroid_a, asteroid_b)

        for _ in range(150):
            universe.step(0.01)

        assert asteroid_a.pos.x < asteroid_b.pos.x, "The asteroids shouldn't fly past each other"
        assert asteroid_a.vel.y == asteroid_b.vel.y == absolute_vel.y, (
            "The asteroids shouldn't move vertically at all"
        )
        # Test related to https://github.com/Tim2othy/spacegame/issues/9
        assert absolute_vel.x > asteroid_a.vel.x > (absolute_vel - relative_vel).x - 0.1, (
            "asteroid_a should be moving to the left with less speed"
        )
        assert absolute_vel.x < asteroid_b.vel.x < (absolute_vel + relative_vel).x - 0.1, (
            "asteroid_b should be moving to the right with less speed"
        )


def test_newtons_cradle():
    # When we have a setup like this:
    #  o->   oooo
    # We expect it to look something like this afterwards:
    #        oooo    o->
    # (https://en.wikipedia.org/wiki/Newton's_cradle)
    # At least, if bounciness==1, which is not the case here, but
    # we still expect the rightmost asteroid to gain velocity afterwards.

    world = Vec2(3000, 3000)
    asteroid_radius = 50

    # Do this 5 times for different directions
    for i in range(5):
        direction = Vec2()
        direction.from_polar((asteroid_radius, i * math.tau / 5))

        universe = Universe(world, [], [], [])
        first_asteroid = Asteroid(world / 2, direction, 1, asteroid_radius)
        universe.add_asteroids(first_asteroid)
        other_asteroids = [
            Asteroid(world / 2 + 2 * i * direction, Vec2(), 1, asteroid_radius) for i in range(2, 7)
        ]
        universe.add_asteroids(*other_asteroids)

        # Run for 2 seconds
        for _ in range(200):
            universe.step(0.01)

        assert first_asteroid.vel * direction < asteroid_radius, "First asteroid should have lost speed"
        assert other_asteroids[-1].vel * direction > 0, "Last asteroid should have gained speed"
