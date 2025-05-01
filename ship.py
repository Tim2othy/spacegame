"""Spaceships, shooting through space."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from physics import Disk, Pos, PosVel
from projectiles import Bullet, Flare, Missile, Rocket

if TYPE_CHECKING:
    from camera import Camera
GRAY = Color("gray")
THRUST_COLOR = Color("orange")
BULLET_ENEMY_COLOR = Color("lightblue")
ROCKET_ENEMY_COLOR = Color("purple")
MISSILE_ENEMY_COLOR = Color("lime")
MARKOV_ENEMY_COLOR = Color("red")
PLAYER_COLOR = Color("darkslategray")

BULLET_RATE_OF_FIRE = 0.08
ROCKET_RATE_OF_FIRE = 0.5
MISSILE_RATE_OF_FIRE = 3.0
FLARE_RATE_OF_FIRE = 5.0

# Release speeds
FLARE_MEAN_RELEASE_SPEED = 140
FLARE_SD_RELEASE_SPEED = 28
BULLET_RELEASE_SPEED = 700.0
ROCKET_RELEASE_SPEED = 300.0

NUM_FLARES = 40
SD_FLARE_ANGLE = 25

HEALTH = 100
DAMAGE_INDICATOR_TIME = 1
GUNBARREL_LENGTH = 3  # relative to radius
GUNBARREL_WIDTH = 0.5  # relative to radius

RETREAT_HEALTH_THRESHOLD = 30.0
ENEMY_FIRE_RANGE_SQUARED = 1700**2
ENEMY_ACTION_TIMER = 6
DESIRED_APPROACH_SPEED = 500
SMALL_ANGLE = 5


class AIState(Enum):
    """Possible AI states for enemies chain."""

    SEARCH = auto()
    ATTACK = auto()
    AIM = auto()
    RETREAT = auto()
    RANDOM = auto()


type MatrixRow = dict[AIState, float]
type Matrix = dict[AIState, MatrixRow]

_DEFAULT_MATRIX: Matrix = {
    AIState.SEARCH: {AIState.SEARCH: 0.6, AIState.ATTACK: 0.2, AIState.RETREAT: 0.2},
    AIState.ATTACK: {AIState.SEARCH: 0.2, AIState.ATTACK: 0.8},
    AIState.AIM: {AIState.SEARCH: 1.0},
    AIState.RETREAT: {AIState.SEARCH: 0.3, AIState.ATTACK: 0.2, AIState.RETREAT: 0.5},
}

_LOW_HEALTH_MATRIX: Matrix = {
    AIState.SEARCH: {AIState.SEARCH: 0.4, AIState.ATTACK: 0.3, AIState.RETREAT: 0.3},
    AIState.ATTACK: {AIState.SEARCH: 0.5, AIState.ATTACK: 0.3, AIState.RETREAT: 0.2},
    AIState.AIM: {AIState.RETREAT: 1.0},
    AIState.RETREAT: {AIState.SEARCH: 0.2, AIState.ATTACK: 0.1, AIState.RETREAT: 0.7},
}

_PLAYER_VISIBLE_MATRIX: Matrix = {
    AIState.SEARCH: {AIState.ATTACK: 0.8, AIState.AIM: 0.2},
    AIState.ATTACK: {AIState.ATTACK: 0.7, AIState.AIM: 0.3},
    AIState.AIM: {AIState.ATTACK: 0.4, AIState.AIM: 0.4, AIState.RETREAT: 0.2},
    AIState.RETREAT: {AIState.SEARCH: 0.2, AIState.ATTACK: 0.3, AIState.RETREAT: 0.5},
}

_LOW_HEALTH_AND_PLAYER_VISIBLE_MATRIX: Matrix = {
    AIState.SEARCH: {AIState.SEARCH: 0.0, AIState.ATTACK: 0.4, AIState.AIM: 0.4, AIState.RETREAT: 0.2},
    AIState.ATTACK: {AIState.ATTACK: 0.0, AIState.AIM: 0.1, AIState.RETREAT: 0.9},
    AIState.AIM: {AIState.ATTACK: 0.1, AIState.AIM: 0.8, AIState.RETREAT: 0.1},
    AIState.RETREAT: {AIState.ATTACK: 0.1, AIState.AIM: 0.1, AIState.RETREAT: 0.8},
}


def generate_complementary_color(base_color: Color) -> Color:
    """Generate a complementary bullet color based on a color.

    >>> generate_complementary_color(Color("red"))  # should return cyan
    Color(0, 255, 255, 255)
    >>> generate_complementary_color(Color("white"))  # should return white
    Color(255, 255, 255, 255)
    >>> generate_complementary_color(Color(0, 128, 0))  # dark green, should return violet
    Color(166, 0, 166, 255)
    """
    h, s, v, a = base_color.hsva

    new_h = (h + 180.0) % 360.0  # Shift hue by 180° for complementary color
    new_s = min(100.0, s * 1.2)  # Slightly more saturated
    new_v = min(100.0, v * 1.3)  # Slightly brighter

    complementary_color = Color(0, 0, 0, 0)
    complementary_color.hsva = (new_h, new_s, new_v, a)
    return complementary_color


@dataclass
class ShipConfig:
    """Configuration for a spaceship.

    Attributes:
        relative_pos (Vec2): Relative position of the player-spaceship
        relative_vel (Vec2): Relative velocity of the player-spaceship
        size (float): Size of the ship

    """

    relative_pos: Vec2
    relative_vel: Vec2 = field(default_factory=lambda: Vec2(0, 0))
    size: float = 10.0


class Ship(Disk):
    """A basic spaceship."""

    # Class configuration
    SHIP_COLOR = BULLET_ENEMY_COLOR
    SHIP_GUN_COOLDOWN = BULLET_RATE_OF_FIRE
    SHIP_PROJECTILE_SPEED = BULLET_RELEASE_SPEED

    def __init__(self, relative_to: PosVel, config: ShipConfig) -> None:
        """Create a new spaceship."""
        super().__init__(relative_to, config.relative_pos, config.relative_vel, config.size, self.SHIP_COLOR)

        self._flare_cooldown: float = FLARE_RATE_OF_FIRE
        self.projectile_color: Color = generate_complementary_color(self.SHIP_COLOR)
        self.thrust: float = 250 * self.mass
        self.rotation_thrust: float = 0.15 * self.mass

        self.projectiles: list[Bullet] = []
        self.health: float = HEALTH
        self.angle: float = 0

        self.damage_indicator_timer: float = 0
        self.gun_cooldown_timer: float = 0
        self.flare_cooldown_timer: float = 0

        self.releasing_flares: bool = False
        self.shooting: bool = False

        self.thruster_rot_left: bool = False
        self.thruster_rot_right: bool = False
        self.thruster_backward: bool = False
        self.thruster_forward: bool = False

    def get_faced_direction(self) -> Vec2:
        """Get `self`'s (normalized) faced direction from its `angle`."""
        direction = Vec2(0, 0)
        direction.from_polar((1, self.angle))
        return direction

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new bullet at `pos` with velocity `vel`, relative to self."""
        return Bullet(self, pos, vel, self.projectile_color)

    def new_flare(self, pos: Vec2, vel: Vec2) -> Flare:
        """Create a new Flare at `pos` with velocity `vel`, relative to self."""
        return Flare(self, pos, vel)

    def handle_shooting(self, dt: float) -> None:
        """Handle bullet-shooting."""
        if not self.shooting:
            # The ship doesn't want to shoot at the moment,
            # so just decrease the cooldown if it's > 0.
            # If it's <= 0, don't decrease the cooldown further.
            if self.gun_cooldown_timer > 0:
                self.gun_cooldown_timer = max(0, self.gun_cooldown_timer - dt)
        else:
            # The ship wants to shoot.
            self.gun_cooldown_timer -= dt

            # To handle multiple shots per frame:
            while self.gun_cooldown_timer < 0:
                forward = self.get_faced_direction()
                bullet_vel = forward * self.SHIP_PROJECTILE_SPEED

                # When multiple shots are fired per frame,
                # but we spawn them all at the end of the gunbarrel,
                # they'd all spawn on top of each other, see issue #47.
                # To mitigate this, we offset the spawn-position
                # by the (time since the shot was fired) * bullet_vel.
                # The time since the shot was fired is simply the
                # negative of the current gun_cooldown.
                gunbarrel_offset = forward * self.radius * GUNBARREL_LENGTH
                bullet_pos = gunbarrel_offset - self.gun_cooldown_timer * bullet_vel

                self.projectiles.append(self.new_bullet(bullet_pos, bullet_vel))
                self.gun_cooldown_timer += self.SHIP_GUN_COOLDOWN

    def handle_flares(self, dt: float) -> None:
        """Handle flare-releasing."""
        if not self.releasing_flares:
            # The ship doesn't want to release flares at the moment,
            # so just decrease the cooldown if it's > 0.
            # If it's <= 0, don't decrease the cooldown further.
            if self.flare_cooldown_timer > 0:
                self.flare_cooldown_timer = max(0, self.flare_cooldown_timer - dt)
        else:
            # The ship wants to shoot.
            self.flare_cooldown_timer -= dt

            while self.flare_cooldown_timer < 0:
                forward = self.get_faced_direction()

                for _ in range(NUM_FLARES):
                    random_rotation = random.normalvariate(0, SD_FLARE_ANGLE)
                    flare_direction = forward.rotate(random_rotation)
                    flare_vel = -flare_direction * random.normalvariate(
                        FLARE_MEAN_RELEASE_SPEED, FLARE_SD_RELEASE_SPEED
                    )
                    self.projectiles.append(self.new_flare(Vec2(0, 0), flare_vel))
                self.flare_cooldown_timer += self._flare_cooldown

    def suffer_damage(self, damage: float) -> None:
        """Deal damage to the ship and activate its damage-indicator.

        Does nothing if damage is <= 0.
        """
        if damage > 0:
            self.health -= damage
            self.damage_indicator_timer = DAMAGE_INDICATOR_TIME

    def step(self, dt: float) -> None:
        """Step physics, control, and `self`'s bullets."""
        if self.thruster_rot_left:
            self.angle += self.rotation_thrust * dt
        if self.thruster_rot_right:
            self.angle -= self.rotation_thrust * dt

        forward = self.get_faced_direction()
        force = forward * self.thrust
        if self.thruster_forward:
            self.apply_force(force, dt)
        if self.thruster_backward:
            self.apply_force(-force, dt)

        self.damage_indicator_timer = max(0, self.damage_indicator_timer - dt)

        super().step(dt)

        for projectile in self.projectiles:
            projectile.step(dt)

        self.handle_shooting(dt)
        self.handle_flares(dt)

    def draw(self, camera: Camera, color: Color | None = None) -> None:
        """Draw `self` on `camera`."""
        forward = self.get_faced_direction()
        right = Vec2(-forward.y, forward.x)
        left = -right
        backward = -forward

        base_color = (color or self.color).lerp(Color("red"), self.damage_indicator_timer)
        darker_color: Color = base_color.lerp(Color("black"), 0.5)

        # Helper function for drawing polygons relative to the ship-position
        def drawy(color: Color, points: list[Vec2]) -> None:
            camera.draw_polygon(color, [Pos(self, self.radius * p) for p in points])

        # thruster_backward
        if self.thruster_backward:
            drawy(THRUST_COLOR, [forward * 2, left * 1.25, right * 1.25])

        # "For his neutral special, he wields a gun"
        camera.draw_line(
            darker_color, self, Pos(self, forward * self.radius * GUNBARREL_LENGTH), GUNBARREL_WIDTH * self.radius
        )

        # thruster_rot_left, material
        drawy(
            darker_color,
            [
                0.7 * left + 0.7 * forward,
                0.5 * left + 0.5 * backward,
                2.0 * left + 1.0 * backward,
            ],
        )
        if self.thruster_rot_left:
            # thruster_rot_left, active
            drawy(
                THRUST_COLOR,
                [
                    1.5 * left + 1.25 * backward,
                    0.5 * left + 0.5 * backward,
                    2.0 * left + 1.0 * backward,
                ],
            )

        # thruster_rot_right, material
        drawy(
            darker_color,
            [
                0.7 * right + 0.7 * forward,
                0.5 * right + 0.5 * backward,
                2.0 * right + 1.0 * backward,
            ],
        )
        if self.thruster_rot_right:
            # thruster_rot_right, active
            drawy(
                THRUST_COLOR,
                [
                    1.5 * right + 1.25 * backward,
                    0.5 * right + 0.5 * backward,
                    2.0 * right + 1.0 * backward,
                ],
            )

        # thruster_forward, active
        if self.thruster_forward:
            drawy(
                THRUST_COLOR,
                [
                    0.7 * left + 0.7 * backward,
                    0.5 * left + 1.5 * backward,
                    1.25 * backward,
                    0.5 * right + 1.5 * backward,
                    0.7 * right + 0.7 * backward,
                ],
            )
        # thruster_forward, material
        drawy(
            darker_color,
            [
                0.7 * left + 0.7 * backward,
                0.5 * left + 1.25 * backward,
                1.0 * backward,
                0.5 * right + 1.25 * backward,
                0.7 * right + 0.7 * backward,
            ],
        )

        # Draw the circular body ("hitbox") with the base color
        super().draw(camera, color=base_color)

        for projectile in self.projectiles:
            projectile.draw(camera)


