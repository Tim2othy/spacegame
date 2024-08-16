import pygame
import sys
import math
import random
import time
from math import atan2, cos, sin, sqrt
sign = lambda x: (1 if x > 0 else -1 if x < 0 else 0)




# config
SCREEN_WIDTH = 1700
SCREEN_HEIGHT = 900
WORLD_WIDTH = 10000
WORLD_HEIGHT = 10000
GRID_SIZE = 300
GRID_COLOR = (0, 70, 0)


def vec_add(v1, v2):
    return [v1[0] + v2[0], v1[1] + v2[1]]

def vec_scale(v, scalar):
    return [v[0] * scalar, v[1] * scalar]

def vec_length(v):
    return math.sqrt(v[0]**2 + v[1]**2)




# region --- basics, screen, world ---

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Game")



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

G = (0.0006)  # Gravitational constant

def calculate_gravity(pos, mass, planets):
    total_force_x, total_force_y = 0, 0
    for planet in planets:
        dx = planet.pos[0] - pos[0]
        dy = planet.pos[1] - pos[1]
        distance_squared = dx**2 + dy**2
        force_magnitude = G * (4/3 * 3.14 * planet.radius**3) * mass / distance_squared
        distance = math.sqrt(distance_squared)
        total_force_x += force_magnitude * dx / distance
        total_force_y += force_magnitude * dy / distance
    return total_force_x, total_force_y


# endregion





# region --- Ship properties ---


class Ship:
    def __init__(self, x, y):
        self.angle = 0
        self.speed = [0, 0]
        self.radius = 9
        self.mass = 1000
        self.health = 100
        self.REPAIR_RATE = 0.1
        self.MAX_health = 200
        self.bullets = []
        self.gun_cooldown = 0
        self.pos = [x, y]

        self.ammo = 250
        self.thrust = 0.19
        self.rotation_thrust = 3
        self.left_rotation_thruster_on = False
        self.right_rotation_thruster_on = False
        self.fuel = 100
        self.fuel_consumption_rate = 0.07
        self.rotation_fuel_consumption_rate = 0.03
        self.MAX_FUEL = 100

    def rotate_left(self):
        if self.fuel > 0:
            self.angle += self.rotation_thrust
            self.fuel -= self.rotation_fuel_consumption_rate
            self.left_rotation_thruster_on = True
        else:
            self.left_rotation_thruster_on = False

    def rotate_right(self):
        if self.fuel > 0:
            self.angle -= self.rotation_thrust
            self.fuel -= self.rotation_fuel_consumption_rate
            self.right_rotation_thruster_on = True
        else:
            self.right_rotation_thruster_on = False

    def reset_rotation_thrusters(self):
        self.left_rotation_thruster_on = False
        self.right_rotation_thruster_on = False

    def forward(self):
        if self.fuel > 0:
            self.speed[0] += math.cos(math.radians(self.angle)) * self.thrust
            self.speed[1] -= math.sin(math.radians(self.angle)) * self.thrust
            self.fuel -= self.fuel_consumption_rate

    def backward(self):
        if self.fuel > 0:
            self.speed[0] -= math.cos(math.radians(self.angle)) * self.thrust
            self.speed[1] += math.sin(math.radians(self.angle)) * self.thrust
            self.fuel -= self.fuel_consumption_rate

    def shoot(self):
        if self.gun_cooldown <= 0 and self.ammo > 0:
            angle = math.radians(-self.angle)
            bullet_x = self.pos[0] + math.cos(-angle) * (self.radius + 20)
            bullet_y = self.pos[1] - math.sin(-angle) * (self.radius + 20)
            self.bullets.append(Bullet(bullet_x, bullet_y, angle, self.speed))
            self.gun_cooldown = 4
            self.ammo -= 1

    def update(self):
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]

        self.gun_cooldown = max(0, self.gun_cooldown - 1)
        self.fuel = max(0, self.fuel)

    def draw(self, screen, camera_x, camera_y):
        ship_screen_pos = (int(self.pos[0] - camera_x), int(self.pos[1] - camera_y))
        pygame.draw.circle(screen, (255, 255, 255), ship_screen_pos, self.radius)
        
        # Draw gun
        gun_length = 25
        gun_end_x = ship_screen_pos[0] + math.cos(math.radians(self.angle)) * (self.radius + gun_length)
        gun_end_y = ship_screen_pos[1] - math.sin(math.radians(self.angle)) * (self.radius + gun_length)
        pygame.draw.line(screen, (200, 200, 200), ship_screen_pos, (gun_end_x, gun_end_y), 6)

        # Draw thrusters
        self.draw_thruster(screen, ship_screen_pos, True)
        self.draw_thruster(screen, ship_screen_pos, False)
        self.draw_rotation_thruster(screen, ship_screen_pos, True)
        self.draw_rotation_thruster(screen, ship_screen_pos, False)

    def draw_thruster(self, screen, ship_screen_pos, is_front):
        angle_offset = 0 if is_front else 180
        thruster_pos = (
            int(ship_screen_pos[0] + math.cos(math.radians(self.angle + angle_offset)) * self.radius),
            int(ship_screen_pos[1] - math.sin(math.radians(self.angle + angle_offset)) * self.radius)
        )
        color = (0, 0, 255) if (is_front and self.speed[0] > 0) or (not is_front and self.speed[0] < 0) else (255, 255, 255)
        self.draw_thruster_shape(screen, thruster_pos, color, self.angle + angle_offset)

    def draw_rotation_thruster(self, screen, ship_screen_pos, is_left):
        angle_offset = 90 if is_left else -90
        thruster_pos = (
            int(ship_screen_pos[0] + math.cos(math.radians(self.angle + angle_offset)) * self.radius),
            int(ship_screen_pos[1] - math.sin(math.radians(self.angle + angle_offset)) * self.radius)
        )
        color = (0, 255, 255) if (is_left and self.left_rotation_thruster_on) or (not is_left and self.right_rotation_thruster_on) else (255, 255, 255)
        self.draw_thruster_shape(screen, thruster_pos, color, self.angle + angle_offset)

    def draw_thruster_shape(self, screen, pos, color, angle):
        thruster_width = 5
        thruster_height = 10
        points = [
            (pos[0] - math.sin(math.radians(angle)) * thruster_width/2,
             pos[1] - math.cos(math.radians(angle)) * thruster_width/2),
            (pos[0] + math.sin(math.radians(angle)) * thruster_width/2,
             pos[1] + math.cos(math.radians(angle)) * thruster_width/2),
            (pos[0] + math.sin(math.radians(angle)) * thruster_width/2 + math.cos(math.radians(angle)) * thruster_height,
             pos[1] + math.cos(math.radians(angle)) * thruster_width/2 - math.sin(math.radians(angle)) * thruster_height),
            (pos[0] - math.sin(math.radians(angle)) * thruster_width/2 + math.cos(math.radians(angle)) * thruster_height,
             pos[1] - math.cos(math.radians(angle)) * thruster_width/2 - math.sin(math.radians(angle)) * thruster_height)
        ]
        pygame.draw.polygon(screen, color, points)


