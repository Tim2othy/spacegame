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

        universe = Universe(Vec2(30, 30), [], [], [], [])
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
