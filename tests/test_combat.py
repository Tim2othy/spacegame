import random
import sys

import pytest
from pygame.math import Vector2 as Vec2

from enemy_ai import (
    _LOW_HEALTH_AND_PLAYER_VISIBLE_MATRIX,
    _LOW_HEALTH_MATRIX,
    _PLAYER_VISIBLE_MATRIX,
    _STANDARD_MATRIX,
    AIState,
)
from physics import MovingObject
from ship import HEALTH, BulletEnemy, MarkovEnemy, MissileEnemy, PlayerShip, RocketEnemy
from universe import Planet, Universe


@pytest.mark.parametrize("enemy_type", [BulletEnemy, RocketEnemy, MissileEnemy, MarkovEnemy])
def test_enemy_hostility(enemy_type: type[BulletEnemy]) -> None:
    """Verify that any enemy will eventually find and hit the player."""
    world = Vec2(1000, 1000)
    player_ship = PlayerShip(MovingObject.ur(), world / 2, Vec2())
    random_relative_pos = Vec2(random.random() * world.x, random.random() * world.y) / 2.0

    enemy = enemy_type(player_ship, random_relative_pos, Vec2(0, 0), player_ship)

    universe = Universe(
        world, sys.float_info.epsilon, [player_ship], [enemy], max(player_ship.radius, enemy.radius) * 2
    )
    starting_health = player_ship.health

    # 30 seconds
    for _ in range(3000):
        universe.step(0.01)
        if player_ship.health < starting_health:
            break

    assert player_ship.health < starting_health


@pytest.mark.parametrize("enemy_type", [BulletEnemy, RocketEnemy, MissileEnemy])
# TODO: add MarkovEnemy here and make sure test passes
def test_bullet_paths(enemy_type: type[BulletEnemy]) -> None:
    world = Vec2(1000, 1000)
    player_ship = PlayerShip(MovingObject.ur(), world / 2, Vec2())

    enemy_right = enemy_type(player_ship, Vec2(500, 0), Vec2(0, 0), player_ship)
    enemy_up = enemy_type(player_ship, Vec2(0, 500), Vec2(0, 0), player_ship)

    planet = Planet(player_ship, Vec2(250, 0), Vec2(0, 0), 1)
    universe = Universe(
        world,
        sys.float_info.epsilon,
        [player_ship],
        [enemy_right, enemy_up],
        max(player_ship.radius, enemy_right.radius, enemy_up.radius, planet.radius) * 2,
    )
    universe.add_planet(planet)

    bullet_right = player_ship.new_bullet(Vec2(), Vec2(100, 0))
    bullet_up = player_ship.new_bullet(Vec2(), Vec2(0, 100))

    player_ship.projectiles.append(bullet_right)
    player_ship.projectiles.append(bullet_up)

    # Also try shooting the enemy on the right with enemy bullets (hopefully won't work)
    enemy_up.new_bullet(enemy_right.pos_relative_to(enemy_up) - Vec2(1, 0), Vec2(0.1, 0))
    enemy_right.new_bullet(-Vec2(1, 0), Vec2(0.1, 0))

    # 10 seconds
    for _ in range(1000):
        # Cull enemies to prevent them from moving
        for enemy in [enemy_up, enemy_right]:
            enemy.action_timer = 1e8
            enemy.seek_towards = MovingObject(enemy, Vec2(), Vec2())
            enemy.current_action = BulletEnemy.Action.accelerate_randomly
        universe.step(0.01)

    assert len(player_ship.projectiles) == 0, "Both bullets should have hit something"
    assert (enemy_right.health == HEALTH) is not (enemy_up.health == HEALTH), "Exactly one enemy should be unharmed"
    assert universe._enemy_ships[0].health == HEALTH, "The enemy on the right should be unharmed"


@pytest.mark.parametrize(
    "matrix",
    [
        _STANDARD_MATRIX,
        _LOW_HEALTH_MATRIX,
        _PLAYER_VISIBLE_MATRIX,
        _LOW_HEALTH_AND_PLAYER_VISIBLE_MATRIX,
    ],
)
def test_transition_matrix_sums(matrix: dict) -> None:
    """Verify that each row in the transition matrices sums to 1."""
    for from_state, transitions in matrix.items():
        total = sum(transitions.values())
        assert total == 1.0, f"Row for {from_state} does not sum to 1: {total}"


def test_markov_enemy_retreat_behavior() -> None:
    """Test that a MarkovEnemy moves away from player when in retreat mode."""
    world = Vec2(1000, 1000)
    player = PlayerShip(world / 2, Vec2())
    enemy = MarkovEnemy(world / 2 + Vec2(100, 100), Vec2(), player)
    universe = Universe(world, [], [player], [enemy], max(player.radius, enemy.radius) * 2)

    # Run simulation for a few seconds
    for _ in range(10):
        distance_squared_0 = player.distance_to(enemy)
        for _ in range(100):
            enemy.ai.current_state = AIState.RETREAT
            universe.step(0.01)

        distance_squared_1 = player.distance_to(enemy)
        assert distance_squared_0 < distance_squared_1, "Enemy should move away from player in retreat mode"


def test_markov_enemy_aim() -> None:
    """Test that a MarkovEnemy will hit a moving player."""
    world = Vec2(5000, 5000)
    player_ship = PlayerShip(world / 2, Vec2(50, 40))
    enemy = MarkovEnemy(world / 2 + Vec2(-800, 400), Vec2(27, -42), player_ship)
    universe = Universe(world, [], [player_ship], [enemy], max(player_ship.radius, enemy.radius) * 2)

    # Run simulation for a few seconds
    for _ in range(200):
        enemy.ai.current_state = AIState.AIM
        universe.step(0.01)

    assert player_ship.health != HEALTH, "Enemy should have hit the player"


def test_markov_low_health_search() -> None:
    """Test whether a low health MarkovEnemy eventually finds a distant player."""
    world = Vec2(80000, 80000)
    player_ship = PlayerShip(Vec2(1000, 1000), Vec2())
    enemy = MarkovEnemy(Vec2(79500, 79500), Vec2(), player_ship)
    universe = Universe(world, [], [player_ship], [enemy], max(player_ship.radius, enemy.radius) * 2)
    enemy.health = 1
    enemy.ai.current_state = AIState.RETREAT

    for _ in range(100000):
        universe.step(0.01)
        if player_ship.health < HEALTH:
            break

    assert player_ship.health < HEALTH, "Enemy should have eventually found and damaged player"
