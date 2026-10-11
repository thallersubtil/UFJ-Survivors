import pygame

from jogo.aplicacao import Aplicacao
from jogo.cenas.partida import CenaPartida
from jogo.jogador.alunos import AlunoAgil


def tecla(k, tipo=pygame.KEYDOWN):
    return pygame.event.Event(tipo, key=k, mod=0, unicode="", scancode=0)


def test_partida_roda_alguns_quadros_e_desenha_o_hud():
    app = Aplicacao(pygame.Surface((1280, 720)))
    app.trocar(CenaPartida(app, AlunoAgil))
    for _ in range(30):
        app.passo(1 / 60, [])
    assert app.cena_atual.jogo.placar.tempo > 0.4


def test_espaco_usa_o_especial():
    app = Aplicacao(pygame.Surface((1280, 720)))
    cena = CenaPartida(app, AlunoAgil)
    app.trocar(cena)
    app.passo(1 / 60, [tecla(pygame.K_SPACE)])
    assert not cena.jogo.jogador.especial.pronto
