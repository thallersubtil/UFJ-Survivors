"""Cassino do Centro Acadêmico: apostas com as moedas do jogo."""
import random

import pytest

from jogo.loja.cassino import Cassino, DadoDoMestre, JogoDeAposta, MaquinaDeSalgadinho
from jogo.loja.progresso import Progresso


class RngFixo:
    """Devolve sempre os valores dados, em ordem, para testar os prêmios."""

    def __init__(self, *valores):
        self.valores = list(valores)

    def choice(self, sequencia):
        return self.valores.pop(0)

    def randint(self, a, b):
        return self.valores.pop(0)


def test_jogo_de_aposta_e_abstrato():
    with pytest.raises(TypeError):
        JogoDeAposta()


def test_tres_iguais_pagam_mais_que_dois():
    maquina = MaquinaDeSalgadinho()
    tres = maquina.jogar(10, None, RngFixo("Pequi", "Pequi", "Pequi"))
    dois = maquina.jogar(10, None, RngFixo("Pequi", "Pequi", "Café"))
    nada = maquina.jogar(10, None, RngFixo("Pequi", "Café", "Nota 10"))
    assert tres.premio > dois.premio > nada.premio == 0
    assert tres.simbolos == ("Pequi", "Pequi", "Pequi")


def test_67_67_67_e_o_premio_maximo():
    maquina = MaquinaDeSalgadinho()
    jackpot = maquina.jogar(10, None, RngFixo("67", "67", "67"))
    assert jackpot.premio == 10 * max(MaquinaDeSalgadinho.TRIO.values())


def test_dado_acima_ou_abaixo():
    dado = DadoDoMestre()
    assert dado.jogar(10, "acima", RngFixo(15)).premio == 19
    assert dado.jogar(10, "acima", RngFixo(5)).premio == 0
    assert dado.jogar(10, "abaixo", RngFixo(5)).premio == 19
    assert dado.jogar(10, "abaixo", RngFixo(20)).premio == DadoDoMestre.CRITICO * 10   # 20 natural sempre paga
    assert dado.jogar(10, "acima", RngFixo(1)).premio == 0                               # 1 natural sempre perde
    with pytest.raises(ValueError):
        dado.jogar(10, "talvez", RngFixo(3))


def test_a_casa_sempre_ganha_no_longo_prazo():
    rng = random.Random(1)
    for jogo, escolha in ((MaquinaDeSalgadinho(), None), (DadoDoMestre(), "acima")):
        assert sum(jogo.jogar(10, escolha, rng).premio for _ in range(20_000)) < 10 * 20_000


def test_apostar_desconta_e_paga_no_progresso(tmp_path):
    p = Progresso(tmp_path / "p.json")
    p.ganhar(100)
    resultado = Cassino.apostar(p, DadoDoMestre(), 50, "acima", RngFixo(15))
    assert resultado.premio == 95 and p.moedas == 145
    with pytest.raises(ValueError):
        Cassino.apostar(p, DadoDoMestre(), 1000, "acima", RngFixo(15))
    with pytest.raises(ValueError):
        Cassino.apostar(p, DadoDoMestre(), 0, "acima", RngFixo(15))
    assert p.moedas == 145
