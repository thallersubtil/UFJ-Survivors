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


@pytest.fixture
def jogo_limpo():
    from jogo.fase import Fase
    from jogo.jogador.alunos import AlunoAgil
    from jogo.jogo import Jogo

    class FaseVazia(Fase):
        NOME = "Fase de teste"

        def criar_eventos(self):
            return []

    def criar(classe=AlunoAgil):
        jogo = Jogo(classe, fase=FaseVazia(), semente=3)
        for e in jogo.entidades:
            if e.grupo == "decoracao":
                e.remover()
        jogo._limpar()
        return jogo

    return criar
