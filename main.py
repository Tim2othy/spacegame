import pygame
from pygame.math import Vector2
from pygame import Color
import sys
import math
import random
import time
from math import atan2, sqrt

from init import (
    screen,
    camera_pos,
    total_force_x,
    total_force_y,
    collision_time,
)

from ship import Ship
from bullet import Bullet
from planets import Planet

from enemy_info import (
    ENEMY_ACCELERATION,
    ENEMY_SHOOT_RANGE,
    ROCKET_ACCELERATION,
)
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, G

from grid import draw_grid

# Initialize Pygame
pygame.init()

ship_color = Color("white")
collision_time = 0

# Game state
has_item = False
mission_complete = False
game_over = False


ship = Ship(5000, 5000)

# I can't *believe* that math doesn't have a sign-function
def sign(x: int | float):
    return math.copysign(1, x)


# region --- calc gravity---


def calculate_gravity(pos: Vector2, mass: float, planets: list[Planet]):
    total_force = Vector2(0, 0)
    for planet in planets:
        delta = planet.pos - pos
        distance_squared = delta.magnitude_squared()
        if distance_squared > 0:
            force_magnitude = (
                G * (4 / 3 * 3.14 * planet.radius**3) * mass / distance_squared
            )
            distance = math.sqrt(distance_squared)
            total_force += delta * force_magnitude / distance
    return total_force


# endregion


# region --- Planets and squares---


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


# Create planets (increased size)


planets = [
    Planet(700, 1300, 400, Color("turquoise")),
    Planet(1800, 6700, 370, Color("darkred")),
    Planet(2300, 900, 280, Color("green")),
    Planet(3400, 5300, 420, Color("blue")),
    Planet(4000, 3700, 280, Color("deeppink")),
    Planet(5000, 9000, 380, Color("darkorange")),
    Planet(6000, 400, 350, Color("royalblue")),
    Planet(7000, 3700, 280, Color("orange")),
    Planet(8500, 8000, 380, Color("mediumpurple")),
    Planet(9200, 4400, 440, Color("darkslategray")),
]


# Create squares

pos_refuel = (5000, 1000)
pos_item = (3000, 5000)
pos_complete = (1000, 5000)

squares = [
    Square(
        pos_refuel[0], pos_refuel[1], 200, Color("cyan"), "refuel"
    ),  # Top-right, refuel
    Square(
        pos_item[0], pos_item[1], 200, Color("purple"), "get_item"
    ),  # bottom-right, get item
    Square(
        pos_complete[0], pos_complete[1], 200, Color("orange"), "complete_mission"
    ),  # bottom-left, complete mission
]


# TODO: We should just have one single bounce-method for all kinds of celestial bodies
def bounce_from_planet(planet: Planet):
    # TODO: The pygame.math module already has methods for normal-vector
    # calculation

    # Calculate normal vector
    delta = ship.pos - planet.pos
    delta_magnitude = delta.magnitude()
    normal_vector = delta / delta_magnitude
    ship_speed_along_normal = ship.speed.dot(normal_vector)

    # Do not resolve if velocities are separating
    if ship_speed_along_normal > 0:
        return

    # Calculate restitution (bounciness)
    restitution = 1

    # Calculate impulse scalar
    j = -(1 + restitution) * ship_speed_along_normal
    j /= 1 / ship.mass + 1 / (4 / 3 * math.pi * planet.radius**3)

    # Apply impulse
    ship.speed += normal_vector * j / ship.mass

    # Move ship outside planet
    overlap = ship.radius + planet.radius - delta_magnitude
    ship.pos += normal_vector * overlap


# endregion


# region --- asteroids


