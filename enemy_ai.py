"""Enemy AI using Markov chains for state transitions."""

from __future__ import annotations

import random
from enum import Enum, auto
from typing import TYPE_CHECKING

import pygame
from pygame.math import Vector2 as Vec2

if TYPE_CHECKING:
    from ship import Ship

# Constants for state transitions
VISUAL_RANGE = 300.0  # Maximum distance to see player
ATTACK_RANGE = 150.0  # Optimal firing range
RETREAT_HEALTH = 30.0  # Health threshold to consider retreating
FLANK_DISTANCE = 100.0  # Distance to maintain when flanking
PATROL_RADIUS = 200.0  # Radius of patrol pattern


class AIState(Enum):
    """Possible AI states in the Markov chain."""

    HUNT = auto()  # Actively pursue player
    ATTACK = auto()  # Focus on firing at player
    EVADE = auto()  # Take evasive action
    FLANK = auto()  # Circle to player's side
    PATROL = auto()  # Search when player not visible
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
        self.current_state = AIState.PATROL
        self.state_timer = 0.0
        self.min_state_time = 0.5  # Minimum time to stay in a state

        # Patrol pattern variables
        self.patrol_points: list[Vec2] = []
        self.current_patrol_point = 0
        self._generate_patrol_pattern()

        # Flank variables
        self.flank_direction = 1  # 1 for clockwise, -1 for counter-clockwise

        # Previous positions for tracking
        self.prev_positions: list[tuple[float, float]] = []

    def _generate_patrol_pattern(self) -> None:
        """Generate a random patrol pattern around the current position."""
        center = self.ship.pos
        self.patrol_points = []

        # Create a somewhat random patrol pattern
        num_points = random.randint(3, 6)
        for i in range(num_points):
            angle = i * (360 / num_points)
            distance = random.uniform(0.5, 1.0) * PATROL_RADIUS
            offset = Vec2()
            offset.from_polar((distance, angle))
            self.patrol_points.append(center + offset)

    def _calculate_transition_matrix(self) -> dict[AIState, dict[AIState, float]]:
        """Calculate state transition probabilities based on current context.

        Returns:
            Dict[AIState, Dict[AIState, float]]: Nested dictionary mapping states to possible
                transitions and their probabilities.

        """
        # Initialize the transition matrix with zeroes
        matrix = {state: {other_state: 0.0 for other_state in AIState} for state in AIState}

        # Get context information
        delta = self.target_ship.pos - self.ship.pos
        distance = delta.length() if delta.length() > 0 else 0.1
        health_ratio = self.ship.health / 100.0  # Assuming max health is 100

        # Can we see the player?
        can_see_player = distance < VISUAL_RANGE

        # Is the player in attack range?
        in_attack_range = ATTACK_RANGE * 0.5 < distance < ATTACK_RANGE * 1.5

        # Are we at low health?
        low_health = health_ratio < (RETREAT_HEALTH / 100.0)

        # Calculate transition probabilities based on context
        # From HUNT state
        if can_see_player:
            matrix[AIState.HUNT][AIState.HUNT] = 0.6
            matrix[AIState.HUNT][AIState.ATTACK] = 0.3 if in_attack_range else 0.0
            matrix[AIState.HUNT][AIState.FLANK] = 0.1
            if low_health:
                matrix[AIState.HUNT][AIState.RETREAT] = 0.3
                matrix[AIState.HUNT][AIState.HUNT] = 0.3
        else:
            matrix[AIState.HUNT][AIState.PATROL] = 0.8
            matrix[AIState.HUNT][AIState.HUNT] = 0.2

        # From ATTACK state
        if can_see_player and in_attack_range:
            matrix[AIState.ATTACK][AIState.ATTACK] = 0.7
            matrix[AIState.ATTACK][AIState.EVADE] = 0.1
            matrix[AIState.ATTACK][AIState.FLANK] = 0.2
            if low_health:
                matrix[AIState.ATTACK][AIState.RETREAT] = 0.4
                matrix[AIState.ATTACK][AIState.ATTACK] = 0.3
        else:
            matrix[AIState.ATTACK][AIState.HUNT] = 0.7
            matrix[AIState.ATTACK][AIState.ATTACK] = 0.3

        # From EVADE state
        matrix[AIState.EVADE][AIState.EVADE] = 0.3
        matrix[AIState.EVADE][AIState.FLANK] = 0.3
        matrix[AIState.EVADE][AIState.ATTACK] = 0.2 if (can_see_player and in_attack_range) else 0.0
        matrix[AIState.EVADE][AIState.HUNT] = 0.2
        if low_health:
            matrix[AIState.EVADE][AIState.RETREAT] = 0.5
            matrix[AIState.EVADE][AIState.EVADE] = 0.5

        # From FLANK state
        if can_see_player:
            matrix[AIState.FLANK][AIState.FLANK] = 0.5
            matrix[AIState.FLANK][AIState.ATTACK] = 0.3 if in_attack_range else 0.0
            matrix[AIState.FLANK][AIState.HUNT] = 0.2
            if low_health:
                matrix[AIState.FLANK][AIState.RETREAT] = 0.3
                matrix[AIState.FLANK][AIState.FLANK] = 0.2
        else:
            matrix[AIState.FLANK][AIState.HUNT] = 0.7
            matrix[AIState.FLANK][AIState.PATROL] = 0.3

        # From PATROL state
        if can_see_player:
            matrix[AIState.PATROL][AIState.HUNT] = 0.8
            matrix[AIState.PATROL][AIState.PATROL] = 0.2
        else:
            matrix[AIState.PATROL][AIState.PATROL] = 0.9
            matrix[AIState.PATROL][AIState.HUNT] = 0.1

        # From RETREAT state
        if low_health:
            matrix[AIState.RETREAT][AIState.RETREAT] = 0.7
            matrix[AIState.RETREAT][AIState.EVADE] = 0.3
        else:
            matrix[AIState.RETREAT][AIState.HUNT] = 0.4
            matrix[AIState.RETREAT][AIState.EVADE] = 0.4
            matrix[AIState.RETREAT][AIState.PATROL] = 0.2

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
            if next_state == AIState.PATROL:
                self._generate_patrol_pattern()
            elif next_state == AIState.FLANK:
                self.flank_direction = 1 if random.random() > 0.5 else -1

    def _execute_hunt_behavior(self, dt: float) -> Vec2:
        """Execute hunting behavior - direct pursuit of player.

        Args:
            dt (float): Time delta

        Returns:
            Vec2: Desired force direction

        """
        return self.target_ship.pos - self.ship.pos

    def _execute_attack_behavior(self, dt: float) -> Vec2:
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

    def _execute_evade_behavior(self, dt: float) -> Vec2:
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

    def _execute_flank_behavior(self, dt: float) -> Vec2:
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

    def _execute_patrol_behavior(self, dt: float) -> Vec2:
        """Execute patrol behavior - follow patrol pattern.

        Args:
            dt (float): Time delta

        Returns:
            Vec2: Desired force direction

        """
        if not self.patrol_points:
            self._generate_patrol_pattern()

        # Move toward current patrol point
        current_point = self.patrol_points[self.current_patrol_point]
        direction = current_point - self.ship.pos

        # If reached the point, move to next point
        if direction.length_squared() < 100:  # Within 10 units
            self.current_patrol_point = (self.current_patrol_point + 1) % len(self.patrol_points)

        return direction

    def _execute_retreat_behavior(self, dt: float) -> Vec2:
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
                force_direction = self._execute_hunt_behavior(dt)
            case AIState.ATTACK:
                force_direction = self._execute_attack_behavior(dt)
            case AIState.EVADE:
                force_direction = self._execute_evade_behavior(dt)
            case AIState.FLANK:
                force_direction = self._execute_flank_behavior(dt)
            case AIState.PATROL:
                force_direction = self._execute_patrol_behavior(dt)
            case AIState.RETREAT:
                force_direction = self._execute_retreat_behavior(dt)

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
            if vel_dot_dir > 50:  # Arbitrary speed threshold
                self.ship.thruster_forward = False

            # Use backward thrust if needed to slow down when moving away from target
            if self.current_state in (AIState.RETREAT, AIState.EVADE):
                if vel_dot_dir < -50:
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
