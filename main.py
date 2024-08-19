from __future__ import annotations
import pygame
from pygame.math import Vector2
from pygame import Color
import sys
import math
import random
from physics import Asteroid, Planet, Bullet, Rocket
from collections.abc import Sequence

from init import (
    camera,
    collision_time,
)

from ship import Ship

from enemy_info import (
    ENEMY_ACCELERATION,
    ENEMY_SHOOT_RANGE,
)
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, G

# Initialize Pygame
pygame.init()

ship_color = Color("white")
collision_time = 0

# Game state
has_item = False
mission_complete = False
game_over = False


ship = Ship(
    Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2), Vector2(0, 0), 1, 10, Color("turquoise")
)


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

# Generate asteroids
asteroids: list[Asteroid] = []
for _ in range(5):  # Adjust the number of asteroids as needed
    pos = Vector2(random.uniform(0, WORLD_WIDTH), random.uniform(0, WORLD_HEIGHT))
    speed = Vector2(random.uniform(0, WORLD_WIDTH), random.uniform(0, WORLD_HEIGHT))
    radius = random.uniform(40, 120)
    asteroids.append(Asteroid(pos, speed, 1, radius))

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
    def update(self, ship: Ship, planets: list[Planet]) -> "Sequence[Bullet]":
        delta = ship.pos - self.pos
        dist = delta.magnitude()
        # TODO: Rather than storing an int for current_action, store some enum. See:
        # https://stackoverflow.com/questions/36932/how-can-i-represent-an-enum-in-python
        self.current_action = 6
        force = calculate_gravity(self.pos, 100, planets)  # Assume enemy mass is 100
        self.speed += force / 100
        self.check_planet_collision(planets)

        # Check if period has elapsed
        if self.action_timer <= 0:
            self.current_action = random.randint(1, 4)
            self.action_timer = 0.5 * 60  # Reset timer to seconds

        if self.current_action == 1:  # Accelerate towards player
            self.speed += delta * ENEMY_ACCELERATION * 2 / dist

        elif self.current_action == 2:  # Accelerate randomly
            rand_speed = Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
            self.speed += rand_speed * ENEMY_ACCELERATION * 0.2

        elif self.current_action == 3:  # Decelerate
            self.speed.move_towards_ip(Vector2(0, 0), ENEMY_ACCELERATION * 0.2)

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
                return [
                    Bullet(
                        self.pos[0], self.pos[1], delta.angle_to(Vector2(1, 0)), self
                    )
                ]
            else:
                # Set cooldown for rocket enemy
                self.shoot_cooldown = ROCKET_SHOOT_COOLDOWN
                return [Rocket(self.pos, self.speed * 2, Color("red"))]
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

        # Answer:
        # not sure if mass is realy something we need in the game, I don't think we need to make the physics too complicated, but not sure yet.
        # I guess you can create pretty realistic gravity without mass just having all enemies affected by the same force.

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

            # Probably
            if self.pos.distance_to(planet.pos) < self.radius + planet.radius:
                self.bounce(planet)


# Add these to your global variables
enemies: list[Enemy] = []
enemy_projectiles: list[Bullet] = []


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
    # TODO: Reimplement this with another instance of the Camera class :)
    pass
    """
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


# endregion


# Game loop
running = True
clock = pygame.time.Clock()
while running:
    dt = clock.tick()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        camera.start_drawing_new_frame()
        # TODO: reimplement drawing the grid

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
            bullet.draw(camera)

            bullet.step(dt)
            if any(
                map(lambda planet: planet.intersects_point(bullet.pos), planets)
            ) or any(
                map(lambda asteroid: asteroid.intersects_point(bullet.pos), asteroids)
            ):
                ship.bullets.remove(bullet)
                continue

            if (
                bullet.pos[0] < 0
                or bullet.pos[0] > WORLD_WIDTH
                or bullet.pos[1] < 0
                or bullet.pos[1] > WORLD_HEIGHT
            ):
                ship.bullets.remove(bullet)

        # Draw ship and bullets
        ship.draw(camera)

        # endregion

        # region --- Draw spacegun---

        # Draw space guns and their bullets
        for spacegun in spaceguns:
            spacegun.draw(camera.surface, camera.pos)
            spacegun.draw_bullets(camera.surface, camera.pos)
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
            projectile.step(dt)

            if any(
                map(lambda planet: planet.intersects_point(bullet.pos), planets)
            ) or any(
                map(lambda asteroid: asteroid.intersects_point(bullet.pos), asteroids)
            ):
                enemy_projectiles.remove(projectile)
                continue  # TODO: Is this `continue` here wrong?

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
            enemy.draw(camera.surface, camera.pos)

            for planet in planets:
                if enemy.pos.distance_to(planet.pos) < enemy.radius + planet.radius:
                    enemy.bounce(planet)

        for projectile in enemy_projectiles:
            projectile.draw(camera)

        ship.gun_cooldown = max(0, ship.gun_cooldown - 1)

        # endregion

        # region --- world border, camera ---

        ship_screen_pos = ship.pos - camera.pos

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
        camera_pos = Vector2(camera_x, camera_y)

        # endregion

        # region --- moving ship---

        # Update ship position
        ship.pos += ship.speed

        # Calculate thruster positions and sizes

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
            asteroid.apply_gravitational_forces(planets, dt)
            asteroid.step(dt)
            asteroid.draw(camera)

            # Check for collision with ship

            if asteroid.intersects_point(ship.pos):
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

                # Reverse the ship's speed and reduce it
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
                asteroid1.bounce_off_of_disk(asteroid2)
                # TODO: We can't have asteroid2 bounce off of asteroid1
                # meaningfully, because asteroid1 already bounced off of
                # asteroid2. Instead of these two lines, we should have
                # a new method on disks, like bounce_off_of_each_other,
                # which will be non-trivially different from bounce_off_of_disk
                asteroid2.bounce_off_of_disk(asteroid1)

        # Check asteroid-planet collisions
        for asteroid in asteroids:
            for planet in planets:
                asteroid.bounce_off_of_disk(planet)

        # endregion

        # region --- planets ---

        ship.
        for planet in planets:
            planet.draw(screen, camera_pos)

            # In the collision detection loop for planets:
            if ship.bounce_off_of_disk(planet):
            if planet.check_collision(ship):
                bounce_from_planet(planet)
                collision = True
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

        # draw_minimap()

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

    # In your main game loop

    pygame.display.flip()

# Quit the game
pygame.quit()
sys.exit()
