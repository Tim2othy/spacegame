import pygame
from pygame.math import Vector2
from pygame import Color
import math
from physics import Disk, Bullet, Rocket
from camera import Camera
from enum import Enum
from enemy_info import ENEMY_SHOOT_RANGE
import random


# TODO: Move constant somewhere else
BULLET_SPEED = 500
GUNBARREL_LENGTH = 3  # relative to radius
GUNBARREL_WIDTH = 0.5  # relative to radius


class Ship(Disk):
    def __init__(
        self, pos: Vector2, vel: Vector2, density: float, size: float, color: Color
    ):
        super().__init__(pos, vel, density, size, color)
        self.size = size
        self.angle = 0
        self.health = 10000.0
        self.REPAIR_RATE = 0.1
        self.REFUEL_RATE = 0.2
        self.MAX_health = 200.0
        self.projectiles: list[Bullet] = []
        self.gun_cooldown = 3
        self.has_trophy = True

        self.ammo: int = 250
        self.thrust = 500 * self.mass
        self.rotation_thrust = 150
        self.thruster_rot_left = False
        self.thruster_rot_right = False
        self.thruster_backward = False
        self.thruster_forward = False
        self.fuel = 100.0
        self.fuel_consumption_rate = 0.07
        self.fuel_rot_consumption_rate = 0.03
        self.MAX_FUEL = 100.0

    def get_faced_direction(self):
        # TODO: Why doesn't Vector2.from_polar() work?
        return Vector2(
            math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle))
        )

    def shoot(self):
        if self.gun_cooldown <= 0 and self.ammo > 0:
            forward = self.get_faced_direction()
            bullet_pos = self.pos + forward * self.radius * GUNBARREL_LENGTH
            bullet_vel = self.vel + forward * BULLET_SPEED
            self.projectiles.append(Bullet(bullet_pos, bullet_vel, self.color))
            self.gun_cooldown = 0.25
            self.ammo -= 1

    def step(self, dt: float):
        if self.fuel > 0:
            if self.thruster_rot_left:
                self.fuel = max(0, self.fuel - dt * self.fuel_rot_consumption_rate)
                self.angle += self.rotation_thrust * dt
            if self.thruster_rot_right:
                self.fuel = max(0, self.fuel - dt * self.fuel_rot_consumption_rate)
                self.angle -= self.rotation_thrust * dt

            forward = self.get_faced_direction()
            if self.thruster_forward:
                self.fuel = max(0, self.fuel - dt * self.fuel_consumption_rate)
                self.apply_force(forward * self.thrust, dt)
            if self.thruster_backward:
                self.fuel = max(0, self.fuel - dt * self.fuel_consumption_rate)
                self.apply_force(-forward * self.thrust, dt)

        super().step(dt)

        for projectile in self.projectiles:
            projectile.step(dt)

        self.gun_cooldown = max(0, self.gun_cooldown - dt)

    def draw(self, camera: Camera):
        forward = self.get_faced_direction()
        right = pygame.math.Vector2(-forward.y, forward.x)
        left = -right
        backward = -forward

        darker_color = Color(self.color)
        darker_color.r = darker_color.r // 2
        darker_color.g = darker_color.g // 2
        darker_color.b = darker_color.b // 2

        # Helper function for drawing polygons relative to the ship-position
        def drawy(color: Color, points: list[Vector2]):
            camera.draw_polygon(color, [self.pos + self.radius * p for p in points])

        # TODO: Especially the backward-thruster is super ugly
        # thruster_backward (active)
        if self.thruster_backward:
            drawy(Color("red"), [forward * 2, left * 1.25, right * 1.25])

        # "For his neutral special, he wields a gun"
        camera.draw_line(
            Color("blue"),
            self.pos,
            self.pos + forward * self.radius * GUNBARREL_LENGTH,
            GUNBARREL_WIDTH * self.radius,
        )

        # thruster_rot_left (material)
        drawy(
            darker_color,
            [
                0.7 * left + 0.7 * forward,
                0.5 * left + 0.5 * backward,
                2.0 * left + 1.0 * backward,
            ],
        )
        # thruster_rot_left (active)
        if self.thruster_rot_left:
            drawy(
                Color("yellow"),
                [
                    1.5 * left + 1.25 * backward,
                    0.5 * left + 0.5 * backward,
                    2.0 * left + 1.0 * backward,
                ],
            )

        # thruster_rot_right (material)
        drawy(
            darker_color,
            [
                0.7 * right + 0.7 * forward,
                0.5 * right + 0.5 * backward,
                2.0 * right + 1.0 * backward,
            ],
        )
        # thruster_rot_right (active)
        if self.thruster_rot_right:
            drawy(
                Color("yellow"),
                [
                    1.5 * right + 1.25 * backward,
                    0.5 * right + 0.5 * backward,
                    2.0 * right + 1.0 * backward,
                ],
            )

        # thruster_forward (flame)
        if self.thruster_forward:
            drawy(
                Color("orange"),
                [
                    0.7 * left + 0.7 * backward,
                    0.5 * left + 1.5 * backward,
                    1.25 * backward,
                    0.5 * right + 1.5 * backward,
                    0.7 * right + 0.7 * backward,
                ],
            )
        # thruster_forward (material)
        drawy(
            darker_color,
            [
                0.7 * left + 0.7 * backward,
                0.5 * left + 1.25 * backward,
                1.0 * backward,
                0.5 * right + 1.25 * backward,
                0.7 * right + 0.7 * backward,
            ],
        )

        super().draw(camera)  # Draw circular body ("hitbox")

        for projectile in self.projectiles:
            projectile.draw(camera)

    # TODO: Either revive or delete this code at some point
    # If reviving, add `self.load_image('ship_sprite.png')` back
    # to the Ship.__init__ method.
    """
    def load_image(self, image_path: str):
        
        #Load and prepare the ship image.
        #param image_path: Path to the ship image file
        
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (60, 28))  # Resize 
        self.original_image = self.image  # Store the original image for rotation

    def draw_with_image(self, screen: pygame.Surface, camera_pos: Vector2): 
        ship_relative_pos = self.pos - camera_pos 
            
        # Rotate the image
        rotated_image = pygame.transform.rotate(self.original_image, self.angle)
        
        # Get the rect of the rotated image and set its center
        rect = rotated_image.get_rect()
        rect.center = ship_relative_pos
            
        # Draw the rotated image
        screen.blit(rotated_image, rect)
    """


