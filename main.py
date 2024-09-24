"""Staging-grounds for the game."""

from __future__ import annotations

import random
import sys

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from camera import Camera
from ship import BulletEnemy, RocketEnemy, ShipInput
from universe import Area, Asteroid, RefuelArea, TrophyArea, Universe

from variables import (
    TEST_MODE,
    SCREEN_SIZE,
    MINIMAP_SIZE,
    WORLD_SIZE,
    SPAWNPOINT,
    planets,
    player_ships,
)

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Space Game")


SCREEN_SURFACE = pygame.display.set_mode(SCREEN_SIZE)


asteroids: list[Asteroid] = []
for _ in range(40):
    pos = Vec2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
    radius = random.uniform(10, 200)
    asteroids.append(Asteroid(pos, Vec2(0, 0), 1, radius, Color("white")))

enemy_ships: list[BulletEnemy] = []
for _ in range(20):
    pos = Vec2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
    if random.random() > 0.5:
        enemy_ships.append(BulletEnemy(pos, Vec2(0, 0), random.choice(player_ships)))
    else:
        enemy_ships.append(RocketEnemy(pos, Vec2(0, 0), random.choice(player_ships)))


areas: list[Area] = []

"""
areas: list[Area] = [
    RefuelArea(pygame.Rect((7_000, 1_000), (200, 200))),
    TrophyArea(pygame.Rect((3_000, 8_000), (200, 200))),
]
"""

universe = Universe(
    WORLD_SIZE,
    planets,
    asteroids,
    player_ships,
    areas,
    enemy_ships,
    ["assets/astral-0.png", "assets/astral-1.png", "assets/astral-1.png"],
)
cameras: list[Camera] = []

player_count = len(player_ships)
for player_ix, player in enumerate(player_ships):
    # TODO: Probably fix the off-by-one-error in here.
    topleft = (player_ix * SCREEN_SIZE.x / player_count, 0)
    size = (SCREEN_SIZE.x / player_count, SCREEN_SIZE.y)
    subsurface = SCREEN_SURFACE.subsurface((topleft, size))
    camera = Camera(player.pos, 1.0, subsurface)
    cameras.append(camera)

minimap_surface = SCREEN_SURFACE.subsurface(
    ((SCREEN_SIZE.x - MINIMAP_SIZE.x, 0), MINIMAP_SIZE),
)

minimap_camera = Camera(WORLD_SIZE / 2, MINIMAP_SIZE.x / WORLD_SIZE.x, minimap_surface)

clock = pygame.time.Clock()

while True:
    dt = clock.tick() / 1_000

    if any(e.type == pygame.QUIT for e in pygame.event.get()):
        break

    universe.handle_input(pygame.key.get_pressed())
    universe.step(dt)

    for player_ix, player_ship in enumerate(player_ships):
        player_camera = cameras[player_ix]
        player_camera.start_drawing_new_frame()
        gameover = (
            not universe.contains_point(player_ship.pos) or player_ship.health <= 0
        ) and not TEST_MODE
        if gameover:
            font = pygame.font.Font(None, int(64 / player_count))
            player_camera.draw_text("GAME OVER", None, font, Color("red"))
        else:
            universe.move_camera(player_camera, player_ix, dt)
            universe.draw_background(player_camera)
            universe.draw_grid(player_camera)
            universe.draw(player_camera)
            universe.draw_text(player_camera, player_ix)

    minimap_camera.start_drawing_new_frame()
    universe.draw(minimap_camera)
    # Draw minimap border
    # This being worldspace is a kinda bad hack.
    MINIMAP_BORDER_COLOR = Color("aquamarine")
    minimap_camera.draw_vertical_hairline(MINIMAP_BORDER_COLOR, 0, 0, WORLD_SIZE.y)
    minimap_camera.draw_horizontal_hairline(
        MINIMAP_BORDER_COLOR,
        0,
        WORLD_SIZE.x,
        WORLD_SIZE.y - 1,
    )
    pygame.display.flip()

pygame.quit()
sys.exit()
