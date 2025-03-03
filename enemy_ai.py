"""Enemy AI using Markov chains for state transitions."""

from __future__ import annotations

import random
from enum import Enum, auto
from typing import TYPE_CHECKING

import pygame
from pygame.math import Vector2 as Vec2

from constants import ATTACK_RANGE, ENEMY_VISUAL_RANGE, FLANK_DISTANCE, RETREAT_HEALTH

if TYPE_CHECKING:
    from ship import Ship

MARKOV_ENEMY_SPEED_THRESHOLD = 50


class AIState(Enum):
    """Possible AI states in the Markov chain."""

    HUNT = auto()  # Actively pursue player
    ATTACK = auto()  # Focus on firing at player
    EVADE = auto()  # Take evasive action
    FLANK = auto()  # Circle to player's side
    RETREAT = auto()  # Back away to recover


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
        self.current_state = AIState.HUNT
        self.state_timer = 0.0
        self.min_state_time = 0.5  # Minimum time to stay in a state

        # Flank variables
        self.flank_direction = 1  # 1 for clockwise, -1 for counter-clockwise

        # Previous positions for tracking
        self.prev_positions: list[tuple[float, float]] = []

    def _calculate_transition_matrix(self) -> dict[AIState, dict[AIState, float]]:
        """Calculate state transition probabilities based on current context.

        Returns:
            Dict[AIState, Dict[AIState, float]]: Nested dictionary mapping states to possible
                transitions and their probabilities.

        """
        # Get context information
        delta = self.target_ship.pos - self.ship.pos
        distance = delta.length() if delta.length() > 0 else 0.1
        health_ratio = self.ship.health / 100.0

        # Can we see the player?
        can_see_player = distance < ENEMY_VISUAL_RANGE
        in_attack_range = ATTACK_RANGE * 0.5 < distance < ATTACK_RANGE * 1.5
        low_health = health_ratio < (RETREAT_HEALTH / 100.0)

        # Base transition matrices for different contexts
        # Format: {from_state: {to_state: probability}}  # noqa: ERA001

        # Base matrix - default transitions
        matrix = {state: {other_state: 0.0 for other_state in AIState} for state in AIState}

        # Standard behavior matrix
        standard_matrix = {
            AIState.HUNT: {AIState.HUNT: 0.6, AIState.ATTACK: 0.3, AIState.FLANK: 0.1},
            AIState.ATTACK: {AIState.ATTACK: 0.7, AIState.EVADE: 0.1, AIState.FLANK: 0.2},
            AIState.EVADE: {AIState.EVADE: 0.3, AIState.FLANK: 0.3, AIState.ATTACK: 0.2, AIState.HUNT: 0.2},
            AIState.FLANK: {AIState.FLANK: 0.5, AIState.ATTACK: 0.3, AIState.HUNT: 0.2},
            AIState.RETREAT: {AIState.HUNT: 0.4, AIState.EVADE: 0.4, AIState.RETREAT: 0.2},
        }

        # Low health matrix - prioritize retreat
        low_health_matrix = {
            AIState.HUNT: {AIState.RETREAT: 0.3, AIState.HUNT: 0.3, AIState.ATTACK: 0.0},
            AIState.ATTACK: {AIState.RETREAT: 0.4, AIState.ATTACK: 0.3},
            AIState.EVADE: {AIState.RETREAT: 0.5, AIState.EVADE: 0.5},
            AIState.FLANK: {AIState.RETREAT: 0.3, AIState.FLANK: 0.2},
            AIState.RETREAT: {AIState.RETREAT: 0.7, AIState.EVADE: 0.3},
        }

        # Can't see player matrix - prioritize search
        player_visible_matrix = {
            AIState.HUNT: {AIState.HUNT: 0.2},
            AIState.ATTACK: {AIState.HUNT: 0.7, AIState.ATTACK: 0.3},
            AIState.FLANK: {AIState.HUNT: 0.7, AIState.FLANK: 0.3},
        }

        # First apply standard matrix
        for from_state, transitions in standard_matrix.items():
            for to_state, prob in transitions.items():
                # Apply probabilities conditionally
                if from_state == AIState.ATTACK and to_state == AIState.ATTACK and not in_attack_range:
                    continue
                if from_state == AIState.FLANK and to_state == AIState.ATTACK and not in_attack_range:
                    continue
                if (
                    from_state == AIState.EVADE
                    and to_state == AIState.ATTACK
                    and not (can_see_player and in_attack_range)
                ):
                    continue

                matrix[from_state][to_state] = prob

        # Apply context-specific matrices
        if low_health:
            for from_state, transitions in low_health_matrix.items():
                for to_state, prob in transitions.items():
                    matrix[from_state][to_state] = prob

        if not can_see_player:
            for from_state, transitions in standard_matrix.items():
                for to_state, prob in transitions.items():
                    matrix[from_state][to_state] = prob

        if can_see_player:
            for from_state, transitions in player_visible_matrix.items():
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
        next_state = random.choices(states, weights=probabilities, k=1)[0]

        # If state changes, reset timer and update behavior
        if next_state != self.current_state:
            self.current_state = next_state
            self.state_timer = self.min_state_time

            # Reset state-specific variables
            if next_state == AIState.FLANK:
                self.flank_direction = random.choice([1, -1])

    def _execute_hunt_behavior(self) -> Vec2:
        """Execute hunting behavior - direct pursuit of player.

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
        delta = self.target_ship.pos - self.ship.pos
        distance = delta.length() if delta.length() > 0 else 0.1

        # Try to maintain optimal attack distance
        desired_distance = ATTACK_RANGE

        # If too close, back up slightly
        if distance < desired_distance * 0.8:
            return -delta
        # If too far, move closer
        if distance > desired_distance * 1.2:
            return delta
        # Otherwise, match velocity to maintain distance
        return self.target_ship.vel - self.ship.vel

    def _execute_evade_behavior(self) -> Vec2:
        """Execute evasive behavior - erratic movement.

        Args:
            dt (float): Time delta

        Returns:
            Vec2: Desired force direction

        """
        # Get perpendicular direction to player
        delta = self.target_ship.pos - self.ship.pos
        perp = Vec2(-delta.y, delta.x).normalize()

        # Add some randomness for erratic movement
        random_direction = Vec2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()

        # Combine perpendicular and random for unpredictable evasion
        return perp + random_direction * 0.5

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
        # Direct retreat - opposite of direction to player
        away_direction = self.ship.pos - self.target_ship.pos

        # Add some jitter for less predictable retreat
        jitter = Vec2(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2))

        return away_direction + jitter

    def update(self, dt: float) -> None:
        """Update AI state and execute appropriate behavior.

        Args:
            dt (float): Time delta

        """
        # Record ship position for tracking
        self.prev_positions.append((self.ship.pos.x, self.ship.pos.y))
        if len(self.prev_positions) > 60:  # Keep last 60 positions (~1 second at 60 FPS)
            self.prev_positions.pop(0)

        # Update state timer
        self.state_timer -= dt

        # Check for state transition
        if self.state_timer <= 0:
            self._transition_state()

        # Execute behavior based on current state
        force_direction = Vec2(0, 0)

        # Determine shooting behavior
        delta = self.target_ship.pos - self.ship.pos
        distance = delta.length() if delta.length() > 0 else 0.1

        # Only shoot when in attack or flank states and within range
        self.ship.shooting = (
            self.current_state in (AIState.ATTACK, AIState.FLANK)
        ) and distance < ATTACK_RANGE * 1.5

        # Execute behavior based on current state
        match self.current_state:
            case AIState.HUNT:
                force_direction = self._execute_hunt_behavior()
            case AIState.ATTACK:
                force_direction = self._execute_attack_behavior()
            case AIState.EVADE:
                force_direction = self._execute_evade_behavior()
            case AIState.FLANK:
                force_direction = self._execute_flank_behavior()
            case AIState.RETREAT:
                force_direction = self._execute_retreat_behavior()

        # Set ship properties for movement
        if force_direction.length() > 0:
            # Calculate angle to face
            self.ship.angle = pygame.math.Vector2.as_polar(force_direction)[1]

            # Apply thrust in that direction
            normalized_direction = force_direction.normalize()
            self.ship.thruster_forward = True

            # Calculate dot product to slow down when needed
            vel_dot_dir = self.ship.vel.dot(normalized_direction)

            # If moving too fast in the desired direction, stop thrusting
            if vel_dot_dir > MARKOV_ENEMY_SPEED_THRESHOLD:  # Arbitrary speed threshold
                self.ship.thruster_forward = False

            # Use backward thrust if needed to slow down when moving away from target
            if self.current_state in (AIState.RETREAT, AIState.EVADE):
                if vel_dot_dir < -MARKOV_ENEMY_SPEED_THRESHOLD:
                    self.ship.thruster_backward = True
                else:
                    self.ship.thruster_backward = False
        else:
            self.ship.thruster_forward = False
            self.ship.thruster_backward = False

    def get_state_name(self) -> str:
        """Get the current state name for debugging.

        Returns:
            str: Current state name

        """
        return self.current_state.name
