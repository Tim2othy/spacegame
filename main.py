"""Staging-grounds for the game."""

from __future__ import annotations

import random
import sys

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from camera import Camera
from ship import BulletEnemy, PlayerShip, ShipInput
from universe import Planet, Universe

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Ocean Game")

SCREEN_SIZE = Vec2(1800, 950)

WORLD_SIZE = Vec2(5000, 5000)
SPAWNPOINT = Vec2(1000, 1000)
SCREEN_SURFACE = pygame.display.set_mode(SCREEN_SIZE)

planets: list[Planet] = [
    Planet(Vec2(800, 2700), 1, 370, Color("darkgreen")),
    Planet(Vec2(2300, 900), 1, 280, Color("darkgreen")),
    Planet(Vec2(4200, 3700), 1, 280, Color("darkgreen")),
]


player_ships = [
    PlayerShip(
        SPAWNPOINT + Vec2(100, 0),
        Vec2(0, 0),
        1,
        10,
        Color("brown"),
        ShipInput(
            pygame.K_RIGHT, pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN, pygame.K_SPACE
        ),
    )
]


enemy_ships: list[BulletEnemy] = []
enemy_ships.append(BulletEnemy(Vec2(1020, 1020), Vec2(0, 0), player_ships[0]))


universe = Universe(
    WORLD_SIZE,
    planets,
    player_ships,
    enemy_ships,
)
cameras: list[Camera] = []

for player_ix, player in enumerate(player_ships):
    topleft = (player_ix * SCREEN_SIZE.x, 0)
    size = (SCREEN_SIZE.x, SCREEN_SIZE.y)
    subsurface = SCREEN_SURFACE.subsurface((topleft, size))
    camera = Camera(player.pos, 1.0, subsurface)
    cameras.append(camera)


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
        universe.move_camera(player_camera, player_ix, dt)
        universe.draw(player_camera)
        universe.draw_text(player_camera, player_ix)

    pygame.display.flip()

pygame.quit()
sys.exit()
