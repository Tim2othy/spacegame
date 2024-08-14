import pygame
import sys
import math

# region --- basics, screen, world ---

# Initialize Pygame
pygame.init()

# Set up the display
SCREEN_WIDTH, SCREEN_HEIGHT = 1700, 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Game")

# World size
WORLD_WIDTH, WORLD_HEIGHT = 8000, 8000

# define distance
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

# endregion

# region --- grid ---

GRID_SIZE = 300  # Size of each grid cell
GRID_COLOR = (0, 100, 0)  # Dark green color for the grid

def draw_grid(screen, camera_x, camera_y):
    # Vertical lines
    for x in range(0, WORLD_WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GRID_COLOR, 
                         (x - camera_x, 0), 
                         (x - camera_x, SCREEN_HEIGHT))
    
    # Horizontal lines
    for y in range(0, WORLD_HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GRID_COLOR, 
                         (0, y - camera_y), 
                         (SCREEN_WIDTH, y - camera_y))

# endregion

# region --- Ship properties ---
# basic properties
ship_pos = [1700, 3000] 
ship_angle = 0
ship_speed = [0, 0]
ship_radius = 10
thrust = 0.05
drag = 1
rotation_thrust = 0.9
rotation_fuel_consumption_rate = 0.02

# Ship health
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

# endregion

# region --- Space gun ---

# Space Gun
class SpaceGun:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.size = 50
        self.color = (150, 150, 150)
        self.last_shot_time = 0
        self.shoot_interval = 400
        self.bullets = []

    def draw(self, screen, camera_x, camera_y):
        pygame.draw.rect(screen, self.color, 
                         (int(self.pos[0] - camera_x), int(self.pos[1] - camera_y), 
                          self.size, self.size))

    def shoot(self, target_pos):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > self.shoot_interval:
            direction = [target_pos[0] - self.pos[0], target_pos[1] - self.pos[1]]
            length = math.sqrt(direction[0]**2 + direction[1]**2)
            if length > 0:
                direction = [direction[0] / length, direction[1] / length]
            
            self.bullets.append({
                'pos': self.pos.copy(),
                'direction': direction,
                'speed': 7,
                'creation_time': current_time
            })
            self.last_shot_time = current_time

    def update_bullets(self, ship_pos, ship_radius):
        current_time = pygame.time.get_ticks()
        for bullet in self.bullets[:]:
            bullet['pos'][0] += bullet['direction'][0] * bullet['speed']
            bullet['pos'][1] += bullet['direction'][1] * bullet['speed']
            
            if current_time - bullet['creation_time'] > 20000:  # 20 seconds
                self.bullets.remove(bullet)
            elif distance(bullet['pos'], ship_pos) < ship_radius:
                self.bullets.remove(bullet)
                return True  # Collision detected
        return False

    def draw_bullets(self, screen, camera_x, camera_y):
        for bullet in self.bullets:
            pygame.draw.circle(screen, (255, 0, 0), 
                               (int(bullet['pos'][0] - camera_x), int(bullet['pos'][1] - camera_y)), 
                               5)

# Create space gun
space_gun1 = SpaceGun(3000, 5000)
space_gun2 = SpaceGun(5000, 3000)


# endregion

# region --- Planets and squares---

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

    def check_collision(self, ship_pos, ship_radius):
        return distance(ship_pos, self.pos) < self.radius + ship_radius

class Square:
    def __init__(self, x, y, size, color, action):
        self.pos = [x, y]
        self.size = size
        self.color = color
        self.action = action

    def draw(self, screen, camera_x, camera_y):
        if (0 <= self.pos[0] - camera_x < SCREEN_WIDTH and 
            0 <= self.pos[1] - camera_y < SCREEN_HEIGHT):
            pygame.draw.rect(screen, self.color, 
                             (int(self.pos[0] - camera_x), int(self.pos[1] - camera_y), 
                              self.size, self.size))

    def check_collision(self, ship_pos, ship_radius):
        return (self.pos[0] - ship_radius < ship_pos[0] < self.pos[0] + self.size + ship_radius and
                self.pos[1] - ship_radius < ship_pos[1] < self.pos[1] + self.size + ship_radius)

# Create planets (increased size)
planets = [
    Planet(0, 0, 3000, (255, 0, 0)),   # Top-left
    Planet(7000, 1000, 1000, (0, 255, 0)),  # Top-right
    Planet(1000, 7000, 1500, (0, 0, 255)),    # Bottom-left
    Planet(7000, 7000, 500, (255, 255, 0))  # Bottom-right
]

# Create squares
squares = [
    Square(5000, 1000, 100, (0, 255, 255), "refuel"),  # Top-right, refuel
    Square(5000, 5000, 100, (255, 0, 255), "get_item"),  # bottom-right, get item
    Square(1000, 5000, 50, (255, 165, 0), "complete_mission")  # bottom-left, complete mission
]