ship = Ship(3000, 3000)



# Thruster states
front_thruster_on = False
rear_thruster_on = False
left_rotation_thruster_on = False
right_rotation_thruster_on = False


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

    def check_collision(self, ship):
        return (self.pos[0] - ship.radius < ship.pos[0] < self.pos[0] + self.size + ship.radius and
                self.pos[1] - ship.radius < ship.pos[1] < self.pos[1] + self.size + ship.radius)

# Create planets (increased size)


planets = [
    Planet(2100, 6800, 450, (0, 255, 0)),  
    Planet(3500, 1600, 250, (0, 0, 255)),
    Planet(5000, 3700, 280, (255, 255, 0)),
    Planet(6000, 8000, 380, (255, 100, 255)),
    Planet(7000, 2400, 400, (50, 20, 200)),
    Planet(7800, 5000, 350, (50, 140, 100))
]

# Create squares

pos_refuel = (5000, 1000)
pos_item = (5000, 5000)
pos_complete = (1000, 5000)

squares = [
    Square(pos_refuel[0], pos_refuel[1], 1000, (0, 255, 255), "refuel"),  # Top-right, refuel
    Square(pos_item[0], pos_item[1], 1000, (255, 0, 255), "get_item"),  # bottom-right, get item
    Square(pos_complete[0], pos_complete[1], 1000, (255, 165, 0), "complete_mission")  # bottom-left, complete mission
]

def bounce_from_planet(planet):
    # Calculate normal vector
    nx = ship.pos[0] - planet.pos[0]
    ny = ship.pos[1] - planet.pos[1]
    norm = math.sqrt(nx*nx + ny*ny)
    nx /= norm
    ny /= norm

    # Calculate relative velocity
    rv_x = ship.speed[0]
    rv_y = ship.speed[1]

    # Calculate velocity component along normal
    vel_along_normal = rv_x * nx + rv_y * ny

    # Do not resolve if velocities are separating
    if vel_along_normal > 0:
        return

    # Calculate restitution (bounciness)
    restitution = 1

    # Calculate impulse scalar
    j = -(1 + restitution) * vel_along_normal
    j /= 1/ship.mass + 1/(4/3 * math.pi * planet.radius**3)

    # Apply impulse
    ship.speed[0] += j * nx / ship.mass
    ship.speed[1] += j * ny / ship.mass

    # Move ship outside planet
    overlap = ship.radius + planet.radius - distance(ship.pos, planet.pos)
    ship.pos[0] += overlap * nx
    ship.pos[1] += overlap * ny




