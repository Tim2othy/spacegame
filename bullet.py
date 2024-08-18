import pygame
import math


from enemy_info import ENEMY_ACCELERATION, ENEMY_SHOOT_RANGE, BULLET_SPEED, ROCKET_ACCELERATION


import numpy as np


class Bullet:
    def __init__(self, x, y, angle, ship):
        self.pos = [x, y]
        bullet_speed = BULLET_SPEED + math.sqrt(ship.speed[0]**2 + ship.speed[1]**2)
        self.speed = [
            bullet_speed * math.cos(angle) + ship.speed[0]+ ship.speed[0],
            bullet_speed * math.sin(angle) + ship.speed[1]+ ship.speed[1]
        ]
    def update(self):
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]

    def draw(self, screen, camera_x, camera_y):
        pygame.draw.circle(screen, (255, 255, 0), 
                           (int(self.pos[0] - camera_x), int(self.pos[1] - camera_y)), 
                           3) 


