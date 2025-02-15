from universe import Universe, Asteroid
from pygame.math import Vector2 as Vec2


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
