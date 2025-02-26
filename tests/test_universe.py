import random
from typing import TYPE_CHECKING

import pytest
from pygame import Color
from pygame.math import Vector2 as Vec2

from ship import BulletEnemy, PlayerShip
from universe import Asteroid, Planet, Universe

if TYPE_CHECKING:
    from physics import Disk


def test_planet_gravitation():
    world = Vec2(3000, 3000)
    planet = Planet(world / 2, 1000, Color(0, 0, 0))
    player = PlayerShip(world / 4, Vec2(100, -200))
    enemy = BulletEnemy(3 * world / 4, Vec2(100, -200), player)

    asteroid = Asteroid(world / 2 + world.rotate(90) / 2, Vec2(100, -200), 10)
    universe = Universe(
        world, [planet], [player], [enemy], max(player.radius, enemy.radius, asteroid.radius) * 2
    )
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
        asteroid_a = Asteroid(Vec2(10, start_y), absolute_vel + relative_vel, 1)
        asteroid_b = Asteroid(Vec2(20, start_y), absolute_vel - relative_vel, 0.9)

        universe = Universe(Vec2(30, 30), [], [], [], max(asteroid_a.radius, asteroid_b.radius) * 2)
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
        direction.from_polar((asteroid_radius, i * 360 / 5))

        universe = Universe(world, [], [], [], asteroid_radius * 2)
        first_asteroid = Asteroid(world / 2, direction, asteroid_radius)
        universe.add_asteroids(first_asteroid)
        other_asteroids = [
            Asteroid(world / 2 + 2.1 * i * direction, Vec2(), asteroid_radius) for i in range(1, 6)
        ]
        universe.add_asteroids(*other_asteroids)

        # Run for 2 seconds
        for _ in range(200):
            universe.step(0.01)

        assert first_asteroid.vel * direction < asteroid_radius**2, "First asteroid should have lost speed"
        assert other_asteroids[-1].vel * direction > 0.01, "Last asteroid should have gained speed"


def test_precise_asteroid_collision():
    # In several different directions, just barely have two asteroids graze past each other.

    world = Vec2(3000, 3000)
    asteroid_radius = 50

    num_directions = 23

    universe = Universe(world, [], [], [], asteroid_radius * 2)

    start_asteroids: list[Asteroid] = []
    hit_asteroids: list[Asteroid] = []

    for i in range(num_directions):
        direction = Vec2()
        direction.from_polar((1, i * 360 / num_directions))
        direction_rotated = direction.rotate(90)

        start_asteroid = Asteroid(
            world / 2 + direction * num_directions * asteroid_radius,
            direction * asteroid_radius,
            asteroid_radius,
        )
        start_asteroids.append(start_asteroid)
        hit_asteroid = Asteroid(
            world / 2
            + direction * (num_directions + 1) * asteroid_radius
            + 1.99 * direction_rotated * asteroid_radius,
            Vec2(0, 0),
            asteroid_radius,
        )
        hit_asteroids.append(hit_asteroid)

        universe.add_asteroids(start_asteroid, hit_asteroid)

    # Run the universe for 1 second
    for _ in range(1000):
        universe.step(0.001)

    for hit_asteroid in hit_asteroids:
        assert 0.001 < hit_asteroid.vel.magnitude() / asteroid_radius < 0.1, (
            "The hit asteroid should have gained a tiny bit of velocity"
        )


def test_precise_collision_failures():
    # This is kind of a bad test, because it tests the implementation of universe-collision
    # is correct by testing that it fails if we relax the rules just a little.
    # This is useful to know, to see that the implementation is maximally efficient.

    world = Vec2(1000, 1000)
    # Now, try for 1000 iterations to see the ill effects:
    for _ in range(1000):
        # This sets the universe-chunk-calculation
        universe = Universe(world, [], [], [], 190)
        # Setting universe.max_nonplanet_size overrides the check for asteroid-radii, without
        # changing the way chunks are calculated. So asteroids are added to chunks that are
        # effectively too small for them.
        universe.max_nonplanet_size = 200

        pos = world / 2 + Vec2(random.random() * 200, random.random() * 200)
        asteroid_a = Asteroid(pos, Vec2(), 100)
        universe.add_asteroids(asteroid_a)

        delta = Vec2()
        delta.from_polar((199, random.random() * 360))

        # Now pos + delta has distance 199 from asteroid_a, so if we put an asteroid of
        # radius 200 at (pos+delta), then that asteroid would definitely intersect asteroid_a,
        # and hence querying asteroids near (pos+delta) should return asteroid_a

        if asteroid_a not in universe._nearby_asteroids(pos + delta):  # noqa: SLF001
            # Verify it really would fail successfully:
            asteroid_b = Asteroid(pos + delta, Vec2(), 100)
            universe.add_asteroids(asteroid_b)
            assert asteroid_a.intersects_disk(asteroid_b), (
                "The two asteroids should intersect, the test-setup did not go as expected."
            )
            universe.apply_bounce()
            assert asteroid_a.pos == pos, "asteroid_a should be unaffected, because collision-tests failed"
            assert asteroid_b.pos == pos + delta, (
                "asteroid_b should be unaffected, because collision-tests failed"
            )
            return

    pytest.fail(
        "The universe collision-detection should have failed at some point in the above loop, but it did "
        "not, which indicates the implementation of collision-detection is not maximally efficient."
    )
