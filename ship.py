"""Spaceships, shooting through space."""

from __future__ import annotations

import math
import random
from enum import Enum
from typing import TYPE_CHECKING

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from constants import (
    BULLET_RELEASE_SPEED,
    ENEMY_ACTION_TIMER,
    ENEMY_ACTION_WEIGHTS,
    ENEMY_FIRE_RANGE_SQUARED,
    ENEMY_VISUAL_RANGE_SQUARED,
    FLARE_MEAN_RELEASE_SPEED,
    FLARE_SD_RELEASE_SPEED,
    PLAYER_COLOR,
    ROCKET_RELEASE_SPEED,
    THRUST_COLOR,
    generate_complementary_color,
)
from enemy_ai import MarkovAI
from physics import Disk
from projectiles import Bullet, Flare, Missile, Rocket

if TYPE_CHECKING:
    from camera import Camera

SHIP_SIZE = 10.0

# Rate of fire
BULLET_ROF = 0.08
ROCKET_ROF = 0.5
MISSILE_ROF = 3.0
FLARE_ROF = 5.0

GRAY = Color("gray")
BULLET_ENEMY_COLOR = Color("lightblue")
ROCKET_ENEMY_COLOR = Color("purple")
MISSILE_ENEMY_COLOR = Color("lime")
MARKOV_ENEMY_COLOR = Color("red")
HEALTH = 100
# ship constants
GUNBARREL_LENGTH = 3  # relative to radius
GUNBARREL_WIDTH = 0.5  # relative to radius

DAMAGE_INDICATOR_TIME = 1
"""Time (in seconds) a ship should flash red after taking damage"""
NUM_FLARES = 40
SD_FLARE_ANGLE = 25


