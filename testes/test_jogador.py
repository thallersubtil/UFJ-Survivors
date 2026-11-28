import random
from types import SimpleNamespace

import pygame
import pytest

from jogo.efeitos import AuraSSJ

from jogo.armas.caramelo import Caramelo
from jogo.armas.cobra_python import CobraPython
from jogo.itens.item import Item
from jogo.jogador.classes import CLASSES, MestreDeRPG, Programador, Otaku
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
        self.entrada = SimpleNamespace(direcao=pygame.Vector2(direcao), mira=mira, segurando_especial=False)
        self.arena = pygame.Rect(0, 0, 3200, 1800)
        self.rng = random.Random(1)      # o Programador sorteia se o disparo repete
        self.adicionados = []

    def passo_do_chao(self, posicao):
        return 1.0

    def resolver_obstaculos(self, posicao, raio):
        return posicao

    def adicionar(self, e):
        self.adicionados.append(e)

    def inimigo_mais_proximo(self, posicao, raio, excluir=None):
        return None

    def inimigos_proximos(self, posicao, raio):
        return []


def test_jogador_e_abstrato():
    with pytest.raises(TypeError):
        Jogador((0, 0))


def test_herois_comecam_com_arma_e_especial_proprios():
    from jogo.armas.lightstick import Lightstick
    from jogo.armas.teclado import TecladoMecanico
    agil, forte = Programador((0, 0)), Otaku((0, 0))
    assert isinstance(agil.armas[0], TecladoMecanico)
    assert isinstance(forte.armas[0], Lightstick) and isinstance(forte.especial, SuperSaiyajin)
    assert agil.vida == Programador.VIDA and forte.vida == Otaku.VIDA and forte.vida > agil.vida
    assert agil.velocidade > forte.velocidade
    assert set(CLASSES) >= {Programador, Otaku}


def test_movimento_normalizado_e_preso_na_arena():
    j = Programador((100, 100))
    j.atualizar(0.1, JogoFalso(direcao=(1, 1)))
    andou = j.posicao - pygame.Vector2(100, 100)
    assert andou.length() == pytest.approx(j.velocidade * 0.1)
    j.posicao.update(5, 5)
    j.atualizar(0.1, JogoFalso(direcao=(-1, -1)))
    assert j.posicao.x >= j.raio and j.posicao.y >= j.raio


def test_mira_segue_movimento_ou_mouse():
    j = Programador((100, 100))
    j.atualizar(0.01, JogoFalso(direcao=(0, -1)))
    assert j.direcao_mira == pygame.Vector2(0, -1)
    j.atualizar(0.01, JogoFalso(mira=pygame.Vector2(100, 300)))
    assert j.direcao_mira.y == pytest.approx(1)


def test_curva_de_experiencia_igual_ate_o_nivel_10_e_bem_mais_cara_depois():
    """Até o nível 10 os níveis vêm só das notas, como antes; depois disso o custo cresce em cubo, e
    quem quer passar muito do 15 tem de caçar mini-chefes."""
    def quadratica(nivel):
        n = nivel - 1
        return round(Jogador.XP_BASE + Jogador.XP_LINEAR * n + Jogador.XP_QUADRATICO * n * n)
    for nivel in range(1, Jogador.NIVEL_DA_VIRADA + 1):
        assert Jogador.experiencia_do_nivel(nivel) == quadratica(nivel)
    for nivel in (11, 15, 20, 30):
        extra = Jogador.XP_CUBICO * (nivel - Jogador.NIVEL_DA_VIRADA) ** 3
        assert Jogador.experiencia_do_nivel(nivel) == round(quadratica(nivel) + extra)
    assert Jogador.NIVEL_DA_VIRADA == 10 and Jogador.XP_CUBICO == 10
    assert Jogador.experiencia_do_nivel(20) > 2 * quadratica(20)


@pytest.mark.parametrize("nivel", (3, 9, 12, 18))
def test_experiencia_para_subir_quatro_niveis_e_a_soma_dos_quatro_seguintes(nivel):
    j = Programador((0, 0))
    j.nivel, j.experiencia = nivel, 0
    assert j.experiencia_para_subir(4) == sum(Jogador.experiencia_do_nivel(nivel + i) for i in range(4))
    j.experiencia = 30
    assert j.experiencia_para_subir(4) == sum(Jogador.experiencia_do_nivel(nivel + i) for i in range(4)) - 30


def test_experiencia_sobe_varios_niveis_de_uma_vez():
    j = Programador((0, 0))
    necessario = j.experiencia_necessaria
    assert j.ganhar_experiencia(necessario - 1) == 0
    ganhos = j.ganhar_experiencia(500)
    assert ganhos > 1
    assert j.nivel == 1 + ganhos
    assert 0 <= j.experiencia < j.experiencia_necessaria
    with pytest.raises(ValueError):
        j.ganhar_experiencia(-1)


def test_invencibilidade_depois_de_dano():
    j = Programador((0, 0))
    j.receber_dano(10)
    assert not j.pode_levar_dano
    j.atualizar(0.6, JogoFalso())
    assert j.pode_levar_dano


def test_bonus_multiplicam_e_expiram():
    j = Programador((0, 0))
    base = j.velocidade
    j.adicionar_bonus(BonusTemporario("combo67", "velocidade", 1.5, 1.0))
    j.adicionar_bonus(BonusTemporario("combo67", "velocidade", 1.5, 1.0))
    assert j.velocidade == pytest.approx(base * 1.5)
    j.atualizar(1.1, JogoFalso())
    assert j.velocidade == pytest.approx(base)


def test_itens_recalculam_atributos_e_curam_a_vida_ganha():
    j = Programador((0, 0))
    base = j.velocidade
    item = Turbo()
    j.adicionar_item(item)
    assert j.velocidade == pytest.approx(base * 1.5)
    assert j.vida_maxima == Programador.VIDA + 10 and j.vida == Programador.VIDA + 10
    j.subir_nivel_item(item)
    assert j.velocidade == pytest.approx(base * 2.0)
    assert j.vida_maxima == Programador.VIDA + 20


def test_limites_de_armas_e_itens():
    j = Programador((0, 0))
    for _ in range(3):
        j.adicionar_arma(Caramelo())
    with pytest.raises(ValueError):
        j.adicionar_arma(Caramelo())
    for _ in range(4):
        j.adicionar_item(Turbo())
    with pytest.raises(ValueError):
        j.adicionar_item(Turbo())


def test_super_saiyajin_dobra_o_dano_e_cria_aura():
    j = Otaku((0, 0))
    jogo = JogoFalso()
    assert j.usar_especial(jogo)
    assert j.tem_bonus("ssj")
    assert j.multiplicador_dano == pytest.approx(2.0)
    assert sum(isinstance(e, AuraSSJ) for e in jogo.adicionados) == 1
    assert not j.usar_especial(jogo)


def test_zoltraak_cria_raio():
    j = MestreDeRPG((0, 0))
    jogo = JogoFalso()
    assert j.usar_especial(jogo)
    assert type(jogo.adicionados[0]).__name__ == "RaioZoltraak"


def test_cura_do_aluno_passa_pelo_multiplicador_de_cura():
    j = Programador((0, 0))
    j.vida = 10
    j.curar(10)
    assert j.vida == 20                      # sem Garrafa Térmica a cura é a de sempre
    j.mult_cura = 1.5
    j.curar(10)
    assert j.vida == 35
