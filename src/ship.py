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

from physics import (
    APPROACH_SPEED,
    FUEL,
    FUEL_USAGE,
    SMALL_ANGULAR_VEL,
    BasicAI,
    Mover,
    Pos,
    PosVel,
    RotationState,
    ThrustState,
)
from projectiles import Bullet, Flare, Missile, Rocket

if TYPE_CHECKING:
    from camera import Camera

GRAY = Color("gray")
THRUST_COLOR = Color("orange")
BULLET_ENEMY_COLOR = Color("lightblue")
ROCKET_ENEMY_COLOR = Color("aquamarine4")
MISSILE_ENEMY_COLOR = Color("lightgoldenrod")
PLAYER_COLOR = Color("lightcoral")
ENEMY_INDICATOR_COLOR = Color("red")

# Make sure these are all positive and finite
BULLET_RATE_OF_FIRE = 0.08
ROCKET_RATE_OF_FIRE = 0.7
MISSILE_RATE_OF_FIRE = 4.0
FLARE_RATE_OF_FIRE = 4.0

FLARE_MEAN_RELEASE_SPEED = 140
FLARE_SD_RELEASE_SPEED = 35.0
BULLET_RELEASE_SPEED = 700.0
ROCKET_RELEASE_SPEED = 300.0

NUM_FLARES = 40
SD_FLARE_ANGLE = 30

HEALTH = 100
DAMAGE_INDICATOR_TIME = 1
REPAIR_DELAY = 1.0  # Is this in seconds?
GUNBARREL_LENGTH = 3  # relative to radius
GUNBARREL_WIDTH = 0.5  # relative to radius
ROT_STATE_DELTA = 1.0
ARROW_THRESHOLD = 2000.0**2
REFUEL = FUEL_USAGE / 5

ENEMY_FIRE_RANGE_SQUARED = 1700**2
ENEMY_ACTION_TIMER = 6
APPROACH_LOWER = 50
APPROACH_UPPER = 90


class AIState(Enum):
    """Possible AI states for enemies chain."""

    RAM = auto()
    ATTACK = auto()
    AIM = auto()
    RETREAT = auto()
    HEAL = auto()


type MatrixRow = dict[AIState, float]
type Matrix = dict[AIState, MatrixRow]

_DEFAULT_MATRIX: Matrix = {
    AIState.RAM: {AIState.RAM: 0.6, AIState.ATTACK: 0.2, AIState.RETREAT: 0.2},
    AIState.ATTACK: {AIState.RAM: 0.2, AIState.ATTACK: 0.8},
    AIState.AIM: {AIState.RAM: 1.0},
    AIState.RETREAT: {AIState.RAM: 0.3, AIState.ATTACK: 0.2, AIState.RETREAT: 0.5},
    AIState.HEAL: {AIState.RAM: 0.3, AIState.HEAL: 0.7},
}