# TODO: Eventually make Asteroid and Planet subclasses of a shared class
class Asteroid:
    def __init__(self, x: float, y: float, radius: float):
        self.pos = Vector2(x, y)
        self.radius = radius
        self.color = (100, 100, 100)  # Grey color
        self.speed = Vector2(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
        self.mass = 4 / 3 * math.pi * self.radius**3  # Assuming density of 1

    def draw(self, screen: pygame.Surface, camera_pos: Vector2):
        if (
            self.pos[0] - self.radius - camera_pos.x < SCREEN_WIDTH
            and self.pos[0] + self.radius - camera_pos.x > 0
            and self.pos[1] - self.radius - camera_pos.y < SCREEN_HEIGHT
            and self.pos[1] + self.radius - camera_pos.y > 0
        ):
            pygame.draw.circle(
                screen,
                self.color,
                self.pos - camera_pos,
                self.radius,
            )

    def update(self, planets: list[Planet]):
        # Update position based on speed
        # TODO: This should definitely incorporate ∆t
        self.pos += self.speed

        # Stop at world border
        if self.pos[0] - self.radius < 0:
            self.pos[0] = self.radius
            self.speed[0] = 0
        elif self.pos[0] + self.radius > WORLD_WIDTH:
            self.pos[0] = WORLD_WIDTH - self.radius
            self.speed[0] = 0
        if self.pos[1] - self.radius < 0:
            self.pos[1] = self.radius
            self.speed[1] = 0
        elif self.pos[1] + self.radius > WORLD_HEIGHT:
            self.pos[1] = WORLD_HEIGHT - self.radius
            self.speed[1] = 0

        # Apply gravity from planets
        for planet in planets:
            force = planet.calculate_gravity(self)
            self.speed += force / self.mass

    def check_collision(self, other: "Asteroid | Planet | Vector2"):
        # TODO: This should be split up into two different methods, one for
        # positions, one for celestial bodies
        if isinstance(other, Asteroid) or isinstance(other, Planet):
            return self.pos.distance_to(other.pos) < self.radius + other.radius
        else:
            # other is instance of Vector2
            return self.pos.distance_to(other) < self.radius + ship.radius

    # TODO: Disgusting union-type, we should create a superclass of Asteroid and Planet
    def bounce(self, other: "Asteroid | Planet"):
        # TODO: Because `self` (an Asteroid) moves as well,
        # shouldn't this impulse also affect the way that `other`
        # is deflected?

        # TODO: The pygame.math module already has methods for normal-vector
        # calculation

        # Calculate normal vector
        delta = self.pos - other.pos
        delta_magnitude = delta.magnitude()
        normal_vector = delta / delta_magnitude
        self_speed_along_normal = self.speed.dot(normal_vector)

        # Do not resolve if velocities are separating
        if self_speed_along_normal > 0:
            return

        # Calculate restitution (bounciness)
        restitution = 1

        # Calculate impulse scalar
        j = -(1 + restitution) * self_speed_along_normal
        j /= 1 / self.mass + 1 / (4 / 3 * math.pi * other.radius**3)

        # Apply impulse
        self.speed += normal_vector * j / self.mass

        # Move self outside other
        overlap = self.radius + other.radius - delta_magnitude
        self.pos += normal_vector * overlap


# TODO: These two methods will eventually be merged into the superclass of
# Asteroid and Planet
# TODO: Neither of these should have a type-union "Bullet | Rocket" in their
# arguments. Instead, there should be a superclass of Bullet and Rocket, say,
# `Projectile`, and that's the type of its argument


def check_projectile_planet_collision(
    projectile: "Bullet | Rocket", planets: list[Planet]
):
    for planet in planets:
        if projectile.pos.distance_to(planet.pos) < planet.radius:
            return True
    return False

def check_projectile_asteroid_collision(
    projectile: "Bullet | Rocket", asteroids: list[Asteroid]
):
    for asteroid in asteroids:
        if projectile.pos.distance_to(asteroid.pos) < asteroid.radius:
            return True
    return False


# Generate asteroids
asteroids: list[Asteroid] = []
for _ in range(5):  # Adjust the number of asteroids as needed
    x = random.uniform(0, WORLD_WIDTH)
    y = random.uniform(0, WORLD_HEIGHT)
    radius = random.uniform(40, 120)
    asteroids.append(Asteroid(x, y, radius))

# endregion


# region --- space guns ---


class Spacegun:
    def __init__(self, x: float, y: float):
        self.pos = Vector2(x, y)
        self.size = 40
        self.color = (50, 50, 100)
        self.last_shot_time = 60
        self.shoot_interval = 300
        self.bullets: list[object] = []
        # TODO: The "object" type is super-unspecific.
        # `self.bullets` *should* be a `list[Bullet]`, but
        # currently the `Bullet` class does not implement the
        # features that Spacegun wants, and so Spacegun uses
        # a dictionary instead of a `Bullet`. Once Spacegun
        # uses a proper `Bullet`, this should have
        # its type changed to `list[Bullet]`.

    def draw(self, screen: pygame.Surface, camera_pos: Vector2):
        pygame.draw.rect(
            screen,
            self.color,
            (self.pos - camera_pos, (self.size, self.size)),
        )

    def shoot(self, target_pos: Vector2):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > self.shoot_interval:
            direction = target_pos - self.pos
            length = direction.magnitude()
            if length > 0:
                direction /= length

            # TODO: Do we really want to append even if direction is the zero-vector?
            self.bullets.append(
                {
                    "pos": self.pos.copy(),
                    "direction": direction,
                    "speed": 7,
                    "creation_time": current_time,
                }
            )
            self.last_shot_time = current_time

    def update_bullets(self, ship: Ship):
        current_time = pygame.time.get_ticks()
        for bullet in self.bullets[:]:
            bullet["pos"][0] += bullet["direction"][0] * bullet["speed"]
            bullet["pos"][1] += bullet["direction"][1] * bullet["speed"]

            if current_time - bullet["creation_time"] > 4000:
                self.bullets.remove(bullet)
            elif bullet["pos"].distance_to(ship.pos) < ship.radius:
                self.bullets.remove(bullet)
                return True  # Collision detected
        return False

    def draw_bullets(self, screen: pygame.Surface, camera_pos: Vector2):
        for bullet in self.bullets:
            pygame.draw.circle(
                screen,
                (255, 0, 0),
                bullet["pos"] - camera_pos,
                5,
            )


spaceguns = [Spacegun(9000, 9000), Spacegun(2000, 6000), Spacegun(5000, 2000)]

# endregion


# region --- enemy ships ---


# Define cooldown values
ROCKET_SHOOT_COOLDOWN = 2
BULLET_SHOOT_COOLDOWN = 0.5


# New classes for enemies and projectiles


class Enemy:
    # TODO: Rather than an enemy_type:str parameter, have an Enemy-class,
    # with BulletEnemy and RocketEnemy as sub-classes
    def __init__(self, x: float, y: float, enemy_type: str, health: int = 100):
        self.pos = Vector2(x, y)
        self.speed = Vector2(0, 0)
        self.radius = 15
        self.type = enemy_type  # 'bullet' or 'rocket'
        self.color = (155, 77, 166) if enemy_type == "bullet" else (255, 165, 0)
        self.shoot_cooldown = 0
        self.action_timer = 1 * 60

        self.health = health

    # TODO: Add return-type to this function
    def update(
        self, ship: Ship, planets: list[Planet]
    ) -> "list[Rocket] | list[Bullet]":
        delta = ship.pos - self.pos
        dist = delta.magnitude()
        # TODO: Rather than storing an int for current_action, store some enum. See:
        # https://stackoverflow.com/questions/36932/how-can-i-represent-an-enum-in-python
        self.current_action = 6
        force = calculate_gravity(self.pos, 100, planets)  # Assume enemy mass is 100
        self.speed += force / 100
        self.check_planet_collision(planets)

        # Check if the 4-second period has elapsed
        if self.action_timer <= 0:
            self.current_action = random.randint(1, 4)
            self.action_timer = 0.5 * 60  # Reset timer to 4 seconds (240 frames)

        if self.current_action == 1:  # Accelerate towards player
            self.speed[0] += (dx / dist) * ENEMY_ACCELERATION * 2
            self.speed[1] += (dy / dist) * ENEMY_ACCELERATION * 2

        elif self.current_action == 2:  # Accelerate randomly
            rand_speed = Vector2(random.uniform(-1, 1), random.uniform(-1, 1))

            self.speed[0] += rand_speed[0] * ENEMY_ACCELERATION * 0.2
            self.speed[1] += rand_speed[1] * ENEMY_ACCELERATION * 0.2

        elif self.current_action == 3:  # Decelerate
            self.speed[0] -= sign(self.speed[0]) * ENEMY_ACCELERATION * 0.2
            self.speed[1] -= sign(self.speed[1]) * ENEMY_ACCELERATION * 0.2

        # Update position
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]

        self.action_timer -= 1

        # Shooting logic
        if dist < ENEMY_SHOOT_RANGE and self.shoot_cooldown <= 0:
            if self.type == "bullet":
                # Set cooldown for bullet enemy
                self.shoot_cooldown = BULLET_SHOOT_COOLDOWN
                # TODO: `self` is not of type `Ship`. Perhaps `Enemy` should be subclass of `Ship`?
                return [Bullet(self.pos[0], self.pos[1], atan2(dy, dx), self)]
            else:
                # Set cooldown for rocket enemy
                self.shoot_cooldown = ROCKET_SHOOT_COOLDOWN
                return [Rocket(self.pos[0], self.pos[1], ship.pos)]
        self.shoot_cooldown = max(0, self.shoot_cooldown - 1)
        return []

    def draw(self, screen: pygame.Surface, camera_pos: Vector2):
        pygame.draw.circle(
            screen,
            self.color,
            self.pos - camera_pos,
            self.radius,
        )

    # TODO: Disgusting union-type, we should create a superclass of Asteroid and Planet
    def bounce(self, other: Asteroid | Planet):
        # TODO: Because `self` (an Asteroid) moves as well,
        # shouldn't this impulse also affect the way that `other`
        # is deflected?

        # TODO: The pygame.math module already has methods for normal-vector
        # calculation

        # Assume enemy's mass is 100
        # TODO: Should we at some point have `mass` as an attribute of `enemy`?
        mass = 100

        # Calculate normal vector
        delta = self.pos - other.pos
        delta_magnitude = delta.magnitude()
        normal_vector = delta / delta_magnitude
        self_speed_along_normal = self.speed.dot(normal_vector)

        # Do not resolve if velocities are separating
        if self_speed_along_normal > 0:
            return

        # Calculate restitution (bounciness)
        restitution = 1

        # Calculate impulse scalar
        j = -(1 + restitution) * self_speed_along_normal
        j /= 1 / mass + 1 / (4 / 3 * math.pi * other.radius**3)

        # Apply impulse
        self.speed += normal_vector * j / mass

        # Move self outside other
        overlap = self.radius + other.radius - delta_magnitude
        self.pos += normal_vector * overlap

    def check_planet_collision(self, planets: list[Planet]):
        for planet in planets:
            # TODO: Couldn't this if-condition just be part of `bounce`?
            # Should it be?
            if self.pos.distance_to(planet.pos) < self.radius + planet.radius:
                self.bounce(planet)


