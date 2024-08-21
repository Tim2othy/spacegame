import pygame
from camera import Camera

# TODO: Deprecate this entirely, likely in favour
# of a Game class that has this code as an instance-method
# (not necessarily as its __init__ method)

SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 700
WORLD_WIDTH = 30_000
WORLD_HEIGHT = WORLD_WIDTH


# Set up the display
pygame.display.set_caption("Space Game")

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
camera = Camera(pygame.math.Vector2(0, 0), 1.0, screen)