_PLAYER_VISIBLE_MATRIX: Matrix = {
    AIState.RAM: {AIState.ATTACK: 0.8, AIState.AIM: 0.2},
    AIState.ATTACK: {AIState.ATTACK: 0.7, AIState.AIM: 0.3},
    AIState.AIM: {AIState.ATTACK: 0.4, AIState.AIM: 0.4, AIState.RETREAT: 0.2},
    AIState.RETREAT: {AIState.RAM: 0.2, AIState.ATTACK: 0.3, AIState.RETREAT: 0.5},
    AIState.HEAL: {AIState.AIM: 1.0},
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


class Ship(Mover):
    """A basic spaceship."""

    # Class configuration
    _SHIP_COLOR = BULLET_ENEMY_COLOR
    _SHIP_GUN_COOLDOWN = BULLET_RATE_OF_FIRE
    _SHIP_PROJECTILE_SPEED = BULLET_RELEASE_SPEED
    THRUST = 1050000
    ROTATION_THRUST = 132000000

    def __init__(self, relative_to: PosVel, config: ShipConfig) -> None:
        """Create a new spaceship."""
        super().__init__(relative_to, config.relative_pos, config.relative_vel, config.size, self._SHIP_COLOR)

        self.projectile_color: Color = generate_complementary_color(self._SHIP_COLOR)

        self.projectiles: list[Bullet] = []
        self.health: float = HEALTH
        self.max_repair_health: float = HEALTH

        self.damage_indicator_timer: float = 0
        self.gun_cooldown_timer: float = 0
        self.flare_cooldown_timer: float = 0
        self.boost_cooldown_timer: float = 0
        self.repair_eligibility_timer: float = 0

        self.releasing_flares: bool = False
        self.shooting: bool = False
        self.boost: bool = False

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
                bullet_base_vel = self.forward * self._SHIP_PROJECTILE_SPEED

                # When multiple shots are fired per frame,
                # but we spawn them all at the end of the gunbarrel,
                # they'd all spawn on top of each other, see issue #47.
                # To mitigate this, we offset the spawn-position
                # by the (time since the shot was fired) * bullet_vel.
                # The time since the shot was fired is simply the
                # negative of the current gun_cooldown.
                gunbarrel_distance = self.radius * GUNBARREL_LENGTH
                bullet_pos = self.forward * gunbarrel_distance - self.gun_cooldown_timer * bullet_base_vel

                # Calculate tangential velocity
                # The angular velocity in the physics system is in degrees/second
                # We need to convert to radians/second for correct physics
                angular_vel_radians = math.radians(self.angular_velocity)

                # The tangential velocity vector is perpendicular to the radius vector
                # with magnitude ω [cross] r
                perpendicular_direction = Vec2(-self.forward.y, self.forward.x)

                # Calculate tangential velocity: v_t = ω [crossp] r = ω * r * perpendicular_unit_vector
                tangential_vel = perpendicular_direction * angular_vel_radians * gunbarrel_distance

                # Combine all velocity components
                bullet_vel = bullet_base_vel + tangential_vel

                self.projectiles.append(self.new_bullet(bullet_pos, bullet_vel))
                self.gun_cooldown_timer += self._SHIP_GUN_COOLDOWN

    def handle_flares(self, dt: float) -> None:
        """Handle flare-releasing."""
        if self.flare_cooldown_timer > 0:
            self.flare_cooldown_timer -= dt
            return

        if self.releasing_flares:
            # Convert angular velocity to radians for physics calculations
            angular_vel_radians = math.radians(self.angular_velocity)

            # Calculate flare position relative to ship
            flare_exit_point_distance = self.radius * 1.2
            flare_exit_point = -self.forward * flare_exit_point_distance

            # Calculate tangential velocity component from ship's rotation
            perpendicular_direction = Vec2(-flare_exit_point.y, flare_exit_point.x)
            tangential_vel = perpendicular_direction * angular_vel_radians * flare_exit_point_distance

            for _ in range(NUM_FLARES):
                random_rotation = random.normalvariate(0, SD_FLARE_ANGLE)
                flare_direction = self.forward.rotate(random_rotation)

                # Calculate base velocity (opposite to flare direction)
                base_vel = -flare_direction * random.normalvariate(FLARE_MEAN_RELEASE_SPEED, FLARE_SD_RELEASE_SPEED)

                # Combine velocities for realistic momentum transfer
                flare_vel = base_vel + tangential_vel
                self.projectiles.append(self.new_flare(flare_exit_point, flare_vel))
            self.flare_cooldown_timer = FLARE_RATE_OF_FIRE

    def handle_boost(self, dt: float) -> None:
        """Give player instantaneous strong forward boost."""
        if self.boost_cooldown_timer > 0:
            self.boost_cooldown_timer -= dt
            return
        if self.boost:
            force = self.forward * self.THRUST * 100
            self.thrust_state = ThrustState.FORWARD
            self.apply_force(force, dt)
            self.boost_cooldown_timer = 5.0

    def suffer_damage(self, damage: float) -> None:
        """Deal damage to the ship and activate its damage-indicator.

        Does nothing if damage is <= 0.
        """
        if damage > 0:
            self.health -= damage
            self.damage_indicator_timer = DAMAGE_INDICATOR_TIME

            # Sometimes degrade the ship's maximum repairable health.
            p = 1 - math.exp(-0.0026 * damage**2)
            # sigmoid like function with p(0) = 0, p(inf) = 1
            if random.random() < p:
                self.max_repair_health -= damage * random.random()

    def repair_refuel(self) -> None:
        """Repair the ship, if it hasn't been damaged and no thrusters have been active for 5 seconds. Refuel."""
        if self.fuel < FUEL:
            self.fuel += REFUEL
        if (
            self.damage_indicator_timer > 0
            or self.rotation_state != RotationState.NONE
            or self.thrust_state != ThrustState.NONE
        ):
            self.repair_eligibility_timer = 0
            return

        self.repair_eligibility_timer += 0.01

        if self.repair_eligibility_timer >= REPAIR_DELAY and self.health < self.max_repair_health - 0.05:
            self.health += 0.05

    def step(self, dt: float) -> None:
        """Step physics, control, and `self`'s bullets."""
        self.damage_indicator_timer = max(0, self.damage_indicator_timer - dt)

        super().step(dt)

        for projectile in self.projectiles:
            projectile.step(dt)

        self.handle_shooting(dt)
        self.handle_flares(dt)
        self.handle_boost(dt)
        self.repair_refuel()

    def draw(self, camera: Camera, color: Color | None = None) -> None:
        """Draw `self` on `camera`."""
        forward = self.forward
        right = Vec2(-forward.y, forward.x)
        left = -right
        backward = -forward

        base_color = (color or self.color).lerp(Color("red"), self.damage_indicator_timer)
        darker_color: Color = base_color.lerp(Color("black"), 0.5)

        # Helper function for drawing polygons relative to the ship-position
        def drawy(color: Color, points: list[Vec2]) -> None:
            camera.draw_polygon(color, [Pos(self, self.radius * p) for p in points])

        # "For his neutral special, he wields a gun"
        camera.draw_line(
            darker_color, self, Pos(self, forward * self.radius * GUNBARREL_LENGTH), GUNBARREL_WIDTH * self.radius
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
        # thruster_L, material
        drawy(
            darker_color,
            [
                0.7 * left + 0.7 * forward,
                0.5 * left + 0.5 * backward,
                2.0 * left + 1.0 * backward,
            ],
        )
        # thruster_R, material
        drawy(
            darker_color,
            [
                0.7 * right + 0.7 * forward,
                0.5 * right + 0.5 * backward,
                2.0 * right + 1.0 * backward,
            ],
        )
        if self.fuel > FUEL_USAGE * 2:
            # thruster_L, active
            if self.rotation_state == RotationState.LEFT:
                drawy(
                    THRUST_COLOR,
                    [
                        1.5 * left + 1.25 * backward,
                        0.5 * left + 0.5 * backward,
                        2.0 * left + 1.0 * backward,
                    ],
                )
            # thruster_R, active
            if self.rotation_state == RotationState.RIGHT:
                drawy(
                    THRUST_COLOR,
                    [
                        1.5 * right + 1.25 * backward,
                        0.5 * right + 0.5 * backward,
                        2.0 * right + 1.0 * backward,
                    ],
                )
            # thruster_forward, active
            if self.thrust_state == ThrustState.FORWARD:
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
            # thruster_backward
            if self.thrust_state == ThrustState.BACKWARD:
                drawy(THRUST_COLOR, [forward * 2, left * 1.25, right * 1.25])

        # Draw the circular body ("hitbox") with the base color
        super().draw(camera, color=base_color)

        for projectile in self.projectiles:
            projectile.draw(camera)


type PygameKey = int


@dataclass
class ShipInput:
    """Specification for which keys trigger what spaceship-action.

    Attributes:
        thruster_L (pygame_key): Left rotation thruster's key
        thruster_R (pygame_key): Right rotation thruster's key
        thruster_forward (pygame_key): Forward thruster's key
        thruster_backward (pygame_key): Backward thruster's key
        shoot (pygame_key): Pew pew key
        release_flares (pygame_key): Flare-release key

    """

    thruster_L: PygameKey  # noqa: N815
    thruster_R: PygameKey  # noqa: N815
    thruster_forward: PygameKey
    thruster_backward: PygameKey
    shoot: PygameKey
    release_flares: PygameKey
    boost: PygameKey

    @classmethod
    def arrows(cls) -> ShipInput:
        """Create a new ShipInput, Arrow-Key-movement and return-shooting."""
        return cls(pygame.K_RIGHT, pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN, pygame.K_RETURN, pygame.K_m, pygame.K_b)

    @classmethod
    def wasd(cls) -> ShipInput:
        """Create a new ShipInput, WASD-movement and space-shooting."""
        return cls(pygame.K_d, pygame.K_a, pygame.K_w, pygame.K_s, pygame.K_SPACE, pygame.K_e, pygame.K_g)


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
    _SHIP_COLOR = PLAYER_COLOR

    def __init__(self, relative_to: PosVel, config: PlayerConfig) -> None:
        """Create a new player-spaceship."""
        super().__init__(relative_to, config)
        self.spaceship_input = config.ship_input
        self.turn_L: float = 0.0
        self.turn_R: float = 0.0
        self.turn_back_L: float = 0.0
        self.turn_back_R: float = 0.0

        self.closest_enemy: Ship | None = None

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Handle input for `self` using ScancodeWrapper `keys`.

        `keys` is typically retreived using `pygame.key.get_pressed()`.
        """
        match (keys[self.spaceship_input.thruster_L], keys[self.spaceship_input.thruster_R]):
            case (True, True) | (False, False):
                rotation_state = RotationState.NONE
            case (True, False):
                rotation_state = RotationState.LEFT
            case (False, True):
                rotation_state = RotationState.RIGHT

        match (keys[self.spaceship_input.thruster_forward], keys[self.spaceship_input.thruster_backward]):
            case (True, True) | (False, False):
                self.thrust_state = ThrustState.NONE
            case (True, False):
                self.thrust_state = ThrustState.FORWARD
            case (False, True):
                self.thrust_state = ThrustState.BACKWARD

        self.increment_rot_counters(rotation_state)

        self.shooting = keys[self.spaceship_input.shoot]
        self.releasing_flares = keys[self.spaceship_input.release_flares]
        self.boost = keys[self.spaceship_input.boost]

    def do_rotation_for_player(self) -> None:
        """Activates rotation thrusters for player based on attributes modified by `increment_rot_counters()`.

        If you want to turn from 40° to 110° you have to press the left key until you reach 75°.
        Then you automatically decelerate from  75° to 110° and come to a stop there.
        """
        self.rotation_state = RotationState.NONE

        if self.turn_L > 0:
            self.turn_L -= ROT_STATE_DELTA
            self.rotation_state = RotationState.LEFT
        elif self.turn_back_R > 0:
            self.turn_back_R -= ROT_STATE_DELTA
            self.rotation_state = RotationState.RIGHT

        if self.turn_R > 0:
            self.turn_R -= ROT_STATE_DELTA
            self.rotation_state = RotationState.RIGHT
        elif self.turn_back_L > 0:
            self.turn_back_L -= ROT_STATE_DELTA
            self.rotation_state = RotationState.LEFT

        if self.rotation_state == RotationState.NONE:
            if self.angular_velocity < -SMALL_ANGULAR_VEL:
                self.rotation_state = RotationState.LEFT
            if self.angular_velocity > SMALL_ANGULAR_VEL:
                self.rotation_state = RotationState.RIGHT

    def increment_rot_counters(self, rotation_state: RotationState) -> None:
        """Increment rotation counters based on key-press info taken from `handle_input`."""
        if rotation_state == RotationState.LEFT:
            self.turn_L += ROT_STATE_DELTA
            self.turn_back_R += ROT_STATE_DELTA
        if rotation_state == RotationState.RIGHT:
            self.turn_R += ROT_STATE_DELTA
            self.turn_back_L += ROT_STATE_DELTA

    def step(self, dt: float) -> None:
        """Handle player rotation and call super step."""
        self.do_rotation_for_player()

        super().step(dt)

    def update_closest_enemy(self, enemy_ships: list[BulletEnemy]) -> None:
        """Find and store the closest enemy from the provided list."""
        self.closest_enemy = None
        self.closest_enemy_distance = float("inf")

        for enemy in enemy_ships:
            dist = self.distance_squared_to(enemy)
            if dist < self.closest_enemy_distance:
                self.closest_enemy = enemy
                self.closest_enemy_distance = dist

    def draw(self, camera: Camera, color: Color | None = None) -> None:
        """Draw the player ship and enemy indicator if applicable."""
        super().draw(camera, color)

        if self.closest_enemy:
            direction = self.closest_enemy.pos_relative_to(self)
            if direction.length_squared() > ARROW_THRESHOLD:
                arrow_pos = Pos(self, direction.normalize() * 60)
                camera.draw_arrow(ENEMY_INDICATOR_COLOR, arrow_pos, direction, 30)


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
    _SHIP_COLOR = ROCKET_ENEMY_COLOR
    _SHIP_GUN_COOLDOWN = ROCKET_RATE_OF_FIRE
    _SHIP_PROJECTILE_SPEED = ROCKET_RELEASE_SPEED

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new rocket relative to `self` targeting `self.target`."""
        return Rocket(self, pos, vel, self.projectile_color, self.target)


class MissileEnemy(BulletEnemy):
    """An enemy ship shooting powerful, smart, homing missiles, targeting a specific other ship."""

    # Class configuration
    _SHIP_COLOR = MISSILE_ENEMY_COLOR
    _SHIP_GUN_COOLDOWN = MISSILE_RATE_OF_FIRE
    _SHIP_PROJECTILE_SPEED = ROCKET_RELEASE_SPEED

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new missile relative to `self` targeting `self.target`."""
        return Missile(self, pos, vel, self.projectile_color, self.target)


class EnemyAI(BasicAI):
    """AI for enemy ships."""

    def __init__(self, ship: BulletEnemy) -> None:
        """Create a new AI controller."""
        super().__init__()
        self.ship: BulletEnemy = ship
        self.current_state = AIState.RAM
        self.can_see_target: bool = False
        self.low_health: bool = False

    def step(self, dt: float) -> None:
        """Transition state and apply appropriate behavior for different enemy types."""
        self.action_timer -= dt
        self.can_see_target: bool = self.ship.distance_squared_to(self.ship.target) < ENEMY_FIRE_RANGE_SQUARED

        if self.action_timer <= 0:
            self.action_timer = ENEMY_ACTION_TIMER
            self._transition()

        self.delta_target = self.ship.target.pos_relative_to(self.ship)
        self.delta_target_vel = self.ship.target.vel_relative_to(self.ship)

        self._match()
        self.ship.shooting = self.current_state in {AIState.ATTACK, AIState.AIM} and self.can_see_target

    def _transition(self) -> None:
        """Transition to a new state based on the Markov transition matrix."""
        self.low_health = self.ship.health < 55 + 0.6 * (self.ship.max_repair_health - 100)
        match (self.can_see_target, self.low_health):
            case (True, True):
                self.current_state = AIState.RETREAT
                return
            case (False, True):
                self.current_state = AIState.HEAL
                return
            case (True, False):
                matrix = _PLAYER_VISIBLE_MATRIX
            case (False, False):
                matrix = _DEFAULT_MATRIX

        # Extract probabilities for current state
        current_row: MatrixRow = matrix[self.current_state]
        states, probabilities = list(current_row.keys()), list(current_row.values())
        self.current_state = random.choices(states, probabilities)[0]

    def _match(self) -> None:
        """Match current state to behavior."""
        match self.current_state:
            case AIState.RAM:
                self._execute_ram()
                self.ship.thrust_state = (
                    ThrustState.FORWARD if self.delta_target_vel.length() < APPROACH_SPEED else ThrustState.NONE
                )
            case AIState.ATTACK:
                self._execute_attack()
            case AIState.AIM:
                self._execute_aim()
            case AIState.RETREAT:
                self._execute_retreat()
            case AIState.HEAL:
                self.ship.thrust_state = ThrustState.NONE
                self.ship.rotation_state = RotationState.NONE
                return

        self.ship.rotation_state = self.ship.calculate_rotation(self.desired_direction)

    def _execute_attack(self) -> None:
        """Return desired direction and thrust state for attack behavior."""
        self.ship.thrust_state = self._keep_distance()
        self.desired_direction = self.delta_target

    def _execute_aim(self) -> None:
        """Return desired direction and thrust state for aim behavior."""
        self.ship.thrust_state = self._keep_distance()

        # Quadratic equation coefficients:
        a = self.delta_target_vel.length_squared() - BULLET_RELEASE_SPEED**2
        b = 2 * self.delta_target.dot(self.delta_target_vel)
        c = self.delta_target.length_squared()

        discriminant = b**2 - 4 * a * c
        if discriminant < 0 or a == 0.0:
            self.desired_direction = self.delta_target
        else:
            # Calculate both solutions
            t1 = (-b + math.sqrt(discriminant)) / (2 * a)
            t2 = (-b - math.sqrt(discriminant)) / (2 * a)

            intercept_time = min(max(0, t1), max(0, t2))
            self.desired_direction = self.delta_target + self.delta_target_vel * intercept_time

    def _execute_retreat(self) -> None:
        """Return desired angle and thrust state for retreat behavior."""
        if not self.can_see_target:
            self.ship.thrust_state = ThrustState.NONE
            self.desired_direction = None
        else:
            self.ship.thrust_state = ThrustState.FORWARD
            self.desired_direction = -self.delta_target

    def _keep_distance(self) -> ThrustState:
        approach_speed = (-self.delta_target_vel).dot(self.delta_target.normalize())
        return (
            ThrustState.FORWARD
            if approach_speed < APPROACH_LOWER
            else (ThrustState.BACKWARD if approach_speed > APPROACH_UPPER else ThrustState.NONE)
        )
