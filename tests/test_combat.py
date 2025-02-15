import random

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from constants import ENEMY_VISUAL_RANGE
from ship import BulletEnemy, MissileEnemy, PlayerShip, RocketEnemy, ShipInput
from universe import Universe


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

    enemies = [
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
