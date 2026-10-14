import pygame
import pytest

from jogo.aplicacao import Aplicacao
from jogo.cenas.bau import CenaBau
from jogo.cenas.fim import CenaFimDeJogo
from jogo.cenas.nivel import CenaNivel
from jogo.cenas.partida import CenaPartida
from jogo.cenas.pausa import CenaPausa
from jogo.cenas.ranking import CenaRanking
from jogo.cenas.selecao import CenaSelecao
from jogo.cenas.titulo import CenaTitulo
from jogo.jogador.alunos import AlunoAgil, AlunoResistente
from jogo.ranking import Ranking


def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def texto(t):
    return pygame.event.Event(pygame.TEXTINPUT, text=t)


@pytest.fixture
def app(tmp_path):
    a = Aplicacao(pygame.Surface((1280, 720)))
    a.ranking = Ranking(tmp_path / "ranking.json")
    return a


def test_titulo_jogar_leva_a_selecao(app):
    app.trocar(CenaTitulo(app))
    app.passo(1 / 60, [])
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaSelecao)


def test_titulo_ranking_e_sair(app):
    app.trocar(CenaTitulo(app))
    app.passo(1 / 60, [tecla(pygame.K_DOWN), tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaRanking)
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])
    assert isinstance(app.cena_atual, CenaTitulo)
    app.passo(1 / 60, [tecla(pygame.K_UP), tecla(pygame.K_RETURN)])
    assert not app.rodando


def test_selecao_escolhe_o_segundo_aluno(app):
    app.trocar(CenaSelecao(app))
    app.passo(1 / 60, [tecla(pygame.K_RIGHT), tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaPartida)
    assert isinstance(app.cena_atual.jogo.jogador, AlunoResistente)


def test_selecao_esc_volta_ao_titulo(app):
    app.trocar(CenaSelecao(app))
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])
    assert isinstance(app.cena_atual, CenaTitulo)


def test_subir_de_nivel_abre_cartas_e_tecla_1_escolhe(app):
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    partida.jogo.niveis_pendentes = 2
    app.passo(1 / 60, [])
    assert isinstance(app.cena_atual, CenaNivel)
    app.passo(1 / 60, [tecla(pygame.K_1)])
    assert partida.jogo.niveis_pendentes == 1
    app.passo(1 / 60, [])
    assert isinstance(app.cena_atual, CenaNivel)


def test_sortear_de_novo_e_pular(app):
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    partida.jogo.niveis_pendentes = 1
    app.passo(1 / 60, [])
    app.passo(1 / 60, [tecla(pygame.K_r)])
    assert partida.jogo.sorteios_restantes == 2
    partida.jogo.jogador.vida = 10
    app.passo(1 / 60, [tecla(pygame.K_p)])
    assert partida.jogo.jogador.vida == 30
    assert app.cena_atual is partida


def test_bau_abre_aplica_premio_e_fecha(app):
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    partida.jogo.baus_pendentes = 1
    app.passo(1 / 60, [])
    assert isinstance(app.cena_atual, CenaBau)
    for _ in range(80):
        app.passo(1 / 60, [])
    assert partida.jogo.jogador.armas[0].nivel == 2
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert app.cena_atual is partida and partida.jogo.baus_pendentes == 0


def test_pausa_alterna_mira_e_volta(app):
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])
    assert isinstance(app.cena_atual, CenaPausa)
    tempo = partida.jogo.placar.tempo
    assert app.modo_mira == "mouse"
    app.passo(1 / 60, [tecla(pygame.K_DOWN), tecla(pygame.K_RETURN)])
    assert app.modo_mira == "automatica"
    assert partida.jogo.placar.tempo == tempo
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])
    assert app.cena_atual is partida


def test_fim_de_jogo_grava_nome_no_ranking(app):
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    partida.jogo.placar.adicionar_pontos(321)
    partida.jogo.terminar(False)
    for _ in range(100):
        app.passo(1 / 60, [])
    assert isinstance(app.cena_atual, CenaFimDeJogo)
    app.passo(1 / 60, [texto("A"), texto("n"), texto("a"), tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaRanking)
    assert app.ranking.registros[0].nome == "Ana"
    assert Ranking(app.ranking.caminho).registros[0].nome == "Ana"


def test_espaco_nao_escolhe_carta_nem_fecha_bau(app):
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    partida.jogo.niveis_pendentes = 1
    app.passo(1 / 60, [])
    app.passo(1 / 60, [tecla(pygame.K_SPACE)])
    assert isinstance(app.cena_atual, CenaNivel)
    assert partida.jogo.niveis_pendentes == 1
    app.passo(1 / 60, [tecla(pygame.K_p)])
    partida.jogo.baus_pendentes = 1
    app.passo(1 / 60, [])
    for _ in range(80):
        app.passo(1 / 60, [])
    app.passo(1 / 60, [tecla(pygame.K_SPACE)])
    assert isinstance(app.cena_atual, CenaBau)


def clique(pos=(640, 360)):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


def test_clique_alterna_entre_mira_no_mouse_e_automatica(app):
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    assert app.modo_mira == "mouse"
    app.passo(1 / 60, [])
    assert partida.jogo.entrada.mira is not None
    app.passo(1 / 60, [clique()])
    assert app.modo_mira == "automatica"
    app.passo(1 / 60, [clique()])
    assert app.modo_mira == "mouse"


def test_mira_automatica_aponta_para_o_inimigo_mais_proximo(app):
    from jogo.inimigos.bug import Bug
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    app.modo_mira = "automatica"
    jogo = partida.jogo
    perto = Bug(jogo.jogador.posicao + (150, -40))
    longe = Bug(jogo.jogador.posicao + (-500, 0))
    perto.velocidade = longe.velocidade = 0
    jogo.adicionar(perto)
    jogo.adicionar(longe)
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    partida._ler_entrada()
    assert jogo.entrada.mira == perto.posicao
