import random

import pytest
from pygame.math import Vector2 as Vec2

from constants import (
    HEALTH,
)
from enemy_ai import (
    _LOW_HEALTH_AND_PLAYER_VISIBLE_MATRIX,
    _LOW_HEALTH_MATRIX,
    _PLAYER_VISIBLE_MATRIX,
    _STANDARD_MATRIX,
)
from ship import BulletEnemy, MarkovEnemy, MissileEnemy, PlayerShip, RocketEnemy
from universe import Asteroid, Universe


@pytest.mark.parametrize("enemy_type", [BulletEnemy, RocketEnemy, MissileEnemy, MarkovEnemy])
def test_enemy_hostility(enemy_type: type[BulletEnemy]):
    """Verify that any enemy will eventually find and hit the player."""
    world = Vec2(1000, 1000)
    player_ship = PlayerShip(world / 2, Vec2())

    enemy = enemy_type(Vec2(random.random() * world.x, random.random() * world.y), Vec2(0, 0), player_ship)

    universe = Universe(world, [], [player_ship], [enemy], max(player_ship.radius, enemy.radius) * 2)
    starting_health = player_ship.health

    # 30 seconds
    for _ in range(3000):
        universe.step(0.01)
        if player_ship.health < starting_health:
            break

    assert player_ship.health < starting_health


@pytest.mark.parametrize("enemy_type", [BulletEnemy, RocketEnemy, MissileEnemy])
def test_bullet_paths(enemy_type: type[BulletEnemy]):
    world = Vec2(1000, 1000)
    player_ship = PlayerShip(world / 2, Vec2())

    enemy_start_right = Vec2(player_ship.pos + Vec2(500, 0))
    enemy_start_up = Vec2(player_ship.pos + Vec2(0, 500))
    enemy_right = enemy_type(enemy_start_right, Vec2(0, 0), player_ship)
    enemy_up = enemy_type(enemy_start_up, Vec2(0, 0), player_ship)

    asteroid = Asteroid(player_ship.pos + Vec2(250, 0), Vec2(0, 0), 1)
    universe = Universe(
        world,
        [],
        [player_ship],
        [enemy_right, enemy_up],
        max(player_ship.radius, enemy_right.radius, enemy_up.radius, asteroid.radius) * 2,
    )
    universe.add_asteroids(asteroid)

    bullet_right = player_ship.new_bullet(player_ship.pos, Vec2(100, 0))
    bullet_up = player_ship.new_bullet(player_ship.pos, Vec2(0, 100))

    player_ship.projectiles.append(bullet_right)
    player_ship.projectiles.append(bullet_up)

    # Also try shooting the enemy on the right with enemy bullets (hopefully won't work)
    enemy_up.new_bullet(enemy_right.pos - Vec2(1, 0), Vec2(0.1, 0))
    enemy_right.new_bullet(enemy_right.pos - Vec2(1, 0), Vec2(0.1, 0))

    # 10 seconds
    for _ in range(1000):
        # Cull enemies to prevent them from moving
        for enemy in [enemy_up, enemy_right]:
            enemy.action_timer = 1e8
            enemy.current_action = BulletEnemy.Action.decelerate
        universe.step(0.01)

    assert len(player_ship.projectiles) == 0, "Both bullets should have hit something"
    assert (enemy_right.health == HEALTH) is not (
        enemy_up.health == HEALTH
    ), "Exactly one enemy should be unharmed"
    assert (
        universe._enemy_ships[0].health == HEALTH  # noqa: SLF001
    ), "The enemy on the right should be unharmed"


@pytest.mark.parametrize(
    "matrix",
    [
        _STANDARD_MATRIX,
        _LOW_HEALTH_MATRIX,
        _PLAYER_VISIBLE_MATRIX,
        _LOW_HEALTH_AND_PLAYER_VISIBLE_MATRIX,
    ],
)
def test_transition_matrix_sums(matrix: dict):
    """Verify that each row in the transition matrices sums to 1."""
    for from_state, transitions in matrix.items():
        total = sum(transitions.values())
        assert total == 1.0, f"Row for {from_state} does not sum to 1: {total}"
