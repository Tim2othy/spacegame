import pygame
from pygame.math import Vector2
from pygame import Color
import math

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bullet import Bullet

class Ship:
    def __init__(self, x: float, y: float):
        self.angle = 0
        self.speed = Vector2(0, 0)
        self.radius = 9
        self.mass = 1000.0
        self.health = 10000.0
        self.REPAIR_RATE = 0.1
        self.REFUEL_RATE = 0.2
        self.MAX_health = 200.0
        self.bullets: list[Bullet] = []
        self.gun_cooldown = 3
        self.pos = Vector2(0, 0)

        self.ammo = 250
        self.thrust = 0.19
        self.rotation_thrust = 3
        self.left_rotation_thruster_on = False
        self.right_rotation_thruster_on = False
        self.front_thruster_on = False
        self.rear_thruster_on = False
        self.fuel = 100.0
        self.fuel_consumption_rate = 0.07
        self.rotation_fuel_consumption_rate = 0.03
        self.MAX_FUEL = 100.0

    def rotate_left(self):
        if self.fuel > 0:
            self.angle += self.rotation_thrust
            self.fuel -= self.rotation_fuel_consumption_rate
            self.left_rotation_thruster_on = True
        else:
            self.left_rotation_thruster_on = False

    def rotate_right(self):
        if self.fuel > 0:
            self.angle -= self.rotation_thrust
            self.fuel -= self.rotation_fuel_consumption_rate
            self.right_rotation_thruster_on = True
        else:
            self.right_rotation_thruster_on = False

    def forward(self):
        if self.fuel > 0:
            self.speed[0] += math.cos(math.radians(self.angle)) * self.thrust
            self.speed[1] -= math.sin(math.radians(self.angle)) * self.thrust
            self.fuel -= self.fuel_consumption_rate
            self.rear_thruster_on = True
        else:
            self.rear_thruster_on = False

    def backward(self):
        if self.fuel > 0:
            self.speed[0] -= math.cos(math.radians(self.angle)) * self.thrust
            self.speed[1] += math.sin(math.radians(self.angle)) * self.thrust
            self.fuel -= self.fuel_consumption_rate
            self.front_thruster_on = True
        else:
            self.front_thruster_on = False

    def shoot(self):
        if self.gun_cooldown <= 0 and self.ammo > 0:
            angle = math.radians(-self.angle)
            bullet_x = self.pos[0] + math.cos(-angle) * (self.radius + 20)
            bullet_y = self.pos[1] - math.sin(-angle) * (self.radius + 20)
            self.bullets.append(Bullet(bullet_x, bullet_y, angle, self))
            self.gun_cooldown = 9
            self.ammo -= 1

    def update(self):
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]

        self.gun_cooldown = max(0, self.gun_cooldown - 1)
        self.fuel = max(0, self.fuel)

    def draw(self, screen: pygame.Surface, camera_pos: Vector2):
        ship_relative_pos = self.pos - camera_pos
        pygame.draw.circle(screen, (255, 255, 255), ship_relative_pos, self.radius)

        # Draw gun
        gun_length = 25
        gun_end_x = ship_relative_pos[0] + math.cos(math.radians(self.angle)) * (
            self.radius + gun_length
        )
        gun_end_y = ship_relative_pos[1] - math.sin(math.radians(self.angle)) * (
            self.radius + gun_length
        )
        pygame.draw.line(
            screen, (200, 200, 200), ship_relative_pos, (gun_end_x, gun_end_y), 6
        )

        # Draw thrusters
        self.draw_thruster(
            screen,
            ship_relative_pos,
            angle_offset=0,
            is_active=self.front_thruster_on,
            is_rotation=False,
        )  # Front thruster
        self.draw_thruster(
            screen,
            ship_relative_pos,
            angle_offset=180,
            is_active=self.rear_thruster_on,
            is_rotation=False,
        )  # Rear thruster
        self.draw_thruster(
            screen,
            ship_relative_pos,
            angle_offset=90,
            is_active=self.left_rotation_thruster_on,
            is_rotation=True,
        )  # Left rotation thruster
        self.draw_thruster(
            screen,
            ship_relative_pos,
            angle_offset=-90,
            is_active=self.right_rotation_thruster_on,
            is_rotation=True,
        )  # Right rotation thruster

    def draw_thruster(
        self,
        screen: pygame.Surface,
        ship_screen_pos: Vector2,
        angle_offset: float,
        is_active: bool,
        is_rotation: bool = False,
    ):
        thruster_pos = Vector2(
            ship_screen_pos[0]
            + math.cos(math.radians(self.angle + angle_offset)) * self.radius,
            ship_screen_pos[1]
            - math.sin(math.radians(self.angle + angle_offset)) * self.radius,
        )

        color = Color(("cyan" if is_rotation else "blue") if is_active else "white")
        self.draw_thruster_shape(screen, thruster_pos, color, self.angle + angle_offset)

    def draw_thruster_shape(
        self,
        screen: pygame.Surface,
        pos: Vector2,
        color: pygame.Color,
        angle: float,
    ):
        thruster_width = 5
        thruster_height = 10
        points = [
            (
                pos[0] - math.sin(math.radians(angle)) * thruster_width / 2,
                pos[1] - math.cos(math.radians(angle)) * thruster_width / 2,
            ),
            (
                pos[0] + math.sin(math.radians(angle)) * thruster_width / 2,
                pos[1] + math.cos(math.radians(angle)) * thruster_width / 2,
            ),
            (
                pos[0]
                + math.sin(math.radians(angle)) * thruster_width / 2
                + math.cos(math.radians(angle)) * thruster_height,
                pos[1]
                + math.cos(math.radians(angle)) * thruster_width / 2
                - math.sin(math.radians(angle)) * thruster_height,
            ),
            (
                pos[0]
                - math.sin(math.radians(angle)) * thruster_width / 2
                + math.cos(math.radians(angle)) * thruster_height,
                pos[1]
                - math.cos(math.radians(angle)) * thruster_width / 2
                - math.sin(math.radians(angle)) * thruster_height,
            ),
        ]
        pygame.draw.polygon(screen, color, points)
