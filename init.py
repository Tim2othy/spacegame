import pygame


from config import SCREEN_WIDTH, SCREEN_HEIGHT


# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Game")


# Camera offset
camera_x = 0
camera_y = 0

total_force_x = 0
total_force_y = 0
collision_time = 0