# endregion

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:

        # region --- Handle input ---
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

        # endregion

        # Ensure fuel doesn't go below 0
        fuel = max(0, fuel)

        # Update ship position
        new_ship_pos = [
            ship_pos[0] + ship_speed[0],
            ship_pos[1] + ship_speed[1]
        ]


        ship_screen_pos = (int(ship_pos[0] - camera_x), int(ship_pos[1] - camera_y))

        # region --- collisions ---

        # Check for collisions with planets
        collision = False
        current_time = pygame.time.get_ticks()
        for planet in planets:
            if planet.check_collision(new_ship_pos, ship_radius):
                collision = True
                ship_color = (255, 0, 0)  # Red
                if collision_time == 0:
                    collision_time = current_time
                # Reduce health when colliding with a planet
                ship_health -= 10 * (current_time - collision_time) / 1000
                break

        if not collision:
            ship_pos = new_ship_pos
            collision_time = 0
        else:
            collision_time = current_time

        # Check for collisions with squares
        for square in squares:
            if square.check_collision(ship_pos, ship_radius):
                if square.action == "refuel":
                    fuel = MAX_FUEL
                elif square.action == "get_item":
                    has_item = True
                elif square.action == "complete_mission" and has_item:
                    mission_complete = True
                    ship_color = (255, 255, 0)  # Yellow

        # endregion

        # Reset ship color after 1 second if it's red
        if ship_color == (255, 0, 0) and pygame.time.get_ticks() - collision_time > 1000:
            ship_color = (255, 255, 255)  # White

        # Apply drag
        ship_speed[0] *= drag
        ship_speed[1] *= drag

       # region --- world border, camera ---

        # Clamp the ship's x position
        if ship_pos[0] < 0:
            ship_pos[0] = 0
        elif ship_pos[0] > WORLD_WIDTH:
            ship_pos[0] = WORLD_WIDTH

        # Clamp the ship's y position
        if ship_pos[1] < 0:
            ship_pos[1] = 0
        elif ship_pos[1] > WORLD_HEIGHT:
            ship_pos[1] = WORLD_HEIGHT


        # Update camera position
        camera_x = ship_pos[0] - SCREEN_WIDTH // 2
        camera_y = ship_pos[1] - SCREEN_HEIGHT // 2

        # Clamp camera position to world boundaries
        camera_x = max(0, min(camera_x, WORLD_WIDTH - SCREEN_WIDTH))
        camera_y = max(0, min(camera_y, WORLD_HEIGHT - SCREEN_HEIGHT))

        # endregion



        # region --- spacegun ---

        # Space gun shooting
        space_gun1.shoot(ship_pos)
        if space_gun1.update_bullets(ship_pos, ship_radius):
            ship_health -= 15


         # Space gun shooting
        space_gun2.shoot(ship_pos)
        if space_gun2.update_bullets(ship_pos, ship_radius):
            ship_health -= 15


        # endregion

        

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


        # region --- drawing ---


        # Draw everything
        screen.fill((0, 0, 0))

        draw_grid(screen, camera_x, camera_y)

        # Draw planets
        for planet in planets:
            planet.draw(screen, camera_x, camera_y)

        # Draw squares
        for square in squares:
            square.draw(screen, camera_x, camera_y)

        # Draw space guns
        space_gun1.draw(screen, camera_x, camera_y)
        space_gun1.draw_bullets(screen, camera_x, camera_y)
        
        space_gun2.draw(screen, camera_x, camera_y)
        space_gun2.draw_bullets(screen, camera_x, camera_y)

        # Draw ship
        
        # Draw the main ship body (white circle)
        pygame.draw.circle(screen, ship_color, ship_screen_pos, ship_radius)

        # Draw thrusters
        draw_thruster(front_thruster_pos, front_thruster_on)
        draw_thruster(rear_thruster_pos, rear_thruster_on)
        draw_rotation_thruster(left_rotation_thruster_pos, left_rotation_thruster_on, True)
        draw_rotation_thruster(right_rotation_thruster_pos, right_rotation_thruster_on, False)

        # endregion



        # region --- displaying ---
        
        # Display ship coordinates
        font = pygame.font.Font(None, 22)
        coord_text = font.render(f"X: {int(ship_pos[0])}, Y: {int(ship_pos[1])}", True, (255, 255, 255))
        screen.blit(coord_text, (10, 10))

        # Display fuel
        fuel_text = font.render(f"Fuel: {fuel:.3f}", True, (255, 255, 255))
        screen.blit(fuel_text, (10, 50))

        # Display item status
        item_text = font.render("Item: Collected" if has_item else "Item: Not Collected", True, (255, 255, 255))
        screen.blit(item_text, (10, 90))

        # Display mission status
        mission_text = font.render("Mission Complete!" if mission_complete else "Mission: In Progress", True, (255, 255, 255))
        screen.blit(mission_text, (10, 130))

        # Display ship health
        health_text = font.render(f"Health: {int(ship_health)}", True, (255, 255, 255))
        screen.blit(health_text, (10, 170))


        # endregion

        # Check if ship health reaches 0
        if ship_health <= 0:
            game_over = True

    else:
        # Game over screen
        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 64)
        game_over_text = font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                                     SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2))

    pygame.time.Clock().tick(60)  # Limit to 60 FPS

    pygame.display.flip()

# Quit the game
pygame.quit()
sys.exit()