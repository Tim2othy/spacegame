import pygame
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, G
from distance import distance

class Planet:
    def __init__(self, x, y, radius, color):
        self.pos = [x, y]
        self.radius = radius
        self.color = color

    def draw(self, screen, camera_x, camera_y):
        if (self.pos[0] - self.radius - camera_x < SCREEN_WIDTH and
            self.pos[0] + self.radius - camera_x > 0 and
            self.pos[1] - self.radius - camera_y < SCREEN_HEIGHT and
            self.pos[1] + self.radius - camera_y > 0):
            pygame.draw.circle(screen, self.color, 
                               (int(self.pos[0] - camera_x), int(self.pos[1] - camera_y)), 
                               self.radius)

    def check_collision(self, ship):
        return distance(ship.pos, self.pos) < self.radius + ship.radius
    

    def calculate_gravity(self, ship):
        dx = self.pos[0] - ship.pos[0]
        dy = self.pos[1] - ship.pos[1]
        distance_squared = dx**2 + dy**2
        force_magnitude = G * (4/3 * 3.13 * self.radius**3) * ship.mass / distance_squared
        
        # Normalize the direction
        distance = math.sqrt(distance_squared)
        force_x = force_magnitude * dx / distance
        force_y = force_magnitude * dy / distance
        
        return force_x, force_y