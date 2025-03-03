"""Enemy AI using Markov chains for state transitions."""

from __future__ import annotations

import math
import random
from enum import Enum, auto
from typing import TYPE_CHECKING

from pygame.math import Vector2 as Vec2

from constants import ENEMY_FIRE_RANGE, ENEMY_VISUAL_RANGE, EPSILON, FLANK_DISTANCE, RETREAT_HEALTH

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
        self.state_timer = 0.0
        self.min_state_time = 0.5  # Minimum time to stay in a state
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
            AIState.SEARCH: {AIState.SEARCH: 1.0},
            AIState.ATTACK: {AIState.RETREAT: 1.0},
            AIState.FLANK: {AIState.RETREAT: 0.8, AIState.FLANK: 0.2},
            AIState.RETREAT: {AIState.RETREAT: 0.7, AIState.SEARCH: 0.3},
        }

        player_visible_matrix = {
            AIState.SEARCH: {AIState.ATTACK: 1.0},
            AIState.ATTACK: {AIState.ATTACK: 1.0, AIState.FLANK: 0.0},
            AIState.FLANK: {AIState.ATTACK: 0.8, AIState.FLANK: 0.1, AIState.RETREAT: 0.1},
            AIState.RETREAT: {AIState.ATTACK: 1.0},
        }

        low_health_and_player_visible_matrix = {
            AIState.SEARCH: {AIState.RETREAT: 0.8, AIState.ATTACK: 0.1, AIState.FLANK: 0.1},
            AIState.ATTACK: {AIState.RETREAT: 0.8, AIState.ATTACK: 0.1, AIState.FLANK: 0.1},
            AIState.FLANK: {AIState.RETREAT: 0.9, AIState.FLANK: 0.1},
            AIState.RETREAT: {AIState.RETREAT: 0.9, AIState.FLANK: 0.1},
        }

        # Apply matrices based on priority
        if can_see_player and low_health:
            active_matrix = low_health_and_player_visible_matrix
        elif low_health:
            active_matrix = low_health_matrix
        elif can_see_player:
            active_matrix = player_visible_matrix
        else:
            active_matrix = standard_matrix

        # Apply  selected matrix
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

        # Choose next state based on probabilities
        next_state = random.choices(states, probabilities)[0]

        # If state changes, reset timer and update behavior
        if next_state != self.current_state:
            self.current_state = next_state
            self.state_timer = self.min_state_time

            # Reset state-specific variables
            if next_state == AIState.FLANK:
                self.flank_direction = random.choice([1, -1])

    def _execute_search_behavior(self) -> Vec2:
        """Execute searching behavior - direct pursuit of player.

        Args:
            dt (float): Time delta

        Returns:
            Vec2: Desired force direction

        """
        return self.target_ship.pos - self.ship.pos

    def _execute_attack_behavior(self) -> Vec2:
        """Execute attack behavior - maintain optimal firing distance.

        Args:
            dt (float): Time delta

        Returns:
            Vec2: Desired force direction

        """
        return self.target_ship.pos - self.ship.pos

    def _execute_flank_behavior(self) -> Vec2:
        """Execute flanking behavior - circle around player.

        Args:
            dt (float): Time delta

        Returns:
            Vec2: Desired force direction

        """
        delta = self.target_ship.pos - self.ship.pos
        distance = delta.length() if delta.length() > 0 else 0.1

        # Calculate tangential direction for circling
        # Rotate 90 degrees (clockwise or counter-clockwise)
        orbit_dir = Vec2(-delta.y * self.flank_direction, delta.x * self.flank_direction).normalize()

        # Adjust distance if needed
        radial_dir = Vec2(0, 0)
        if distance > FLANK_DISTANCE * 1.2:
            # Too far, move closer
            radial_dir = delta.normalize()
        elif distance < FLANK_DISTANCE * 0.8:
            # Too close, move away
            radial_dir = -delta.normalize()

        # Combined direction: mostly orbit with minor radial adjustment
        return orbit_dir * 0.8 + radial_dir * 0.2

    def _execute_retreat_behavior(self) -> Vec2:
        """Execute retreat behavior - move away from player.

        Args:
            dt (float): Time delta

        Returns:
            Vec2: Desired force direction

        """
        return self.ship.pos - self.target_ship.pos

    def update(self, dt: float) -> None:
        """Update AI state and execute appropriate behavior.

        Args:
            dt (float): Time delta

        """
        # Update state timer
        self.state_timer -= dt

        # Check for state transition
        if self.state_timer <= 0:
            self._transition_state()
            health_status = "LOW HEALTH" if self.ship.health < RETREAT_HEALTH else "HEALTHY"
            print(f"State={self.current_state.name}, Health={self.ship.health} ({health_status})")

        # Determine shooting behavior
        delta = self.target_ship.pos - self.ship.pos
        distance = delta.length() if delta.length() > 0 else 0.1

        # Only shoot when in attack or flank states and within range
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
            self.ship.apply_force(force, dt)

        self.ship.angle = math.degrees(math.atan2(force_direction.y, force_direction.x))
