from __future__ import annotations
import pygame
from pygame.math import Vector2
from pygame import Color
import sys
import random
from ship import Ship, BulletEnemy, RocketEnemy
from camera import Camera
from universe import Universe, Planet, Asteroid, RefuelArea, TrophyArea, Area

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Space Game")
game_over = False
testmode = False
SPAWNPOINT = Vector2(300_000, 300_000)

# Cameras
SCREEN_SIZE = Vector2(1700, 900)
WORLD_SIZE = Vector2(1_000_000, 1_000_000)
surface = pygame.display.set_mode(SCREEN_SIZE)
camera = Camera(SPAWNPOINT, 1.0, surface)
MINIMAP_SIZE = Vector2(250, 250)
minimap_surface = surface.subsurface((SCREEN_SIZE - MINIMAP_SIZE, MINIMAP_SIZE))
minimap_camera = Camera(SPAWNPOINT, MINIMAP_SIZE.x / WORLD_SIZE.x, minimap_surface)

# Create planets
planets = [
    Planet(Vector2(100_000, 130_000), 1, 20000, Color("turquoise")),
    Planet(Vector2(180_000, 670_000), 1, 37000, Color("darkred")),
    Planet(Vector2(230_000, 290_000), 1, 28000, Color("green")),
    Planet(Vector2(370_000, 530_000), 1, 42000, Color("deeppink")),
    Planet(Vector2(420_000, 370_000), 1, 28000, Color("mediumpurple")),
    Planet(Vector2(400_000, 900_000), 1, 3800, Color("darkorange")),
    Planet(Vector2(400_000, 400_000), 1, 3500, Color("royalblue")),
    Planet(Vector2(410_000, 370_000), 1, 2800, Color("orange")),
    Planet(Vector2(570_000, 900_000), 1, 3800, Color("darkslategray")),
    Planet(Vector2(520_000, 440_000), 1, 5400, Color("yellow")),
    Planet(Vector2(570_000, 870_000), 1, 3800, Color("black")),
    Planet(Vector2(600_000, 200_000), 1, 4000, Color("lightblue")),
    Planet(Vector2(600_000, 430_000), 1, 19700, Color("crimson")),
    Planet(Vector2(600_000, 600_000), 1, 2800, Color("lime")),
    Planet(Vector2(600_000, 800_000), 1, 9200, Color("hotpink")),
    Planet(Vector2(600_000, 700_000), 1, 28000, Color("plum")),
    Planet(Vector2(710_000, 120_000), 1, 3800, Color("coral")),
    Planet(Vector2(730_000, 640_000), 1, 3500, Color("blue")),
    Planet(Vector2(750_000, 260_000), 1, 28000, Color("gold")),
    Planet(Vector2(870_000, 380_000), 1, 3800, Color("slategray")),
    Planet(Vector2(990_000, 500_000), 1, 5400, Color("khaki")),
    Planet(Vector2(910_000, 420_000), 1, 30000, Color("navy")),
]


player_ship = Ship(
    SPAWNPOINT,
    Vector2(0, 0),
    1,
    10,
    Color("turquoise"),
)

areas: list[Area] = [
    RefuelArea(Vector2(7000, 1000), Vector2(200, 200)),
    TrophyArea(Vector2(3000, 8000), Vector2(200, 200)),
]

asteroids: list[Asteroid] = []
for _ in range(50):
    pos = Vector2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
    vel = Vector2(random.uniform(-100, 100), random.uniform(-100, 100))
    radius = random.uniform(4, 60)
    asteroids.append(Asteroid(pos, vel, 1, radius))

enemy_ships: list[BulletEnemy] = []
for _ in range(50):
    pos = Vector2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
    if random.random() > 0.5:
        enemy_ships.append(BulletEnemy(pos, Vector2(0, 0), player_ship))
    else:
        enemy_ships.append(RocketEnemy(pos, Vector2(0, 0), player_ship))


if testmode == True:
    SPAWNPOINT = Vector2(5000, 5000)
    planets = [
        Planet(Vector2(1800, 6700), 1, 370, Color("darkred")),
        Planet(Vector2(2300, 900), 1, 280, Color("green")),
        Planet(Vector2(4200, 3700), 1, 280, Color("mediumpurple")),
        Planet(Vector2(5000, 9000), 1, 380, Color("darkorange")),
        Planet(Vector2(6000, 400), 1, 350, Color("royalblue")),
        Planet(Vector2(8600, 8700), 1, 880, Color("orange")),
        Planet(Vector2(6700, 7200), 1, 380, Color("darkslategray")),
        Planet(Vector2(9200, 4400), 1, 540, Color("yellow")),
    ]
    WORLD_SIZE = Vector2(10_000, 10_000)
    camera = Camera(SPAWNPOINT, 1.0, surface)

    asteroids = []
    enemy_ships = []
    minimap_surface = surface.subsurface((SCREEN_SIZE - MINIMAP_SIZE, MINIMAP_SIZE))
    minimap_camera = Camera(
        SPAWNPOINT,
        MINIMAP_SIZE.x / WORLD_SIZE.x,
        minimap_surface,
    )
    player_ship = Ship(
        SPAWNPOINT,
        Vector2(0, 0),
        1,
        10,
        Color("orange"),
    )

universe = Universe(
    WORLD_SIZE,
    planets,
    asteroids,
    player_ship,
    areas,
    enemy_ships,
)


running = True
clock = pygame.time.Clock()
while running:
    dt = clock.tick() / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

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
        ) and testmode == 0:
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