class Ship(Disk):
    """A basic spaceship."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        size: float = SHIP_SIZE,
        color: Color = GRAY,
        gun_cooldown: float = BULLET_ROF,
        projectile_speed: float = BULLET_RELEASE_SPEED,
    ) -> None:
        """Create a new spaceship.

        Raises a ValueError if `gun_cooldown` is not strictly positive.

        Args:
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            size (float): Radius of disk-body
            color (Color): Material and bullet color
            gun_cooldown (float): Minimum time between shots
            projectile_speed (float): Speed at which projectiles are fired

        >>> Ship(Vec2(), Vec2(), gun_cooldown=1)
        <ship.Ship object at ...>
        >>> Ship(Vec2(), Vec2(), gun_cooldown=-1)
        Traceback (most recent call last):
            ...
        ValueError

        """
        super().__init__(pos, vel, size, color)
        self.size: float = size

        self.health: float = HEALTH
        self.damage_indicator_timer: float = 0

        self.projectiles: list[Bullet] = []
        if not gun_cooldown > 0:
            raise ValueError
        self._gun_cooldown: float = gun_cooldown
        self._flare_cooldown: float = FLARE_ROF
        self.gun_cooldown_timer: float = 0
        self.flare_cooldown_timer: float = 0
        self.shooting: bool = False
        self.releasing_flares: bool = False
        self.projectile_speed: float = projectile_speed

        self.projectile_color = generate_complementary_color(color)

        self.angle: float = 0
        self.thrust: float = 250 * self.mass
        self.rotation_thrust: float = 0.15 * self.mass
        self.thruster_rot_left: bool = False
        self.thruster_rot_right: bool = False
        self.thruster_backward: bool = False
        self.thruster_forward: bool = False

    def get_faced_direction(self) -> Vec2:
        """Get `self`'s faced direction from its `angle`.

        Returns:
            Vec2: Faced direction, normalized

        """
        # For unknown reasons, `Vec2.from_polar((self.angle, 1))` won't work.
        direction = Vec2()
        direction.from_polar((1, self.angle))
        return direction

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new bullet at `pos` with velocity `vel`."""
        return Bullet(pos, vel, self.projectile_color)

    def new_flare(self, pos: Vec2, vel: Vec2) -> Flare:
        """Create a new Flare at `pos` with velocity `vel`."""
        return Flare(pos, vel)

    def shoot(self, dt: float) -> None:
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
                bullet_vel = self._vel + forward * self.projectile_speed

                # When multiple shots are fired per frame,
                # but we spawn them all at the end of the gunbarrel,
                # they'd all spawn on top of each other, see issue #47.
                # To mitigate this, we offset the spawn-position
                # by the (time since the shot was fired) * bullet_vel.
                # The time since the shot was fired is simply the
                # negative of the current gun_cooldown.
                gunbarrel_offset = forward * self.radius * GUNBARREL_LENGTH
                bullet_pos = self._pos + gunbarrel_offset - self.gun_cooldown_timer * bullet_vel

                self.projectiles.append(self.new_bullet(bullet_pos, bullet_vel))
                self.gun_cooldown_timer += self._gun_cooldown

    def release_flares(self, dt: float) -> None:
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
                    flare_vel = self._vel - flare_direction * random.normalvariate(
                        FLARE_MEAN_RELEASE_SPEED, FLARE_SD_RELEASE_SPEED
                    )
                    self.projectiles.append(self.new_flare(self._pos, flare_vel))
                self.flare_cooldown_timer += self._flare_cooldown

    def suffer_damage(self, damage: float) -> None:
        """Deal damage to the ship and activate its damage-indicator.

        Does nothing if damage is <= 0.

        Args:
            damage (float): Amount of damage to deal.

        """
        if damage > 0:
            self.health -= damage
            self.damage_indicator_timer = DAMAGE_INDICATOR_TIME

    def step(self, dt: float) -> None:
        """Physics, control, and bullet-stepping for `self`.

        Args:
            dt (float): Passed time

        """
        if self.thruster_rot_left:
            self.angle += self.rotation_thrust * dt
        if self.thruster_rot_right:
            self.angle -= self.rotation_thrust * dt

        forward = self.get_faced_direction()
        if self.thruster_forward:
            self.apply_force(forward * self.thrust, dt)
        if self.thruster_backward:
            self.apply_force(-forward * self.thrust, dt)

        self.damage_indicator_timer = max(0, self.damage_indicator_timer - dt)

        super().step(dt)

        for projectile in self.projectiles:
            projectile.step(dt)

        self.shoot(dt)
        self.release_flares(dt)

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera.

        Args:
            camera (Camera): Camera to draw on

        """
        forward = self.get_faced_direction()
        right = Vec2(-forward.y, forward.x)
        left = -right
        backward = -forward

        base_color: Color = self.color.lerp(Color("red"), self.damage_indicator_timer)
        darker_color: Color = base_color.lerp(Color("black"), 0.5)

        # Helper function for drawing polygons relative to the ship-position
        def drawy(color: Color, points: list[Vec2]) -> None:
            camera.draw_polygon(color, [self._pos + self.radius * p for p in points])

        # thruster_backward
        if self.thruster_backward:
            drawy(THRUST_COLOR, [forward * 2, left * 1.25, right * 1.25])

        # "For his neutral special, he wields a gun"
        camera.draw_line(
            darker_color, self._pos, self._pos + forward * self.radius * GUNBARREL_LENGTH, GUNBARREL_WIDTH * self.radius
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

        # HACK: UGLY
        backup_self_color = Color(self.color)
        self.color = base_color
        super().draw(camera)  # Draw circular body ("hitbox")
        self.color = backup_self_color

        for projectile in self.projectiles:
            projectile.draw(camera)


class ShipInput:
    """Specification for which keys trigger what spaceship-action."""

    type PygameKey = int

    def __init__(
        self,
        thruster_rot_left: PygameKey,
        thruster_rot_right: PygameKey,
        thruster_forward: PygameKey,
        thruster_backward: PygameKey,
        shoot: PygameKey,
        release_flares: PygameKey,
    ) -> None:
        """Create a new map from keys to spaceship-actions.

        Args:
            thruster_rot_left (pygame_key): Left rotation thruster's key
            thruster_rot_right (pygame_key): Right rotation thruster's key
            thruster_forward (pygame_key): Forward thruster's key
            thruster_backward (pygame_key): Backward thruster's key
            shoot (pygame_key): Pew pew key
            release_flares (pygame_key): Flare-release key

        """
        self.thruster_rot_left = thruster_rot_left
        self.thruster_rot_right = thruster_rot_right
        self.thruster_forward = thruster_forward
        self.thruster_backward = thruster_backward
        self.shoot = shoot
        self.release_flares = release_flares

    @classmethod
    def arrows(cls) -> ShipInput:
        """Create a new ShipInput, Arrow-Key-movement and return-shooting."""
        return cls(pygame.K_RIGHT, pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN, pygame.K_RETURN, pygame.K_m)

    @classmethod
    def wasd(cls) -> ShipInput:
        """Create a new ShipInput, WASD-movement and space-shooting."""
        return cls(pygame.K_d, pygame.K_a, pygame.K_w, pygame.K_s, pygame.K_SPACE, pygame.K_e)


PLAYER_DEFAULT_CONTROLS = ShipInput.arrows()


class PlayerShip(Ship):
    """A player-controlled spaceship."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        size: float = SHIP_SIZE,
        color: Color = PLAYER_COLOR,
        spaceship_input: ShipInput = PLAYER_DEFAULT_CONTROLS,
    ) -> None:
        """Create a new player-spaceship.

        Args:
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            size (float): Radius of disk-body
            color (Color): Material color
            spaceship_input (SpaceshipInput): Map from keys to actions

        """
        super().__init__(pos, vel, size, color, BULLET_ROF, BULLET_RELEASE_SPEED)
        self.spaceship_input = spaceship_input

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Handle input for `self` using ScancodeWrapper `keys`.

        `keys` is typically retreived using `pygame.key.get_pressed()`

        Args:
            keys (pygame.key.ScancodeWrapper): Pressed keys

        """
        self.thruster_rot_left = keys[self.spaceship_input.thruster_rot_left]
        self.thruster_rot_right = keys[self.spaceship_input.thruster_rot_right]
        self.thruster_forward = keys[self.spaceship_input.thruster_forward]
        self.thruster_backward = keys[self.spaceship_input.thruster_backward]
        self.shooting = keys[self.spaceship_input.shoot]
        self.releasing_flares = keys[self.spaceship_input.release_flares]


class BulletEnemy(Ship):
    """An enemy ship, targeting a specific other ship."""

    SHIP_COLOR = BULLET_ENEMY_COLOR
    SHIP_GUN_COOLDOWN = BULLET_ROF
    SHIP_PROJECTILE_SPEED = BULLET_RELEASE_SPEED
    SHIP_SIZE = SHIP_SIZE

    Action = Enum(
        "Action",
        [
            "accelerate_to_player",
            "accelerate_randomly",
            "decelerate",
        ],
    )

    def __init__(self, pos: Vec2, vel: Vec2, target_ship: Ship) -> None:
        """Create a new enemy ship.

        Args:
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            target_ship (Ship): Ship to target

        """
        super().__init__(pos, vel, self.SHIP_SIZE, self.SHIP_COLOR, self.SHIP_GUN_COOLDOWN, self.SHIP_PROJECTILE_SPEED)

        self.action_timer: float = 0.0
        self.current_action: BulletEnemy.Action = BulletEnemy.Action.accelerate_randomly
        self.target_ship: Ship = target_ship
        self.projectiles: list[Bullet] = []
        self.random_point: Vec2 = Vec2(0.0, 0.0)

    def step(self, dt: float) -> None:
        """Apply physics and "AI" to `self`.

        Args:
            dt (float): Passed time

        """
        self.action_timer -= dt
        delta_target_ship = self.target_ship.pos_relative_to(self)
        distance_to_target_squared = delta_target_ship.length_squared()
        distance_to_target = math.sqrt(distance_to_target_squared)

        if self.action_timer <= 0:
            random_x = random.uniform(-distance_to_target, distance_to_target)
            random_y = random.uniform(-distance_to_target, distance_to_target)
            # TODO@tim2othy: What is this supposed to do? Maybe add a comment?  ~lumi-a
            self.random_point = self._pos + (delta_target_ship + Vec2(random_x, random_y)) / 2

            if distance_to_target_squared < ENEMY_VISUAL_RANGE_SQUARED:
                self.current_action = BulletEnemy.Action.accelerate_to_player
            else:
                [self.current_action] = random.choices(
                    population=[
                        BulletEnemy.Action.accelerate_randomly,
                        BulletEnemy.Action.decelerate,
                    ],
                    weights=ENEMY_ACTION_WEIGHTS,
                )

            self.action_timer = ENEMY_ACTION_TIMER

        match self.current_action:
            case BulletEnemy.Action.accelerate_to_player:
                force_direction = delta_target_ship
            case BulletEnemy.Action.decelerate:
                force_direction = -self._vel
            case BulletEnemy.Action.accelerate_randomly:
                force_direction = self.random_point - self._pos

        if force_direction != Vec2(0, 0):
            force = force_direction.normalize() * self.thrust
            self.apply_force(force, dt)

        self.shooting = (
            self.current_action == BulletEnemy.Action.accelerate_to_player
            and distance_to_target_squared < ENEMY_FIRE_RANGE_SQUARED
        )
        self.angle = math.degrees(math.atan2(force_direction.y, force_direction.x))

        super().step(dt)


class RocketEnemy(BulletEnemy):
    """An enemy ship shooting rockets, targeting a specific other ship."""

    # Override class configuration for RocketEnemy
    SHIP_COLOR = ROCKET_ENEMY_COLOR
    SHIP_GUN_COOLDOWN = ROCKET_ROF
    SHIP_PROJECTILE_SPEED = ROCKET_RELEASE_SPEED

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new rocket targeting `self.target_ship`."""
        return Rocket(pos, vel, self.projectile_color, self.target_ship)