class Rocket:
    def __init__(self, x: float, y: float, target_pos: Vector2):
        self.pos = Vector2(x, y)
        self.target_pos = target_pos
        self.speed = Vector2(0, 0)  # Initial speed is zero
        self.last_acceleration_time = time.time()
        self.accelerating = True
        self.color = (255, 0, 0)

    def update(self, ship: Ship):
        current_time = time.time()
        time_since_last_acceleration = current_time - self.last_acceleration_time

        if self.accelerating:
            self.color = (255, 0, 200)  # Red while accelerating
        else:
            self.color = (255, 100, 0)  # Orange while not accelerating

        # Check if it's time to start accelerating
        if not self.accelerating and time_since_last_acceleration >= 9:
            self.accelerating = True
            self.last_acceleration_time = current_time

        # Check if the acceleration period should end
        elif self.accelerating and time_since_last_acceleration >= 3:
            self.accelerating = False
            self.last_acceleration_time = current_time

        # Update the target position to the ship's current position
        self.target_pos = ship.pos
        dx = self.target_pos[0] - self.pos[0]
        dy = self.target_pos[1] - self.pos[1]
        dist = sqrt(dx**2 + dy**2)

        if dist != 0:  # Avoid division by zero
            # Update speed direction towards the player
            if self.accelerating:
                # Apply additional acceleration in the direction of the player
                self.speed[0] += (dx / dist) * ROCKET_ACCELERATION
                self.speed[1] += (dy / dist) * ROCKET_ACCELERATION

        # Update position based on speed
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]

    def draw(self, screen: pygame.Surface, camera_pos: Vector2):
        pygame.draw.circle(
            screen,
            self.color,
            self.pos - camera_pos,
            5,
        )


