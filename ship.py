import pygame
from pygame.math import Vector2
from pygame import Color
import math
from physics import Disk, Bullet, Rocket
from camera import Camera
from enum import Enum
import random


BULLET_SPEED = 500
GUNBARREL_LENGTH = 3  # relative to radius
GUNBARREL_WIDTH = 0.5  # relative to radius
ENEMY_SHOOT_RANGE = 1000


class Ship(Disk):
    def __init__(
        self, pos: Vector2, vel: Vector2, density: float, size: float, color: Color
    ):
        super().__init__(pos, vel, density, size, color)
        self.size = size
        self.angle = 0
        self.health = 100.0
        # self.REPAIR_RATE = 0.1 not currently being used
        # self.REFUEL_RATE = 0.2
        # self.MAX_health = 200.0
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
        self.MAX_FUEL = 100.0
        self.fuel = self.MAX_FUEL
        self.fuel_consumption_rate = 0.7
        self.fuel_rot_consumption_rate = 0.7

    def get_faced_direction(self) -> Vector2:
        # For unknown reasons, `Vector2.from_polar((self.angle, 1))` won't work.
        dir = Vector2()
        dir.from_polar((1, self.angle))
        return dir

    def shoot(self):
        if self.gun_cooldown <= 0 and self.ammo > 0:
            forward = self.get_faced_direction()
            bullet_pos = self.pos + forward * self.radius * GUNBARREL_LENGTH
            bullet_vel = self.vel + forward * BULLET_SPEED
            self.projectiles.append(Bullet(bullet_pos, bullet_vel, self.color))
            self.gun_cooldown = 0.1
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
            self.gun_cooldown = 0.025
            self.ammo -= 1