type PygameKey = int


@dataclass
class ShipInput:
    """Specification for which keys trigger what spaceship-action.

    Attributes:
        thruster_rot_left (pygame_key): Left rotation thruster's key
        thruster_rot_right (pygame_key): Right rotation thruster's key
        thruster_forward (pygame_key): Forward thruster's key
        thruster_backward (pygame_key): Backward thruster's key
        shoot (pygame_key): Pew pew key
        release_flares (pygame_key): Flare-release key

    """

    thruster_rot_left: PygameKey
    thruster_rot_right: PygameKey
    thruster_forward: PygameKey
    thruster_backward: PygameKey
    shoot: PygameKey
    release_flares: PygameKey

    @classmethod
    def arrows(cls) -> ShipInput:
        """Create a new ShipInput, Arrow-Key-movement and return-shooting."""
        return cls(pygame.K_RIGHT, pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN, pygame.K_RETURN, pygame.K_m)

    @classmethod
    def wasd(cls) -> ShipInput:
        """Create a new ShipInput, WASD-movement and space-shooting."""
        return cls(pygame.K_d, pygame.K_a, pygame.K_w, pygame.K_s, pygame.K_SPACE, pygame.K_e)


@dataclass(kw_only=True)
class PlayerConfig(ShipConfig):
    """Configuration for a player-spaceship.

    Attributes:
        relative_pos (Vec2): Relative position of the player-spaceship
        relative_vel (Vec2): Relative velocity of the player-spaceship
        ship_input (ShipInput): Controls for the player-spaceship

    """

    ship_input: ShipInput = field(default_factory=ShipInput.arrows)


