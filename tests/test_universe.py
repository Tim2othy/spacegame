from universe import Planet, Universe, Asteroid
from pygame.math import Vector2 as Vec2
from pygame import Color


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


def test_stable_orbits():
    for _ in range(10):
        world = Vec2(500, 500)
        planet = Planet(world / 2, 100, Color(0, 0, 0), 1)
        universe = Universe(world, [planet], [], [], [])
        universe.generate_asteroid(planet)
        asteroid = universe.asteroids[0]

        start = asteroid.pos
        previous_distance = 0
        was_previously_approaching = False
        last_orbit_duration = None
        last_orbit_timestamp = 0

        epsilon = 1e-4

        # 300 seconds
        for t in range(300 * 100):
            universe.step(0.01)
            distance = start.distance_to(asteroid.pos)

            if was_previously_approaching and distance > previous_distance:
                # Our distance to `start` is locally minimal
                assert distance < epsilon

                period_length = t - last_orbit_timestamp
                if last_orbit_duration is not None:
                    assert abs(1 - last_orbit_duration / period_length) < epsilon, (
                        "Orbits should take roughly the same duration"
                    )

                last_orbit_timestamp = t
                last_orbit_duration = period_length

                was_previously_approaching = False

            was_previously_approaching = distance < previous_distance
            previous_distance = distance

        assert last_orbit_duration is not None, (
            "The asteroid should complete at least one orbit in 300 seconds"
        )
