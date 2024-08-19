import pygame
from pygame.math import Vector2
from pygame import Color
import math
from physics import Bullet

# TODO: Move constant somewhere else
BULLET_SPEED = 6

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
        self.pos = Vector2(x, y)

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

        self.load_image('ship_sprite.png')

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
            normalized_vel = self.speed.normalize()
            bullet_pos = self.pos + normalized_vel * self.radius
            bullet_vel = self.speed + normalized_vel * BULLET_SPEED
            self.bullets.append(Bullet(bullet_pos, bullet_vel, pygame.Color("blue")))
            self.gun_cooldown = 9
            self.ammo -= 1

    def update(self):
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]

        self.gun_cooldown = max(0, self.gun_cooldown - 1)
        self.fuel = max(0, self.fuel)
    
    def draw(self, screen: pygame.Surface, camera_pos: Vector2):
        ship_relative_pos = self.pos - camera_pos
        pygame.draw.circle(screen, Color("gray"), ship_relative_pos, self.radius)

        # Draw gun
        gun_length = 35
        gun_end_x = ship_relative_pos[0] + math.cos(math.radians(self.angle)) * (
            self.radius + gun_length
        )
        gun_end_y = ship_relative_pos[1] - math.sin(math.radians(self.angle)) * (
            self.radius + gun_length
        )
        pygame.draw.line(
            screen, (Color("blue")), ship_relative_pos, (gun_end_x, gun_end_y), 7
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