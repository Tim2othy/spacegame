import pygame
import math
import random



import numpy as np




from calcu import distance

from planets import Planet


from bullet import Bullet





class Ship:
    def __init__(self, x, y):
        self.angle = 0
        self.speed = [0, 0]
        self.radius = 9
        self.mass = 1000
        self.health = 10000
        self.REPAIR_RATE = 0.1
        self.REFUEL_RATE = 0.2
        self.MAX_health = 200
        self.bullets = []
        self.gun_cooldown = 3
        self.pos = [x, y]

        self.ammo = 250
        self.thrust = 0.19
        self.rotation_thrust = 3
        self.left_rotation_thruster_on = False
        self.right_rotation_thruster_on = False
        self.front_thruster_on = False
        self.rear_thruster_on = False
        self.fuel = 100
        self.fuel_consumption_rate = 0.07
        self.rotation_fuel_consumption_rate = 0.03
        self.MAX_FUEL = 100

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









    def draw(self, screen, camera_x, camera_y):
        ship_screen_pos = (int(self.pos[0] - camera_x), int(self.pos[1] - camera_y))
        pygame.draw.circle(screen, (255, 255, 255), ship_screen_pos, self.radius)
    
        # Draw gun
        gun_length = 25
        gun_end_x = ship_screen_pos[0] + math.cos(math.radians(self.angle)) * (self.radius + gun_length)
        gun_end_y = ship_screen_pos[1] - math.sin(math.radians(self.angle)) * (self.radius + gun_length)
        pygame.draw.line(screen, (200, 200, 200), ship_screen_pos, (gun_end_x, gun_end_y), 6)

        # Draw thrusters
        self.draw_thruster(screen, ship_screen_pos, angle_offset=0,   is_active=self.front_thruster_on,             is_rotation=False)    # Front thruster
        self.draw_thruster(screen, ship_screen_pos, angle_offset=180, is_active=self.rear_thruster_on,              is_rotation=False)  # Rear thruster
        self.draw_thruster(screen, ship_screen_pos, angle_offset=90,  is_active=self.left_rotation_thruster_on,     is_rotation=True)  # Left rotation thruster
        self.draw_thruster(screen, ship_screen_pos, angle_offset=-90, is_active=self.right_rotation_thruster_on,    is_rotation=True) # Right rotation thruster



    def draw_thruster(self, screen, ship_screen_pos, angle_offset, is_active, is_rotation=False):
        thruster_pos = (
            int(ship_screen_pos[0] + math.cos(math.radians(self.angle + angle_offset)) * self.radius),
            int(ship_screen_pos[1] - math.sin(math.radians(self.angle + angle_offset)) * self.radius)
        )
    
        if is_rotation == True:
            color = (0, 255, 255) if is_active == True else (255, 255, 255)  # Cyan for rotation thrusters

        else:
            color = (0, 0, 255) if is_active == True else (255, 255, 255)  # Blue for front/rear thrusters
    
        self.draw_thruster_shape(screen, thruster_pos, color, self.angle + angle_offset)



    

    def draw_thruster_shape(self, screen, pos, color, angle):
        thruster_width = 5
        thruster_height = 10
        points = [
            (pos[0] - math.sin(math.radians(angle)) * thruster_width / 2,
             pos[1] - math.cos(math.radians(angle)) * thruster_width / 2),
            (pos[0] + math.sin(math.radians(angle)) * thruster_width / 2,
             pos[1] + math.cos(math.radians(angle)) * thruster_width / 2),
            (pos[0] + math.sin(math.radians(angle)) * thruster_width / 2 + math.cos(math.radians(angle)) * thruster_height,
             pos[1] + math.cos(math.radians(angle)) * thruster_width / 2 - math.sin(math.radians(angle)) * thruster_height),
            (pos[0] - math.sin(math.radians(angle)) * thruster_width / 2 + math.cos(math.radians(angle)) * thruster_height,
             pos[1] - math.cos(math.radians(angle)) * thruster_width / 2 - math.sin(math.radians(angle)) * thruster_height)
        ]
        pygame.draw.polygon(screen, color, points)


