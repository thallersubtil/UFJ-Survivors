import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest


@pytest.fixture(scope="session", autouse=True)
def pygame_iniciado():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()