# endregion




# region --- asteroids

class Asteroid:
    def __init__(self, x, y, radius):
        self.pos = [x, y]
        self.radius = radius
        self.color = (100, 100, 100)  # Grey color
        self.speed = [random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)]
        self.mass = 4/3 * math.pi * self.radius**3  # Assuming density of 1

    def draw(self, screen, camera_x, camera_y):
        if (self.pos[0] - self.radius - camera_x < SCREEN_WIDTH and
            self.pos[0] + self.radius - camera_x > 0 and
            self.pos[1] - self.radius - camera_y < SCREEN_HEIGHT and
            self.pos[1] + self.radius - camera_y > 0):
            pygame.draw.circle(screen, self.color, 
                               (int(self.pos[0] - camera_x), int(self.pos[1] - camera_y)), 
                               self.radius)

    def update(self, planets):
        # Update position based on speed
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]



        # Stop at world border
        if self.pos[0] - self.radius < 0:
            self.pos[0] = self.radius
            self.speed[0] = 0
        elif self.pos[0] + self.radius > WORLD_WIDTH:
            self.pos[0] = WORLD_WIDTH - self.radius
            self.speed[0] = 0
        if self.pos[1] - self.radius < 0:
            self.pos[1] = self.radius
            self.speed[1] = 0
        elif self.pos[1] + self.radius > WORLD_HEIGHT:
            self.pos[1] = WORLD_HEIGHT - self.radius
            self.speed[1] = 0


        # Apply gravity from planets
        for planet in planets:
            planet.draw(screen, camera_x, camera_y)
            force_x, force_y = planet.calculate_gravity(self.pos, self.mass)
            self.speed[0] += force_x / self.mass
            self.speed[1] += force_y / self.mass

    def check_collision(self, other):
        if isinstance(other, Asteroid) or isinstance(other, Planet):
            return distance(self.pos, other.pos) < self.radius + other.radius
        elif isinstance(other, tuple) or isinstance(other, list):  # For ship position
            return distance(self.pos, other) < self.radius + ship.radius

    def bounce(self, other):
        # Calculate normal vector
        nx = self.pos[0] - other.pos[0]
        ny = self.pos[1] - other.pos[1]
        norm = math.sqrt(nx*nx + ny*ny)
        nx /= norm + 0.0003456
        ny /= norm + 0.0003456

        # Calculate relative velocity
        rv_x = self.speed[0]
        rv_y = self.speed[1]

        # Calculate velocity component along normal
        vel_along_normal = rv_x * nx + rv_y * ny

        # Do not resolve if velocities are separating
        if vel_along_normal > 0:
            return

        # Calculate restitution (bounciness)
        restitution = 1

        # Calculate impulse scalar
        j = -(1 + restitution) * vel_along_normal
        j /= 1/self.mass + 1/(4/3 * math.pi * other.radius**3)

        # Apply impulse
        self.speed[0] += j * nx / self.mass
        self.speed[1] += j * ny / self.mass

        # Move asteroid outside other object
        overlap = self.radius + other.radius - distance(self.pos, other.pos)
        self.pos[0] += overlap * nx
        self.pos[1] += overlap * ny
    
    

# Generate asteroids
asteroids = []
for _ in range(20):  # Adjust the number of asteroids as needed
    x = random.randint(0, WORLD_WIDTH)
    y = random.randint(0, WORLD_HEIGHT)
    radius = random.randint(15, 80)
    asteroids.append(Asteroid(x, y, radius))

# endregion




# region --- Space gun ---

# Space Gun
class SpaceGun:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.size = 40
        self.color = (150, 150, 150)
        self.last_shot_time = 0
        self.shoot_interval = 1200
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
                'speed': 10,
                'creation_time': current_time
            })
            self.last_shot_time = current_time

    def update_bullets(self, ship):
        current_time = pygame.time.get_ticks()
        for bullet in self.bullets[:]:
            bullet['pos'][0] += bullet['direction'][0] * bullet['speed']
            bullet['pos'][1] += bullet['direction'][1] * bullet['speed']
            
            if current_time - bullet['creation_time'] > 60*9:
                self.bullets.remove(bullet)
            elif distance(bullet['pos'], ship.pos) < ship.radius:
                self.bullets.remove(bullet)
                return True  # Collision detected
        return False

    def draw_bullets(self, screen, camera_x, camera_y):
        for bullet in self.bullets:
            pygame.draw.circle(screen, (255, 0, 0), 
                               (int(bullet['pos'][0] - camera_x), int(bullet['pos'][1] - camera_y)), 
                               5)

# Create space gun

# endregion




# region --- enemy ships ---