class PlayerShip(Ship):
    """A player-controlled spaceship."""

    # Class configuration
    SHIP_COLOR = PLAYER_COLOR

    def __init__(self, relative_to: PosVel, config: PlayerConfig) -> None:
        """Create a new player-spaceship."""
        super().__init__(relative_to, config)
        self.spaceship_input = config.ship_input

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Handle input for `self` using ScancodeWrapper `keys`.

        `keys` is typically retreived using `pygame.key.get_pressed()`.
        """
        self.thruster_rot_left = keys[self.spaceship_input.thruster_rot_left]
        self.thruster_rot_right = keys[self.spaceship_input.thruster_rot_right]
        self.thruster_forward = keys[self.spaceship_input.thruster_forward]
        self.thruster_backward = keys[self.spaceship_input.thruster_backward]
        self.shooting = keys[self.spaceship_input.shoot]
        self.releasing_flares = keys[self.spaceship_input.release_flares]


@dataclass(kw_only=True)
class EnemyConfig(ShipConfig):
    """Configuration for an enemy-spaceship.

    Attributes:
        relative_pos (Vec2): Relative position of the enemy-spaceship
        relative_vel (Vec2): Relative velocity of the enemy-spaceship
        target_ship (Ship): Ship to target

    """

    target_ship: Ship


class BulletEnemy(Ship):
    """An enemy ship, targeting a specific other ship."""

    def __init__(self, relative_to: PosVel, config: EnemyConfig) -> None:
        """Create a new enemy ship."""
        super().__init__(relative_to, config)
        self.target: Ship = config.target_ship
        self.ai = EnemyAI(self)

    def step(self, dt: float) -> None:
        """Apply physics and "AI" to `self`."""
        self.ai.step(dt)
        super().step(dt)


class RocketEnemy(BulletEnemy):
    """An enemy ship shooting rockets, targeting a specific other ship."""

    # Class configuration
    SHIP_COLOR = ROCKET_ENEMY_COLOR
    SHIP_GUN_COOLDOWN = ROCKET_RATE_OF_FIRE
    SHIP_PROJECTILE_SPEED = ROCKET_RELEASE_SPEED

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new missile relative to `self` targeting `self.target`."""
        return Rocket(self, pos, vel, self.projectile_color, self.target)


