"""Enemy AI using Markov chains for state transitions."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum, auto

from pygame import Color
from pygame.math import Vector2 as Vec2

from physics import Pos, PosVel
from projectiles import Bullet, Missile, Rocket
from ship import Ship, ShipConfig

ENEMY_FIRE_RANGE_SQUARED = 1700**2
ENEMY_ACTION_TIMER = 6
ROCKET_RELEASE_SPEED = 300.0
RETREAT_HEALTH_THRESHOLD = 30.0
DESIRED_APPROACH_SPEED = 500
ROCKET_RATE_OF_FIRE = 0.5
MISSILE_RATE_OF_FIRE = 3.0

# colors
BULLET_ENEMY_COLOR = Color("lightblue")
ROCKET_ENEMY_COLOR = Color("purple")
MISSILE_ENEMY_COLOR = Color("lime")
MARKOV_ENEMY_COLOR = Color("red")


class AIState(Enum):
    """Possible AI states in the Markov chain."""

    SEARCH = auto()
    ATTACK = auto()
    AIM = auto()
    RETREAT = auto()


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


class EnemyAI:
    """Markov chain-based AI for enemy ships."""

    def __init__(self, ship: Ship, target_ship: Ship) -> None:
        """Create a new AI controller for the ship `ship`, targeting `target_ship`."""
        self.ship = ship
        self.target = target_ship
        self.current_state = AIState.SEARCH
        self.action_timer = 0.0
        self.projectile_speed = ship.projectile_speed
        self.gun_cooldown = ship.gun_cooldown
        self.can_see_target = self.ship.distance_squared_to(self.target) < ENEMY_FIRE_RANGE_SQUARED

    def _transition_state(self) -> None:
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

    def _execute_search_behavior(self) -> Vec2:
        """Return force required for the search-behavior."""
        delta_target_ship = self.target.pos_relative_to(self.ship)
        relative_velocity = self.ship.vel_relative_to(self.target)

        if delta_target_ship == Vec2(0, 0):
            return Vec2(0, 0)
        approach_direction = delta_target_ship.normalize()
        desired_relative_vel = approach_direction * DESIRED_APPROACH_SPEED
        # Force required to change from current relative velocity to desired relative velocity
        return desired_relative_vel - relative_velocity

    def _execute_attack_behavior(self) -> Vec2:
        """Return force required for the attack-behavior."""
        return self.target.pos_relative_to(self.ship)

    def _execute_aim_behavior(self) -> Vec2:
        """Return force required for the aim-behavior."""
        # Relative position and velocity
        relative_pos = self.target.pos_relative_to(self.ship)
        relative_vel = self.target.vel_relative_to(self.ship)

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
        a = relative_vel.length_squared() - self.projectile_speed**2
        b = 2 * relative_pos.dot(relative_vel)
        c = relative_pos.length_squared()

        # Standard quadratic formula
        discriminant = b**2 - 4 * a * c

        if discriminant < 0:
            # No real solution exists (target unreachable)
            # Fall back to simpler approach
            force = relative_pos + relative_vel * (relative_pos.length() / self.projectile_speed)
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
            intercept_time = relative_pos.length() / self.projectile_speed

        # Calculate predicted position
        if intercept_time <= 0:
            # Fallback if no solution found
            return relative_pos.normalize()

        # Now calculate what direction the bullet must be fired in
        return (relative_pos + relative_vel * intercept_time) / (self.projectile_speed * intercept_time)

    def _execute_retreat_behavior(self) -> Vec2:
        """Return force required for the retreat-behavior."""
        delta = self.ship.pos_relative_to(self.target)
        if not self.can_see_target:
            return Vec2(0, 0)
        return delta

    def _accelerate_randomly(self) -> Vec2:
        return self.seek_towards.pos_relative_to(self.ship)

    def update(self, dt: float) -> None:
        """Update AI state and execute appropriate behavior."""
        self.update_all(dt)

        if self.action_timer <= 0:
            self._transition_state()
            self.action_timer = ENEMY_ACTION_TIMER

        # Only shoot when in attack or aim states and within range
        self.ship.shooting = (self.current_state in {AIState.ATTACK, AIState.AIM}) and self.can_see_target

        # Execute behavior based on current state
        match self.current_state:
            case AIState.SEARCH:
                force_direction = self._execute_search_behavior()
            case AIState.ATTACK:
                force_direction = self._execute_attack_behavior()
            case AIState.AIM:
                force_direction = self._execute_aim_behavior()
            case AIState.RETREAT:
                force_direction = self._execute_retreat_behavior()

        if force_direction != Vec2(0, 0):
            force = force_direction.normalize() * self.ship.thrust
            self.ship.apply_force(force, dt)

        self.ship.angle = math.degrees(math.atan2(force_direction.y, force_direction.x))

    def update_simple(self, dt: float) -> None:
        """Execute `self`'s ai."""
        self.update_all(dt)

        if self.action_timer <= 0:
            if self.can_see_target:
                self.current_action = BulletEnemy.Action.ATTACK
            else:
                self.current_action = BulletEnemy.Action.accelerate_randomly

                if self.current_action == BulletEnemy.Action.accelerate_randomly:
                    # Accelerate towards a random point near the player.
                    distance_to_target = self.target.distance_to(self.ship)
                    # I think (but haven't proved) that, by choosing the standard-deviation proportional
                    # to the distance to the player, we should eventually find a non-accelerating player.
                    random_x = random.gauss(sigma=distance_to_target)
                    random_y = random.gauss(sigma=distance_to_target)
                    self.seek_towards = Pos(self.target, Vec2(random_x, random_y))

            self.action_timer = ENEMY_ACTION_TIMER

        match self.current_action:
            case BulletEnemy.Action.ATTACK:
                force_direction = self._execute_attack_behavior()
            case BulletEnemy.Action.accelerate_randomly:
                force_direction = self._accelerate_randomly()

        if force_direction != Vec2(0, 0):
            force = force_direction.normalize() * self.ship.thrust
            self.ship.apply_force(force, dt)

        self.ship.shooting = self.current_action == BulletEnemy.Action.ATTACK and self.can_see_target
        self.ship.angle = math.degrees(math.atan2(force_direction.y, force_direction.x))

    def update_all(self, dt: float) -> None:
        """Update all ais use."""
        self.action_timer -= dt


