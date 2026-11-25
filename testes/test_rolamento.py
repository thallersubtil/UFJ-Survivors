from types import SimpleNamespace

import pygame
import pytest

from jogo.jogador.classes import Programador
from jogo.jogador.rolamento import Rolamento


class JogoFalso:
    def __init__(self, direcao=(0, 0)):
        self.entrada = SimpleNamespace(direcao=pygame.Vector2(direcao), mira=None)
        self.arena = pygame.Rect(0, 0, 3200, 1800)

    def resolver_obstaculos(self, posicao, raio):
        return posicao

    def inimigo_mais_proximo(self, posicao, raio_max, excluir=None):
        return None

    def adicionar(self, entidade):
        pass


def test_rolamento_comeca_pronto_e_entra_em_recarga():
    r = Rolamento()
    assert r.pronto and not r.rolando
    assert r.iniciar(pygame.Vector2(1, 0))
    assert r.rolando and not r.pronto
    assert not r.iniciar(pygame.Vector2(1, 0))
    r.atualizar(Rolamento.DURACAO + Rolamento.RECARGA + 0.01)
    assert r.pronto


def test_impulso_cai_do_maximo_ate_a_velocidade_normal():
    r = Rolamento()
    r.iniciar(pygame.Vector2(0, 1))
    assert r.fator_velocidade == pytest.approx(Rolamento.IMPULSO)
    r.atualizar(Rolamento.DURACAO * 0.99)
    assert 1.0 <= r.fator_velocidade < Rolamento.IMPULSO * 0.5


def test_rolar_deixa_o_heroi_invencivel_so_enquanto_dura():
    j = Programador((500, 500))
    assert j.rolar()
    assert not j.pode_levar_dano
    j.atualizar(Rolamento.DURACAO + Rolamento.TOLERANCIA + 0.01, JogoFalso())
    assert j.pode_levar_dano


def test_rolar_vai_mais_longe_que_andar():
    andando, rolando = Programador((500, 500)), Programador((500, 500))
    rolando.rolar()
    for _ in range(10):
        andando.atualizar(0.02, JogoFalso(direcao=(1, 0)))
        rolando.atualizar(0.02, JogoFalso(direcao=(1, 0)))
    assert rolando.posicao.x - 500 > (andando.posicao.x - 500) * 1.5


def test_rolamento_segue_a_direcao_do_movimento_e_nao_curva():
    j = Programador((500, 500))
    j.atualizar(0.01, JogoFalso(direcao=(0, -1)))
    j.rolar()
    j.atualizar(0.05, JogoFalso(direcao=(1, 0)))
    assert j.posicao.y < 499 and j.posicao.x == pytest.approx(500)


def test_recarga_do_rolamento_cai_com_o_modificador():
    r = Rolamento()
    r.iniciar(pygame.Vector2(1, 0))
    r.atualizar(Rolamento.DURACAO + Rolamento.RECARGA / 2 + 0.01, mult_recarga=0.5)
    assert r.pronto