class BulletEnemy(Ship):
    """An enemy ship, targeting a specific other ship."""

    Action = Enum(
        "Action", ["accelerate_to_player", "accelerate_randomly", "decelerate"]
    )

    def __init__(
        self,
        pos: Vector2,
        vel: Vector2,
        target_ship: Ship,
        shoot_cooldown: float = 0.125,
        color: Color = Color("purple"),
    ):
        super().__init__(pos, vel, 1, 8, color)
        self.thrust /= 2
        self.time_until_next_shot = 0
        self.action_timer = 6
        self.health = 100
        self.current_action: BulletEnemy.Action = BulletEnemy.Action.accelerate_randomly
        self.target_ship = target_ship
        self.shoot_cooldown = shoot_cooldown
        self.projectiles: list[Bullet] = []

    def step(self, dt: float):
        # TODO: Enemies should be affected by gravity and collisions, this
        # must be added back into the main-loop (or applied into some
        # superclass step-function)

        self.action_timer -= dt
        if self.action_timer <= 0:
            self.current_action = random.choice(list(BulletEnemy.Action))
            self.action_timer = 6

        delta_target_ship = self.target_ship.pos - self.pos

        force_direction: Vector2
        match self.current_action:
            case BulletEnemy.Action.accelerate_to_player:
                force_direction = delta_target_ship
            case BulletEnemy.Action.accelerate_randomly:
                # TODO: Almost certainly, these accelerations will cancel each other out,
                # and the ship will not experience significant change in speed
                force_direction = Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
            case BulletEnemy.Action.decelerate:
                force_direction = -self.vel
        force = force_direction * self.thrust / force_direction.magnitude()
        self.apply_force(force, dt)

        super().step(dt)
        self.angle = math.degrees(math.atan2(self.vel.y, self.vel.x))

        # Shooting logic
        self.time_until_next_shot -= 1
        if (
            delta_target_ship.magnitude_squared() < ENEMY_SHOOT_RANGE**2
            and self.time_until_next_shot <= 0
        ):
            self.shoot()
            self.time_until_next_shot = self.shoot_cooldown


class RocketEnemy(BulletEnemy):
    """An enemy ship shooting rockets, targeting a specific other ship."""

    def __init__(
        self,
        pos: Vector2,
        vel: Vector2,
        target_ship: Ship,
        shoot_cooldown: float = 0.5,
        color: Color = Color("red"),
    ):
        super().__init__(pos, vel, target_ship, shoot_cooldown, color)

    def shoot(self):
        if self.gun_cooldown <= 0 and self.ammo > 0:
            forward = self.get_faced_direction()
            bullet_pos = self.pos + forward * self.radius * GUNBARREL_LENGTH
            bullet_vel = self.vel + forward * BULLET_SPEED
            self.projectiles.append(
                Rocket(bullet_pos, bullet_vel, self.color, self.target_ship)
            )
            self.gun_cooldown = 0.25
            self.ammo -= 1


# TODO: Revive spaceguns, or decide they're not worth reviving
"""
class Spacegun:
    def __init__(self, x: float, y: float):
        self.pos = Vector2(x, y)
        self.size = 40
        self.color = (50, 50, 100)
        self.last_shot_time = 60
        self.shoot_interval = 300
        self.bullets: list[Bullet] = []

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
            self.bullets.append(Bullet(self.pos, direction, Color("orange")))
            self.last_shot_time = current_time

    def update_bullets(self, ship: Ship) -> bool:
        for bullet in self.bullets:
            bullet.step(dt)
            # TODO: reimplement that old bullets get destroyed.
            # Or perhaps we limit the size of the bullets-array,
            # and always throw out the oldest ones?
            if ship.intersects_point(bullet.pos):
                self.bullets.remove(bullet)
                return True  # Collision detected
        return False

    def draw_bullets(self, camera: Camera):
        for bullet in self.bullets:
            bullet.draw(camera)
"""
