from __future__ import annotations
import pygame
from pygame.math import Vector2
from pygame import Color
import sys
import math
import random
from ship import Ship, BulletEnemy, RocketEnemy
from init import camera
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT
from universe import Universe, Planet, Asteroid, RefuelArea, TrophyArea, Area

# Initialize Pygame
pygame.init()

# Game state
has_item = False
mission_complete = False
game_over = False


# Create planets
planets = [
    Planet(Vector2(700, 1300), 1, 400, Color("turquoise")),
    Planet(Vector2(1800, 6700), 1, 370, Color("darkred")),
    Planet(Vector2(2300, 900), 1, 280, Color("green")),
    Planet(Vector2(3400, 5300), 1, 420, Color("blue")),
    Planet(Vector2(4000, 3700), 1, 280, Color("deeppink")),
    Planet(Vector2(5000, 9000), 1, 380, Color("darkorange")),
    Planet(Vector2(6000, 400), 1, 350, Color("royalblue")),
    Planet(Vector2(7000, 3700), 1, 280, Color("orange")),
    Planet(Vector2(8500, 8000), 1, 380, Color("mediumpurple")),
    Planet(Vector2(9200, 4400), 1, 440, Color("darkslategray")),
]

player_ship = Ship(
    Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2),
    Vector2(0, 0),
    1,
    10,
    Color("turquoise"),
)

areas: list[Area] = [
    RefuelArea(Vector2(5000, 1000), Vector2(5200, 1200)),
    TrophyArea(Vector2(3000, 5000), Vector2(3200, 5200)),
]

asteroids: list[Asteroid] = []
for _ in range(5):
    pos = Vector2(random.uniform(0, WORLD_WIDTH), random.uniform(0, WORLD_HEIGHT))
    vel = Vector2(random.uniform(0, WORLD_WIDTH), random.uniform(0, WORLD_HEIGHT))
    radius = random.uniform(40, 120)
    asteroids.append(Asteroid(pos, vel, 1, radius))

enemy_ships: list[BulletEnemy] = []
for _ in range(16):
    pos = Vector2(random.randint(0, WORLD_WIDTH), random.randint(0, WORLD_HEIGHT))
    if random.random() > 0.5:
        enemy_ships.append(BulletEnemy(pos, Vector2(0, 0), player_ship))
    else:
        enemy_ships.append(RocketEnemy(pos, Vector2(0, 0), player_ship))

universe = Universe(
    Vector2(WORLD_WIDTH, WORLD_HEIGHT),
    planets,
    asteroids,
    player_ship,
    areas,
    enemy_ships,
)


# I can't *believe* that math doesn't have a sign-function
def sign(x: int | float):
    return math.copysign(1, x)


class Square:
    # TODO: It's probably better to create different subclasses for Square that have different
    # inherent actions associated with them, rather than have an `action` parameter for
    # creation here.
    def __init__(self, x: float, y: float, size: float, color: Color, action: str):
        self.pos = Vector2(x, y)
        self.size = size
        self.color = color
        self.action = action

    def draw(self, screen: pygame.Surface, camera_pos: Vector2):
        if (
            0 <= self.pos[0] - camera_pos.x < SCREEN_WIDTH
            and 0 <= self.pos[1] - camera_pos.y < SCREEN_HEIGHT
        ):
            pygame.draw.rect(
                screen,
                self.color,
                (
                    self.pos - camera_pos,
                    (
                        self.size,
                        self.size,
                    ),
                ),
            )

    def check_collision(self, ship: Ship):
        return (
            self.pos.x - ship.radius < ship.pos.x < self.pos.x + self.size + ship.radius
            and self.pos.y - ship.radius
            < ship.pos.y
            < self.pos.y + self.size + ship.radius
        )


