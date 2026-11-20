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


def _app(tmp_path):
    from jogo.aplicacao import Aplicacao
    from jogo.loja.progresso import Progresso
    from jogo.ranking import Ranking
    app = Aplicacao(pygame.Surface((1280, 720)))
    app.ranking, app.progresso = Ranking(tmp_path / "r.json"), Progresso(tmp_path / "p.json")
    return app


def _tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def test_nivel_carimba_a_escolhida_e_volta_depois(tmp_path):
    from jogo.cenas.nivel import CenaNivel
    from jogo.cenas.partida import CenaPartida
    from jogo.jogador.classes import Programador
    app = _app(tmp_path)
    partida = CenaPartida(app, Programador)
    app.trocar(partida)
    partida.jogo.niveis_pendentes = 1
    app.passo(1 / 60, [])
    cena = app.cena_atual
    assert isinstance(cena, CenaNivel)
    app.passo(1 / 60, [_tecla(pygame.K_2)])
    assert cena.escolhida == 1 and partida.jogo.niveis_pendentes == 0
    app.passo(1 / 60, [_tecla(pygame.K_1)])          # durante o carimbo não escolhe de novo
    assert cena.escolhida == 1
    cena.desenhar(pygame.Surface((1280, 720)))
    for _ in range(40):
        app.passo(1 / 60, [])
    assert app.cena_atual is partida


def test_nivel_mouse_acha_a_folha_na_tela(tmp_path):
    from jogo.cenas.nivel import CenaNivel
    from jogo.cenas.partida import CenaPartida
    from jogo.jogador.classes import Programador
    app = _app(tmp_path)
    partida = CenaPartida(app, Programador)
    cena = CenaNivel(app, partida.jogo)
    alvo = cena.cartoes[-1]
    cena.tratar_evento(pygame.event.Event(pygame.MOUSEMOTION, pos=alvo.center, rel=(0, 0), buttons=(0, 0, 0)))
    assert cena.indice == len(cena.opcoes) - 1


def test_pausa_desce_do_menu_para_as_fotos_e_volta(tmp_path):
    from jogo.cenas.partida import CenaPartida
    from jogo.cenas.pausa import CenaPausa
    from jogo.jogador.classes import Otaku
    app = _app(tmp_path)
    partida = CenaPartida(app, Otaku)
    app.trocar(partida)
    app.passo(1 / 60, [_tecla(pygame.K_ESCAPE)])
    pausa = app.cena_atual
    assert isinstance(pausa, CenaPausa)
    app.passo(1 / 60, [_tecla(pygame.K_DOWN)] * 3)
    assert not pausa.no_menu and pausa.foto == 0
    pausa.desenhar(pygame.Surface((1280, 720)))       # mostra a descrição da foto no quadro
    app.passo(1 / 60, [_tecla(pygame.K_UP)])
    assert pausa.no_menu
    app.passo(1 / 60, [_tecla(pygame.K_RETURN)])        # "Ir embora"
    from jogo.cenas.titulo import CenaTitulo
    assert isinstance(app.cena_atual, CenaTitulo)


def test_personalizacao_tira_a_foto_e_so_depois_abre_a_classe(tmp_path):
    from jogo.cenas.personalizacao import CenaPersonalizacao
    from jogo.cenas.selecao import CenaSelecao
    app = _app(tmp_path)
    cena = CenaPersonalizacao(app)
    app.trocar(cena)
    app.passo(1 / 60, [_tecla(pygame.K_DOWN), _tecla(pygame.K_RIGHT)])     # troca a pele
    cena.desenhar(pygame.Surface((1280, 720)))                            # durante a cor se espalhando
    app.passo(1 / 60, [_tecla(pygame.K_RETURN)])
    assert cena.foto_tirada_em is not None and app.cena_atual is cena
    app.passo(1 / 60, [_tecla(pygame.K_DOWN)])                            # depois da foto não mexe mais
    assert cena.linha == 1
    cena.desenhar(pygame.Surface((1280, 720)))
    for _ in range(80):
        app.passo(1 / 60, [])
    assert isinstance(app.cena_atual, CenaSelecao)
