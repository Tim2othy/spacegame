"""Enemy AI using Markov chains for state transitions."""

from __future__ import annotations

import math
import random
from enum import Enum, auto
from typing import TYPE_CHECKING

from pygame.math import Vector2 as Vec2

from constants import (
    BULLET_RELEASE_SPEED,
    DESIRED_APPROACH_SPEED,
    ENEMY_ACCELERATE_LESS,
    ENEMY_ACTION_TIMER,
    ENEMY_FIRE_RANGE,
    ENEMY_VISUAL_RANGE,
    FLANK_DISTANCE,
    RETREAT_HEALTH,
)

if TYPE_CHECKING:
    from ship import Ship


class AIState(Enum):
    """Possible AI states in the Markov chain."""

    SEARCH = auto()
    ATTACK = auto()
    FLANK = auto()
    RETREAT = auto()


class MarkovAI:
    """Markov chain-based AI for enemy ships."""

    def __init__(self, ship: Ship, target_ship: Ship) -> None:
        """Create a new AI controller.

        Args:
            ship (Ship): The ship to control
            target_ship (Ship): The ship to target (usually player)

        """
        self.ship = ship
        self.target_ship = target_ship
        self.current_state = AIState.SEARCH
        self.action_timer = 0.0
        self.flank_direction = 1

    def _calculate_transition_matrix(self) -> dict[AIState, dict[AIState, float]]:
        """Calculate state transition probabilities based on current context.

        Returns:
            Dict[AIState, Dict[AIState, float]]: Nested dictionary mapping states to possible
                transitions and their probabilities.

        """
        # Get context information
        delta = self.target_ship.pos - self.ship.pos
        distance = delta.magnitude() if delta != Vec2(EPSILON, EPSILON) else EPSILON
        # TODO(Tim2othy) do this everywhere else also

        can_see_player = distance < ENEMY_VISUAL_RANGE
        low_health = self.ship.health < RETREAT_HEALTH

        matrix = {state: {other_state: 0.0 for other_state in AIState} for state in AIState}

        standard_matrix = {
            AIState.SEARCH: {AIState.SEARCH: 1},
            AIState.ATTACK: {AIState.SEARCH: 1},
            AIState.FLANK: {AIState.SEARCH: 1},
            AIState.RETREAT: {AIState.SEARCH: 1},
        }

        low_health_matrix = {
            AIState.SEARCH: {AIState.SEARCH: 0.9, AIState.RETREAT: 0.1},
            AIState.ATTACK: {AIState.RETREAT: 1.0},
            AIState.FLANK: {AIState.RETREAT: 1.0},
            AIState.RETREAT: {AIState.SEARCH: 0.2, AIState.RETREAT: 0.8},
        }

        player_visible_matrix = {
            AIState.SEARCH: {AIState.ATTACK: 1.0},
            AIState.ATTACK: {AIState.ATTACK: 0.8, AIState.FLANK: 0.2},
            AIState.FLANK: {AIState.ATTACK: 0.4, AIState.FLANK: 0.4, AIState.RETREAT: 0.2},
            AIState.RETREAT: {AIState.ATTACK: 1.0},
        }

        low_health_and_player_visible_matrix = {
            AIState.SEARCH: {AIState.ATTACK: 0.2, AIState.FLANK: 0.6, AIState.RETREAT: 0.2},
            AIState.ATTACK: {AIState.RETREAT: 0.8, AIState.ATTACK: 0.1, AIState.FLANK: 0.1},
            AIState.FLANK: {AIState.ATTACK: 0.1, AIState.RETREAT: 0.1, AIState.FLANK: 0.8},
            AIState.RETREAT: {AIState.ATTACK: 0.1, AIState.RETREAT: 0.8, AIState.FLANK: 0.1},
        }

        if can_see_player and low_health:
            active_matrix = low_health_and_player_visible_matrix
        elif low_health:
            active_matrix = low_health_matrix
        elif can_see_player:
            active_matrix = player_visible_matrix
        else:
            active_matrix = standard_matrix

        # Apply selected matrix
        for from_state, transitions in active_matrix.items():
            for to_state, prob in transitions.items():
                matrix[from_state][to_state] = prob

        # Normalize probabilities to ensure they sum to 1.0
        for state in AIState:
            total = sum(matrix[state].values())
            if total > 0:
                for next_state in AIState:
                    matrix[state][next_state] /= total

        return matrix

    def _transition_state(self) -> None:
        """Transition to a new state based on the Markov transition matrix."""
        matrix = self._calculate_transition_matrix()

        # Extract probabilities for current state
        probabilities = list(matrix[self.current_state].values())
        states = list(AIState)
        self.current_state = random.choices(states, probabilities)[0]

        if self.current_state == AIState.FLANK:
            self.flank_direction = random.choice([1, -1])

        """
        For the next 4 functions:

        Args:
            dt (float): Passed time

        Returns:
            Vec2: Force direction

        """

    def _execute_search_behavior(self) -> Vec2:
        """Execute searching behavior respecting relativity principles."""
        delta_target_ship = self.target_ship.pos - self.ship.pos
        relative_velocity = self.ship.vel - self.target_ship.vel

        if delta_target_ship.magnitude() > EPSILON:
            approach_direction = delta_target_ship.normalize()
            desired_relative_vel = approach_direction * DESIRED_APPROACH_SPEED
            # Force required to change from current relative velocity to desired relative velocity
            force_direction = desired_relative_vel - relative_velocity
        else:
            force_direction = Vec2(EPSILON, EPSILON)

        if force_direction.magnitude() < EPSILON:
            force_direction = Vec2(EPSILON, EPSILON)

        return force_direction

    def _execute_attack_behavior(self) -> Vec2:
        """Execute attack behavior."""
        return self.target_ship.pos - self.ship.pos

    def _execute_flank_behavior(self) -> Vec2:
        """Execute behavior with predictive aiming to hit moving targets."""
        # Current positions and velocities
        ship_pos = self.ship.pos
        ship_vel = self.ship.vel
        target_pos = self.target_ship.pos
        target_vel = self.target_ship.vel
        # Relative position and velocity
        relative_pos = target_pos - ship_pos
        relative_vel = target_vel - ship_vel

        """
        We need to find the direction where:
        # target_pos + target_vel*t = ship_pos + ship_vel*t + direction*bullet_speed*t

        Solve quadratic equation for intercept time:
        |relative_pos + relative_vel*t| = bullet_speed*t

        This expands to:
        |relative_pos|^2 + 2*relative_pos·relative_vel*t + (|relative_vel|^2 - bullet_speed^2)*t^2 = 0
        """

        # Quadratic equation coefficients:
        a = relative_vel.magnitude_squared() - BULLET_RELEASE_SPEED**2
        b = 2 * relative_pos.dot(relative_vel)
        c = relative_pos.magnitude_squared()

        # Standard quadratic formula
        discriminant = b**2 - 4 * a * c

        if discriminant < 0:
            # No real solution exists (target unreachable)
            # Fall back to simpler approach
            return (
                relative_pos + relative_vel * (relative_pos.magnitude() / BULLET_RELEASE_SPEED)
            ).normalize()

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
            intercept_time = relative_pos.magnitude() / BULLET_RELEASE_SPEED

        # Calculate predicted position
        if intercept_time <= 0:
            # Fallback if no solution found
            return relative_pos.normalize()

        # Calculate where to aim to hit the target
        target_future_pos = target_pos + target_vel * intercept_time

        # Now calculate what direction the bullet must be fired in
        aim_direction = (target_future_pos - ship_pos - ship_vel * intercept_time) / (
            BULLET_RELEASE_SPEED * intercept_time
        )
        # Normalize to get pure direction
        if aim_direction.magnitude() > EPSILON:
            aim_direction = aim_direction.normalize()
        else:
            # Fallback if direction calculation fails
            aim_direction = relative_pos.normalize()

        return aim_direction

    def _execute_retreat_behavior(self) -> Vec2:
        """Execute retreat behavior - move away from player."""
        return self.ship.pos - self.target_ship.pos

    def update(self, dt: float) -> None:
        """Update AI state and execute appropriate behavior.

        Args:
            dt (float): Passed time

        """
        self.action_timer -= dt

        if self.action_timer <= 0:
            self._transition_state()
            health_status = "LOW HEALTH" if self.ship.health < RETREAT_HEALTH else "HEALTHY"
            print(f"State={self.current_state.name}, Health={self.ship.health} ({health_status})")
            self.action_timer = ENEMY_ACTION_TIMER

        # Only shoot when in attack or flank states and within range
        delta = self.target_ship.pos - self.ship.pos
        distance = delta.length() if delta.length() > 0 else 0.1
        self.ship.shooting = (
            self.current_state in (AIState.ATTACK, AIState.FLANK)
        ) and distance < ENEMY_FIRE_RANGE

        # Execute behavior based on current state
        match self.current_state:
            case AIState.SEARCH:
                force_direction = self._execute_search_behavior()
            case AIState.ATTACK:
                force_direction = self._execute_attack_behavior()
            case AIState.FLANK:
                force_direction = self._execute_flank_behavior()
            case AIState.RETREAT:
                force_direction = self._execute_retreat_behavior()

        if force_direction.magnitude() != 0:
            force = force_direction.normalize() * self.ship.thrust
            if (
                self.current_state == AIState.ATTACK
                and (self.ship.vel - self.target_ship.vel).magnitude() < ENEMY_ACCELERATE_LESS
            ):
                force *= 0.3
            self.ship.apply_force(force, dt)

        self.ship.angle = math.degrees(math.atan2(force_direction.y, force_direction.x))