BULLET_SPEED = 4
ENEMY_SHOOT_RANGE = 900
ENEMY_ACCELERATION = 0.6
ENEMY_SHOOT_COOLDOWN = 50  # Adjust this value as needed
ROCKET_ACCELERATION = 0.04  # Acceleration applied during the 1-second acceleration phase

# Define cooldown values
ROCKET_SHOOT_COOLDOWN = 2
BULLET_SHOOT_COOLDOWN = 0.5


# New classes for enemies and projectiles



class Enemy:
    def __init__(self, x, y, enemy_type, health=100):
        self.pos = [x, y]
        self.speed = [0, 0]
        self.radius = 15
        self.type = enemy_type  # 'bullet' or 'rocket'
        self.color = (155, 77, 166) if enemy_type == 'bullet' else (255, 165, 0)
        self.shoot_cooldown = 0
        self.current_action = 6
        self.action_timer = 0
        self.random_direction = None
        self.orbit_angle = 0
        self.difficulty = 1.0
        self.rand_speed = [0, 0]
        self.health = health

    def update(self, ship, planets, other_enemies):
        dx = ship.pos[0] - self.pos[0]
        dy = ship.pos[1] - self.pos[1]
        dist = sqrt(dx**2 + dy**2)

        # Apply gravitational forces
        force_x, force_y = calculate_gravity(self.pos, 100, planets)  # Assume enemy mass is 100
        self.speed[0] += force_x / 100
        self.speed[1] += force_y / 100
        self.check_planet_collision(planets)


        # Check if the 4-second period has elapsed
        if self.action_timer <= 0:
            self.choose_action(ship.pos, other_enemies)
            self.action_timer = 4 * 60  # Reset timer to 4 seconds (240 frames)


        # Execute current action
        if self.current_action == 1:  # Accelerate towards player
            self.speed = vec_add(self.speed, vec_scale([dx/dist, dy/dist], ENEMY_ACCELERATION * self.difficulty))
        
        elif self.current_action == 2:  # Accelerate randomly
            if not self.random_direction:
                angle = random.uniform(0, 2 * math.pi)
                self.random_direction = [math.cos(angle), math.sin(angle)]
            self.speed = vec_add(self.speed, vec_scale(self.random_direction, ENEMY_ACCELERATION * self.difficulty))
        
        elif self.current_action == 3:  # Decelerate
            self.speed = vec_add(self.speed, vec_scale([math.copysign(1, self.speed[0]), math.copysign(1, self.speed[1])], -ENEMY_ACCELERATION * 0.2 * self.difficulty))
        
        elif self.current_action == 4:  # Orbit player
            self.orbit_player(ship)
        
        elif self.current_action == 5:  # Evasive maneuvers
            self.evade(ship)
        
        elif self.current_action == 6:  # Formation flying
            self.fly_formation(other_enemies)

        elif self.current_action == 7:  # Accelerate randomly
            self.rand_speed[0] = self.rand_speed[0] + random.uniform(-1, 1)
            self.rand_speed[1] = self.rand_speed[1] + random.uniform(-1, 1)
            
            self.speed[0] += self.rand_speed[0] * ENEMY_ACCELERATION*0.2
            self.speed[1] += self.rand_speed[1] * ENEMY_ACCELERATION*0.2
            
        elif self.current_action == 8:  # Decelerate
            self.speed[0] -= sign(self.speed[0]) * ENEMY_ACCELERATION*0.2
            self.speed[1] -= sign(self.speed[1]) * ENEMY_ACCELERATION*0.2



        
        # Update position
        self.pos = vec_add(self.pos, self.speed)

        self.action_timer -= 1


        # Check collision with player bullets
        for bullet in ship.bullets[:]:
            if distance(enemy.pos, bullet.pos) < enemy.radius + 3:
                self.health -= 10
                ship.bullets.remove(bullet)

            return []

        # Shooting logic
        if dist < ENEMY_SHOOT_RANGE and self.shoot_cooldown <= 0:
            if self.type == 'bullet':
                self.shoot_cooldown = BULLET_SHOOT_COOLDOWN  # Set cooldown for bullet enemy
                return [Bullet(self.pos[0], self.pos[1], atan2(dy, dx), self.speed)]
            else:
                self.shoot_cooldown = ROCKET_SHOOT_COOLDOWN  # Set cooldown for rocket enemy
                return [Rocket(self.pos[0], self.pos[1], ship.pos)]
        self.shoot_cooldown = max(0, self.shoot_cooldown - 1)
        return []

    def generate_random_speed(self):
        self.rand_speed = [random.uniform(-1, 1), random.uniform(-1, 1)]


    def choose_action(self, ship, other_enemies):
        # Implement a more sophisticated action selection here
        # This could include checking distances, player's weapon status, etc.
        self.current_action = random.randint(1, 8)
        self.random_direction = None  # Reset random direction when changing actions

    def orbit_player(self, ship):
        orbit_distance = 200  # Adjust as needed
        self.orbit_angle += 0.02  # Adjust for orbit speed
        target_x = ship.pos[0] + math.cos(self.orbit_angle) * orbit_distance
        target_y = ship.pos[1] + math.sin(self.orbit_angle) * orbit_distance
        dx = target_x - self.pos[0]
        dy = target_y - self.pos[1]
        dist = math.sqrt(dx**2 + dy**2)
        self.speed = vec_add(self.speed, vec_scale([dx/dist, dy/dist], ENEMY_ACCELERATION * self.difficulty))

    def evade(self, ship):
        dx = self.pos[0] - ship.pos[0]
        dy = self.pos[1] - ship.pos[1]
        dist = math.sqrt(dx**2 + dy**2)
        self.speed = vec_add(self.speed, vec_scale([dx/dist, dy/dist], ENEMY_ACCELERATION * 1.5 * self.difficulty))

    def draw(self, screen, camera_x, camera_y):
        pygame.draw.circle(screen, self.color, 
                           (int(self.pos[0] - camera_x), int(self.pos[1] - camera_y)), 
                           self.radius)
    
    def fly_formation(self, other_enemies):
        if not other_enemies:
            return
        # Simple V formation
        leader = other_enemies[0]
        index = other_enemies.index(self)
        offset = 50 * (index + 1)
        target_x = leader.pos[0] - offset
        target_y = leader.pos[1] + offset
        dx = target_x - self.pos[0]
        dy = target_y - self.pos[1]
        dist = math.sqrt(dx**2 + dy**2)
        self.speed = vec_add(self.speed, vec_scale([dx/dist, dy/dist], ENEMY_ACCELERATION * self.difficulty))


    def bounce(self, other):
        # Calculate normal vector
        nx = self.pos[0] - other.pos[0]
        ny = self.pos[1] - other.pos[1]
        norm = math.sqrt(nx*nx + ny*ny)
        nx /= norm
        ny /= norm

        # Calculate relative velocity
        rv_x = self.speed[0]
        rv_y = self.speed[1]

        # Calculate velocity component along normal
        vel_along_normal = rv_x * nx + rv_y * ny

        # Do not resolve if velocities are separating
        if vel_along_normal > 0:
            return

        # Calculate restitution (bounciness)
        restitution = 1

        # Calculate impulse scalar
        j = -(1 + restitution) * vel_along_normal
        j /= 1/100 + 1/(4/3 * math.pi * other.radius**3)  # Assume enemy mass is 100

        # Apply impulse
        self.speed[0] += j * nx / 100
        self.speed[1] += j * ny / 100

        # Move enemy outside other object
        overlap = self.radius + other.radius - distance(self.pos, other.pos)
        self.pos[0] += overlap * nx
        self.pos[1] += overlap * ny



    def check_planet_collision(self, planets):
        for planet in planets:
            if distance(self.pos, planet.pos) < self.radius + planet.radius:
                # Calculate normal vector
                nx = self.pos[0] - planet.pos[0]
                ny = self.pos[1] - planet.pos[1]
                norm = math.sqrt(nx*nx + ny*ny)
                nx /= norm
                ny /= norm

                # Calculate relative velocity
                rv_x = self.speed[0]
                rv_y = self.speed[1]
            
                # Calculate velocity component along normal
                vel_along_normal = rv_x * nx + rv_y * ny
            
                # Do not resolve if velocities are separating
                if vel_along_normal > 0:
                    return
            
                # Calculate restitution (bounciness)
                restitution = 1
            
                # Calculate impulse scalar
                j = -(1 + restitution) * vel_along_normal
                j /= 1/100 + 1/(4/3 * 3.14 * planet.radius**3)  # Assume enemy mass is 100
            
                # Apply impulse
                self.speed[0] += j * nx / 100
                self.speed[1] += j * ny / 100
            
                # Move enemy outside planet
                overlap = self.radius + planet.radius - distance(self.pos, planet.pos)
                self.pos[0] += overlap * nx
                self.pos[1] += overlap * ny


