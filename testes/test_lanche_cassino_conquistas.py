"""Lanche comprado antes da partida, Roleta do Bandejão e conquistas."""
import random

import pytest

from jogo.jogador.classes import Otaku, Programador
from jogo.jogo import Jogo
from jogo.loja.cassino import JOGOS_DE_APOSTA, RoletaDoBandejao
from jogo.loja.conquistas import CONQUISTAS, Conquistas
from jogo.loja.lanches import LANCHES, Coxinha, PaoDeQueijo
from jogo.loja.progresso import Progresso
from jogo.opcoes import OpcoesDePartida


@pytest.fixture
def progresso(tmp_path):
    p = Progresso(tmp_path / "progresso.json")
    p.moedas = 5000
    return p


def test_lanche_e_guardado_um_por_vez_e_salvo(progresso, tmp_path):
    assert progresso.comprar_lanche(PaoDeQueijo)
    assert not progresso.comprar_lanche(Coxinha)          # um lanche por vez
    assert progresso.lanche_reservado is PaoDeQueijo
    assert Progresso(tmp_path / "progresso.json").lanche_reservado is PaoDeQueijo


def test_lanche_vale_so_na_proxima_partida(progresso):
    progresso.comprar_lanche(PaoDeQueijo)
    opcoes = OpcoesDePartida().com_progresso(progresso)
    assert opcoes.lanche is PaoDeQueijo
    base = Programador((0, 0)).vida_maxima
    jogo = Jogo.a_partir_de(Programador, opcoes, semente=1)
    assert jogo.jogador.vida_maxima == base + PaoDeQueijo.VIDA
    progresso.consumir_lanche()
    assert progresso.lanche_reservado is None


def test_treino_nao_gasta_nem_usa_lanche(progresso):
    from jogo.fase import ProvaDeCalculo
    progresso.comprar_lanche(Coxinha)
    opcoes = OpcoesDePartida.treino_contra(ProvaDeCalculo).com_progresso(progresso)
    assert opcoes.lanche is None


def test_todos_os_lanches_aplicam_algo():
    for classe in LANCHES:
        heroi = Otaku((0, 0))
        antes = (heroi.vida_maxima, heroi.mult_dano, heroi.mult_recarga, heroi.velocidade, heroi.mult_experiencia)
        heroi.receber_melhorias((classe(),))
        depois = (heroi.vida_maxima, heroi.mult_dano, heroi.mult_recarga, heroi.velocidade, heroi.mult_experiencia)
        assert antes != depois, classe.NOME


def test_roleta_do_bandejao_tem_retorno_abaixo_de_100():
    assert RoletaDoBandejao in JOGOS_DE_APOSTA
    roleta = RoletaDoBandejao()
    rng = random.Random(7)
    total = sum(roleta.jogar(100, None, rng).premio for _ in range(20000))
    assert 0.75 < total / (100 * 20000) < 0.98


def jogo_terminado(classe=Programador):
    jogo = Jogo(classe, semente=1)
    return jogo


def test_conquistas_pagam_uma_vez_so(progresso):
    jogo = jogo_terminado()
    jogo.placar.combos_67 = 1
    novas = Conquistas.verificar(jogo, progresso)
    assert any(c.NOME == "67!" for c in novas)
    moedas = progresso.moedas
    assert Conquistas.verificar(jogo, progresso) == []
    assert progresso.moedas == moedas


def test_marcos_da_partida_viram_conquista(progresso):
    jogo = jogo_terminado()
    jogo.marcos.update({"pego_colando", "greve"})
    nomes = {c.CHAVE for c in Conquistas.verificar(jogo, progresso)}
    assert {"pego_colando", "greve"} <= nomes


def test_todos_os_alunos_conta_classes_entre_partidas(progresso):
    from jogo.jogador.classes import CLASSES
    for classe in CLASSES[:-1]:
        Conquistas.verificar(jogo_terminado(classe), progresso)
    assert "todas_as_classes" not in progresso.conquistas
    Conquistas.verificar(jogo_terminado(CLASSES[-1]), progresso)
    assert "todas_as_classes" in progresso.conquistas


def test_conquistas_tem_chave_unica():
    chaves = [c.CHAVE for c in CONQUISTAS]
    assert len(chaves) == len(set(chaves)) >= 8
