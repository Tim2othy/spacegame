import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from camera import Camera

# TODO: Deprecate this entirely, likely in favour
# of a Game class that has this code as an instance-method
# (not necessarily as its __init__ method)

# Set up the display
pygame.display.set_caption("Space Game")

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
camera = Camera(pygame.math.Vector2(0, 0), 1.0, screen)

collision_time = 0  # TODO: Should be an attribute of some class-instance
