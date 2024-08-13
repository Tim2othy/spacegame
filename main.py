import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Set up the display
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spaceship Game")

# World size
WORLD_WIDTH, WORLD_HEIGHT = 3000, 3000

def distance(pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

class Planet:
    def __init__(self, x, y, radius, color):
        self.pos = [x, y]
        self.radius = radius
        self.color = color

    def draw(self, screen, camera_x, camera_y):
        if (0 <= self.pos[0] - camera_x < SCREEN_WIDTH and 
            0 <= self.pos[1] - camera_y < SCREEN_HEIGHT):
            pygame.draw.circle(screen, self.color, 
                               (int(self.pos[0] - camera_x), int(self.pos[1] - camera_y)), 
                               self.radius)

    def check_collision(self, ship_pos, ship_radius):
        return distance(ship_pos, self.pos) < self.radius + ship_radius

# Camera offset
camera_x = 0
camera_y = 0

ship_color = (255, 255, 255)  # White
collision_time = 0

# Ship properties
ship_pos = [WORLD_WIDTH // 2, WORLD_HEIGHT // 2]
ship_angle = 0
ship_speed = [0, 0]
ship_radius = 15
thrust = 0.05
drag = 1
rotation_thrust = 0.1
rotation_fuel_consumption_rate = 0.02

# Thruster states
front_thruster_on = False
rear_thruster_on = False
left_rotation_thruster_on = False
right_rotation_thruster_on = False

# Fuel
fuel = 100
fuel_consumption_rate = 0.04

# Create planets
planets = [
    Planet(100, 2000, 50, (255, 0, 0)),   # Top-left
    Planet(2000, 2000, 50, (0, 255, 0)),  # Top-right
    Planet(100, 100, 50, (0, 0, 255)),    # Bottom-left
    Planet(2000, 100, 50, (255, 255, 0))  # Bottom-right
]

def draw_thruster(pos, is_on):
    color = (0, 0, 255) if is_on else (255, 255, 255)
    thruster_width = 10
    thruster_height = 20
    points = [
        (pos[0] - math.sin(math.radians(ship_angle)) * thruster_width/2,
         pos[1] - math.cos(math.radians(ship_angle)) * thruster_width/2),
        (pos[0] + math.sin(math.radians(ship_angle)) * thruster_width/2,
         pos[1] + math.cos(math.radians(ship_angle)) * thruster_width/2),
        (pos[0] + math.sin(math.radians(ship_angle)) * thruster_width/2 + math.cos(math.radians(ship_angle)) * thruster_height,
         pos[1] + math.cos(math.radians(ship_angle)) * thruster_width/2 - math.sin(math.radians(ship_angle)) * thruster_height),
        (pos[0] - math.sin(math.radians(ship_angle)) * thruster_width/2 + math.cos(math.radians(ship_angle)) * thruster_height,
         pos[1] - math.cos(math.radians(ship_angle)) * thruster_width/2 - math.sin(math.radians(ship_angle)) * thruster_height)
    ]
    pygame.draw.polygon(screen, color, points)

def draw_rotation_thruster(pos, is_on, is_left):
    color = (0, 255, 255) if is_on else (255, 255, 255)  # Cyan when on, white when off
    rotation_thruster_width = 5
    rotation_thruster_height = 10
    angle_offset = 90 if is_left else -90
    thruster_angle = ship_angle + angle_offset
    
    points = [
        (pos[0] - math.sin(math.radians(thruster_angle)) * rotation_thruster_width/2,
         pos[1] - math.cos(math.radians(thruster_angle)) * rotation_thruster_width/2),
        (pos[0] + math.sin(math.radians(thruster_angle)) * rotation_thruster_width/2,
         pos[1] + math.cos(math.radians(thruster_angle)) * rotation_thruster_width/2),
        (pos[0] + math.sin(math.radians(thruster_angle)) * rotation_thruster_width/2 + math.cos(math.radians(thruster_angle)) * rotation_thruster_height,
         pos[1] + math.cos(math.radians(thruster_angle)) * rotation_thruster_width/2 - math.sin(math.radians(thruster_angle)) * rotation_thruster_height),
        (pos[0] - math.sin(math.radians(thruster_angle)) * rotation_thruster_width/2 + math.cos(math.radians(thruster_angle)) * rotation_thruster_height,
         pos[1] - math.cos(math.radians(thruster_angle)) * rotation_thruster_width/2 - math.sin(math.radians(thruster_angle)) * rotation_thruster_height)
    ]
    pygame.draw.polygon(screen, color, points)

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Handle input
    keys = pygame.key.get_pressed()
    left_rotation_thruster_on = False
    right_rotation_thruster_on = False

    if keys[pygame.K_LEFT] and fuel > 0:
        ship_angle += rotation_thrust
        fuel -= rotation_fuel_consumption_rate
        left_rotation_thruster_on = True
    if keys[pygame.K_RIGHT] and fuel > 0:
        ship_angle -= rotation_thrust
        fuel -= rotation_fuel_consumption_rate
        right_rotation_thruster_on = True

    front_thruster_on = False
    rear_thruster_on = False

    if keys[pygame.K_UP] and fuel > 0:
        ship_speed[0] += math.cos(math.radians(ship_angle)) * thrust
        ship_speed[1] -= math.sin(math.radians(ship_angle)) * thrust
        fuel -= fuel_consumption_rate
        rear_thruster_on = True
    if keys[pygame.K_DOWN] and fuel > 0:
        ship_speed[0] -= math.cos(math.radians(ship_angle)) * thrust
        ship_speed[1] += math.sin(math.radians(ship_angle)) * thrust
        fuel -= fuel_consumption_rate
        front_thruster_on = True

    # Ensure fuel doesn't go below 0
    fuel = max(0, fuel)

    # Update ship position
    ship_pos[0] += ship_speed[0]
    ship_pos[1] += ship_speed[1]

    # Check for collisions
    for planet in planets:
        if planet.check_collision(ship_pos, ship_radius):
            ship_color = (255, 0, 0)  # Red
            collision_time = pygame.time.get_ticks()
            break

    # Reset ship color after 1 second
    if ship_color == (255, 0, 0) and pygame.time.get_ticks() - collision_time > 1000:
        ship_color = (255, 255, 255)  # White

    # Apply drag
    ship_speed[0] *= drag
    ship_speed[1] *= drag

    # Wrap around world
    ship_pos[0] %= WORLD_WIDTH
    ship_pos[1] %= WORLD_HEIGHT

    # Update camera position
    camera_x = ship_pos[0] - SCREEN_WIDTH // 2
    camera_y = ship_pos[1] - SCREEN_HEIGHT // 2

    # Clamp camera position to world boundaries
    camera_x = max(0, min(camera_x, WORLD_WIDTH - SCREEN_WIDTH))
    camera_y = max(0, min(camera_y, WORLD_HEIGHT - SCREEN_HEIGHT))

    # Draw everything
    screen.fill((0, 0, 0))

    # Draw planets
    for planet in planets:
        planet.draw(screen, camera_x, camera_y)

    # Draw ship
    ship_screen_pos = (int(ship_pos[0] - camera_x), int(ship_pos[1] - camera_y))
    # Draw the main ship body (white circle)
    pygame.draw.circle(screen, ship_color, ship_screen_pos, ship_radius)

    # Calculate thruster positions and sizes
    front_thruster_pos = (
        int(ship_screen_pos[0] + math.cos(math.radians(ship_angle)) * ship_radius),
        int(ship_screen_pos[1] - math.sin(math.radians(ship_angle)) * ship_radius)
    )
    rear_thruster_pos = (
        int(ship_screen_pos[0] - math.cos(math.radians(ship_angle)) * ship_radius),
        int(ship_screen_pos[1] + math.sin(math.radians(ship_angle)) * ship_radius)
    )

    # Calculate rotation thruster positions
    left_rotation_thruster_pos = (
        int(ship_screen_pos[0] + math.cos(math.radians(ship_angle + 90)) * ship_radius),
        int(ship_screen_pos[1] - math.sin(math.radians(ship_angle + 90)) * ship_radius)
    )
    right_rotation_thruster_pos = (
        int(ship_screen_pos[0] + math.cos(math.radians(ship_angle - 90)) * ship_radius),
        int(ship_screen_pos[1] - math.sin(math.radians(ship_angle - 90)) * ship_radius)
    )

    # Draw thrusters
    draw_thruster(front_thruster_pos, front_thruster_on)
    draw_thruster(rear_thruster_pos, rear_thruster_on)
    draw_rotation_thruster(left_rotation_thruster_pos, left_rotation_thruster_on, True)
    draw_rotation_thruster(right_rotation_thruster_pos, right_rotation_thruster_on, False)

    # Display ship coordinates
    font = pygame.font.Font(None, 22)
    coord_text = font.render(f"X: {int(ship_pos[0])}, Y: {int(ship_pos[1])}", True, (255, 255, 255))
    screen.blit(coord_text, (10, 10))

    # Display fuel
    fuel_text = font.render(f"Fuel: {fuel:.3f}", True, (255, 255, 255))
    screen.blit(fuel_text, (10, 50))

    pygame.time.Clock().tick(60)  # Limit to 60 FPS

    pygame.display.flip()

# Quit the game
pygame.quit()
sys.exit()