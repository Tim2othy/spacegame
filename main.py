"""Staging-grounds for the game."""

from __future__ import annotations

from ast import List
import dis
import sys

import random

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from camera import Camera
from universe import (
    Universe,
    Area,
    Asteroid,
    RefuelArea,
    TrophyArea,
    Planet,
    generate_asteroid,
)
from ship import PlayerShip, ShipInput, BulletEnemy, RocketEnemy
from constants import (
    GRAVITATIONAL_CONSTANT,
    ORBIT_MODE,
    TEST_MODE,
    MULTI_MODE,
    SCREEN_SIZE,
    MINIMAP_SIZE,
    WORLD_SIZE,
    SPAWNPOINT,
    NUMBER_OF_ASTEROIDS,
    NUMBER_OF_ENEMIES,
    ASTEROID_MAX_SIZE,
    ASTEROID_MIN_SIZE,
)

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Space Game")

SCREEN_SURFACE = pygame.display.set_mode(SCREEN_SIZE)

player_ships_single: list[PlayerShip] = [
    PlayerShip(
        SPAWNPOINT,
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

player_ships_multi: list[PlayerShip] = [
    PlayerShip(
        SPAWNPOINT,
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

planets_test: list[Planet] = [
    Planet(Vec2(1_800, 6_700), 1, 370, Color("darkred")),
    Planet(Vec2(2_300, 900), 1, 280, Color("green")),
    Planet(Vec2(4_200, 3_700), 1, 280, Color("mediumpurple")),
    Planet(Vec2(5_000, 9_000), 1, 380, Color("darkorange")),
    Planet(Vec2(6_000, 400), 1, 350, Color("royalblue")),
    Planet(Vec2(8_600, 8_700), 1, 880, Color("orange")),
    Planet(Vec2(6_700, 7_200), 1, 380, Color("darkslategray")),
    Planet(Vec2(9_200, 4_400), 1, 540, Color("yellow")),
]

planets_play: list[Planet] = [
    Planet(Vec2(27_000, 29_000), 1, 700, Color("darkred")),
    Planet(Vec2(21_000, 28_000), 1, 800, Color("khaki")),
    Planet(Vec2(2_000, 27_000), 1, 900, Color("royalblue")),
    Planet(Vec2(17_000, 26_000), 1, 900, Color("mediumpurple")),
    Planet(Vec2(14_000, 23_000), 1, 900, Color("darkslategray")),
    Planet(Vec2(17_000, 22_000), 1, 800, Color("darkgreen")),
    Planet(Vec2(13_000, 21_000), 1, 400, Color("crimson")),
    Planet(Vec2(10_000, 20_000), 1, 900, Color("hotpink")),
    Planet(Vec2(18_000, 19_000), 1, 300, Color("coral")),
    Planet(Vec2(16_000, 18_000), 1, 600, Color("gold")),
    Planet(Vec2(13_000, 17_000), 1, 400, Color("blue")),
    Planet(Vec2(8_000, 16_000), 1, 500, Color("turquoise")),
    Planet(Vec2(24_000, 15_000), 1, 270, Color("green")),
    Planet(Vec2(25_000, 14_000), 1, 300, Color("deeppink")),
    Planet(Vec2(18_000, 12_000), 1, 900, Color("darkorange")),
    Planet(Vec2(3_000, 5_000), 1, 100, Color("yellow")),
    Planet(Vec2(22_000, 4_000), 1, 850, Color("lightblue")),
    Planet(Vec2(14_500, 3_000), 1, 600, Color("plum")),
    Planet(Vec2(28_000, 2_000), 1, 200, Color("slategray")),
    Planet(Vec2(3_000, 1_000), 1, 700, Color("navy")),
]

if MULTI_MODE:
    player_ships: list[PlayerShip] = player_ships_multi
else:
    player_ships: list[PlayerShip] = player_ships_single

if TEST_MODE:
    planets: list[Planet] = planets_test
    areas: list[Area] = []
else:
    planets = planets_play
    areas: list[Area] = [
        RefuelArea(pygame.Rect((10_000, 20_000), (500, 500))),
        TrophyArea(pygame.Rect((20_000, 10_000), (500, 500))),
    ]

asteroids: list[Asteroid] = []
for planet in planets:
    for _ in range(NUMBER_OF_ASTEROIDS):
        generate_asteroid(planet.radius, planet.pos, asteroids)

enemy_ships: list[BulletEnemy] = []
for _ in range(NUMBER_OF_ENEMIES):
    pos = Vec2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
    if random.random() > 0.5:
        enemy_ships.append(BulletEnemy(pos, Vec2(0, 0), random.choice(player_ships)))
    else:
        enemy_ships.append(RocketEnemy(pos, Vec2(0, 0), random.choice(player_ships)))

# Generating celestialbody Values
radius_planet = random.uniform(200, 1000)
pos_planet = Vec2(random.uniform(1000, 8000), random.uniform(1000, 8000))

if ORBIT_MODE:
    planets = [
        Planet(pos_planet, 1, radius_planet, Color("darkred")),
    ]
    asteroids: list[Asteroid] = []
    for _ in range(5):
        generate_asteroid(radius_planet, pos_planet, asteroids)

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
