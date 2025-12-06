import random
from itertools import chain
from math import isclose

import pytest
from pygame.math import Vector2 as Vec2

from physics import PosVel
from ship import PlayerConfig, PlayerShip, ShipInput
from universe import Planet, PlanetConfig, Universe


def test_mutual_bounce(monkeypatch: pytest.MonkeyPatch) -> None:
    # Two planets
    #  o   -->        <--  O
    #  planet_a     planet_b
    monkeypatch.setattr(Universe, "apply_gravity", lambda _self, _dt: None)

    universe = Universe(None, 2)
    planet_a = universe.add_planet(PlanetConfig(relative_pos=Vec2(-5, 0), relative_vel=Vec2(5, 0), radius=0.5))
    planet_b = universe.add_planet(PlanetConfig(relative_pos=Vec2(5, 0), relative_vel=Vec2(-5, 0), radius=1.0))
    original_a_state = PosVel(planet_a, Vec2(0, 0), Vec2(0, 0))
    original_b_state = PosVel(planet_b, Vec2(0, 0), Vec2(0, 0))

    for _ in range(150):
        universe.step(0.01)

    assert planet_a.pos_relative_to(planet_b).x < 0, "The planets shouldn't fly past each other"
    assert (
        planet_a.vel_relative_to(original_a_state).y == 0 == planet_b.vel_relative_to(original_b_state).y
    ), "The planets shouldn't move vertically at all"
    # Test related to https://github.com/Tim2othy/spacegame/issues/9
    assert planet_a.vel_relative_to(original_a_state).x < -0.1, "planet_a should be moving to the left with less speed"
    assert planet_b.vel_relative_to(original_b_state).x > 0.1, "planet_b should be moving to the right with less speed"


@pytest.mark.parametrize("direction_angle", [360 * i / 5 for i in range(5)])
def test_newtons_cradle(monkeypatch: pytest.MonkeyPatch, direction_angle: float) -> None:
    # When we have a setup like this:
    #  o-->   oooo
    # We expect it to look something like this afterwards:
    #         oooo    o->
    # (https://en.wikipedia.org/wiki/Newton's_cradle)
    # At least, if bounciness==1, which is not the case here, but
    # we still expect the rightmost planet to gain velocity afterwards.
    monkeypatch.setattr(Universe, "apply_gravity", lambda _self, _dt: None)

    radius = 50
    universe = Universe(None, radius * 2)

    direction = Vec2(0, 0)
    direction.from_polar((radius, direction_angle))

    first_planet = universe.add_planet(PlanetConfig(relative_pos=Vec2(0, 0), relative_vel=direction, radius=radius))
    first_planet_reference = PosVel(first_planet, Vec2(0, 0), Vec2(0, 0))
    other_planets = [
        universe.add_planet(PlanetConfig(relative_pos=2.1 * i * direction, radius=radius)) for i in range(1, 6)
    ]
    last_planet_reference = PosVel(other_planets[-1], Vec2(0, 0), Vec2(0, 0))

    # Run for 2 seconds
    for _ in range(200):
        universe.step(0.01)

    assert (
        first_planet.vel_relative_to(first_planet_reference) * direction < -0.1
    ), "First planet should have lost speed"

    assert (
        other_planets[-1].vel_relative_to(last_planet_reference) * direction > 0.1
    ), "Last planet should have gained speed"


def test_precise_planet_collision(monkeypatch: pytest.MonkeyPatch) -> None:
    # In several different directions, just barely have two planets without gravity graze past each other.
    monkeypatch.setattr(Universe, "apply_gravity", lambda _self, _dt: None)

    radius = 50
    universe = Universe(None, radius * 2)

    num_directions = 23

    hit_planets: list[tuple[Planet, PosVel]] = []

    for i in range(num_directions):
        direction = Vec2(0, 0)
        direction.from_polar((1, i * 360 / num_directions))
        direction_rotated = direction.rotate(90)

        _start_planet = universe.add_planet(
            PlanetConfig(
                relative_pos=direction * num_directions * radius, relative_vel=direction * radius, radius=radius
            )
        )

        hit_planet = universe.add_planet(
            PlanetConfig(
                relative_pos=direction * (num_directions + 1) * radius + 1.99 * direction_rotated * radius,
                radius=radius,
            )
        )
        hit_planet_reference = PosVel(hit_planet, Vec2(0, 0), Vec2(0, 0))
        hit_planets.append((hit_planet, hit_planet_reference))

    # Run the universe for 1 second
    for _ in range(1000):
        universe.step(0.001)

    for hit_planet, hit_planet_reference in hit_planets:
        assert (
            0.001 < hit_planet.vel_relative_to(hit_planet_reference).length() / radius < 0.1
        ), "The hit planet should have gained a tiny bit of velocity"