''''''

class Bullet:
    def __init__(self, x, y, angle, ship):
        self.pos = [x, y]
        bullet_speed = BULLET_SPEED + math.sqrt(ship.speed[0]**2 + ship.speed[1]**2)
        self.speed = [bullet_speed * math.cos(angle) + ship.speed[0], 
                      bullet_speed * math.sin(angle) + ship.speed[1]]

    def update(self):
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]

    def draw(self, screen, camera_x, camera_y):
        pygame.draw.circle(screen, (255, 255, 0), 
                           (int(self.pos[0] - camera_x), int(self.pos[1] - camera_y)), 
                           3) 


def check_bullet_planet_collision(bullet, planets):
    for planet in planets:
        if distance(bullet.pos, planet.pos) < planet.radius:
            return True
    return False


class Rocket:
    def __init__(self, x, y, target_pos):
        self.pos = [x, y]
        self.target_pos = target_pos
        self.speed = [0, 0]  # Initial speed is zero
        self.last_acceleration_time = time.time()
        self.accelerating = True
        self.color = (255, 0, 0)

    def update(self, ship):
        current_time = time.time()
        time_since_last_acceleration = current_time - self.last_acceleration_time

        if self.accelerating:
            self.color = (255, 0, 200)  # Red while accelerating
        else:
            self.color = (255, 100, 0)  # Orange while not accelerating
        
        # Check if it's time to start accelerating
        if not self.accelerating and time_since_last_acceleration >= 9:
            self.accelerating = True
            self.last_acceleration_time = current_time
        
        # Check if the acceleration period should end
        elif self.accelerating and time_since_last_acceleration >= 3:
            self.accelerating = False
            self.last_acceleration_time = current_time
        
        # Update the target position to the ship's current position
        self.target_pos = ship.pos
        dx = self.target_pos[0] - self.pos[0]
        dy = self.target_pos[1] - self.pos[1]
        dist = sqrt(dx**2 + dy**2)
        
        if dist != 0:  # Avoid division by zero
            # Update speed direction towards the player
            if self.accelerating:
                # Apply additional acceleration in the direction of the player
                self.speed[0] += (dx / dist) * ROCKET_ACCELERATION
                self.speed[1] += (dy / dist) * ROCKET_ACCELERATION

        # Update position based on speed
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]

    def draw(self, screen, camera_x, camera_y):
        pygame.draw.circle(screen, self.color, 
                           (int(self.pos[0] - camera_x), int(self.pos[1] - camera_y)), 
                           5)



