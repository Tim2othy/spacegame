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
    BULLET_SPEED,
    DAMAGE_INDICATOR_TIME,
    ENEMY_ACTION_TIMER,
    ENEMY_ACTION_WEIGHTS,
    ENEMY_BULLET_COOLDOWN,
    ENEMY_HEALTH,
    ENEMY_MISSILE_COOLDOWN,
    ENEMY_ROCKET_COOLDOWN,
    ENEMY_SHOOT_RANGE,
    ENEMY_THRUST_MULTIPLIER,
    ENEMY_VISUAL_RANGE,
    EPSILON,
    GUN_COOLDOWN_PLAYER,
    GUNBARREL_LENGTH,
    GUNBARREL_WIDTH,
)
from physics import Disk
from projectiles import Bullet, Missile, Rocket

if TYPE_CHECKING:
    from camera import Camera


class Ship(Disk):
    """A basic spaceship."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        density: float,
        size: float,
        color: Color,
        bullet_color: Color,
        gun_cooldown: float,
        bullet_speed: float,
    ) -> None:
        """Create a new spaceship.

        Raises a ValueError if `gun_cooldown` is not strictly positive.

        Args:
        ----
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            density (float): Density (of disk-body)
            size (float): Radius of disk-body
            color (Color): Material color
            bullet_color (Color): Bullet_color

        >>> v0, c = Vec2(0, 0), Color(0,0,0)
        >>> Ship(v0, v0, 1, 1, c, c, 1, 1)
        <ship.Ship object at ...>
        >>> Ship(v0, v0, 1, 1, c, c, -1, 1)
        Traceback (most recent call last):
            ...
        ValueError

        """
        super().__init__(pos, vel, density, size, color)
        self.size: float = size

        self.health: float = 100.0
        self.damage_indicator_timer: float = 0

        self.projectiles: list[Bullet] = []
        if not gun_cooldown > 0:
            raise ValueError
        self._gun_cooldown: float = gun_cooldown
        self.gun_cooldown_timer: float = 0
        self.shooting: bool = False
        self.bullet_color = Color(bullet_color)
        self.bullet_speed = bullet_speed

        self.angle: float = 0
        self.thrust: float = 250 * self.mass
        self.rotation_thrust: float = 230
        self.thruster_rot_left: bool = False
        self.thruster_rot_right: bool = False
        self.thruster_backward: bool = False
        self.thruster_forward: bool = False

    def get_faced_direction(self) -> Vec2:
        """Get `self`'s faced direction from its `angle`.

        Returns
        -------
            Vec2: Faced direction, normalized

        """
        # For unknown reasons, `Vec2.from_polar((self.angle, 1))` won't work.
        direction = Vec2()
        direction.from_polar((1, self.angle))
        return direction

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new bullet at `pos` with velocity `vel`."""
        return Bullet(pos, vel, self.bullet_color)

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
                bullet_vel = self.vel + forward * BULLET_SPEED

                # When multiple shots are fired per frame,
                # but we spawn them all at the end of the gunbarrel,
                # they'd all spawn on top of each other, see issue #47.
                # To mitigate this, we offset the spawn-position
                # by the (time since the shot was fired) * bullet_vel.
                # The time since the shot was fired is simply the
                # negative of the current gun_cooldown.
                gunbarrel_offset = forward * self.radius * GUNBARREL_LENGTH
                bullet_pos = self.pos + gunbarrel_offset - self.gun_cooldown_timer * bullet_vel

                self.projectiles.append(self.new_bullet(bullet_pos, bullet_vel))
                self.gun_cooldown_timer += self._gun_cooldown

    def suffer_damage(self, damage: float) -> None:
        """Deal damage to the ship and activate its damage-indicator.

        Does nothing if damage is <= 0.

        Args:
        ----
            damage (float): Amount of damage to deal.

        """
        if damage > 0:
            self.health -= damage
            self.damage_indicator_timer = DAMAGE_INDICATOR_TIME

    def step(self, dt: float) -> None:
        """Physics, control, and bullet-stepping for `self`.

        Args:
        ----
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

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera.

        Args:
        ----
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
            camera.draw_polygon(color, [self.pos + self.radius * p for p in points])

        # thruster_backward
        if self.thruster_backward:
            drawy(Color("orange"), [forward * 2, left * 1.25, right * 1.25])

        # "For his neutral special, he wields a gun"
        camera.draw_line(
            darker_color,
            self.pos,
            self.pos + forward * self.radius * GUNBARREL_LENGTH,
            GUNBARREL_WIDTH * self.radius,
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
                Color("orange"),
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
                Color("orange"),
                [
                    1.5 * right + 1.25 * backward,
                    0.5 * right + 0.5 * backward,
                    2.0 * right + 1.0 * backward,
                ],
            )

        # thruster_forward, active
        if self.thruster_forward:
            drawy(
                Color("orange"),
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

        # Ugly hack
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
    ) -> None:
        """Create a new map from keys to spaceship-actions.

        Args:
        ----
            thruster_rot_left (pygame_key): Left rotation thruster's key
            thruster_rot_right (pygame_key): Right rotation thruster's key
            thruster_forward (pygame_key): Forward thruster's key
            thruster_backward (pygame_key): Backward thruster's key
            shoot (pygame_key): Pew pew key

        """
        self.thruster_rot_left = thruster_rot_left
        self.thruster_rot_right = thruster_rot_right
        self.thruster_forward = thruster_forward
        self.thruster_backward = thruster_backward
        self.shoot = shoot

    @classmethod
    def arrows(cls) -> ShipInput:
        """Create a new ShipInput, Arrow-Key-movement and return-shooting."""
        return cls(
            pygame.K_RIGHT,
            pygame.K_LEFT,
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_RETURN,
        )

    @classmethod
    def wasd(cls) -> ShipInput:
        """Create a new ShipInput, WASD-movement and space-shooting."""
        return cls(pygame.K_d, pygame.K_a, pygame.K_w, pygame.K_s, pygame.K_SPACE)


class PlayerShip(Ship):
    """A player-controlled spaceship."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        density: float,
        size: float,
        color: Color,
        bullet_color: Color,
        spaceship_input: ShipInput,
        image_path: str,
    ) -> None:
        """Create a new player-spaceship.

        Args:
        ----
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            density (float): Density (of disk-body)
            size (float): Radius of disk-body
            color (Color): Material color
            bullet_color (Color): Bullet_color
            spaceship_input (SpaceshipInput): Map from keys to actions
            image_path (str): Path to image

        """
        super().__init__(pos, vel, density, size, color, bullet_color, GUN_COOLDOWN_PLAYER, BULLET_SPEED)
        self.spaceship_input = spaceship_input
        self.image = pygame.image.load(image_path)

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Handle input for `self` using ScancodeWrapper `keys`.

        `keys` is typically retreived using `pygame.key.get_pressed()`

        Args:
        ----
            keys (pygame.key.ScancodeWrapper): Pressed keys

        """
        self.thruster_rot_left = keys[self.spaceship_input.thruster_rot_left]
        self.thruster_rot_right = keys[self.spaceship_input.thruster_rot_right]
        self.thruster_forward = keys[self.spaceship_input.thruster_forward]
        self.thruster_backward = keys[self.spaceship_input.thruster_backward]
        self.shooting = keys[self.spaceship_input.shoot]

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera.

        Args:
        ----
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
            camera.draw_polygon(color, [self.pos + self.radius * p for p in points])

        # thruster_backward, active
        if self.thruster_backward:
            drawy(Color("orange"), [forward * 2, left * 1.25, right * 1.25])

        # "For his neutral special, he wields a gun"
        camera.draw_line(
            darker_color,
            self.pos,
            self.pos + forward * self.radius * GUNBARREL_LENGTH,
            GUNBARREL_WIDTH * self.radius,
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
        # thruster_rot_left, active
        if self.thruster_rot_left:
            drawy(
                Color("orange"),
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
        # thruster_rot_right, active
        if self.thruster_rot_right:
            drawy(
                Color("orange"),
                [
                    1.5 * right + 1.25 * backward,
                    0.5 * right + 0.5 * backward,
                    2.0 * right + 1.0 * backward,
                ],
            )

        # thruster_forward, flame
        if self.thruster_forward:
            drawy(
                Color("orange"),
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

        rotated_image = pygame.transform.rotate(self.image, -self.angle - 90)

        # Get the width and height of the rotated image
        image_rect = rotated_image.get_rect()
        center_offset = Vec2(image_rect.width / 2, image_rect.height / 2)

        # Adjust the position to center the image
        adjusted_pos = self.pos - center_offset

        # Ugly hack
        backup_self_color = Color(self.color)
        self.color = base_color
        super().draw(camera)  # Draw circular body ("hitbox")
        self.color = backup_self_color

        for projectile in self.projectiles:
            projectile.draw(camera)

        camera.draw_image(rotated_image, adjusted_pos)


LIME = Color("lime")
PINK = Color("hotpink")


class BulletEnemy(Ship):
    """An enemy ship, targeting a specific other ship."""

    Action = Enum(
        "Action",
        [
            "accelerate_to_player",
            "accelerate_randomly",
            "decelerate",
        ],
    )

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        target_ship: Ship,
        world_size: Vec2,
        gun_cooldown: float = ENEMY_BULLET_COOLDOWN,
        bullet_speed: float = BULLET_SPEED,
        color: Color = LIME,
        bullet_color: Color = PINK,
    ) -> None:
        """Create a new enemy ship.

        Args:
        ----
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            target_ship (Ship): Ship to target
            world_size (Vec2): Size of the world

        """
        super().__init__(pos, vel, 1, 8, color, bullet_color, gun_cooldown, bullet_speed)
        self.thrust *= ENEMY_THRUST_MULTIPLIER
        self.action_timer = 0.0
        self.health = ENEMY_HEALTH
        self.current_action: BulletEnemy.Action = BulletEnemy.Action.accelerate_randomly
        self.target_ship = target_ship
        self.projectiles: list[Bullet] = []
        self.random_point = Vec2(0.0, 0.0)
        self.world_size = world_size

    def step(self, dt: float) -> None:
        """Apply physics and "AI" to `self`.

        Args:
        ----
            dt (float): Passed time

        """
        self.action_timer -= dt
        delta_target_ship = self.target_ship.pos - self.pos

        if self.action_timer <= 0:
            self.random_point = Vec2(
                random.uniform(0, self.world_size.x),
                random.uniform(0, self.world_size.y),
            )
            if delta_target_ship == Vec2(0, 0):
                delta_target_ship = Vec2(EPSILON, EPSILON)

            if delta_target_ship.magnitude_squared() < ENEMY_VISUAL_RANGE**2:
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
                desired_velocity = delta_target_ship * self.thrust / delta_target_ship.magnitude()
                perfect_multiplier = max(self.target_ship.vel.magnitude() * 1.5, desired_velocity.magnitude())
                perfect_velocity = desired_velocity.normalize() * perfect_multiplier
                required_acceleration = perfect_velocity - self.vel
                force_direction = required_acceleration
            case BulletEnemy.Action.decelerate:
                force_direction = -self.vel
            case BulletEnemy.Action.accelerate_randomly:
                delta_random_point = self.random_point - self.pos
                force_direction = delta_random_point

        if force_direction.magnitude() != 0:
            force = force_direction * self.thrust / force_direction.magnitude()
            self.apply_force(force, dt)

        self.shooting = (
            self.current_action == BulletEnemy.Action.accelerate_to_player
            and delta_target_ship.magnitude_squared() < ENEMY_SHOOT_RANGE**2
        )
        self.angle = math.degrees(math.atan2(force_direction.y, force_direction.x))

        super().step(dt)


PLUM = Color("Plum")


class RocketEnemy(BulletEnemy):
    """An enemy ship shooting rockets, targeting a specific other ship."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        target_ship: Ship,
        world_size: Vec2,
        color: Color = PLUM,
    ) -> None:
        """Create a new Rocket-Ship.

        Args:
        ----
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            target_ship (Ship): Ship to target
            world_size (Vec2): Size of the world


        """
        super().__init__(pos, vel, target_ship, world_size, ENEMY_ROCKET_COOLDOWN, 0, color)

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new rocket targeting `self.target_ship`."""
        return Rocket(pos, vel, self.color, self.target_ship)


BLUE = Color("Blue")


class MissileEnemy(BulletEnemy):
    """An enemy ship shooting powerful, smart, homing missiles, targeting a specific other ship."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        target_ship: Ship,
        world_size: Vec2,
        color: Color = BLUE,
    ) -> None:
        """Create a new Missile-Ship.

        Args:
        ----
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            target_ship (Ship): Ship to target
            world_size (Vec2): Size of the world

        """
        super().__init__(pos, vel, target_ship, world_size, ENEMY_MISSILE_COOLDOWN, 0, color)

    def new_bullet(self, pos: Vec2, vel: Vec2) -> Bullet:
        """Create a new missile targeting `self.target_ship`."""
        return Missile(pos, vel, self.color, self.target_ship, "assets/missile.png")
