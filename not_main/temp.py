class GameState:
    def __init__(self):
        self.running = True
        self.game_over = False
        self.mission_complete = False
        self.has_item = False

    def update(self):
        if self.mission_complete:
            self.game_over = True


game_state = GameState()


class Game:
    def __init__(self):
        pass

    def run(self):
        while not self.game_over:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_over = True

    def update(self):
        self.ship.update()
        self.handle_input()
        self.check_collisions()
        # ... update other game objects ...

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.draw_grid()
        self.ship.draw(self.screen)
        # ... draw other game objects ...
        pygame.display.flip()

    # ... other game methods ...


class Game:
    def __init__(self):
        # ... other initialization ...
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()

    def update(self):
        # ... other updates ...
        self.enemies.update()
        self.bullets.update()
        self.asteroids.update()

    def draw(self):
        # ... other drawing ...
        self.enemies.draw(self.screen)
        self.bullets.draw(self.screen)
        self.asteroids.draw(self.screen)


##########################
# elif self.current_action == 7:  # Accelerate randomly
#    self.rand_speed[0] = self.rand_speed[0] + random.uniform(-1, 1)
#    self.rand_speed[1] = self.rand_speed[1] + random.uniform(-1, 1)
#
#    self.speed[0] += self.rand_speed[0] * ENEMY_ACCELERATION*0.2
#    self.speed[1] += self.rand_speed[1] * ENEMY_ACCELERATION*0.2


class Enemy:
    def __init__(self, x, y, enemy_type, health=100):
        self.pos = [x, y]
        self.speed = [0, 0]
        self.radius = 15
        self.type = enemy_type  # 'bullet' or 'rocket'
        self.color = (155, 77, 166) if enemy_type == "bullet" else (255, 165, 0)
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
        force_x, force_y = calculate_gravity(
            self.pos, 100, planets
        )  # Assume enemy mass is 100
        self.speed[0] += force_x / 100
        self.speed[1] += force_y / 100
        self.check_planet_collision(planets)

        # Check if the 4-second period has elapsed
        if self.action_timer <= 0:
            self.choose_action(ship.pos, other_enemies)
            self.action_timer = 4 * 60  # Reset timer to 4 seconds (240 frames)

        # Execute current action
        if self.current_action == 1:  # Accelerate towards player
            self.speed = vec_add(
                self.speed,
                vec_scale([dx / dist, dy / dist], ENEMY_ACCELERATION * self.difficulty),
            )

        elif self.current_action == 2:  # Accelerate randomly
            if not self.random_direction:
                angle = random.uniform(0, 2 * math.pi)
                self.random_direction = [math.cos(angle), math.sin(angle)]
            self.speed = vec_add(
                self.speed,
                vec_scale(self.random_direction, ENEMY_ACCELERATION * self.difficulty),
            )

        elif self.current_action == 3:  # Decelerate
            self.speed = vec_add(
                self.speed,
                vec_scale(
                    [math.copysign(1, self.speed[0]), math.copysign(1, self.speed[1])],
                    -ENEMY_ACCELERATION * self.difficulty,
                ),
            )

        elif self.current_action == 4:  # Orbit player
            self.orbit_player(ship)

        elif self.current_action == 5:  # Evasive maneuvers
            self.evade(ship)

        elif self.current_action == 6:  # Formation flying
            self.fly_formation(other_enemies)

        elif self.current_action == 7:  # Accelerate randomly
            self.rand_speed[0] = self.rand_speed[0] + random.uniform(-1, 1)
            self.rand_speed[1] = self.rand_speed[1] + random.uniform(-1, 1)

            self.speed[0] += self.rand_speed[0] * ENEMY_ACCELERATION * 0.2
            self.speed[1] += self.rand_speed[1] * ENEMY_ACCELERATION * 0.2

        elif self.current_action == 8:  # Decelerate
            self.speed[0] -= sign(self.speed[0]) * ENEMY_ACCELERATION * 0.2
            self.speed[1] -= sign(self.speed[1]) * ENEMY_ACCELERATION * 0.2

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
            if self.type == "bullet":
                self.shoot_cooldown = (
                    BULLET_SHOOT_COOLDOWN  # Set cooldown for bullet enemy
                )
                return [Bullet(self.pos[0], self.pos[1], atan2(dy, dx), self)]
            else:
                self.shoot_cooldown = (
                    ROCKET_SHOOT_COOLDOWN  # Set cooldown for rocket enemy
                )
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
        self.speed = vec_add(
            self.speed,
            vec_scale([dx / dist, dy / dist], ENEMY_ACCELERATION * self.difficulty),
        )

    def evade(self, ship):
        dx = self.pos[0] - ship.pos[0]
        dy = self.pos[1] - ship.pos[1]
        dist = math.sqrt(dx**2 + dy**2)
        self.speed = vec_add(
            self.speed,
            vec_scale(
                [dx / dist, dy / dist], ENEMY_ACCELERATION * 1.5 * self.difficulty
            ),
        )

    def draw(self, screen, camera_x, camera_y):
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.pos[0] - camera_x), int(self.pos[1] - camera_y)),
            self.radius,
        )

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
        self.speed = vec_add(
            self.speed,
            vec_scale([dx / dist, dy / dist], ENEMY_ACCELERATION * self.difficulty),
        )

    def bounce(self, other):
        # Calculate normal vector
        nx = self.pos[0] - other.pos[0]
        ny = self.pos[1] - other.pos[1]
        norm = math.sqrt(nx * nx + ny * ny)
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
        j /= 1 / 100 + 1 / (
            4 / 3 * math.pi * other.radius**3
        )  # Assume enemy mass is 100

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
                norm = math.sqrt(nx * nx + ny * ny)
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
                j /= 1 / 100 + 1 / (
                    4 / 3 * 3.14 * planet.radius**3
                )  # Assume enemy mass is 100

                # Apply impulse
                self.speed[0] += j * nx / 100
                self.speed[1] += j * ny / 100

                # Move enemy outside planet
                overlap = self.radius + planet.radius - distance(self.pos, planet.pos)
                self.pos[0] += overlap * nx
                self.pos[1] += overlap * ny
