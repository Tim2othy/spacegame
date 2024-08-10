import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Set up the display
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spaceship Game")


# World size
WORLD_WIDTH, WORLD_HEIGHT = 4000, 800  # 3 times wider than the screen

def distance(pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

# Camera offset
camera_x = 0

ship_color = (255, 255, 255)  # White
collision_time = 0



# Ship properties
ship_pos = [WORLD_WIDTH // 2, WORLD_HEIGHT // 2]
ship_angle = 0
ship_speed = [0, 0]
ship_radius = 15
thrust = 0.0007
drag = 1

# Thruster states
front_thruster_on = False
rear_thruster_on = False

# Fuel
fuel = 100
fuel_consumption_rate = 0.007


# Circles at the ends
left_circle_pos = [100, WORLD_HEIGHT // 2]
right_circle_pos = [WORLD_WIDTH - 100, WORLD_HEIGHT // 2]
circle_radius = 50



#game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Handle input
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        ship_angle += 0.3
    if keys[pygame.K_RIGHT]:
        ship_angle -= 0.3

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
    
    

    if (distance(ship_pos, left_circle_pos) < circle_radius + ship_radius or 
        distance(ship_pos, right_circle_pos) < circle_radius + ship_radius):
        ship_color = (255, 0, 0)  # Red
        collision_time = pygame.time.get_ticks()

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
    camera_x = max(0, min(camera_x, WORLD_WIDTH - SCREEN_WIDTH))

    # Draw everything
    screen.fill((0, 0, 0))

    # Draw circles (if in view)
    if 0 <= left_circle_pos[0] - camera_x < SCREEN_WIDTH:
        pygame.draw.circle(screen, (255, 0, 0), 
                           (left_circle_pos[0] - camera_x, left_circle_pos[1]), 
                           circle_radius)
    if 0 <= right_circle_pos[0] - camera_x < SCREEN_WIDTH:
        pygame.draw.circle(screen, (0, 255, 0), 
                           (right_circle_pos[0] - camera_x, right_circle_pos[1]), 
                           circle_radius)

    # Draw ship
    ship_screen_pos = (int(ship_pos[0] - camera_x), int(ship_pos[1]))


    pygame.draw.circle(screen, ship_color, ship_screen_pos, ship_radius)


    # Calculate thruster positions
    front_thruster_pos = (
        int(ship_screen_pos[0] + math.cos(math.radians(ship_angle)) * ship_radius),
        int(ship_screen_pos[1] - math.sin(math.radians(ship_angle)) * ship_radius)
    )
    rear_thruster_pos = (
        int(ship_screen_pos[0] - math.cos(math.radians(ship_angle)) * ship_radius),
        int(ship_screen_pos[1] + math.sin(math.radians(ship_angle)) * ship_radius)
    )

    # Draw thrusters
    thruster_size = 5
    if front_thruster_on:
        pygame.draw.circle(screen, (0, 0, 255), front_thruster_pos, thruster_size)
    if rear_thruster_on:
        pygame.draw.circle(screen, (0, 0, 255), rear_thruster_pos, thruster_size)


    # Draw a line to indicate the ship's facing direction
    direction_end = (
        int(ship_screen_pos[0] + math.cos(math.radians(ship_angle)) * (ship_radius + 10)),
        int(ship_screen_pos[1] - math.sin(math.radians(ship_angle)) * (ship_radius + 10))
    )
    pygame.draw.line(screen, (255, 255, 255), ship_screen_pos, direction_end, 2)


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