# Add these to your global variables
enemies: list[Enemy] = []
enemy_projectiles: list[Rocket | Bullet] = []


# Spawn enemies
for _ in range(15):
    x = random.randint(0, WORLD_WIDTH)
    y = random.randint(0, WORLD_HEIGHT)
    enemy_type = random.choice(["bullet", "rocket"])
    enemies.append(Enemy(x, y, enemy_type))


# endregion


# region --- Minimap ---

MINIMAP_SIZE = 250  # Size of the minimap (width and height)
MINIMAP_MARGIN = 20  # Margin from the top-right corner
MINIMAP_BORDER_COLOR = (150, 150, 150)  # Light gray border
MINIMAP_BACKGROUND_COLOR = (30, 30, 30)  # Dark gray background
MINIMAP_SHIP_COLOR = (0, 255, 0)  # Green for the player's ship


def draw_minimap():
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


# endregion


# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        # Draw everything
        screen.fill((0, 0, 0))
        draw_grid(screen, camera_pos)

        # region --- Handle input ---

        # Handle input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            ship.rotate_left()
        if keys[pygame.K_RIGHT]:
            ship.rotate_right()
        if keys[pygame.K_UP]:
            ship.forward()
        if keys[pygame.K_DOWN]:
            ship.backward()
        if keys[pygame.K_SPACE]:
            ship.shoot()
        if (
            keys[pygame.K_m]
            and not keys[pygame.K_LEFT]
            and not keys[pygame.K_RIGHT]
            and not keys[pygame.K_UP]
            and not keys[pygame.K_DOWN]
        ):
            ship.health = min(ship.MAX_health, ship.health + ship.REPAIR_RATE)
        if (
            keys[pygame.K_b]
            and not keys[pygame.K_LEFT]
            and not keys[pygame.K_RIGHT]
            and not keys[pygame.K_UP]
            and not keys[pygame.K_DOWN]
        ):
            ship.fuel = min(ship.MAX_FUEL, ship.fuel + ship.REFUEL_RATE)

        # Update ship
        ship.update()

        # Update player bullets
        for bullet in ship.bullets[:]:
            bullet.draw(screen, camera_pos)

            bullet.update()
            if check_projectile_planet_collision(bullet, planets):
                ship.bullets.remove(bullet)
            if check_projectile_asteroid_collision(bullet, asteroids):
                ship.bullets.remove(bullet)
            if (
                bullet.pos[0] < 0
                or bullet.pos[0] > WORLD_WIDTH
                or bullet.pos[1] < 0
                or bullet.pos[1] > WORLD_HEIGHT
            ):
                ship.bullets.remove(bullet)

        # Draw ship and bullets
        ship.draw(screen, camera_pos)

        # endregion

        # region --- Draw spacegun---

        # Draw space guns and their bullets
        for spacegun in spaceguns:
            spacegun.draw(screen, camera_pos)
            spacegun.draw_bullets(screen, camera_pos)
            spacegun.shoot(ship.pos)
            if spacegun.update_bullets(ship):
                ship.health -= 15

        # endregion

        # region --- combat ---

        for enemy in enemies:
            new_projectiles = enemy.update(ship, planets)
            enemy_projectiles.extend(new_projectiles)

        # Update enemies and their projectiles
        for enemy in enemies[:]:
            new_projectiles = enemy.update(ship, planets)
            enemy_projectiles.extend(new_projectiles)

            # Check collision with player bullets
            for bullet in ship.bullets[:]:
                if enemy.pos.distance_to(bullet.pos) < enemy.radius + 3:
                    enemies.remove(enemy)
                    ship.bullets.remove(bullet)
                    break

        for projectile in enemy_projectiles[:]:
            if check_projectile_planet_collision(projectile, planets):
                enemy_projectiles.remove(projectile)

            if isinstance(projectile, Rocket):
                projectile.update(ship)
            else:
                projectile.update()

            if (
                projectile.pos[0] < 0
                or projectile.pos[0] > WORLD_WIDTH
                or projectile.pos[1] < 0
                or projectile.pos[1] > WORLD_HEIGHT
            ):
                enemy_projectiles.remove(projectile)
            elif ship.pos.distance_to(projectile.pos) < ship.radius + 3:
                ship.health -= 10
                enemy_projectiles.remove(projectile)

        # Draw enemies and their projectiles
        for enemy in enemies:
            enemy.draw(screen, camera_pos)

            for planet in planets:
                if enemy.pos.distance_to(planet.pos) < enemy.radius + planet.radius:
                    enemy.bounce(planet)

        for projectile in enemy_projectiles:
            projectile.draw(screen, camera_pos)

        ship.gun_cooldown = max(0, ship.gun_cooldown - 1)

        # endregion

        # region --- world border, camera ---

        ship_screen_pos = ship.pos - camera_pos

        # Clamp the ship's x position
        if ship.pos[0] < 0:
            ship.pos[0] = 0
        elif ship.pos[0] > WORLD_WIDTH:
            ship.pos[0] = WORLD_WIDTH

        # Clamp the ship's y position
        if ship.pos[1] < 0:
            ship.pos[1] = 0
        elif ship.pos[1] > WORLD_HEIGHT:
            ship.pos[1] = WORLD_HEIGHT

        # Update camera position
        camera_x = ship.pos[0] - SCREEN_WIDTH // 2
        camera_y = ship.pos[1] - SCREEN_HEIGHT // 2

        # Clamp camera position to world boundaries
        camera_x = max(0, min(camera_x, WORLD_WIDTH - SCREEN_WIDTH))
        camera_y = max(0, min(camera_y, WORLD_HEIGHT - SCREEN_HEIGHT))

        # endregion

        # region --- moving ship---

        # Update ship position
        ship.pos += ship.speed

        # Calculate thruster positions and sizes
        front_thruster_pos = (
            int(ship_screen_pos[0] + math.cos(math.radians(ship.angle)) * ship.radius),
            int(ship_screen_pos[1] - math.sin(math.radians(ship.angle)) * ship.radius),
        )
        rear_thruster_pos = (
            int(ship_screen_pos[0] - math.cos(math.radians(ship.angle)) * ship.radius),
            int(ship_screen_pos[1] + math.sin(math.radians(ship.angle)) * ship.radius),
        )

        # Calculate rotation thruster positions
        left_rotation_thruster_pos = (
            int(
                ship_screen_pos[0]
                + math.cos(math.radians(ship.angle + 90)) * ship.radius
            ),
            int(
                ship_screen_pos[1]
                - math.sin(math.radians(ship.angle + 90)) * ship.radius
            ),
        )
        right_rotation_thruster_pos = (
            int(
                ship_screen_pos[0]
                + math.cos(math.radians(ship.angle - 90)) * ship.radius
            ),
            int(
                ship_screen_pos[1]
                - math.sin(math.radians(ship.angle - 90)) * ship.radius
            ),
        )

        # Ensure fuel doesn't go below 0
        ship.fuel = max(0, ship.fuel)

        # Check if ship is touching world border
        if (
            ship.pos[0] <= 0
            or ship.pos[0] >= WORLD_WIDTH
            or ship.pos[1] <= 0
            or ship.pos[1] >= WORLD_HEIGHT
        ):
            game_over = True

        # endregion

        # region --- collisions ---

        collision = False
        current_time = pygame.time.get_ticks()

        # Check for collisions with squares
        for square in squares:
            if square.check_collision(ship):
                if square.action == "refuel":
                    ship.fuel = ship.MAX_FUEL
                elif square.action == "get_item":
                    has_item = True
                elif square.action == "complete_mission" and has_item:
                    mission_complete = True
                    ship_color = (255, 255, 0)  # Yellow

        # Reset ship color after 1 second if it's red
        if (
            ship_color == (255, 0, 0)
            and pygame.time.get_ticks() - collision_time > 1000
        ):
            ship_color = (255, 255, 255)  # White

        # In the main game loop, update and draw asteroids
        for asteroid in asteroids:
            asteroid.update(planets)
            asteroid.draw(screen, camera_pos)

            # Check for collision with ship

            if asteroid.check_collision(ship.pos):
                collision = True
                ship_color = (255, 0, 0)  # Red
                if collision_time == 0:
                    collision_time = current_time

                # Calculate crash intensity based on ship speed
                crash_intensity = math.sqrt(ship.speed[0] ** 2 + ship.speed[1] ** 2)
                damage = 5 * crash_intensity  # Adjust this multiplier as needed

                # Reduce health based on crash intensity
                ship.health -= damage

                # Bounce off the asteroid
                dx = ship.pos[0] - asteroid.pos[0]
                dy = ship.pos[1] - asteroid.pos[1]
                bounce_angle = math.atan2(dy, dx)

                # Reverse the ship's speed and reduce it (to simulate energy loss)
                ship.speed[0] = -ship.speed[0] * 0.5
                ship.speed[1] = -ship.speed[1] * 0.5

                # Move the ship out of the asteroid
                ship.pos[0] = asteroid.pos[0] + (
                    asteroid.radius + ship.radius + 1
                ) * math.cos(bounce_angle)
                ship.pos[1] = asteroid.pos[1] + (
                    asteroid.radius + ship.radius + 1
                ) * math.sin(bounce_angle)

                break

        if not collision:
            ship.pos = ship.pos
            collision_time = 0
        else:
            collision_time = current_time

        # Check asteroid-asteroid collisions
        for i, asteroid1 in enumerate(asteroids):
            for asteroid2 in asteroids[i + 1 :]:
                if asteroid1.check_collision(asteroid2):
                    # Handle collision (implement bouncing in step 2)
                    asteroid1.bounce(asteroid2)
                    asteroid2.bounce(asteroid1)

        # Check asteroid-planet collisions
        for asteroid in asteroids:
            for planet in planets:
                if asteroid.check_collision(planet):
                    # Handle collision (implement bouncing in step 2)
                    asteroid.bounce(planet)

        # endregion

        # region --- planets ---

        # TODO: The variable "collided_with_any_planets" should probably be
        # removed at some point. In an earlier version of the code, the loop
        # "for planet in planets" immediately "break"ed whenever any planet
        # Collided with the ship. However, this means we won't be drawing
        # the other planets, nor applying their gravity to `ship`.
        # So I removed the "break"-statement in the collision-check, but
        # I didn't know why the break-statement was there in the first
        # place. Did multiple planet-collisions on the same frame cause any
        # bugs? Hence, `collided_with_any_planets` was introduced, to make
        # sure we only collide with at most one planet per frame. Once verified
        # that multiple collisions per frame don't cause any bugs, that variable
        # can be removed.
        collided_with_any_planets = False
        for planet in planets:
            planet.draw(screen, camera_pos)
            force_x, force_y = planet.calculate_gravity(ship)
            total_force_x += force_x
            total_force_y += force_y

            if not collided_with_any_planets:
                # In the collision detection loop for planets:
                if planet.check_collision(ship):
                    bounce_from_planet(planet)
                    collision = True
                    collided_with_any_planets = True
                    ship_color = (255, 0, 0)  # Red

                    # Calculate crash intensity based on ship speed
                    crash_intensity = math.sqrt(ship.speed[0] ** 2 + ship.speed[1] ** 2)
                    damage = 0.5 * crash_intensity  # Adjust this multiplier as needed

                    # Reduce health based on crash intensity
                    ship.health -= damage * (current_time - collision_time) / 1000
                    if collision_time == 0:
                        collision_time = current_time
                    # Calculate and apply damage as before

        # endregion

        # Draw squares
        for square in squares:
            square.draw(screen, camera_pos)

        # region --- displaying ---

        # Display ship coordinates
        font = pygame.font.Font(None, 22)
        coord_text = font.render(
            f"X: {int(ship.pos[0])}, Y: {int(ship.pos[1])}", True, (255, 255, 255)
        )
        screen.blit(coord_text, (10, 10))

        # Display fuel
        fuel_text = font.render(f"Fuel: {ship.fuel:.3f}", True, (255, 255, 255))
        screen.blit(fuel_text, (10, 50))

        # Display item status
        item_text = font.render(
            "Item: Collected" if has_item else "Item: Not Collected",
            True,
            (255, 255, 255),
        )
        screen.blit(item_text, (10, 90))

        # Display mission status
        mission_text = font.render(
            "Mission Complete!" if mission_complete else "Mission: In Progress",
            True,
            (255, 255, 255),
        )
        screen.blit(mission_text, (10, 130))

        # Display ship health
        health_text = font.render(f"Health: {int(ship.health)}", True, (255, 255, 255))
        screen.blit(health_text, (10, 170))

        # Display square coordinates
        pos_refuel_text = font.render(
            f"Coordinates Refuel: {int(pos_refuel[0])}, {int(pos_refuel[1])}",
            True,
            (255, 255, 255),
        )
        pos_item_text = font.render(
            f"Coordinates Item: {int(pos_item[0])}, {int(pos_item[1])}",
            True,
            (255, 255, 255),
        )
        pos_complete_text = font.render(
            f"Coordinates Destination: {int(pos_complete[0])}, {int(pos_complete[1])}",
            True,
            (255, 255, 255),
        )
        screen.blit(pos_refuel_text, (10, 210))
        screen.blit(pos_item_text, (10, 230))
        screen.blit(pos_complete_text, (10, 250))
        ammo_text = font.render(f"Ammo: {ship.ammo}", True, (255, 255, 255))
        screen.blit(ammo_text, (10, 290))

        advice_text = font.render(
            "Ignore the squares, just fight the enemies", True, (255, 255, 255)
        )
        screen.blit(advice_text, (10, 310))

        lag_text1 = font.render(
            f"ship.bullets: {len(ship.bullets[:])}", True, (255, 255, 255)
        )
        screen.blit(lag_text1, (10, 330))

        lag_text2 = font.render(f"enemies: {len(enemies[:])}", True, (255, 255, 255))
        screen.blit(lag_text2, (10, 350))

        lag_text3 = font.render(
            f"enemy_projectiles: {len(enemy_projectiles[:])}", True, (255, 255, 255)
        )
        screen.blit(lag_text3, (10, 370))

        draw_minimap()

        # endregion

        # Check if ship health reaches 0
        if ship.health <= 0:
            game_over = True

    else:
        # Game over screen
        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 64)
        game_over_text = font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(
            game_over_text,
            (
                SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
                SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2,
            ),
        )

    pygame.time.Clock().tick(60)

    pygame.display.flip()

# Quit the game
pygame.quit()
sys.exit()
