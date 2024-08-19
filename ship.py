import pygame
from pygame.math import Vector2
from pygame import Color
import math
from physics import Disk, Bullet
from camera import Camera


# TODO: Move constant somewhere else
BULLET_SPEED = 6
GUNBARREL_LENGTH = 32
GUNBARREL_WIDTH = 8

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
        self.bullets: list[Bullet] = []
        self.gun_cooldown = 3

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
            self.vel[0] += math.cos(math.radians(self.angle)) * self.thrust
            self.vel[1] -= math.sin(math.radians(self.angle)) * self.thrust
            self.fuel -= self.fuel_consumption_rate
            self.rear_thruster_on = True
        else:
            self.rear_thruster_on = False

    def backward(self):
        if self.fuel > 0:
            self.vel[0] -= math.cos(math.radians(self.angle)) * self.thrust
            self.vel[1] += math.sin(math.radians(self.angle)) * self.thrust
            self.fuel -= self.fuel_consumption_rate
            self.front_thruster_on = True
        else:
            self.front_thruster_on = False

    def shoot(self):
        if self.gun_cooldown <= 0 and self.ammo > 0:
            normalized_vel = self.vel.normalize()
            bullet_pos = self.pos + normalized_vel * self.radius
            bullet_vel = self.vel + normalized_vel * BULLET_SPEED
            self.bullets.append(Bullet(bullet_pos, bullet_vel, pygame.Color("blue")))
            self.gun_cooldown = 9
            self.ammo -= 1

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

        self.gun_cooldown = max(0, self.gun_cooldown - 1)
        self.fuel = max(0, self.fuel)

    def draw(self, camera: Camera):
        normalized_vel = self.vel.normalize()

        ship_screen_pos = camera.world_to_camera(self.pos)

        # Draw gun
        gun_end = camera.world_to_camera(self.pos + normalized_vel * GUNBARREL_LENGTH)
        pygame.draw.line(
            camera.surface,
            Color("blue"),
            ship_screen_pos,
            gun_end,
            GUNBARREL_WIDTH,
        )

        # TODO: Probably overhaul Thruster-drawing at some point
        # Draw thrusters
        self.draw_thruster(
            camera.surface,
            ship_screen_pos,
            angle_offset=0,
            is_active=self.front_thruster_on,
            is_rotation=False,
        )  # Front thruster
        self.draw_thruster(
            camera.surface,
            ship_screen_pos,
            angle_offset=180,
            is_active=self.rear_thruster_on,
            is_rotation=False,
        )  # Rear thruster
        self.draw_thruster(
            camera.surface,
            ship_screen_pos,
            angle_offset=90,
            is_active=self.left_rotation_thruster_on,
            is_rotation=True,
        )  # Left rotation thruster
        self.draw_thruster(
            camera.surface,
            ship_screen_pos,
            angle_offset=-90,
            is_active=self.right_rotation_thruster_on,
            is_rotation=True,
        )  # Right rotation thruster

        super().draw(camera)  # Draw circular body ("hitbox")

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

        color = Color(("red" if is_rotation else "orange") if is_active else "white")
        self.draw_thruster_shape(screen, thruster_pos, color, self.angle + angle_offset)

    def draw_thruster_shape(
        self,
        screen: pygame.Surface,
        pos: Vector2,
        color: pygame.Color,
        angle: float,
    ):
        thruster_width = 10
        thruster_height = 20
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

    def draw_with_image(self, screen: pygame.Surface, camera_pos: Vector2): # TODO is this type hinting ???
        ship_relative_pos = self.pos - camera_pos # TODO should all be done using vectors
            
        # Rotate the image
        rotated_image = pygame.transform.rotate(self.original_image, self.angle)
        
        # Get the rect of the rotated image and set its center
        rect = rotated_image.get_rect()
        rect.center = ship_relative_pos
            
        # Draw the rotated image
        screen.blit(rotated_image, rect)
    """