# Add these to your global variables
enemies = []
enemy_projectiles = []


# Spawn enemies
for _ in range(15):
    x = random.randint(0, WORLD_WIDTH)
    y = random.randint(0, WORLD_HEIGHT)
    enemy_type = random.choice(['bullet', 'rocket'])
    enemies.append(Enemy(x, y, enemy_type))


# endregion



# region --- collision detection ---

# endregion

# region --- Minimap ---

MINIMAP_SIZE = 250  # Size of the minimap (width and height)
MINIMAP_MARGIN = 20  # Margin from the top-right corner
MINIMAP_BORDER_COLOR = (150, 150, 150)  # Light gray border
MINIMAP_BACKGROUND_COLOR = (30, 30, 30)  # Dark gray background
MINIMAP_SHIP_COLOR = (0, 255, 0)  # Green for the player's ship
MINIMAP_PLANET_COLOR = (255, 0, 0)  # Red for planets

def draw_minimap(screen, ship, planets, enemies, asteroids):
    # Calculate the position of the minimap
    minimap_x = SCREEN_WIDTH - MINIMAP_SIZE - MINIMAP_MARGIN
    minimap_y = MINIMAP_MARGIN

    # Draw minimap background
    pygame.draw.rect(screen, MINIMAP_BACKGROUND_COLOR, 
                     (minimap_x, minimap_y, MINIMAP_SIZE, MINIMAP_SIZE))

    # Draw minimap border
    pygame.draw.rect(screen, MINIMAP_BORDER_COLOR, 
                     (minimap_x, minimap_y, MINIMAP_SIZE, MINIMAP_SIZE), 2)

    # Calculate scaling factors
    scale = MINIMAP_SIZE / WORLD_WIDTH

    # Draw player's ship
    ship_minimap_x = int(minimap_x + ship.pos[0] * scale)
    ship_minimap_y = int(minimap_y + ship.pos[1] * scale)
    pygame.draw.circle(screen, MINIMAP_SHIP_COLOR, (ship_minimap_x, ship_minimap_y), 2)


    # Draw planets
    for planet in planets:
        planet_minimap_x = int(minimap_x + planet.pos[0] * scale)
        planet_minimap_y = int(minimap_y + planet.pos[1] * scale)
        pygame.draw.circle(screen, MINIMAP_PLANET_COLOR, (planet_minimap_x, planet_minimap_y), max(1, planet.radius/scale**(-1)))

    # Draw enemies
    for enemy in enemies:
        enemy_minimap_x = int(minimap_x + enemy.pos[0] * scale)
        enemy_minimap_y = int(minimap_y + enemy.pos[1] * scale)
        pygame.draw.circle(screen, enemy.color, (enemy_minimap_x, enemy_minimap_y), 2)
            
    for asteroid in asteroids:
        asteroid_minimap_x = int(minimap_x + asteroid.pos[0] * scale)
        asteroid_minimap_y = int(minimap_y + asteroid.pos[1] * scale)
        pygame.draw.circle(screen, asteroid.color, (asteroid_minimap_x, asteroid_minimap_y), max(1, asteroid.radius/scale**(-1)))


