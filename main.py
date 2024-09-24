"""Staging-grounds for the game."""

from __future__ import annotations

import random
import sys

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from camera import Camera
from ship import BulletEnemy, PlayerShip, RocketEnemy, ShipInput
from universe import Area, Asteroid, Planet, RefuelArea, TrophyArea, Universe

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Space Game")

TEST_MODE = True

SCREEN_SIZE = Vec2(1600, 900)
MINIMAP_SIZE = Vec2(350, 350)
WORLD_SIZE = Vec2(10_000, 10_000) if TEST_MODE else Vec2(30_000, 30_000)
SPAWNPOINT = Vec2(5_000, 5_000) if TEST_MODE else Vec2(20_000, 20_000)
SCREEN_SURFACE = pygame.display.set_mode(SCREEN_SIZE)

if TEST_MODE:

    planets: list[Planet] = [
        Planet(Vec2(1_800, 6_700), 1, 370, Color("darkred"), Color("white")),
        Planet(Vec2(2_300, 900), 1, 280, Color("green"), Color("white")),
        Planet(Vec2(4_200, 3_700), 1, 280, Color("mediumpurple"), Color("white")),
        Planet(Vec2(5_000, 9_000), 1, 380, Color("darkorange"), Color("white")),
        Planet(Vec2(6_000, 400), 1, 350, Color("royalblue"), Color("white")),
        Planet(Vec2(8_600, 8_700), 1, 880, Color("orange"), Color("white")),
        Planet(Vec2(6_700, 7_200), 1, 380, Color("darkslategray"), Color("white")),
        Planet(Vec2(9_200, 4_400), 1, 540, Color("yellow"), Color("white")),
    ]
    areas: list[Area] = []

    player_ships = [
        PlayerShip(
            SPAWNPOINT + Vec2(-50, 0),
            Vec2(0, 0),
            1,
            10,
            Color("darkslategray"),
            Color("orange"),
            ShipInput(
                pygame.K_RIGHT,
                pygame.K_LEFT,
                pygame.K_UP,
                pygame.K_DOWN,
                pygame.K_RETURN,
            ),
        ),
    ]

else:

    planets = [
        Planet(Vec2(27_000, 29_000), 1, 700, Color("darkred"), Color("white")),
        Planet(Vec2(21_000, 28_000), 1, 800, Color("khaki"), Color("white")),
        Planet(Vec2(2_000, 27_000), 1, 900, Color("royalblue"), Color("white")),
        Planet(Vec2(17_000, 26_000), 1, 900, Color("mediumpurple"), Color("white")),
        Planet(Vec2(14_000, 23_000), 1, 900, Color("darkslategray"), Color("white")),
        Planet(Vec2(17_000, 22_000), 1, 800, Color("darkgreen"), Color("white")),
        Planet(Vec2(13_000, 21_000), 1, 400, Color("crimson"), Color("white")),
        Planet(Vec2(10_000, 20_000), 1, 900, Color("hotpink"), Color("white")),
        Planet(Vec2(18_000, 19_000), 1, 300, Color("coral"), Color("white")),
        Planet(Vec2(16_000, 18_000), 1, 600, Color("gold"), Color("white")),
        Planet(Vec2(13_000, 17_000), 1, 400, Color("blue"), Color("white")),
        Planet(Vec2(8_000, 16_000), 1, 500, Color("turquoise"), Color("white")),
        Planet(Vec2(24_000, 15_000), 1, 270, Color("green"), Color("white")),
        Planet(Vec2(25_000, 14_000), 1, 300, Color("deeppink"), Color("white")),
        Planet(Vec2(18_000, 12_000), 1, 900, Color("darkorange"), Color("white")),
        Planet(Vec2(3_000, 5_000), 1, 100, Color("yellow"), Color("white")),
        Planet(Vec2(22_000, 4_000), 1, 850, Color("lightblue"), Color("white")),
        Planet(Vec2(14_500, 3_000), 1, 600, Color("plum"), Color("white")),
        Planet(Vec2(28_000, 2_000), 1, 200, Color("slategray"), Color("white")),
        Planet(Vec2(3_000, 1_000), 1, 700, Color("navy"), Color("white")),
    ]

    areas: list[Area] = [
        RefuelArea(pygame.Rect((7_000, 1_000), (200, 200))),
        TrophyArea(pygame.Rect((3_000, 8_000), (200, 200))),
    ]

    player_ships: list[PlayerShip] = [
        PlayerShip(
            SPAWNPOINT + Vec2(-50, 0),
            Vec2(0, 0),
            1,
            10,
            Color("darkslategray"),
            Color("orange"),
            ShipInput(
                pygame.K_RIGHT,
                pygame.K_LEFT,
                pygame.K_UP,
                pygame.K_DOWN,
                pygame.K_RETURN,
            ),
        ),
        PlayerShip(
            SPAWNPOINT + Vec2(50, 0),
            Vec2(0, 0),
            1,
            10,
            Color("blue"),
            Color("yellow"),
            ShipInput(pygame.K_d, pygame.K_a, pygame.K_w, pygame.K_s, pygame.K_SPACE),
        ),
    ]


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
