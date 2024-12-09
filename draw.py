import pygame
from pygame.math import Vector2 as Vec2
from pygame import Color


# Boring Stuff
SCREEN_WIDTH = 200
SCREEN_HEIGHT = 200
BACKGROUND_COLOR = (0, 0, 0)
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Missile Polygon")


# Function to draw the missile polygon
def draw_missile(screen, pos):
    forward = Vec2(0, -1)
    left = forward.rotate(90)
    right = forward.rotate(-90)
    backward = forward.rotate(180)

    points1 = [
        (pos + 13 * forward).xy,  # Central point on top
        (pos + 4 * left + 3 * forward).xy,  # Top-left corner
        (pos + 2 * left + 5 * backward).xy,  # Bottom-left corner
        (pos + 2 * right + 5 * backward).xy,  # Bottom-right corner
        (pos + 4 * right + 3 * forward).xy,  # Top-right corner
    ]

    points2 = [
        (pos + 9 * left + 5 * forward).xy,  # Top-left corner
        (pos + 2 * left + 2 * backward).xy,  # Bottom-left corner
        (pos + 7 * backward).xy,  # Bottom point
        (pos + 2 * right + 2 * backward).xy,  # Bottom-right corner
        (pos + 9 * right + 5 * forward).xy,  # Top-right corner
    ]

    pygame.draw.polygon(screen, Color("Orange"), points1)
    pygame.draw.polygon(screen, Color("Gray"), points2)


# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BACKGROUND_COLOR)

    # Draw the missile polygon
    missile_pos = Vec2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    draw_missile(screen, missile_pos)

    pygame.display.flip()

pygame.quit()