class MissileEnemy(BulletEnemy):
    """An enemy ship shooting powerful, smart, homing missiles, targeting a specific other ship."""

    # Override class configuration for MissileEnemy
    SHIP_COLOR = MISSILE_ENEMY_COLOR
    SHIP_GUN_COOLDOWN = MISSILE_ROF
    SHIP_PROJECTILE_SPEED = ROCKET_RELEASE_SPEED  # Using rocket speed for missiles

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new missile targeting `self.target_ship`."""
        return Missile(pos, vel, self.projectile_color, self.target_ship)


class MarkovEnemy(BulletEnemy):
    """An enemy ship using Markov chain AI for more sophisticated behavior."""

    # Override class configuration for MarkovEnemy
    SHIP_COLOR = MARKOV_ENEMY_COLOR

    def __init__(self, pos: Vec2, vel: Vec2, target_ship: Ship) -> None:
        """Create a new Markov-based enemy ship.

        Args:
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            target_ship (Ship): Ship to target

        """
        super().__init__(pos, vel, target_ship)
        self.ai = MarkovAI(self, target_ship)

    def step(self, dt: float) -> None:
        """Apply physics and AI to this ship.

        Args:
            dt (float): Passed time

        """
        self.ai.update(dt)
        Ship.step(self, dt)