@dataclass(kw_only=True)
class EnemyConfig(ShipConfig):
    """Configuration for an enemy-spaceship.

    Attributes:
        relative_pos (Vec2): Relative position of the enemy-spaceship
        relative_vel (Vec2): Relative velocity of the enemy-spaceship
        color (Color): Color of the player-spaceship
        gun_cooldown (float): Minimum time between shots
        projectile_speed (float): Speed at which projectiles are fired
        target_ship (Ship): Ship to target

    """

    target_ship: Ship


class BulletEnemy(Ship):
    """An enemy ship, targeting a specific other ship."""

    SHIP_COLOR = BULLET_ENEMY_COLOR

    class Action(Enum):
        """Actions the BulletEnemy might take."""

        ATTACK = auto()
        accelerate_randomly = auto()

    def __init__(self, relative_to: PosVel, config: EnemyConfig) -> None:
        """Create a new enemy ship."""
        super().__init__(
            relative_to,
            ShipConfig(
                relative_pos=config.relative_pos,
                relative_vel=config.relative_vel,
                color=self.SHIP_COLOR,
            ),
        )

        self.target: Ship = config.target_ship

        self.action_timer: float = 0.0
        self.current_action: BulletEnemy.Action = BulletEnemy.Action.accelerate_randomly
        self.projectiles: list[Bullet] = []
        self.seek_towards: Pos = Pos(self, Vec2(0, 0))
        self.projectile_speed: float = config.projectile_speed
        self.ai = EnemyAI(self, config.target_ship)

    def step(self, dt: float) -> None:
        """Apply physics and "AI" to `self`."""
        self.ai.update_simple(dt)
        super().step(dt)


class MarkovEnemy(BulletEnemy):
    """An enemy ship using Markov chain AI for more sophisticated behavior."""

    # Override class configuration for MarkovEnemy
    SHIP_COLOR = MARKOV_ENEMY_COLOR

    def __init__(self, relative_to: PosVel, config: EnemyConfig) -> None:
        """Create a new Markov-based enemy ship."""
        super().__init__(relative_to, config)
        self.ai = EnemyAI(self, config.target_ship)

    def step(self, dt: float) -> None:
        """Apply physics and AI to this ship."""
        self.ai.update(dt)
        Ship.step(self, dt)


class RocketEnemy(BulletEnemy):
    """An enemy ship shooting rockets, targeting a specific other ship."""

    # Override class configuration for RocketEnemy
    SHIP_COLOR = ROCKET_ENEMY_COLOR
    SHIP_GUN_COOLDOWN = ROCKET_RATE_OF_FIRE
    SHIP_PROJECTILE_SPEED = ROCKET_RELEASE_SPEED

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new rocket relative to `self` targeting `self.target`."""
        return Rocket(self, pos, vel, self.projectile_color, self.target)


class MissileEnemy(BulletEnemy):
    """An enemy ship shooting powerful, smart, homing missiles, targeting a specific other ship."""

    # Override class configuration for MissileEnemy
    SHIP_COLOR = MISSILE_ENEMY_COLOR
    SHIP_GUN_COOLDOWN = MISSILE_RATE_OF_FIRE
    SHIP_PROJECTILE_SPEED = ROCKET_RELEASE_SPEED  # Using rocket speed for missiles

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new missile relative to `self` targeting `self.target`."""
        return Missile(self, pos, vel, self.projectile_color, self.target)
