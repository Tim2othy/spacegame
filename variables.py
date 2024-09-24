from __future__ import annotations

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from ship import PlayerShip, ShipInput

from universe import Planet

TEST_MODE = True


SCREEN_SIZE = Vec2(1600, 900)
MINIMAP_SIZE = Vec2(350, 350)
WORLD_SIZE = Vec2(10_000, 10_000) if TEST_MODE else Vec2(30_000, 30_000)
SPAWNPOINT = Vec2(5_000, 5_000) if TEST_MODE else Vec2(20_000, 20_000)


planets_test: list[Planet] = [
    Planet(Vec2(1_800, 6_700), 1, 370, Color("darkred"), Color("white")),
    Planet(Vec2(2_300, 900), 1, 280, Color("green"), Color("white")),
    Planet(Vec2(4_200, 3_700), 1, 280, Color("mediumpurple"), Color("white")),
    Planet(Vec2(5_000, 9_000), 1, 380, Color("darkorange"), Color("white")),
    Planet(Vec2(6_000, 400), 1, 350, Color("royalblue"), Color("white")),
    Planet(Vec2(8_600, 8_700), 1, 880, Color("orange"), Color("white")),
    Planet(Vec2(6_700, 7_200), 1, 380, Color("darkslategray"), Color("white")),
    Planet(Vec2(9_200, 4_400), 1, 540, Color("yellow"), Color("white")),
]


planets_play: list[Planet] = [
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
player_ships_test: list[PlayerShip] = [
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
player_ships_play: list[PlayerShip] = [
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


if TEST_MODE:
    planets = planets_test
    player_ships = player_ships_test
else:
    planets = planets_play

    player_ships = player_ships_play
