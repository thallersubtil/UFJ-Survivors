"""Mecânicas inspiradas no HoloCure: variação de dano, crítico acima de 100%, moedas por prova,
pesos (inimigos e cartas), banir carta, cartas de atributo e Bigorna."""
import random

import pytest

from jogo.armas.cobra_python import CobraPython
from jogo.coletaveis.coletaveis import Bigorna
from jogo.fase import ProvaDeCalculo, ProvaDeTDEPOO
from jogo.inimigos.bug import Bug
from jogo.itens.itens import Cola, ITENS
from jogo.jogador.classes import Programador
from jogo.progressao import Progressao


def test_dano_varia_dez_por_cento(jogo_limpo):
    jogo = jogo_limpo()
    danos = set()
    for _ in range(40):
        bug = Bug(jogo.jogador.posicao + (300, 0), escala=1000)
        jogo.adicionar(bug)
        jogo._incorporar_novas()
        vida = bug.vida
        jogo.causar_dano(bug, 100)
        danos.add(vida - bug.vida)
    assert min(danos) >= 90 and max(danos) <= 110 and len(danos) > 5


def test_critico_acima_de_cem_por_cento_bate_mais_forte(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.chance_critico = 1.5
    bug = Bug(jogo.jogador.posicao + (300, 0), escala=1000)
    jogo.adicionar(bug)
    jogo._incorporar_novas()
    vida = bug.vida
    jogo.causar_dano(bug, 100)
    assert vida - bug.vida >= 100 * 2.5 * 0.9


def test_provas_seguintes_pagam_mais_moedas():
    assert ProvaDeTDEPOO.MULT_MOEDAS > ProvaDeCalculo.MULT_MOEDAS == 1.0


def test_inimigos_da_materia_nascem_mais(jogo_limpo):
    jogo = jogo_limpo()
    fase = ProvaDeCalculo()
    fase.atualizar(31, jogo)
    assert fase.pesos[fase.ativos.index("calculadora")] > fase.pesos[fase.ativos.index("bug")]


def test_cartas_respeitam_o_peso():
    heroi = Programador((0, 0))
    rng = random.Random(3)
    contagem = {}
    for _ in range(3000):
        for opcao in Progressao.gerar_opcoes(heroi, rng):
            contagem[opcao.titulo] = contagem.get(opcao.titulo, 0) + 1
    assert contagem.get(Cola.NOME, 0) < contagem["Caderno de Resumos"] * 0.8


def test_banir_tira_a_carta_pelo_resto_da_partida():
    heroi = Programador((0, 0))
    heroi.banir(Cola)
    assert all(o.titulo != Cola.NOME for o in Progressao.candidatas(heroi))


def test_sem_nada_para_oferecer_aparecem_as_cartas_de_vida_e_de_moedas():
    """As cartas de atributo (dano, recarga, vida máxima) saíram: quem baniu tudo escolhe entre vida e moedas."""
    heroi = Programador((0, 0))
    for classe in ITENS + Progressao.ARMAS:
        heroi.banir(classe)
    opcoes = Progressao.gerar_opcoes(heroi, random.Random(1))
    assert len(opcoes) == 2 and {o.tipo for o in opcoes} == {"maximo"}
    dano = heroi.mult_dano
    heroi.vida = 1
    next(o for o in opcoes if "vida" in o.descricao).aplicar(heroi, None)
    assert heroi.vida > 1 and heroi.mult_dano == dano


def test_bigorna_afia_uma_arma(jogo_limpo):
    jogo = jogo_limpo()
    arma = jogo.jogador.armas[0]
    antes = arma.valor("dano")
    Bigorna(jogo.jogador.posicao).ao_coletar(jogo)
    assert arma.carimbos == 1 and arma.valor("dano") == pytest.approx(antes * 1.15)
    assert any("Bigorna" in t for t, _ in jogo.anuncios)


def test_tecla_b_bane_a_carta_destacada(tmp_path):
    import pygame
    from jogo.aplicacao import Aplicacao
    from jogo.cenas.nivel import CenaNivel
    from jogo.cenas.partida import CenaPartida
    from jogo.loja.progresso import Progresso
    from jogo.ranking import Ranking
    app = Aplicacao(pygame.Surface((1280, 720)))
    app.ranking, app.progresso = Ranking(tmp_path / "r.json"), Progresso(tmp_path / "p.json")
    partida = CenaPartida(app, Programador)
    app.trocar(partida)
    partida.jogo.niveis_pendentes = 1
    app.passo(1 / 60, [])
    cena = app.cena_atual
    assert isinstance(cena, CenaNivel)
    alvo = next(o for o in cena.opcoes if o.origem is not None)
    cena.indice = cena.opcoes.index(alvo)
    cena.banir()
    assert alvo.origem in partida.jogo.jogador.banidos
    assert partida.jogo.banimentos_restantes == 2
    assert all(o.origem is not alvo.origem for o in cena.opcoes)
