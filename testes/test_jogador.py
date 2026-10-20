from types import SimpleNamespace

import pygame
import pytest

from jogo.armas.caramelo import Caramelo
from jogo.armas.cobra_python import CobraPython
from jogo.itens.item import Item
from jogo.jogador.alunos import HEROIS, AlunoAgil, AlunoResistente
from jogo.jogador.bonus import BonusTemporario
from jogo.jogador.especiais import SuperSaiyajin, Zoltraak
from jogo.jogador.jogador import Jogador


class Turbo(Item):
    NOME = "Turbo"
    MELHORIAS = ("a", "b")

    def aplicar(self, jogador):
        jogador.mult_velocidade += 0.5 * self.nivel
        jogador.vida_maxima_extra += 10 * self.nivel


class JogoFalso:
    def __init__(self, direcao=(0, 0), mira=None):
        self.entrada = SimpleNamespace(direcao=pygame.Vector2(direcao), mira=mira)
        self.arena = pygame.Rect(0, 0, 3200, 1800)
        self.adicionados = []

    def resolver_obstaculos(self, posicao, raio):
        return posicao

    def adicionar(self, e):
        self.adicionados.append(e)


def test_jogador_e_abstrato():
    with pytest.raises(TypeError):
        Jogador((0, 0))


def test_herois_comecam_com_arma_e_especial_proprios():
    agil, forte = AlunoAgil((0, 0)), AlunoResistente((0, 0))
    assert isinstance(agil.armas[0], CobraPython) and isinstance(agil.especial, Zoltraak)
    assert isinstance(forte.armas[0], Caramelo) and isinstance(forte.especial, SuperSaiyajin)
    assert agil.vida == 80 and forte.vida == 130
    assert agil.velocidade > forte.velocidade
    assert HEROIS == (AlunoAgil, AlunoResistente)


def test_movimento_normalizado_e_preso_na_arena():
    j = AlunoAgil((100, 100))
    j.atualizar(0.1, JogoFalso(direcao=(1, 1)))
    andou = j.posicao - pygame.Vector2(100, 100)
    assert andou.length() == pytest.approx(j.velocidade * 0.1)
    j.posicao.update(5, 5)
    j.atualizar(0.1, JogoFalso(direcao=(-1, -1)))
    assert j.posicao.x >= j.raio and j.posicao.y >= j.raio


def test_mira_segue_movimento_ou_mouse():
    j = AlunoAgil((100, 100))
    j.atualizar(0.01, JogoFalso(direcao=(0, -1)))
    assert j.direcao_mira == pygame.Vector2(0, -1)
    j.atualizar(0.01, JogoFalso(mira=pygame.Vector2(100, 300)))
    assert j.direcao_mira.y == pytest.approx(1)


def test_experiencia_sobe_varios_niveis_de_uma_vez():
    j = AlunoAgil((0, 0))
    necessario = j.experiencia_necessaria
    assert j.ganhar_experiencia(necessario - 1) == 0
    ganhos = j.ganhar_experiencia(500)
    assert ganhos > 1
    assert j.nivel == 1 + ganhos
    assert 0 <= j.experiencia < j.experiencia_necessaria
    with pytest.raises(ValueError):
        j.ganhar_experiencia(-1)


def test_invencibilidade_depois_de_dano():
    j = AlunoAgil((0, 0))
    j.receber_dano(10)
    assert not j.pode_levar_dano
    j.atualizar(0.6, JogoFalso())
    assert j.pode_levar_dano


def test_bonus_multiplicam_e_expiram():
    j = AlunoAgil((0, 0))
    base = j.velocidade
    j.adicionar_bonus(BonusTemporario("combo67", "velocidade", 1.5, 1.0))
    j.adicionar_bonus(BonusTemporario("combo67", "velocidade", 1.5, 1.0))
    assert j.velocidade == pytest.approx(base * 1.5)
    j.atualizar(1.1, JogoFalso())
    assert j.velocidade == pytest.approx(base)


def test_itens_recalculam_atributos_e_curam_a_vida_ganha():
    j = AlunoAgil((0, 0))
    base = j.velocidade
    item = Turbo()
    j.adicionar_item(item)
    assert j.velocidade == pytest.approx(base * 1.5)
    assert j.vida_maxima == 90 and j.vida == 90
    j.subir_nivel_item(item)
    assert j.velocidade == pytest.approx(base * 2.0)
    assert j.vida_maxima == 100


def test_limites_de_armas_e_itens():
    j = AlunoAgil((0, 0))
    for _ in range(3):
        j.adicionar_arma(Caramelo())
    with pytest.raises(ValueError):
        j.adicionar_arma(Caramelo())
    for _ in range(4):
        j.adicionar_item(Turbo())
    with pytest.raises(ValueError):
        j.adicionar_item(Turbo())


def test_super_saiyajin_dobra_o_dano_e_cria_aura():
    j = AlunoResistente((0, 0))
    jogo = JogoFalso()
    assert j.usar_especial(jogo)
    assert j.tem_bonus("ssj")
    assert j.multiplicador_dano == pytest.approx(2.0)
    assert len(jogo.adicionados) == 1
    assert not j.usar_especial(jogo)


def test_zoltraak_cria_raio():
    j = AlunoAgil((0, 0))
    jogo = JogoFalso()
    assert j.usar_especial(jogo)
    assert type(jogo.adicionados[0]).__name__ == "RaioZoltraak"


def test_encher_cafe_so_afeta_armas_de_disparo():
    j = AlunoAgil((0, 0))
    j.adicionar_arma(Caramelo())
    j.armas[0].municao = 0
    j.encher_cafe()
    assert j.armas[0].municao == j.armas[0].municao_maxima
