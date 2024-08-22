"""Staging-grounds for the game."""

from __future__ import annotations
import sys
import random
import pygame
from pygame.math import Vector2
from pygame import Color
from ship import Ship, BulletEnemy, RocketEnemy
from camera import Camera
from universe import Universe, Planet, Asteroid, RefuelArea, TrophyArea, Area

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Space Game")
game_over = False
testmode = True  # Turn this on and the world and planets will be smaller, the player spawns in the smaller world
death = True
SPAWNPOINT = Vector2(100_000, 100_000)

# Cameras
SCREEN_SIZE = Vector2(1700, 900)
WORLD_SIZE = Vector2(200_000, 200_000)
surface = pygame.display.set_mode(SCREEN_SIZE)
camera = Camera(SPAWNPOINT, 1.0, surface)
MINIMAP_SIZE = Vector2(350, 350)
minimap_surface = surface.subsurface((SCREEN_SIZE - MINIMAP_SIZE, MINIMAP_SIZE))
minimap_camera = Camera(SPAWNPOINT, MINIMAP_SIZE.x / WORLD_SIZE.x, minimap_surface)
"""
# Create planets
planets = [  # TODO: I just removed the planets for now because I didn't want to have to give them all a bullet_color argument that they don't need
             #       I guess you can fix this and/or tell me how one can make one disk have an argument but not the others : ) 
    Planet(Vector2(67_000, 18_000), 1, 3_000, Color("darkred")),
    Planet(Vector2(30_000, 32_000), 1, 3_000, Color("khaki")),
    Planet(Vector2(40_000, 40_000), 1, 3_500, Color("royalblue")),
    Planet(Vector2(37_000, 47_000), 1, 2_000, Color("mediumpurple")),
    Planet(Vector2(100_000, 57_000), 1, 6800, Color("darkslategray")),
    Planet(Vector2(87_000, 57_000), 1, 3_800, Color("plum")),
    Planet(Vector2(43_000, 60_000), 1, 700, Color("crimson")),
    Planet(Vector2(180_000, 60_000), 1, 5200, Color("hotpink")),
    Planet(Vector2(12_000, 71_000), 1, 3_800, Color("coral")),
    Planet(Vector2(26_000, 75_000), 1, 2_000, Color("gold")),
    Planet(Vector2(50_000, 99_000), 1, 5_400, Color("red")),
    Planet(Vector2(13_000, 110_000), 1, 2_000, Color("turquoise")),
    Planet(Vector2(30_000, 129_000), 1, 4_000, Color("green")),
    Planet(Vector2(53_000, 137_000), 1, 2_000, Color("deeppink")),
    Planet(Vector2(90_000, 140_000), 1, 3_800, Color("darkorange")),
    Planet(Vector2(37_000, 141_000), 1, 2_800, Color("orange")),
    Planet(Vector2(44_000, 152_000), 1, 400, Color("yellow")),
    Planet(Vector2(120_000, 160_000), 1, 5000, Color("lightblue")),
    Planet(Vector2(60_000, 160_000), 1, 2_800, Color("lime")),
    Planet(Vector2(64_000, 173_000), 1, 3_500, Color("blue")),
    Planet(Vector2(138_000, 187_000), 1, 5_800, Color("slategray")),
    Planet(Vector2(42_000, 191_000), 1, 900, Color("navy")),
]"""

planets = [Planet(Vector2(67_000, 18_000), 1, 3_000, Color("darkred"), None)]


player_ship = Ship(
    SPAWNPOINT, Vector2(0, 0), 1, 10, Color("turquoise"), Color("yellow")
)

areas: list[Area] = [
    RefuelArea(pygame.Rect((7_000, 1_000), (200, 200))),
    TrophyArea(pygame.Rect((3_000, 8_000), (200, 200))),
]

areas = []


if testmode == True:
    SPAWNPOINT = Vector2(5_000, 5_000)
    planets = [
        Planet(Vector2(1_800, 6_700), 1, 370, Color("darkred"), None),
        Planet(Vector2(2_300, 900), 1, 280, Color("green"), None),
        Planet(Vector2(4_200, 3_700), 1, 280, Color("mediumpurple"), None),
        Planet(Vector2(5_000, 9_000), 1, 380, Color("darkorange"), None),
        Planet(Vector2(6_000, 400), 1, 350, Color("royalblue"), None),
        Planet(Vector2(8_600, 8_700), 1, 880, Color("orange"), None),
        Planet(Vector2(6_700, 7_200), 1, 380, Color("darkslategray"), None),
        Planet(Vector2(9_200, 4_400), 1, 540, Color("yellow"), None),
    ]
    WORLD_SIZE = Vector2(10_000, 10_000)
    camera = Camera(SPAWNPOINT, 1.0, surface)

    asteroids = []
    # enemy_ships = []
    minimap_surface = surface.subsurface((SCREEN_SIZE - MINIMAP_SIZE, MINIMAP_SIZE))
    minimap_camera = Camera(
        SPAWNPOINT,
        MINIMAP_SIZE.x / WORLD_SIZE.x,
        minimap_surface,
    )
    player_ship = Ship(
        SPAWNPOINT, Vector2(0, 0), 1, 10, Color("darkslategray"), Color("yellow")
    )


asteroids: list[Asteroid] = []
for _ in range(20):
    pos = Vector2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
    vel = Vector2(random.uniform(-100, 100), random.uniform(-100, 100))
    radius = random.uniform(20, 100)
    asteroids.append(
        Asteroid(pos, vel, 1, radius, None)
    )  # TODO: this None is for bullet_color, I'm sure there is some way to remove this?

enemy_ships: list[BulletEnemy] = []
for _ in range(5):
    pos = Vector2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
    if random.random() > 0.5:
        enemy_ships.append(BulletEnemy(pos, Vector2(0, 0), player_ship))
    else:
        enemy_ships.append(RocketEnemy(pos, Vector2(0, 0), player_ship))


universe = Universe(
    WORLD_SIZE,
    planets,
    asteroids,
    player_ship,
    areas,
    enemy_ships,
)


clock = pygame.time.Clock()
while True:
    dt = clock.tick() / 1_000

    if any(map(lambda e: e.type == pygame.QUIT, pygame.event.get())):
        break

    camera.start_drawing_new_frame()
    if game_over:
        font = pygame.font.Font(None, 64)
        camera.draw_text("GAME OVER", None, font, Color("red"))
    else:
        # Handle input
        keys = pygame.key.get_pressed()
        player_ship.thruster_rot_left = keys[pygame.K_RIGHT]
        player_ship.thruster_rot_right = keys[pygame.K_LEFT]
        player_ship.thruster_forward = keys[pygame.K_UP]
        player_ship.thruster_backward = keys[pygame.K_DOWN]
        if keys[pygame.K_SPACE]:
            player_ship.shoot()

        universe.step(dt)

        if (
            not universe.contains_point(player_ship.pos) or player_ship.health <= 0
        ) and death == True:  # Just so one can't die for now
            game_over = True
        camera.smoothly_focus_points(
            [player_ship.pos, player_ship.pos + 1 * player_ship.vel], 500, dt
        )

        universe.draw(camera)
        universe.draw_text(camera)
        minimap_camera.start_drawing_new_frame()
        universe.draw(minimap_camera)

    pygame.display.flip()

pygame.quit()
sys.exit()
