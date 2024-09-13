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
MINIMAP_SIZE = Vec2(350, 350)

WORLD_SIZE = Vec2(5000, 5000)
SPAWNPOINT = Vec2(1000, 1000)
SCREEN_SURFACE = pygame.display.set_mode(SCREEN_SIZE)

planets: list[Planet] = [
    Planet(Vec2(800, 2700), 1, 370, Color("darkred")),
    Planet(Vec2(2300, 900), 1, 280, Color("green")),
    Planet(Vec2(4200, 3700), 1, 280, Color("mediumpurple")),
]
enemy_ships: list[BulletEnemy] = []


player_ships = [
    PlayerShip(
        SPAWNPOINT + Vec2(100, 0),
        Vec2(0, 0),
        1,
        10,
        Color("brown"),
        ShipInput(
            pygame.K_RIGHT, pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN, pygame.K_RETURN
        ),
    )
]


enemy_ships: list[BulletEnemy] = []
for _ in range(5):
    pos = Vec2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
    enemy_ships.append(BulletEnemy(pos, Vec2(0, 0), random.choice(player_ships)))


universe = Universe(
    WORLD_SIZE,
    planets,
    player_ships,
    enemy_ships,
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
        )
        if gameover:
            font = pygame.font.Font(None, int(64 / player_count))
            player_camera.draw_text("GAME OVER", None, font, Color("red"))
        else:
            universe.move_camera(player_camera, player_ix, dt)
            universe.draw_grid(player_camera)
            universe.draw(player_camera)
            universe.draw_text(player_camera, player_ix)

    minimap_camera.start_drawing_new_frame()
    universe.draw(minimap_camera)
    # Draw minimap border
    # This being worldspace is a kinda bad hack.
    MINIMAP_BORDER_COLOR = Color("gold")
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
