import pygame

from jogo.aplicacao import Aplicacao
from jogo.cenas.partida import CenaPartida
from jogo.jogador.classes import Programador


def tecla(k, tipo=pygame.KEYDOWN):
    return pygame.event.Event(tipo, key=k, mod=0, unicode="", scancode=0)


def test_partida_roda_alguns_quadros_e_desenha_o_hud():
    app = Aplicacao(pygame.Surface((1280, 720)))
    app.trocar(CenaPartida(app, Programador))
    for _ in range(30):
        app.passo(1 / 60, [])
    assert app.cena_atual.jogo.placar.tempo > 0.4


def test_espaco_usa_o_especial():
    app = Aplicacao(pygame.Surface((1280, 720)))
    cena = CenaPartida(app, Programador)
    app.trocar(cena)
    app.passo(1 / 60, [tecla(pygame.K_SPACE)])
    assert not cena.jogo.jogador.especial.pronto


def test_janela_nitida_amplia_o_jogo_sem_suavizar():
    from jogo.aplicacao import JanelaNitida
    janela = JanelaNitida("teste", (64, 36))
    janela.tela.fill((0, 0, 0))
    janela.tela.set_at((10, 10), (255, 0, 0))
    janela.mostrar()
    destino = janela.janela.get_surface()
    fator = destino.get_width() // 64
    assert destino.get_size() == (64 * fator, 36 * fator)
    assert destino.get_at((10 * fator, 10 * fator))[:3] == (255, 0, 0)
    assert destino.get_at((10 * fator + fator - 1, 10 * fator + fator - 1))[:3] == (255, 0, 0)
    janela.janela.destroy()


def test_janela_nitida_se_ajusta_a_tamanho_fora_da_proporcao():
    from jogo.aplicacao import JanelaNitida
    janela = JanelaNitida("teste", (64, 36))
    janela.tela.fill((200, 0, 0))
    janela.janela.size = (100, 80)
    janela.mostrar()
    destino = janela.janela.get_surface()
    w, h = destino.get_size()
    assert destino.get_at((w // 2, h // 2))[:3] == (200, 0, 0)
    assert destino.get_at((w // 2, 0))[:3] == (0, 0, 0)   # faixa preta em cima (proporção mantida)
    janela.janela.destroy()
