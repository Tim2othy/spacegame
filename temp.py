import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Set up the display
SCREEN_WIDTH, SCREEN_HEIGHT = 1400, 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spaceship Game")

# World size (increased)
WORLD_WIDTH, WORLD_HEIGHT = 8000, 8000

def distance(pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

# Camera offset
camera_x = 0
camera_y = 0

ship_color = (255, 255, 255)  # White
collision_time = 0

# Game state
has_item = False
mission_complete = False
game_over = False

# Ship properties
ship_pos = [700, 700]  # Start next to bottom-left planet
ship_angle = 0
ship_speed = [0, 0]
ship_radius = 15
thrust = 0.05
drag = 1
rotation_thrust = 0.9
rotation_fuel_consumption_rate = 0.02

# New: Ship health
ship_health = 100

# Thruster states
front_thruster_on = False
rear_thruster_on = False
left_rotation_thruster_on = False
right_rotation_thruster_on = False

# Fuel
fuel = 100
fuel_consumption_rate = 0.04
MAX_FUEL = 100

# ... [Rest of the existing functions remain unchanged]

# Create planets (increased size)
planets = [
    Planet(1000, 1000, 500, (255, 0, 0)),   # Top-left
    Planet(7000, 1000, 500, (0, 255, 0)),  # Top-right
    Planet(1000, 7000, 500, (0, 0, 255)),    # Bottom-left
    Planet(7000, 7000, 500, (255, 255, 0))  # Bottom-right
]

# ... [Rest of the existing code remains unchanged]

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        # ... [Existing game logic]

        # Check for collisions with planets
        collision = False
        for planet in planets:
            if planet.check_collision(new_ship_pos, ship_radius):
                collision = True
                ship_color = (255, 0, 0)  # Red
                collision_time = pygame.time.get_ticks()
                # New: Reduce health when colliding with a planet
                ship_health -= 10 * (pygame.time.get_ticks() - collision_time) / 1000
                break

        if not collision:
            ship_pos = new_ship_pos

        # ... [Rest of the existing game logic]

        # New: Check if ship health reaches 0
        if ship_health <= 0:
            game_over = True

        # Draw everything
        screen.fill((0, 0, 0))

        # Draw planets (modified to show even if center is not visible)
        for planet in planets:
            if (planet.pos[0] - planet.radius - camera_x < SCREEN_WIDTH and
                planet.pos[0] + planet.radius - camera_x > 0 and
                planet.pos[1] - planet.radius - camera_y < SCREEN_HEIGHT and
                planet.pos[1] + planet.radius - camera_y > 0):
                planet.draw(screen, camera_x, camera_y)

        # ... [Rest of the drawing code]

        # Display ship health
        health_text = font.render(f"Health: {int(ship_health)}", True, (255, 255, 255))
        screen.blit(health_text, (10, 170))

    else:
        # Game over screen
        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 64)
        game_over_text = font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                                     SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2))

    pygame.display.flip()

# Quit the game
pygame.quit()
sys.exit()