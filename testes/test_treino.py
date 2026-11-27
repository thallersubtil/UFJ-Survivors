import pygame
import pytest

from jogo.aplicacao import Aplicacao
from jogo.cenas.fim import CenaFimDeJogo
from jogo.cenas.partida import CenaPartida
from jogo.cenas.matricula import CenaMatricula
from jogo.cenas.titulo import CenaTitulo
from jogo.cenas.treino import CenaTreino
from jogo.fase import CALENDARIO, Semestre
from jogo.jogador.classes import Programador
from jogo.opcoes import OpcoesDePartida
from jogo.loja.progresso import Progresso
from jogo.ranking import Ranking


def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


@pytest.fixture
def app(tmp_path):
    a = Aplicacao(pygame.Surface((1280, 720)))
    a.ranking = Ranking(tmp_path / "ranking.json")
    a.progresso = Progresso(tmp_path / "progresso.json")
    return a


def test_opcoes_padrao_sao_o_semestre_inteiro():
    opcoes = OpcoesDePartida()
    assert not opcoes.treino
    fase = opcoes.criar_fase()
    assert isinstance(fase, Semestre) and fase.provas == CALENDARIO and fase.tempo == 0


def test_opcoes_de_treino_com_um_chefe_e_direto_nele():
    opcoes = OpcoesDePartida.treino_contra(CALENDARIO[2], direto_no_chefe=True, imortal=True)
    assert opcoes.treino
    fase = opcoes.criar_fase()
    assert fase.provas == (CALENDARIO[2],)
    assert fase.tempo == CALENDARIO[2].hora - 3


def test_titulo_tem_botao_de_treino(app):
    app.trocar(CenaTitulo(app))
    app.passo(1 / 60, [tecla(pygame.K_DOWN), tecla(pygame.K_DOWN), tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaTreino)


def test_treino_escolhe_o_professor_e_vai_para_a_matricula(app):
    app.trocar(CenaTreino(app))
    app.passo(1 / 60, [tecla(pygame.K_DOWN), tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaMatricula)
    assert app.cena_atual.opcoes.prova == CALENDARIO[1]
    assert app.cena_atual.opcoes.treino
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])               # Esc no treino volta para a agenda do treino
    assert isinstance(app.cena_atual, CenaTreino)


def test_treino_alterna_direto_no_chefe_e_imortal(app):
    cena = CenaTreino(app)
    app.trocar(cena)
    assert not cena.direto_no_chefe and not cena.imortal
    app.passo(1 / 60, [tecla(pygame.K_c), tecla(pygame.K_i)])
    assert cena.direto_no_chefe and cena.imortal


def test_partida_de_treino_usa_as_opcoes(app):
    opcoes = OpcoesDePartida.treino_contra(CALENDARIO[1], direto_no_chefe=True, imortal=True)
    partida = CenaPartida(app, Programador, opcoes)
    jogo = partida.jogo
    assert jogo.treino and jogo.fase.provas == (CALENDARIO[1],)
    assert jogo.jogador.imortal and not jogo.jogador.pode_levar_dano
    assert not jogo.ferir_jogador(50)


def test_treino_nao_entra_no_ranking(app):
    opcoes = OpcoesDePartida.treino_contra(CALENDARIO[1])
    partida = CenaPartida(app, Programador, opcoes)
    partida.jogo.terminar(venceu=True)
    fim = CenaFimDeJogo(app, partida.jogo)
    app.trocar(fim)
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert len(app.ranking.registros) == 0
    assert isinstance(app.cena_atual, CenaTitulo)


def test_jogo_a_partir_das_opcoes_aplica_tudo():
    from jogo.jogo import Jogo
    opcoes = OpcoesDePartida.treino_contra(CALENDARIO[2], imortal=True)
    jogo = Jogo.a_partir_de(Programador, opcoes, semente=2)
    assert jogo.treino and jogo.jogador.imortal
    assert jogo.fase.provas == (CALENDARIO[2],)


def test_treino_direto_no_chefe_comeca_com_o_aluno_evoluido():
    from jogo.jogo import Jogo
    opcoes = OpcoesDePartida.treino_contra(CALENDARIO[1], direto_no_chefe=True)
    jogo = Jogo.a_partir_de(Programador, opcoes, semente=2)
    assert jogo.jogador.nivel == CALENDARIO[1].nivel_treino
    assert len(jogo.jogador.armas) + len(jogo.jogador.itens) > 3
    assert jogo.niveis_pendentes == 0
    sem_atalho = Jogo.a_partir_de(Programador, OpcoesDePartida.treino_contra(CALENDARIO[1]), semente=2)
    assert sem_atalho.jogador.nivel == 1