# endregion




# region --- grid ---



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





# ___________________________ ALL GOOD ________________ 




# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:

        # Draw everything
        screen.fill((0, 0, 0))
        draw_grid(screen, camera_x, camera_y)



        # region --- Handle input --- # ___________________________ ALL GOOD ________________

        front_thruster_on = False
        rear_thruster_on = False




        # Handle input
        keys = pygame.key.get_pressed()
        ship.reset_rotation_thrusters()
        if keys[pygame.K_LEFT]:
            ship.rotate_left()
        if keys[pygame.K_RIGHT]:
            ship.rotate_right()
        if keys[pygame.K_UP]:
            ship.forward()
        if keys[pygame.K_DOWN]:
            ship.backward()
        if keys[pygame.K_SPACE]:
            ship.shoot()

        # Update ship
        ship.update()

        # Update player bullets
        for bullet in ship.bullets[:]:
            bullet.update()
            if check_bullet_planet_collision(bullet, planets):
                ship.bullets.remove(bullet)
            if (bullet.pos[0] < 0 or bullet.pos[0] > WORLD_WIDTH or
                bullet.pos[1] < 0 or bullet.pos[1] > WORLD_HEIGHT):
                ship.bullets.remove(bullet)

        # Draw ship and bullets
        ship.draw(screen, camera_x, camera_y)
        for bullet in ship.bullets:
            bullet.draw(screen, camera_x, camera_y)




        # endregion


        
        # ___________________________ ALL GOOD above here _______________ 


        # region --- combat player--- 

        # region --- combat enemy---


        enemies = [enemy for enemy in enemies if enemy.health > 0]

        for enemy in enemies:
            new_projectiles = enemy.update(ship, planets, enemies)
            enemy_projectiles.extend(new_projectiles)



        # Update enemies and their projectiles
        for enemy in enemies[:]:
            new_projectiles = enemy.update(ship, planets, enemies)
            enemy_projectiles.extend(new_projectiles)
            
            # Check collision with player bullets
            for bullet in ship.bullets[:]:
                if distance(enemy.pos, bullet.pos) < enemy.radius + 3:
                    enemies.remove(enemy)
                    ship.bullets.remove(bullet)
                    break

        for projectile in enemy_projectiles[:]:
            if isinstance(projectile, Rocket): 
                projectile.update(ship)
            if check_bullet_planet_collision(projectile, planets):
                enemy_projectiles.remove(projectile)


        for projectile in enemy_projectiles[:]:
            if isinstance(projectile, Rocket):
                projectile.update(ship)
            else:
                projectile.update()
            
            if (projectile.pos[0] < 0 or projectile.pos[0] > WORLD_WIDTH or
                projectile.pos[1] < 0 or projectile.pos[1] > WORLD_HEIGHT):
                enemy_projectiles.remove(projectile)
            elif distance(ship.pos, projectile.pos) < ship.radius + 3:
                ship.health -= 10
                enemy_projectiles.remove(projectile)


        # endregion




        # Update player bullets

        ship.gun_cooldown = max(0, ship.gun_cooldown - 1)


        for bullet in ship.bullets[:]:
            bullet.update()
            if check_bullet_planet_collision(bullet, planets):
                ship.bullets.remove(bullet)
            if (bullet.pos[0] < 0 or bullet.pos[0] > WORLD_WIDTH or
                bullet.pos[1] < 0 or bullet.pos[1] > WORLD_HEIGHT):
                ship.bullets.remove(bullet)

        # endregion





       # region --- world border, camera --- # ___________________________ ALL GOOD ________________


        ship_screen_pos = (int(ship.pos[0] - camera_x), int(ship.pos[1] - camera_y))


        # Clamp the ship's x position
        if ship.pos[0] < 0:
            ship.pos[0] = 0
        elif ship.pos[0] > WORLD_WIDTH:
            ship.pos[0] = WORLD_WIDTH

        # Clamp the ship's y position
        if ship.pos[1] < 0:
            ship.pos[1] = 0
        elif ship.pos[1] > WORLD_HEIGHT:
            ship.pos[1] = WORLD_HEIGHT


        # Update camera position
        camera_x = ship.pos[0] - SCREEN_WIDTH // 2
        camera_y = ship.pos[1] - SCREEN_HEIGHT // 2

        # Clamp camera position to world boundaries
        camera_x = max(0, min(camera_x, WORLD_WIDTH - SCREEN_WIDTH))
        camera_y = max(0, min(camera_y, WORLD_HEIGHT - SCREEN_HEIGHT))

        # endregion




        # region --- moving ship--- # ___________________________ ALL GOOD ________________

        # Update ship position
        ship.pos = [
            ship.pos[0] + ship.speed[0],
            ship.pos[1] + ship.speed[1]
        ]

        # Calculate thruster positions and sizes
        front_thruster_pos = (
            int(ship_screen_pos[0] + math.cos(math.radians(ship.angle)) * ship.radius),
            int(ship_screen_pos[1] - math.sin(math.radians(ship.angle)) * ship.radius)
        )
        rear_thruster_pos = (
            int(ship_screen_pos[0] - math.cos(math.radians(ship.angle)) * ship.radius),
            int(ship_screen_pos[1] + math.sin(math.radians(ship.angle)) * ship.radius)
        )                             

         # Calculate rotation thruster positions
        left_rotation_thruster_pos = (
            int(ship_screen_pos[0] + math.cos(math.radians(ship.angle + 90)) * ship.radius),
            int(ship_screen_pos[1] - math.sin(math.radians(ship.angle + 90)) * ship.radius)
        )
        right_rotation_thruster_pos = (
            int(ship_screen_pos[0] + math.cos(math.radians(ship.angle - 90)) * ship.radius),
            int(ship_screen_pos[1] - math.sin(math.radians(ship.angle - 90)) * ship.radius)
        )



        # Ensure fuel doesn't go below 0
        ship.fuel = max(0, ship.fuel)


        # Check if ship is touching world border
        if (ship.pos[0] <= 0 or ship.pos[0] >= WORLD_WIDTH or
            ship.pos[1] <= 0 or ship.pos[1] >= WORLD_HEIGHT):
            game_over = True

        # endregion
        


        # region --- drawing --- # ___________________________ ALL GOOD ________________






        # Draw squares
        for square in squares:
            square.draw(screen, camera_x, camera_y)

        # Draw the main ship body (white circle)
        pygame.draw.circle(screen, ship_color, ship_screen_pos, ship.radius)



        # Draw player bullets
        for bullet in ship.bullets:
            bullet.draw(screen, camera_x, camera_y)

        # Draw enemies and their projectiles
        for enemy in enemies:
            enemy.draw(screen, camera_x, camera_y)
        for projectile in enemy_projectiles:
            projectile.draw(screen, camera_x, camera_y)

        # Draw player's gun
        gun_length = 25
        gun_end_x = ship_screen_pos[0] + cos(math.radians(ship.angle)) * (ship.radius + gun_length)
        gun_end_y = ship_screen_pos[1] - sin(math.radians(ship.angle)) * (ship.radius + gun_length)
        pygame.draw.line(screen, (200, 200, 200), ship_screen_pos, (gun_end_x, gun_end_y), 6)

        


        # endregion





        # region --- displaying --- # ___________________________ ALL GOOD ________________
        
        # Display ship coordinates
        font = pygame.font.Font(None, 22)
        coord_text = font.render(f"X: {int(ship.pos[0])}, Y: {int(ship.pos[1])}", True, (255, 255, 255))
        screen.blit(coord_text, (10, 10))

        # Display fuel
        fuel_text = font.render(f"Fuel: {ship.fuel:.3f}", True, (255, 255, 255))
        screen.blit(fuel_text, (10, 50))

        # Display item status
        item_text = font.render("Item: Collected" if has_item else "Item: Not Collected", True, (255, 255, 255))
        screen.blit(item_text, (10, 90))

        # Display mission status
        mission_text = font.render("Mission Complete!" if mission_complete else "Mission: In Progress", True, (255, 255, 255))
        screen.blit(mission_text, (10, 130))

        # Display ship health
        health_text = font.render(f"Health: {int(ship.health)}", True, (255, 255, 255))
        screen.blit(health_text, (10, 170))

        # Display square coordinates
        pos_refuel_text = font.render(f"Coordinates Refuel: {int(pos_refuel[0])}, {int(pos_refuel[1])}", True, (255, 255, 255))
        pos_item_text = font.render(f"Coordinates Item: {int(pos_item[0])}, {int(pos_item[1])}", True, (255, 255, 255))
        pos_complete_text = font.render(f"Coordinates Destination: {int(pos_complete[0])}, {int(pos_complete[1])}", True, (255, 255, 255))
        screen.blit(pos_refuel_text, (10, 210))
        screen.blit(pos_item_text, (10, 230))
        screen.blit(pos_complete_text, (10, 250))
        ammo_text = font.render(f"Ammo: {ship.ammo}", True, (255, 255, 255))
        screen.blit(ammo_text, (10, 290))

        draw_minimap(screen, ship, planets, enemies, asteroids)
        
        # endregion



    



        # Check if ship health reaches 0
        if ship.health <= 0:
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