def test_precise_collision_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    # This is kind of a bad test, because it tests the implementation of universe-collision
    # is correct by testing that it fails if we relax the rules just a little.
    # This is useful to know, to see that the implementation is maximally efficient.
    monkeypatch.setattr(Universe, "apply_gravity", lambda _self, _dt: None)

    # Now, try for 1000 iterations to see the ill effects:
    for _ in range(1000):
        universe = Universe(None, 95 * 2)
        # Setting universe.max_nonstar_size overrides the check for planet-radii, without
        # changing the way chunks are calculated. So planets are added to chunks that are
        # effectively too small for them.
        universe.max_nonstar_size = 100 * 2

        random_relative_pos = Vec2(random.random() * 200, random.random() * 200)
        planet_a = universe.add_planet(PlanetConfig(relative_pos=random_relative_pos, radius=100))

        delta = Vec2(0, 0)
        delta.from_polar((199, random.random() * 360))

        # Now delta has distance 199 from planet_a, so if we put a planet of
        # radius 100 at (pos+delta), then that planet would definitely intersect planet_a,
        # and hence querying planets near (pos+delta) should return planet_a
        planet_b = universe.add_planet(PlanetConfig(relative_pos=delta, radius=100), relative_to=planet_a)
        if planet_a not in universe._nearby_planets(planet_b):
            # We failed successfully.
            return

    pytest.fail(
        "The universe collision-detection should have failed at some point in the above loop, but it did "
        "not, which indicates the implementation of collision-detection is not maximally efficient."
    )


def test_gravitational_well() -> None:
    universe = Universe(None, 10_000 * 2)
    big_planet = universe.add_planet(PlanetConfig(relative_pos=Vec2(0, 0), radius=10_000))

    num_disks = 23
    for i in range(num_disks):
        pos = Vec2(0, 0)
        pos.from_polar((12_500, 360 * i / num_disks))
        if i % 4 == 0 or i % 3 == 0:
            ship_config = PlayerConfig(relative_pos=pos, relative_vel=Vec2(100, -200), ship_input=ShipInput.wasd())
            universe.add_player(ship_config, relative_to=big_planet)
        else:
            universe.add_planet(
                PlanetConfig(relative_pos=pos, relative_vel=Vec2(100, -200), radius=2 * (i * 31) % 29),
                relative_to=big_planet,
            )

    for _ in range(25 * 100):
        universe.step(0.01)

    disks: list[Planet | PlayerShip] = list(chain(*universe._planet_chunks.values())) + universe._player_ships
    assert len(disks) == num_disks + 1, (
        "The universe should still contain exactly `num_disks+1` disks."
        " This test might fail because player-ships or planets are destroyed when crashing into the planet."
    )
    for disk in disks:
        dist = disk.distance_to(big_planet)
        # Don't consider the distance of the big planet from itself.
        if dist != 0:
            assert isclose(disk.radius + big_planet.radius, dist, rel_tol=1e-3), (
                "Gravity should have pulled the object to the planet's surface within 25 seconds."
                " This test might fail because player-ships or planets are destroyed when crashing into the planet."
            )


def test_planet_generation() -> None:
    # Test that planets generated by generate_planet are not too large or too small.

    universe = Universe(1400, 2 * 1400)

    # run test 10 times
    for _ in range(10):
        planets = universe.add_planets(10)

        for planet in planets:
            assert 200 < planet.radius < 1200, f"Planet has invalid radius: {planet.radius}"


def test_empty_universe() -> None:
    universe = Universe(None, 10000)
    planets = universe.add_planets(5)
    assert len(planets) == 0, "Universe should have generated 0 planets"


def test_orbit_stability() -> None:
    """Test that planets generated in orbit remain stable and don't crash into the star."""
    star_size = 1400
    universe = Universe(star_size, 2 * star_size)
    planets = universe.add_planets(10)

    # Run simulation for 40 seconds
    for step in range(40000):
        universe.step(0.01)

        star = getattr(universe, "_Universe__star", None) if hasattr(universe, "_Universe__star") else None
        if star and hasattr(star, "radius"):
            for planet in planets:
                distance = planet.distance_to(star)
                if distance < (planet.radius + star.radius):
                    pytest.fail(f"Planet collided with star at step {step}.")
