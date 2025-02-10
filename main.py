"""Staging-grounds for the game."""

from __future__ import annotations

import sys
import random
import asyncio
import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from camera import Camera
from universe import Universe, Planet
from ship import PlayerShip, ShipInput, BulletEnemy, RocketEnemy, MissileEnemy
from constants import (
    SMALL_MODE,
    MULTI_MODE,
    INVINCIBLE_MODE,
    SCREEN_SIZE,
    MINIMAP_SIZE,
    WORLD_SIZE,
    SPAWNPOINT,
    ASTS_PER_PLANET,
    NUMBER_OF_ENEMIES,
    PLANET_RADIUS_SIGMA,
    PLANET_RADIUS_MU,
)


async def main():
    """Main async game loop."""
    SCREEN_SURFACE = None
    pygame.init()
    font = pygame.font.Font(None, 36)

    try:
        pygame.display.set_caption("Space Game")
        SCREEN_SURFACE = pygame.display.set_mode(SCREEN_SIZE)

        def show_loading(message: str):
            SCREEN_SURFACE.fill((0, 0, 0))
            loading_text = font.render(message, True, (255, 255, 255))
            text_rect = loading_text.get_rect(
                center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2)
            )
            SCREEN_SURFACE.blit(loading_text, text_rect)
            pygame.display.flip()

        show_menu(SCREEN_SURFACE, font)
        # Wait for the player to press Enter to start the game
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    waiting = False

        show_loading("Initializing game")

        player_ships_single: list[PlayerShip] = [
            PlayerShip(
                SPAWNPOINT,
                Vec2(0, 0),
                1,
                10,
                Color("darkslategray"),
                Color("orange"),
                ShipInput(
                    pygame.K_RIGHT,
                    pygame.K_LEFT,
                    pygame.K_UP,
                    pygame.K_DOWN,
                    pygame.K_RETURN,
                ),
                "assets/player_ship.png",
            ),
        ]

        player_ships_multi: list[PlayerShip] = [
            player_ships_single[0],
            PlayerShip(
                SPAWNPOINT + Vec2(50, 0),
                Vec2(0, 0),
                1,
                10,
                Color("blue"),
                Color("yellow"),
                ShipInput(
                    pygame.K_d, pygame.K_a, pygame.K_w, pygame.K_s, pygame.K_SPACE
                ),
                "assets/player_ship.png",
            ),
        ]

        planets_large: list[Planet] = [
            Planet(Vec2(27_000, 29_000), 700, Color("darkred")),
            Planet(Vec2(21_000, 28_000), 800, Color("khaki")),
            Planet(Vec2(2_000, 27_000), 900, Color("royalblue")),
            Planet(Vec2(17_000, 26_000), 900, Color("mediumpurple")),
            Planet(Vec2(14_000, 23_000), 900, Color("darkslategray")),
            Planet(Vec2(17_000, 22_000), 800, Color("darkgreen")),
            Planet(Vec2(13_000, 21_000), 400, Color("crimson")),
            Planet(Vec2(18_000, 19_000), 300, Color("coral")),
            Planet(Vec2(13_000, 17_000), 400, Color("blue")),
            Planet(Vec2(8_000, 16_000), 500, Color("turquoise")),
            Planet(Vec2(25_000, 14_000), 300, Color("deeppink")),
            Planet(Vec2(18_000, 12_000), 900, Color("darkorange")),
            Planet(Vec2(22_000, 4_000), 850, Color("lightblue")),
            Planet(Vec2(14_500, 3_000), 600, Color("plum")),
            Planet(Vec2(28_000, 2_000), 200, Color("slategray")),
            Planet(Vec2(3_000, 1_000), 700, Color("navy")),
        ]

        planets_small: list[Planet] = [
            Planet(
                Vec2(
                    random.uniform(0, WORLD_SIZE[1]), random.uniform(0, WORLD_SIZE[1])
                ),
                random.lognormvariate(PLANET_RADIUS_MU, PLANET_RADIUS_SIGMA),
                color,
            )
            for color in [
                Color("darkred"),
                Color("green"),
                Color("mediumpurple"),
                Color("darkorange"),
                Color("royalblue"),
                Color("yellow"),
            ]
        ]

        player_ships = player_ships_multi if MULTI_MODE else player_ships_single
        planets = planets_small if SMALL_MODE else planets_large

        show_loading("Setting up universe")
        universe = Universe(
            WORLD_SIZE,
            planets,
            player_ships,
            [],
            ["assets/astral-0.png", "assets/astral-1.png", "assets/astral-1.png"],
        )

        show_loading("Generating asteroids")
        for planet in planets:
            for _ in range(ASTS_PER_PLANET):
                universe.generate_asteroid(planet)

        show_loading("Adding Enemies")

        enemy_ships: list[BulletEnemy] = []
        for _ in range(NUMBER_OF_ENEMIES):
            pos = Vec2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
            enemy_type = random.choices(
                [BulletEnemy, RocketEnemy, MissileEnemy], [0.6, 0.2, 0.2]
            )[0]
            enemy_ships.append(enemy_type(pos, Vec2(0, 0), random.choice(player_ships)))

        universe.enemy_ships = enemy_ships

        show_loading("Adding Players")

        # --- Instead of subsurfaces from SCREEN_SURFACE, create independent surfaces ---
        cameras: list[Camera] = []
        player_count = len(player_ships)
        for player_ix, player in enumerate(player_ships):
            topleft = (player_ix * SCREEN_SIZE[0] / player_count, 0)
            size = (SCREEN_SIZE[0] / player_count, SCREEN_SIZE[1])
            # Create a new surface instead of SCREEN_SURFACE.subsurface(...)
            cam_surface = pygame.Surface((int(size[0]), int(size[1]))).convert()

            camera = Camera(player.pos, 1.0, cam_surface)
            cameras.append(camera)

        show_loading("Creating Minimap")
        minimap_surface = pygame.Surface((MINIMAP_SIZE.x, MINIMAP_SIZE.y)).convert()

        minimap_camera = Camera(
            WORLD_SIZE / 2, MINIMAP_SIZE.x / WORLD_SIZE.x, minimap_surface
        )

        clock = pygame.time.Clock()

        while True:
            dt = clock.tick() / 1_000

            if any(e.type == pygame.QUIT for e in pygame.event.get()):
                break

            universe.handle_input(pygame.key.get_pressed())
            universe.step(dt)

            # Draw each camera's view and then blit it into SCREEN_SURFACE
            for player_ix, player_ship in enumerate(player_ships):
                player_camera = cameras[player_ix]
                player_camera.start_drawing_new_frame()
                gameover = (
                    not universe.contains_point(player_ship.pos)
                    or player_ship.health <= 0
                ) and not INVINCIBLE_MODE
                if gameover:
                    gameover_font = pygame.font.Font(None, int(64 / player_count))
                    player_camera.draw_text(
                        "GAME OVER", None, gameover_font, Color("red")
                    )
                else:
                    universe.move_camera(player_camera, player_ix, dt)
                    universe.draw_background(player_camera)
                    universe.draw_grid(player_camera)
                    universe.draw(player_camera)
                    universe.draw_text(player_camera, player_ix)
                topleft = (int(player_ix * SCREEN_SIZE[0] / player_count), 0)
                SCREEN_SURFACE.blit(player_camera.surface, topleft)

            minimap_camera.start_drawing_new_frame()
            universe.draw(minimap_camera)
            SCREEN_SURFACE.blit(
                minimap_camera.surface, (SCREEN_SIZE[0] - MINIMAP_SIZE.x, 0)
            )

            # Draw minimap borders directly on SCREEN_SURFACE if needed
            MINIMAP_BORDER_COLOR = Color("aquamarine")
            minimap_camera.draw_vertical_hairline(
                MINIMAP_BORDER_COLOR, 0, 0, WORLD_SIZE.y
            )
            minimap_camera.draw_horizontal_hairline(
                MINIMAP_BORDER_COLOR,
                0,
                WORLD_SIZE.x,
                WORLD_SIZE.y - 1,
            )
            pygame.display.flip()
            await asyncio.sleep(0)

    except Exception as e:
        if SCREEN_SURFACE:
            SCREEN_SURFACE.fill((0, 0, 0))
            error_text = font.render(f"Error: {str(e)}", True, (255, 0, 0))
            error_rect = error_text.get_rect(
                center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2)
            )
            SCREEN_SURFACE.blit(error_text, error_rect)
            pygame.display.flip()
            await asyncio.sleep(5)
        raise
    finally:
        pygame.quit()
        sys.exit()


def show_menu(screen, font):
    """Display the main menu."""
    screen.fill((0, 0, 0))
    title_text = font.render("Space Game", True, (255, 255, 255))
    start_text = font.render("Press Enter to Start", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 3))
    start_rect = start_text.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2))
    screen.blit(title_text, title_rect)
    screen.blit(start_text, start_rect)
    pygame.display.flip()


if __name__ == "__main__":
    asyncio.run(main())
