"""Cola: mais experiência em troca de vida máxima, com risco de ser pego colando."""
import random

import pytest

from jogo.itens.itens import Cola, OculosDeGrau
from jogo.jogador.classes import Programador
from jogo.progressao import Progressao


class RngFixo(random.Random):
    """Devolve sempre o mesmo valor em random(), para forçar ou impedir o flagra."""
    def __init__(self, valor):
        super().__init__(0)
        self.valor = valor

    def random(self):
        return self.valor


def heroi_com_cola(nivel=1):
    heroi = Programador((0, 0))
    cola = Cola()
    heroi.adicionar_item(cola)
    while cola.nivel < nivel:
        heroi.subir_nivel_item(cola)
    return heroi, cola


def test_cola_multiplica_experiencia_e_tira_vida_maxima():
    base = Programador((0, 0))
    heroi, cola = heroi_com_cola(1)
    assert heroi.fator_experiencia == pytest.approx(1.5)
    assert heroi.vida_maxima == pytest.approx(base.vida_maxima * 0.85)
    heroi.subir_nivel_item(cola)
    assert heroi.fator_experiencia == pytest.approx(2.0)
    assert heroi.vida_maxima == pytest.approx(base.vida_maxima * 0.80)


def test_cola_no_jogo_rende_mais_notas(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.adicionar_item(Cola())
    jogo.rng = RngFixo(0.99)
    jogo.dar_experiencia(2)
    assert jogo.jogador.experiencia == pytest.approx(3)


def test_pego_colando_reduz_experiencia_por_dois_niveis(jogo_limpo):
    jogo = jogo_limpo()
    heroi = jogo.jogador
    cola = Cola()
    heroi.adicionar_item(cola)
    jogo.rng = RngFixo(0.0)                   # flagra garantido
    jogo.dar_experiencia(heroi.experiencia_necessaria)
    assert cola.punido
    assert heroi.fator_experiencia == pytest.approx(0.5)
    assert any("PEGO COLANDO" in texto for texto, _ in jogo.anuncios)
    vida_cheia = Programador((0, 0)).vida_maxima
    assert heroi.vida_maxima == pytest.approx(vida_cheia)   # a cola foi confiscada: sem bônus e sem custo
    jogo.rng = RngFixo(0.99)
    for _ in range(2):
        jogo.dar_experiencia(heroi.experiencia_necessaria * 2)
    assert not cola.punido
    assert heroi.fator_experiencia == pytest.approx(1.5)


def test_chance_de_flagra_dobra_com_chefe_e_cai_com_oculos(jogo_limpo):
    jogo = jogo_limpo()
    heroi, cola = jogo.jogador, Cola()
    heroi.adicionar_item(cola)
    normal = cola.chance_de_flagra(heroi, jogo)
    class ChefeVivo:
        ativo = True
    jogo.chefe = ChefeVivo()
    assert cola.chance_de_flagra(heroi, jogo) == pytest.approx(normal * 2)
    jogo.chefe = None
    heroi.adicionar_item(OculosDeGrau())
    assert cola.chance_de_flagra(heroi, jogo) < normal


def test_cola_so_aparece_ao_subir_de_nivel_e_nunca_no_bau():
    heroi = Programador((0, 0))
    assert any(o.titulo == Cola.NOME for o in Progressao.candidatas(heroi))
    rng = random.Random(1)
    for _ in range(200):
        assert Progressao.premio_bau(heroi, rng).titulo != Cola.NOME
    heroi, _ = heroi_com_cola(1)
    for _ in range(200):
        assert Progressao.premio_bau(heroi, rng).titulo != Cola.NOME
