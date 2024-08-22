"""Staging-grounds for the game."""

from __future__ import annotations

import random
import sys

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from camera import Camera
from ship import BulletEnemy, RocketEnemy, ShipInput, PlayerShip
from universe import Area, Asteroid, Planet, RefuelArea, TrophyArea, Universe

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Space Game")

TEST_MODE = True
SCREEN_SIZE = Vec2(1700, 900)
MINIMAP_SIZE = Vec2(250, 250)

WORLD_SIZE = Vec2(10_000, 10_000) if TEST_MODE else Vec2(200_000, 200_000)
SPAWNPOINT = Vec2(5_000, 5_000) if TEST_MODE else Vec2(100_000, 100_000)
if TEST_MODE:

    """planets: list[Planet] = [
        Planet(Vec2(1_800, 6_700), 1, 370, Color("darkred")),
        Planet(Vec2(2_300, 900), 1, 280, Color("green")),
        Planet(Vec2(4_200, 3_700), 1, 280, Color("mediumpurple")),
        Planet(Vec2(5_000, 9_000), 1, 380, Color("darkorange")),
        Planet(Vec2(6_000, 400), 1, 350, Color("royalblue")),
        Planet(Vec2(8_600, 8_700), 1, 880, Color("orange")),
        Planet(Vec2(6_700, 7_200), 1, 380, Color("darkslategray")),
        Planet(Vec2(9_200, 4_400), 1, 540, Color("yellow")),
    ]"""
    areas: list[Area] = []
    asteroids: list[Asteroid] = []
    enemy_ships: list[BulletEnemy] = []
else:

    """planets = [
        Planet(Vec2(67_000, 18_000), 1, 3_000, Color("darkred")),
        Planet(Vec2(30_000, 32_000), 1, 3_000, Color("khaki")),
        Planet(Vec2(40_000, 40_000), 1, 3_500, Color("royalblue")),
        Planet(Vec2(37_000, 47_000), 1, 2_000, Color("mediumpurple")),
        Planet(Vec2(100_000, 57_000), 1, 6800, Color("darkslategray")),
        Planet(Vec2(87_000, 57_000), 1, 3_800, Color("plum")),
        Planet(Vec2(43_000, 60_000), 1, 700, Color("crimson")),
        Planet(Vec2(180_000, 60_000), 1, 5200, Color("hotpink")),
        Planet(Vec2(12_000, 71_000), 1, 3_800, Color("coral")),
        Planet(Vec2(26_000, 75_000), 1, 2_000, Color("gold")),
        Planet(Vec2(50_000, 99_000), 1, 5_400, Color("red")),
        Planet(Vec2(13_000, 110_000), 1, 2_000, Color("turquoise")),
        Planet(Vec2(30_000, 129_000), 1, 4_000, Color("green")),
        Planet(Vec2(53_000, 137_000), 1, 2_000, Color("deeppink")),
        Planet(Vec2(90_000, 140_000), 1, 3_800, Color("darkorange")),
        Planet(Vec2(37_000, 141_000), 1, 2_800, Color("orange")),
        Planet(Vec2(44_000, 152_000), 1, 400, Color("yellow")),
        Planet(Vec2(120_000, 160_000), 1, 5000, Color("lightblue")),
        Planet(Vec2(60_000, 160_000), 1, 2_800, Color("lime")),
        Planet(Vec2(64_000, 173_000), 1, 3_500, Color("blue")),
        Planet(Vec2(138_000, 187_000), 1, 5_800, Color("slategray")),
        Planet(Vec2(42_000, 191_000), 1, 900, Color("navy")),
    ]"""

    areas: list[Area] = [
        RefuelArea(pygame.Rect((7_000, 1_000), (200, 200))),
        TrophyArea(pygame.Rect((3_000, 8_000), (200, 200))),
    ]


player_ships = [
    PlayerShip(
        SPAWNPOINT + Vec2(800, 0),
        Vec2(0, 0),
        1,
        10,
        Color("white"),
        Color("orange"),
        ShipInput(
            pygame.K_RIGHT, pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN, pygame.K_SPACE
        ),
    ),
    PlayerShip(
        SPAWNPOINT + Vec2(0, 0),
        Vec2(0, 0),
        1,
        10,
        Color("darkslategray"),
        Color("yellow"),
        ShipInput(
            pygame.K_LEFT, pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN, pygame.K_SPACE
        ),
    ),
]


asteroids: list[Asteroid] = []
for _ in range(50):
    pos = Vec2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
    vel = Vec2(random.uniform(-100, 100), random.uniform(-100, 100))
    radius = random.uniform(4, 60)
    asteroids.append(Asteroid(pos, vel, 1, radius, Color("white")))

enemy_ships: list[BulletEnemy] = []
for _ in range(50):
    pos = Vec2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
    if random.random() > 0.5:
        enemy_ships.append(BulletEnemy(pos, Vec2(0, 0), random.choice(player_ships)))
    else:
        enemy_ships.append(RocketEnemy(pos, Vec2(0, 0), random.choice(player_ships)))

planets = [Planet(Vec2(6_000, 1_000), 1, 300, Color("darkred"), Color("white"))]

universe = Universe(
    WORLD_SIZE,
    planets,
    asteroids,
    player_ships,
    areas,
    enemy_ships,
)

cameras: list[Camera] = []
surface = pygame.display.set_mode(SCREEN_SIZE)
player_count = len(player_ships)
for player_ix, player in enumerate(player_ships):
    # TODO: Probably fix the off-by-one-error in here.
    topleft = (player_ix * SCREEN_SIZE.x / player_count, 0)
    size = (SCREEN_SIZE.x / player_count, SCREEN_SIZE.y)
    subsurface = surface.subsurface((topleft, size))
    camera = Camera(player.pos, 1.0, subsurface)
    cameras.append(camera)
minimap_surface = surface.subsurface(
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
            universe.move_camera(player_camera, dt)
            universe.draw_grid(player_camera)
            universe.draw(player_camera)
            universe.draw_text(player_camera)

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
