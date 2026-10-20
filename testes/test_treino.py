import pygame
import pytest

from jogo.aplicacao import Aplicacao
from jogo.cenas.fim import CenaFimDeJogo
from jogo.cenas.partida import CenaPartida
from jogo.cenas.selecao import CenaSelecao
from jogo.cenas.titulo import CenaTitulo
from jogo.cenas.treino import CenaTreino
from jogo.fase import PROVAS, ProvaDeArquiteturaEED, ProvaDeTDEPOO
from jogo.jogador.classes import Programador
from jogo.opcoes import OpcoesDePartida
from jogo.ranking import Ranking


def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


@pytest.fixture
def app(tmp_path):
    a = Aplicacao(pygame.Surface((1280, 720)))
    a.ranking = Ranking(tmp_path / "ranking.json")
    return a


def test_opcoes_padrao_sao_o_semestre_inteiro():
    opcoes = OpcoesDePartida()
    assert not opcoes.treino
    fases = opcoes.criar_fases()
    assert [type(f) for f in fases] == list(PROVAS)
    assert all(f.tempo == 0 for f in fases)


def test_opcoes_de_treino_com_um_chefe_e_direto_nele():
    opcoes = OpcoesDePartida.treino_contra(ProvaDeTDEPOO, direto_no_chefe=True, imortal=True)
    assert opcoes.treino
    fases = opcoes.criar_fases()
    assert len(fases) == 1 and isinstance(fases[0], ProvaDeTDEPOO)
    assert fases[0].tempo == fases[0].DURACAO - 3


def test_titulo_tem_botao_de_treino(app):
    app.trocar(CenaTitulo(app))
    app.passo(1 / 60, [tecla(pygame.K_DOWN), tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaTreino)


def test_treino_escolhe_o_professor_e_vai_para_a_selecao(app):
    app.trocar(CenaTreino(app))
    app.passo(1 / 60, [tecla(pygame.K_DOWN), tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaSelecao)
    assert app.cena_atual.opcoes.provas == (ProvaDeArquiteturaEED,)
    assert app.cena_atual.opcoes.treino


def test_treino_alterna_direto_no_chefe_e_imortal(app):
    cena = CenaTreino(app)
    app.trocar(cena)
    assert not cena.direto_no_chefe and not cena.imortal
    app.passo(1 / 60, [tecla(pygame.K_c), tecla(pygame.K_i)])
    assert cena.direto_no_chefe and cena.imortal


def test_partida_de_treino_usa_as_opcoes(app):
    opcoes = OpcoesDePartida.treino_contra(ProvaDeArquiteturaEED, direto_no_chefe=True, imortal=True)
    partida = CenaPartida(app, Programador, opcoes)
    jogo = partida.jogo
    assert jogo.treino and len(jogo.fases) == 1
    assert jogo.jogador.imortal and not jogo.jogador.pode_levar_dano
    assert not jogo.ferir_jogador(50)


def test_treino_nao_entra_no_ranking(app):
    opcoes = OpcoesDePartida.treino_contra(ProvaDeArquiteturaEED)
    partida = CenaPartida(app, Programador, opcoes)
    partida.jogo.terminar(venceu=True)
    fim = CenaFimDeJogo(app, partida.jogo)
    app.trocar(fim)
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert len(app.ranking.registros) == 0
    assert isinstance(app.cena_atual, CenaTitulo)


def test_jogo_a_partir_das_opcoes_aplica_tudo():
    from jogo.jogador.aparencia import Aparencia
    from jogo.jogo import Jogo
    aparencia = Aparencia(cabelo="Ruivo")
    opcoes = OpcoesDePartida.treino_contra(ProvaDeTDEPOO, imortal=True).com_aparencia(aparencia)
    jogo = Jogo.a_partir_de(Programador, opcoes, semente=2)
    assert jogo.treino and jogo.jogador.imortal
    assert jogo.jogador.aparencia == aparencia
    assert [type(f) for f in jogo.fases] == [ProvaDeTDEPOO]


def test_treino_direto_no_chefe_comeca_com_o_aluno_evoluido():
    from jogo.jogo import Jogo
    opcoes = OpcoesDePartida.treino_contra(ProvaDeArquiteturaEED, direto_no_chefe=True)
    jogo = Jogo.a_partir_de(Programador, opcoes, semente=2)
    assert jogo.jogador.nivel == ProvaDeArquiteturaEED.NIVEL_TREINO
    assert len(jogo.jogador.armas) + len(jogo.jogador.itens) > 3
    assert jogo.niveis_pendentes == 0
    sem_atalho = Jogo.a_partir_de(Programador, OpcoesDePartida.treino_contra(ProvaDeArquiteturaEED), semente=2)
    assert sem_atalho.jogador.nivel == 1
