from types import SimpleNamespace

import pygame
import pytest

from jogo.armas.caramelo import Caramelo
from jogo.armas.cobra_python import CobraPython
from jogo.projeteis.projeteis import CobraProjetil, ProjetilDivisivel


class JogoFalso:
    def __init__(self):
        self.adicionados = []

    def adicionar(self, entidade):
        self.adicionados.append(entidade)


def dono_falso():
    return SimpleNamespace(posicao=pygame.Vector2(100, 100), direcao_mira=pygame.Vector2(1, 0),
                           multiplicador_dano=1.0, mult_cafe=1.0, mult_recarga=1.0)


@pytest.mark.parametrize("classe", [CobraPython, Caramelo])
def test_tabelas_de_atributos_tem_um_valor_por_nivel(classe):
    for valores in classe.ATRIBUTOS.values():
        assert len(valores) == classe.NIVEL_MAXIMO
    assert len(classe.MELHORIAS) == classe.NIVEL_MAXIMO - 1


def test_cobra_dispara_mais_cobras_nos_niveis_altos():
    jogo, dono = JogoFalso(), dono_falso()
    arma = CobraPython()
    assert arma.disparar(jogo, dono)
    assert len(jogo.adicionados) == 1
    for _ in range(2):
        arma.subir_nivel()
    jogo.adicionados.clear()
    arma.disparar(jogo, dono)
    assert len(jogo.adicionados) == 2
    assert all(isinstance(c, CobraProjetil) for c in jogo.adicionados)
    assert jogo.adicionados[0].dano == arma.valor("dano")


def test_cobra_avanca_ondulando():
    cobra = CobraProjetil((0, 0), (400, 0), 10)
    ys = []
    for _ in range(20):
        cobra.tempo += 0.02
        cobra.mover(0.02)
        ys.append(cobra.posicao.y)
    assert cobra.posicao.x == pytest.approx(160, abs=1)
    assert max(ys) > 5 and min(ys) < -5


def test_projetil_divisivel_cria_duas_metades():
    class Estrelinha(ProjetilDivisivel):
        pass

    jogo = JogoFalso()
    p = Estrelinha((0, 0), (300, 0), 10, geracoes=1)
    p.ao_acertar(None, jogo)
    assert len(jogo.adicionados) == 2
    assert all(f.geracoes == 0 and f.dano == pytest.approx(7) for f in jogo.adicionados)
    jogo.adicionados.clear()
    jogo.adicionados[:] = []
    filho = Estrelinha((0, 0), (300, 0), 10, geracoes=0)
    filho.ao_acertar(None, jogo)
    assert jogo.adicionados == []


def test_caramelo_cria_e_recria_cachorros_conforme_o_nivel():
    jogo, dono = JogoFalso(), dono_falso()
    arma = Caramelo()
    arma.atualizar(0.016, jogo, dono)
    assert len(arma.cachorros) == 1
    arma.subir_nivel()
    arma.atualizar(0.016, jogo, dono)
    assert len(arma.cachorros) == 2
    assert sum(c.ativo for c in jogo.adicionados) == 2
    arma.ao_remover(jogo)
    assert not any(c.ativo for c in jogo.adicionados)