def draw_minimap():
    # TODO: Reimplement this with another instance of the Camera class :)
    # Or maybe we even need specialised draw-methods for every PhysicalObject
    # we want to draw?
    pass
    """
    MINIMAP_SIZE = 250  # Size of the minimap (width and height)
    MINIMAP_MARGIN = 20  # Margin from the top-right corner
    MINIMAP_BORDER_COLOR = (150, 150, 150)  # Light gray border
    MINIMAP_BACKGROUND_COLOR = (30, 30, 30)  # Dark gray background
    MINIMAP_SHIP_COLOR = (0, 255, 0)  # Green for the player's ship
    
    # Calculate the position of the minimap
    minimap_x = SCREEN_WIDTH - MINIMAP_SIZE - MINIMAP_MARGIN
    minimap_y = MINIMAP_MARGIN

    # Draw minimap background
    pygame.draw.rect(
        screen,
        MINIMAP_BACKGROUND_COLOR,
        (minimap_x, minimap_y, MINIMAP_SIZE, MINIMAP_SIZE),
    )

    # Draw minimap border
    pygame.draw.rect(
        screen,
        MINIMAP_BORDER_COLOR,
        (minimap_x, minimap_y, MINIMAP_SIZE, MINIMAP_SIZE),
        2,
    )

    # Calculate scaling factors
    scale = MINIMAP_SIZE / WORLD_WIDTH

    # Draw player's ship
    ship_minimap_x = int(minimap_x + ship.pos[0] * scale)
    ship_minimap_y = int(minimap_y + ship.pos[1] * scale)
    pygame.draw.circle(screen, MINIMAP_SHIP_COLOR, (ship_minimap_x, ship_minimap_y), 2)

    # Draw planets
    for planet in planets:
        planet_minimap_x = int(minimap_x + planet.pos[0] * scale)
        planet_minimap_y = int(minimap_y + planet.pos[1] * scale)
        pygame.draw.circle(
            screen,
            planet.color,
            (planet_minimap_x, planet_minimap_y),
            max(1, planet.radius / scale ** (-1)),
        )

    # Draw enemies
    for enemy in enemies:
        enemy_minimap_x = int(minimap_x + enemy.pos[0] * scale)
        enemy_minimap_y = int(minimap_y + enemy.pos[1] * scale)
        pygame.draw.circle(screen, enemy.color, (enemy_minimap_x, enemy_minimap_y), 2)

    for asteroid in asteroids:
        asteroid_minimap_x = int(minimap_x + asteroid.pos[0] * scale)
        asteroid_minimap_y = int(minimap_y + asteroid.pos[1] * scale)
        pygame.draw.circle(
            screen,
            asteroid.color,
            (asteroid_minimap_x, asteroid_minimap_y),
            max(1, asteroid.radius / scale ** (-1)),
        )

    for spacegun in spaceguns:
        spacegun_minimap_x = int(minimap_x + spacegun.pos[0] * scale)
        spacegun_minimap_y = int(minimap_y + spacegun.pos[1] * scale)
        pygame.draw.rect(
            screen,
            spacegun.color,
            (
                spacegun_minimap_x,
                spacegun_minimap_y,
                max(7, spacegun.size * scale),
                max(7, spacegun.size * scale),
            ),
        )
    """


# Game loop
running = True
clock = pygame.time.Clock()
while running:
    dt = clock.tick() / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        camera.start_drawing_new_frame()
        # TODO: reimplement drawing the grid

        ship = universe.player_ship

        # Handle input
        keys = pygame.key.get_pressed()

        # Look.
        # You might say that having the RIGHT key
        # activate the LEFT thruster must be some kind
        # of sign error.
        # My excuse? Well, "thruster_rot_left" might
        # mean "the thruster that rotates the ship left",
        # OR it might mean "the thruster on the left side".
        # So yes, please just ignore that, it'll be okay :)
        ship.thruster_rot_left = keys[pygame.K_RIGHT]
        ship.thruster_rot_right = keys[pygame.K_LEFT]
        ship.thruster_forward = keys[pygame.K_UP]
        ship.thruster_backward = keys[pygame.K_DOWN]
        if keys[pygame.K_SPACE]:
            ship.shoot()

        # TODO: Have the next two be methods of Ship class, and also respect dt
        if keys[pygame.K_m]:
            ship.health = min(ship.MAX_health, ship.health + ship.REPAIR_RATE)
        if keys[pygame.K_b]:
            ship.fuel = min(ship.MAX_FUEL, ship.fuel + ship.REFUEL_RATE)

        universe.step(dt)

        # Check if ship is touching world border
        if not universe.contains_point(ship.pos):
            game_over = True
        if ship.health <= 0:
            game_over = True
            # Collide with planets

        camera.smoothly_focus_points([ship.pos, ship.pos + 1 * ship.vel], 500, dt)

        universe.draw(camera)

    else:
        # Game over screen
        camera.start_drawing_new_frame()
        font = pygame.font.Font(None, 64)
        game_over_text = font.render("GAME OVER", True, (255, 0, 0))
        camera.surface.blit(
            game_over_text,
            (
                SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
                SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2,
            ),
        )

    # In your main game loop

    pygame.display.flip()

# Quit the game
pygame.quit()
sys.exit()
