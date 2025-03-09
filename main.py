"""Staging-grounds for the game."""

from __future__ import annotations

import asyncio
import platform
import sys
from collections import deque
from typing import TYPE_CHECKING

import pygame
from pygame import Color, Surface
from pygame.font import Font
from universe import Universe, UniverseOptions

from camera import Camera
from constants import (
    FPS_HISTORY_LENGTH,
    SCREEN_SIZE,
)
from profiler import global_profiler

if TYPE_CHECKING:
    from ship import PlayerShip


async def main() -> None:
    """Run the game."""
    screen_surface = None
    pygame.display.init()
    pygame.font.init()
    font = pygame.font.Font(None, 36)
    options = UniverseOptions()

    pygame.display.set_caption("Space Game")
    screen_surface = pygame.display.set_mode(SCREEN_SIZE)
    keep_playing = True

    while keep_playing:
        options = await show_menu(screen_surface, options, font)
        universe, player_ships = universe_from_options(options)

        players_and_cameras: list[tuple[PlayerShip, Camera]] = []
        player_count = len(player_ships)
        for player_ix, player in enumerate(player_ships):
            topleft = (player_ix * SCREEN_SIZE.x / player_count, 0)
            size = (SCREEN_SIZE.x / player_count, SCREEN_SIZE.y)
            subsurface = screen_surface.subsurface((topleft, size))
            camera = Camera(subsurface, player, 1.0 / 4.0)
            players_and_cameras.append((player, camera))

        clock = pygame.time.Clock()

        fps: deque[float] = deque()
        running = True

        while running:
            if any(e.type == pygame.QUIT for e in pygame.event.get()):
                running = False
                keep_playing = False
                break

            dt = clock.tick() / 1_000
            fps.append(clock.get_fps())
            if len(fps) > FPS_HISTORY_LENGTH:
                fps.popleft()

            universe.handle_input(pygame.key.get_pressed())
            universe.step(dt)

            # Draw each camera's view
            for player, camera in players_and_cameras:
                camera.start_drawing_new_frame()
                if player.health <= 0 and not options["invincible"]:
                    gameover_font = pygame.font.Font(None, int(64 / player_count))
                    camera.draw_text("GAME OVER", None, gameover_font, Color("red"))
                    pygame.display.flip()
                    await asyncio.sleep(2)
                    running = False
                    break
                camera.step()
                universe.draw(camera)
                universe.draw_text(camera, player, sum(fps) / len(fps))

            pygame.display.flip()
            await asyncio.sleep(0)

    profiler_stats = global_profiler.stats_to_str()
    print(profiler_stats)  # noqa: T201
    if sys.platform == "emscripten":
        platform.console.log(profiler_stats)

    pygame.quit()
    sys.exit()


async def show_menu(screen: Surface, options: Options, font: Font) -> Options:
    """Display the main menu until player presses Enter.

    Args:
        screen (Surface): To fill and render text on
        options (Options): Current options
        font (Font): Font to use for rendering

    Returns:
        Options: Updated options

    """
    option_selection_ix = 0
    title_text = font.render("Space Game", antialias=True, color=Color("White"))
    start_text = font.render("Press Enter to Start", antialias=True, color=Color("White"))

    def draw_menu() -> None:
        screen.fill(Color("Black"))

        screen.blit(title_text, title_text.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 6)))

        for i, (name, value) in enumerate(options.items()):
            color = (255, 255, 255) if i == option_selection_ix else (100, 100, 100)
            option_text = font.render(f"{name}: <{'On' if value else 'Off'}>", antialias=True, color=color)
            screen.blit(option_text, option_text.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 3 + i * 50)))

        screen.blit(start_text, start_text.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] * 5 / 6)))
        pygame.display.flip()

    option_names = list(options.keys())
    waiting = True
    while waiting:
        draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False
                elif event.key == pygame.K_UP:
                    option_selection_ix = (option_selection_ix - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    option_selection_ix = (option_selection_ix + 1) % len(options)
                elif event.key in {pygame.K_LEFT, pygame.K_RIGHT}:
                    options[option_names[option_selection_ix]] = not options[option_names[option_selection_ix]]
        await asyncio.sleep(0)

    return options


if __name__ == "__main__":
    asyncio.run(main())
