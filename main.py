"""Staging-grounds for the game."""

from __future__ import annotations

import sys
import random
import asyncio
import platform
import pygame
import pygame.constants  # Add this import at the top with other imports
from pygame import Color
from pygame.math import Vector2 as Vec2

from camera import Camera
from universe import (
    Universe,
    Planet,
)
from ship import PlayerShip, ShipInput, BulletEnemy, RocketEnemy, MissileEnemy
from constants import (
    ORBIT_MODE,
    SMALL_MODE,
    MULTI_MODE,
    INVINCIBLE_MODE,
    SCREEN_SIZE,
    MINIMAP_SIZE,
    WORLD_SIZE,
    SPAWNPOINT,
    ASTS_PER_PLANET,
    NUMBER_OF_ENEMIES,
)


async def main():
    """Main async game loop."""
    SCREEN_SURFACE = None
    try:
        pygame.init()  # Initialize all modules (including font)
        pygame.display.set_caption("Space Game")
        SCREEN_SURFACE = pygame.display.set_mode(SCREEN_SIZE)
        await asyncio.sleep(0.1)  # Wait for display initialization

        if sys.platform == "emscripten":
            platform.window.canvas.style.imageRendering = "pixelated"

        # Initialize fonts after display is active
        font = pygame.font.Font(None, 36)
        debug_font = pygame.font.Font(None, 24)

        def show_loading(message: str, debug_info: str = ""):
            SCREEN_SURFACE.fill((0, 0, 0))
            loading_text = font.render(message, True, (255, 255, 255))
            text_rect = loading_text.get_rect(
                center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2)
            )
            SCREEN_SURFACE.blit(loading_text, text_rect)
            if debug_info:
                debug_text = debug_font.render(debug_info, True, (128, 128, 128))
                debug_rect = debug_text.get_rect(bottomleft=(10, SCREEN_SIZE[1] - 10))
                SCREEN_SURFACE.blit(debug_text, debug_rect)
            pygame.display.flip()

        show_loading("Initializing game...", "Debug: Starting initialization")
        await asyncio.sleep(0.5)

        show_loading("Creating player ships...", "Debug: Initializing ships")
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
        await asyncio.sleep(0.1)

        player_ships_multi: list[PlayerShip] = [
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

        planets_small: list[Planet] = [
            Planet(Vec2(1_800, 6_700), 1, 320, Color("darkred")),
            Planet(Vec2(2_300, 900), 1, 300, Color("green")),
            Planet(Vec2(4_200, 3_700), 1, 280, Color("mediumpurple")),
            Planet(Vec2(5_000, 9_000), 1, 310, Color("darkorange")),
            Planet(Vec2(6_000, 400), 1, 340, Color("royalblue")),
            Planet(Vec2(6_700, 7_200), 1, 280, Color("darkslategray")),
            Planet(Vec2(9_200, 4_400), 1, 260, Color("yellow")),
        ]

        planets_play: list[Planet] = [
            Planet(Vec2(27_000, 29_000), 1, 700, Color("darkred")),
            Planet(Vec2(21_000, 28_000), 1, 800, Color("khaki")),
            Planet(Vec2(2_000, 27_000), 1, 900, Color("royalblue")),
            Planet(Vec2(17_000, 26_000), 1, 900, Color("mediumpurple")),
            Planet(Vec2(14_000, 23_000), 1, 900, Color("darkslategray")),
            Planet(Vec2(17_000, 22_000), 1, 800, Color("darkgreen")),
            Planet(Vec2(13_000, 21_000), 1, 400, Color("crimson")),
            Planet(Vec2(10_000, 20_000), 1, 900, Color("hotpink")),
            Planet(Vec2(18_000, 19_000), 1, 300, Color("coral")),
            Planet(Vec2(16_000, 18_000), 1, 600, Color("gold")),
            Planet(Vec2(13_000, 17_000), 1, 400, Color("blue")),
            Planet(Vec2(8_000, 16_000), 1, 500, Color("turquoise")),
            Planet(Vec2(24_000, 15_000), 1, 270, Color("green")),
            Planet(Vec2(25_000, 14_000), 1, 300, Color("deeppink")),
            Planet(Vec2(18_000, 12_000), 1, 900, Color("darkorange")),
            Planet(Vec2(3_000, 5_000), 1, 100, Color("yellow")),
            Planet(Vec2(22_000, 4_000), 1, 850, Color("lightblue")),
            Planet(Vec2(14_500, 3_000), 1, 600, Color("plum")),
            Planet(Vec2(28_000, 2_000), 1, 200, Color("slategray")),
            Planet(Vec2(3_000, 1_000), 1, 700, Color("navy")),
        ]

        planets_orbit: list[Planet] = [
            Planet(
                Vec2(
                    random.uniform(0, WORLD_SIZE[1]), random.uniform(0, WORLD_SIZE[1])
                ),
                1,
                random.uniform(100, 800),
                Color("darkred"),
            ),
            Planet(
                Vec2(
                    random.uniform(0, WORLD_SIZE[1]), random.uniform(0, WORLD_SIZE[1])
                ),
                1,
                random.uniform(100, 800),
                Color("green"),
            ),
        ]

        if MULTI_MODE:
            player_ships: list[PlayerShip] = player_ships_multi
        else:
            player_ships: list[PlayerShip] = player_ships_single

        if SMALL_MODE:
            planets = planets_small
        else:
            planets = planets_play

        if ORBIT_MODE:
            planets = planets_orbit

        show_loading("Setting up universe...", "Debug: Creating universe components")
        universe = Universe(
            WORLD_SIZE,
            planets,
            player_ships,
            [],
            ["assets/astral-0.png", "assets/astral-1.png", "assets/astral-1.png"],
        )
        await asyncio.sleep(0.1)

        show_loading("Generating asteroids...", "Debug: Starting asteroid generation")
        for i, planet in enumerate(planets):
            for _ in range(ASTS_PER_PLANET):
                universe.generate_asteroid(planet)
                await asyncio.sleep(0)
            show_loading(f"Generating asteroids... ({i+1}/{len(planets)} planets)")
            await asyncio.sleep(0)

        show_loading("Starting game...", "Debug: Initialization complete")
        await asyncio.sleep(0.5)

        enemy_ships: list[BulletEnemy] = []
        for _ in range(NUMBER_OF_ENEMIES):
            pos = Vec2(random.uniform(0, WORLD_SIZE.x), random.uniform(0, WORLD_SIZE.y))
            if random.random() > 0.6:
                enemy_ships.append(
                    BulletEnemy(pos, Vec2(0, 0), random.choice(player_ships))
                )
            else:
                if random.random() > 0.5:
                    enemy_ships.append(
                        RocketEnemy(pos, Vec2(0, 0), random.choice(player_ships))
                    )
                else:
                    enemy_ships.append(
                        MissileEnemy(pos, Vec2(0, 0), random.choice(player_ships))
                    )

        universe.enemy_ships = enemy_ships

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

        # Create minimap surface similarly
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
                # Blit the camera's view to the appropriate region in SCREEN_SURFACE
                topleft = (int(player_ix * SCREEN_SIZE[0] / player_count), 0)
                SCREEN_SURFACE.blit(player_camera.surface, topleft)

            minimap_camera.start_drawing_new_frame()
            universe.draw(minimap_camera)
            # Blit the minimap to SCREEN_SURFACE
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

        pygame.quit()
        sys.exit()

    except Exception as e:
        if SCREEN_SURFACE:
            SCREEN_SURFACE.fill((0, 0, 0))
            # Use font if defined; otherwise fallback_font will be available because it was defined after pygame.init()
            err_font = pygame.font.Font(None, 36)

            error_text = err_font.render(f"Error: {str(e)}", True, (255, 0, 0))
            error_rect = error_text.get_rect(
                center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2)
            )
            SCREEN_SURFACE.blit(error_text, error_rect)
            pygame.display.flip()
            await asyncio.sleep(5)
        raise


if __name__ == "__main__":
    asyncio.run(main())