class MissileEnemy(BulletEnemy):
    """An enemy ship shooting powerful, smart, homing missiles, targeting a specific other ship."""

    # Class configuration
    SHIP_COLOR = MISSILE_ENEMY_COLOR
    SHIP_GUN_COOLDOWN = MISSILE_RATE_OF_FIRE
    SHIP_PROJECTILE_SPEED = ROCKET_RELEASE_SPEED

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new missile relative to `self` targeting `self.target`."""
        return Missile(self, pos, vel, self.projectile_color, self.target)


class MarkovEnemy(BulletEnemy):
    """An enemy ship using Markov chain AI for more sophisticated behavior."""

    # Class configuration
    SHIP_COLOR = MARKOV_ENEMY_COLOR


class EnemyAI:
    """Markov chain-based AI for enemy ships."""

    def __init__(self, ship: BulletEnemy) -> None:
        """Create a new AI controller."""
        self.ship = ship
        self.current_state = AIState.SEARCH
        self.action_timer = 0.0
        self.can_see_target = self.ship.distance_squared_to(self.ship.target) < ENEMY_FIRE_RANGE_SQUARED

    def step(self, dt: float) -> None:
        """Transition state and apply appropriate behavior for different enemy types."""
        self.action_timer -= dt
        if self.action_timer <= 0:
            self.action_timer = ENEMY_ACTION_TIMER

            if isinstance(self.ship, MarkovEnemy):
                self._transition_markov()
            else:
                self._transition_simple()

        desired_direction = self._match()
        self.ship.shooting = self.current_state in {AIState.ATTACK, AIState.AIM} and self.can_see_target

        if desired_direction != Vec2(0, 0):
            current_angle = self.ship.angle
            target_angle = math.degrees(math.atan2(desired_direction.y, desired_direction.x))
            angle_diff = (target_angle - current_angle + 180) % 360 - 180

            # Determine which way to turn (left or right)
            self.ship.thruster_rot_left = angle_diff > SMALL_ANGLE
            self.ship.thruster_rot_right = angle_diff < -SMALL_ANGLE

            self.ship.thruster_forward = True

        else:
            self.ship.thruster_forward = False

    def _transition_markov(self) -> None:
        """Transition to a new state based on the Markov transition matrix."""
        # Get context information
        low_health = self.ship.health < RETREAT_HEALTH_THRESHOLD

        match (self.can_see_target, low_health):
            case (True, True):
                matrix = _LOW_HEALTH_AND_PLAYER_VISIBLE_MATRIX
            case (False, True):
                matrix = _LOW_HEALTH_MATRIX
            case (True, False):
                matrix = _PLAYER_VISIBLE_MATRIX
            case (False, False):
                matrix = _DEFAULT_MATRIX

        # Extract probabilities for current state
        current_row: MatrixRow = matrix[self.current_state]
        states, probabilities = list(current_row.keys()), list(current_row.values())
        self.current_state = random.choices(states, probabilities)[0]

    def _transition_simple(self) -> None:
        if self.can_see_target:
            self.current_state = AIState.ATTACK
        else:
            self.current_state = AIState.RANDOM

            # Accelerate towards a random point near the player.
            distance_to_target = self.ship.target.distance_to(self.ship)
            # I think (but haven't proved) that, by choosing the standard-deviation proportional
            # to the distance to the player, we should eventually find a non-accelerating player.
            random_x = random.gauss(sigma=distance_to_target)
            random_y = random.gauss(sigma=distance_to_target)
            self.seek_towards = Pos(self.ship.target, Vec2(random_x, random_y))

    def _match(self) -> Vec2:
        """Match and then, execute behavior based on current state."""
        desired_direction = Vec2(0, 0)
        match self.current_state:
            case AIState.SEARCH:
                desired_direction = self._execute_search()
            case AIState.ATTACK:
                desired_direction = self._execute_attack()
            case AIState.AIM:
                desired_direction = self._execute_aim()
            case AIState.RETREAT:
                desired_direction = self._execute_retreat()
            case AIState.RANDOM:
                desired_direction = self._execute_randomly()
        return desired_direction

    def _execute_search(self) -> Vec2:
        """Return force required for the search-behavior."""
        delta_target_ship = self.ship.target.pos_relative_to(self.ship)
        relative_velocity = self.ship.vel_relative_to(self.ship.target)

        if delta_target_ship == Vec2(0, 0):
            return Vec2(0, 0)
        approach_direction = delta_target_ship.normalize()
        desired_relative_vel = approach_direction * DESIRED_APPROACH_SPEED
        # Force required to change from current relative velocity to desired relative velocity
        return desired_relative_vel - relative_velocity

    def _execute_attack(self) -> Vec2:
        """Return force required for the attack-behavior."""
        return self.ship.target.pos_relative_to(self.ship)

    def _execute_aim(self) -> Vec2:
        """Return force required for the aim-behavior."""
        # Relative position and velocity
        relative_pos = self.ship.target.pos_relative_to(self.ship)
        relative_vel = self.ship.target.vel_relative_to(self.ship)

        if relative_pos == Vec2(0, 0):
            return Vec2(0, 0)

        """
        We need to find the direction where:
            target_pos + target_vel*t = ship_pos + ship_vel*t + direction*bullet_speed*t
        Which is equivalent to:
            relative_pos + relative_vel*t = direction*bullet_speed*t

        Solve quadratic equation for intercept time:
            |relative_pos + relative_vel*t| = bullet_speed*t

        This expands to:
            |relative_pos|^2 + 2*relative_pos·relative_vel*t + (|relative_vel|^2 - bullet_speed^2)*t^2 = 0
        """

        # Quadratic equation coefficients:
        a = relative_vel.length_squared() - BULLET_RELEASE_SPEED**2
        b = 2 * relative_pos.dot(relative_vel)
        c = relative_pos.length_squared()

        # Standard quadratic formula
        discriminant = b**2 - 4 * a * c

        if discriminant < 0:
            # No real solution exists (target unreachable)
            # Fall back to simpler approach
            force = relative_pos + relative_vel * (relative_pos.length() / BULLET_RELEASE_SPEED)
            return force.normalize() if force != Vec2(0, 0) else Vec2(0, 0)

        # Calculate both solutions
        t1 = (-b + math.sqrt(discriminant)) / (2 * a)
        t2 = (-b - math.sqrt(discriminant)) / (2 * a)

        # Select the smallest positive time
        if t1 > 0 and t2 > 0:
            intercept_time = min(t1, t2)
        elif t1 > 0:
            intercept_time = t1
        elif t2 > 0:
            intercept_time = t2
        else:
            # No positive solution, target moving too fast or in wrong direction
            # Fall back to simple leading shot
            intercept_time = relative_pos.length() / BULLET_RELEASE_SPEED

        # Calculate predicted position
        if intercept_time <= 0:
            # Fallback if no solution found
            return relative_pos.normalize()

        # Now calculate what direction the bullet must be fired in
        return (relative_pos + relative_vel * intercept_time) / (BULLET_RELEASE_SPEED * intercept_time)

    def _execute_retreat(self) -> Vec2:
        """Return force required for the retreat-behavior."""
        if not self.can_see_target:
            return Vec2(0, 0)
        return self.ship.pos_relative_to(self.ship.target)

    def _execute_randomly(self) -> Vec2:
        return self.seek_towards.pos_relative_to(self.ship)
