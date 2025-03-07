import random
from math import isclose
from typing import TYPE_CHECKING

import pytest
from pygame.math import Vector2 as Vec2

from ship import PlayerShip
from universe import Planet, Star, Universe

if TYPE_CHECKING:
    from physics import Disk


def test_star_gravitation():
    world = Vec2(3000, 3000)
    worldcenter = world / 2
    star = Star(world / 2, 1000)

    planet = []
    players = []
    num_disks = 23
    for i in range(num_disks):
        offset = Vec2()
        offset.from_polar((1500, 360 * i / num_disks))
        pos = worldcenter + offset
        if i % 4 == 0 or i % 3 == 0:
            players.append(PlayerShip(pos, Vec2(100, -200)))
        else:
            planet.append(Planet(pos, Vec2(100, -200), radius=2 * (i * 31) % 29))

    universe = Universe(world, [star], players, [], max(*(a.radius for a in planet), *(p.radius for p in players)) * 2)
    universe.add_planet(*planet)

    for _ in range(30 * 100):
        universe.step(0.01)

    disks: list[Disk] = planet + players
    for disk in disks:
        assert isclose(disk.radius + star.radius, disk._pos.distance_to(star._pos), rel_tol=1e-3), (
            "Gravity should have pulled the object to the star's surface within 30 seconds"
        )


@pytest.mark.parametrize("absolute_vel", [30 * Vec2(i, j) for i in range(-1, 2) for j in range(-1, 2)])
def test_mutual_bounce(absolute_vel: Vec2):
    # Two planets
    #  o   →               ←   O
    #  planet_a     planet_b

    # Bounces should be relative to the two planets' velocities:
    start_y = 15
    relative_vel = Vec2(5, 0)
    # Boost both planets by absolute_vel
    planet_a = Planet(Vec2(10, start_y), absolute_vel + relative_vel, 1)
    planet_b = Planet(Vec2(20, start_y), absolute_vel - relative_vel, 0.9)

    universe = Universe(Vec2(30, 30), [], [], [], max(planet_a.radius, planet_b.radius) * 2)
    universe.add_planet(planet_a, planet_b)

    for _ in range(150):
        universe.step(0.01)

    assert planet_a._pos.x < planet_b._pos.x, "The planets shouldn't fly past each other"
    assert planet_a._vel.y == planet_b._vel.y == absolute_vel.y, "The planets shouldn't move vertically at all"
    # Test related to https://github.com/Tim2othy/spacegame/issues/9
    assert absolute_vel.x > planet_a._vel.x > (absolute_vel - relative_vel).x - 0.1, (
        "planet_a should be moving to the left with less speed"
    )
    assert absolute_vel.x < planet_b._vel.x < (absolute_vel + relative_vel).x - 0.1, (
        "planet_b should be moving to the right with less speed"
    )


@pytest.mark.parametrize("direction_angle", [360 * i / 5 for i in range(5)])
def test_newtons_cradle(direction_angle: float):
    # When we have a setup like this:
    #  o-->   oooo
    # We expect it to look something like this afterwards:
    #         oooo    o->
    # (https://en.wikipedia.org/wiki/Newton's_cradle)
    # At least, if bounciness==1, which is not the case here, but
    # we still expect the rightmost planet to gain velocity afterwards.

    world = Vec2(3000, 3000)
    planet_radius = 50

    direction = Vec2()
    direction.from_polar((planet_radius, direction_angle))

    universe = Universe(world, [], [], [], planet_radius * 2)
    first_planet = Planet(world / 2, direction, planet_radius)
    universe.add_planet(first_planet)
    other_planets = [Planet(world / 2 + 2.1 * i * direction, Vec2(), planet_radius) for i in range(1, 6)]
    universe.add_planet(*other_planets)

    # Run for 2 seconds
    for _ in range(200):
        universe.step(0.01)

    assert first_planet._vel * direction < planet_radius**2, "First planet should have lost speed"
    assert other_planets[-1]._vel * direction > 0.01, "Last planet should have gained speed"


def test_precise_planet_collision():
    # In several different directions, just barely have two planets without gravity graze past each other.

    world = Vec2(3000, 3000)
    planet_radius = 50

    num_directions = 23

    universe = Universe(world, [], [], [], planet_radius * 2)

    universe.apply_gravity = lambda dt: None  # noqa: ARG005
    start_planets: list[Planet] = []
    hit_planets: list[Planet] = []

    for i in range(num_directions):
        direction = Vec2()
        direction.from_polar((1, i * 360 / num_directions))
        direction_rotated = direction.rotate(90)

        start_planet = Planet(
            world / 2 + direction * num_directions * planet_radius,
            direction * planet_radius,
            planet_radius,
        )
        start_planets.append(start_planet)
        hit_planet = Planet(
            world / 2 + direction * (num_directions + 1) * planet_radius + 1.99 * direction_rotated * planet_radius,
            Vec2(0, 0),
            planet_radius,
        )
        hit_planets.append(hit_planet)

        universe.add_planet(start_planet, hit_planet)

    # Run the universe for 1 second
    for _ in range(1000):
        universe.step(0.001)

    for hit_planet in hit_planets:
        assert 0.001 < hit_planet._vel.magnitude() / planet_radius < 0.1, (
            "The hit planet should have gained a tiny bit of velocity"
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
        # Setting universe.max_nonstar_size overrides the check for planet-radii, without
        # changing the way chunks are calculated. So planets are added to chunks that are
        # effectively too small for them.
        universe.max_nonstar_size = 200

        pos = world / 2 + Vec2(random.random() * 200, random.random() * 200)
        planet_a = Planet(pos, Vec2(), 100)
        universe.add_planet(planet_a)

        delta = Vec2()
        delta.from_polar((199, random.random() * 360))

        # Now pos + delta has distance 199 from planet_a, so if we put an planet of
        # radius 200 at (pos+delta), then that planet would definitely intersect planet_a,
        # and hence querying planets near (pos+delta) should return planet_a

        if planet_a not in universe._nearby_planets(pos + delta):  # noqa: SLF001
            # Verify it really would fail successfully:
            planet_b = Planet(pos + delta, Vec2(), 100)
            universe.add_planet(planet_b)
            assert planet_a.intersects_disk(planet_b), (
                "The two planets should intersect, the test-setup did not go as expected."
            )
            universe.apply_bounce()
            assert planet_a._pos == pos, "planet_a should be unaffected, because collision-tests failed"
            assert planet_b._pos == pos + delta, "planet_b should be unaffected, because collision-tests failed"
            return

    pytest.fail(
        "The universe collision-detection should have failed at some point in the above loop, but it did "
        "not, which indicates the implementation of collision-detection is not maximally efficient."
    )
