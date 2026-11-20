"""Interface nova (inspirada no HoloCure): HUD, nível, pausa e as telas do Centro Acadêmico."""
import pygame

from jogo.cenas.hud import Hud
from jogo.ui.pixel import A, L, CamadaPixel, barra, moldura, texto


def test_camada_pixel_amplia_para_a_tela_inteira():
    camada = CamadaPixel()
    ui = camada.limpar()
    assert ui.get_size() == (L, A) == (640, 360)
    pygame.draw.rect(ui, (255, 0, 0), (0, 0, 1, 1))
    tela = pygame.Surface((1280, 720))
    camada.apresentar(tela)
    assert tela.get_at((1, 1))[:3] == (255, 0, 0)       # 1 px da camada vira um bloco 2x2
    assert CamadaPixel.para_camada((101, 51)) == (50, 25)


def test_pecas_basicas_desenham_sem_erro():
    ui = CamadaPixel().limpar()
    r = texto(ui, "Olá", (10, 10))
    assert r.w > 0
    moldura(ui, (0, 0, 40, 20), alfa=200)
    barra(ui, (0, 30, 50, 6), 1.4, (255, 0, 0), atraso=0.5, segmentos=5, brilho_t=0.3)


def test_hud_desenha_a_partida(jogo_limpo):
    jogo = jogo_limpo()
    hud = Hud()
    tela = pygame.Surface((1280, 720))
    hud.atualizar(1 / 60, jogo)
    hud.desenhar(tela, jogo)


def test_hud_barra_de_vida_cai_aos_poucos(jogo_limpo):
    jogo = jogo_limpo()
    hud = Hud()
    hud.atualizar(1 / 60, jogo)
    jogo.jogador.vida = jogo.jogador.vida_maxima / 2
    hud.atualizar(1 / 60, jogo)
    assert hud.vida_atrasada > 0.9                   # o branco do dano ainda aparece
    for _ in range(180):
        hud.atualizar(1 / 60, jogo)
    assert abs(hud.vida_atrasada - 0.5) < 0.01


def test_hud_avisa_quando_sobe_de_nivel(jogo_limpo):
    jogo = jogo_limpo()
    hud = Hud()
    hud.atualizar(1 / 60, jogo)
    assert hud.destaque_nivel == 0
    jogo.jogador.nivel += 1
    hud.atualizar(1 / 60, jogo)
    assert hud.destaque_nivel > 0
