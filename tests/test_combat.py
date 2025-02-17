import random

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from constants import ENEMY_VISUAL_RANGE
from ship import BulletEnemy, MissileEnemy, PlayerShip, RocketEnemy, ShipInput
from universe import Asteroid, Universe


def new_player_ship(pos: Vec2) -> PlayerShip:
    return PlayerShip(
        pos,
        Vec2(),
        1,
        10,
        Color(0, 0, 0),
        Color(0, 0, 0),
        ShipInput(
            pygame.K_RIGHT,
            pygame.K_LEFT,
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_RETURN,
        ),
        "assets/player_ship.png",
    )


def test_enemy_hostility():
    """Verify that any enemy will eventually find and hit the player."""
    world = Vec2(ENEMY_VISUAL_RANGE / 4, ENEMY_VISUAL_RANGE / 4)
    player_ship = new_player_ship(world / 2)

    def random_worldvec() -> Vec2:
        return Vec2(random.random() * world.x, random.random() * world.y)

    enemies: list[BulletEnemy] = [
        ship_type(random_worldvec(), Vec2(0, 0), player_ship, world)
        for ship_type in [BulletEnemy, RocketEnemy, MissileEnemy]
    ]

    for enemy in enemies:
        universe = Universe(world, [], [player_ship], [enemy], [])
        starting_health = player_ship.health

        # 30 seconds
        for _ in range(3000):
            universe.step(0.01)
            if player_ship.health < starting_health:
                break

        assert player_ship.health < starting_health


def test_bullet_paths():
    world = Vec2(ENEMY_VISUAL_RANGE / 4, ENEMY_VISUAL_RANGE / 4)
    player_ship = new_player_ship(world / 2)

    def random_worldvec() -> Vec2:
        return Vec2(random.random() * world.x, random.random() * world.y)

    enemy_start_right = Vec2(player_ship.pos + Vec2(500, 0))
    enemy_start_up = Vec2(player_ship.pos + Vec2(0, 500))
    enemy_groups: list[tuple[BulletEnemy, BulletEnemy]] = [
        (
            ship_type(enemy_start_right, Vec2(0, 0), player_ship, world),
            ship_type(enemy_start_up, Vec2(0, 0), player_ship, world),
        )
        for ship_type in [BulletEnemy, RocketEnemy, MissileEnemy]
    ]

    for enemy_right, enemy_up in enemy_groups:
        universe = Universe(world, [], [player_ship], [enemy_right, enemy_up], [])
        universe.asteroids.append(Asteroid(player_ship.pos + Vec2(250, 0), Vec2(0, 0), 1, 20))

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
            for enemy in universe.enemy_ships:
                enemy.action_timer = 1e8
                enemy.current_action = BulletEnemy.Action.decelerate
            universe.step(0.01)

        assert len(player_ship.projectiles) == 0, "Both bullets should have hit something"
        assert len(universe.enemy_ships) == 1, "One enemy should be unharmed"
        assert universe.enemy_ships[0].pos == enemy_start_right, "The enemy on the right should be unharmed"
