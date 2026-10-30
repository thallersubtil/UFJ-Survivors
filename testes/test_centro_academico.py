"""Telas do Centro Acadêmico (hub do menu principal): loja e cassino."""
import pygame
import pytest

from jogo.aplicacao import Aplicacao
from jogo.cenas.cassino import CenaCassino
from jogo.cenas.centro_academico import CenaCentroAcademico
from jogo.cenas.fim import CenaFimDeJogo
from jogo.cenas.loja import CenaLoja
from jogo.cenas.partida import CenaPartida
from jogo.cenas.titulo import CenaTitulo
from jogo.jogador.classes import Programador
from jogo.loja.melhorias import MELHORIAS
from jogo.loja.progresso import Progresso
from jogo.ranking import Ranking


def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


@pytest.fixture
def app(tmp_path):
    app = Aplicacao(pygame.Surface((1280, 720)))
    app.progresso = Progresso(tmp_path / "progresso.json")
    app.ranking = Ranking(tmp_path / "ranking.json")
    return app


def test_titulo_leva_ao_centro_academico(app):
    app.trocar(CenaTitulo(app))
    botoes = [b.texto for b in app.cena_atual.menu.botoes]
    assert "CENTRO ACADÊMICO" in botoes
    app.cena_atual.menu.indice = botoes.index("CENTRO ACADÊMICO")
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaCentroAcademico)
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaLoja)


def test_loja_compra_a_melhoria_escolhida(app):
    app.progresso.ganhar(1000)
    app.trocar(CenaLoja(app))
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert app.progresso.nivel_de(MELHORIAS[0]) == 1
    assert app.progresso.moedas == 1000 - MELHORIAS[0].custo(0)


def test_loja_compra_desbloqueio_na_outra_aba(app):
    app.progresso.ganhar(5000)
    cena = CenaLoja(app)
    app.trocar(cena)
    app.passo(1 / 60, [tecla(pygame.K_TAB), tecla(pygame.K_RETURN)])
    classe = cena.desbloqueaveis()[0]
    assert app.progresso.desbloqueado(classe)


def test_loja_sem_moedas_avisa_e_nao_compra(app):
    cena = CenaLoja(app)
    app.trocar(cena)
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert app.progresso.nivel_de(MELHORIAS[0]) == 0
    assert "insuficientes" in cena.mensagem


def test_cassino_aposta_e_mostra_resultado_depois_do_giro(app):
    app.progresso.ganhar(100)
    cena = CenaCassino(app)
    app.trocar(cena)
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert cena.girando
    for _ in range(120):
        app.passo(1 / 60, [])
    assert not cena.girando and cena.resultado is not None
    assert app.progresso.moedas == 100 - cena.resultado.aposta + cena.resultado.premio


def test_cassino_sem_moedas_nao_joga(app):
    cena = CenaCassino(app)
    app.trocar(cena)
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert not cena.girando and "insuficientes" in cena.mensagem


def test_fim_de_jogo_deposita_as_moedas_uma_vez(app):
    partida = CenaPartida(app, Programador)
    partida.jogo.placar.adicionar_moedas(42)
    partida.jogo.terminar(False)
    CenaFimDeJogo(app, partida.jogo)
    assert app.progresso.moedas == partida.jogo.moedas_ganhas() >= 42


def test_partida_usa_as_melhorias_compradas(app):
    app.progresso.ganhar(10_000)
    app.progresso.comprar_melhoria(MELHORIAS[0])
    app.trocar(CenaTitulo(app))
    app.cena_atual._jogar()
    assert app.cena_atual.opcoes.melhorias


def test_shift_rola(app):
    cena = CenaPartida(app, Programador)
    app.trocar(cena)
    app.passo(1 / 60, [tecla(pygame.K_LSHIFT)])
    assert cena.jogo.jogador.rolamento.rolando


@pytest.mark.parametrize("classe", [CenaCentroAcademico, CenaLoja, CenaCassino])
def test_telas_do_centro_desenham_e_voltam_com_esc(app, classe):
    app.trocar(classe(app))
    app.passo(1 / 60, [tecla(pygame.K_TAB), tecla(pygame.K_DOWN), tecla(pygame.K_RIGHT)])
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])
    assert not isinstance(app.cena_atual, classe)
