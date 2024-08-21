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

# Cameras
SCREEN_SIZE = Vector2(1700, 900)
WORLD_SIZE = Vector2(30_000, 30_000)  # Make larger
surface = pygame.display.set_mode(SCREEN_SIZE)
camera = Camera(WORLD_SIZE / 2, 1.0, surface)
MINIMAP_SIZE = Vector2(250, 250)
minimap_surface = surface.subsurface((SCREEN_SIZE - MINIMAP_SIZE, MINIMAP_SIZE))
minimap_camera = Camera(WORLD_SIZE / 2, MINIMAP_SIZE.x / WORLD_SIZE.x, minimap_surface)

# Create planets
planets = [
    Planet(Vector2(700, 1300), 1, 400, Color("turquoise")),
    Planet(Vector2(1800, 6700), 1, 370, Color("darkred")),
    Planet(Vector2(2300, 900), 1, 280, Color("green")),
    Planet(Vector2(3700, 5300), 1, 420, Color("deeppink")),
    Planet(Vector2(4200, 3700), 1, 280, Color("mediumpurple")),
    Planet(Vector2(5000, 9000), 1, 380, Color("darkorange")),
    Planet(Vector2(6000, 400), 1, 350, Color("royalblue")),
    Planet(Vector2(7000, 3700), 1, 280, Color("orange")),
    Planet(Vector2(8500, 9000), 1, 380, Color("yellow")),
    Planet(Vector2(9200, 4400), 1, 440, Color("darkslategray")),
]

player_ship = Ship(
    Vector2(10_000, 10_000),
    Vector2(0, 0),
    1,
    10,
    Color("turquoise"),
)

areas: list[Area] = [
    RefuelArea(pygame.Rect((5000, 1000), (200, 200))),
    TrophyArea(pygame.Rect((3000, 5000), (200, 200))),
]

asteroids: list[Asteroid] = []
for _ in range(0):
    pos = Vector2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
    vel = Vector2(random.uniform(-100, 100), random.uniform(-100, 100))
    radius = random.uniform(4, 60)
    asteroids.append(Asteroid(pos, vel, 1, radius))

enemy_ships: list[BulletEnemy] = []
for _ in range(0):
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
    dt = clock.tick() / 1000

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

        if not universe.contains_point(player_ship.pos) or player_ship.health <= 0:
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
