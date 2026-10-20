from types import SimpleNamespace

import pytest

from jogo.armas.arma import Arma, ArmaDeContato, ArmaDeDisparo
from jogo.itens.item import Item
from jogo.jogador.bonus import BonusTemporario
from jogo.jogador.especial import Especial


class Estilingue(ArmaDeDisparo):
    NOME = "Estilingue"
    ATRIBUTOS = {"recarga": (1.0,) * 7}
    MELHORIAS = ("+",) * 6

    def __init__(self):
        super().__init__()
        self.disparos = 0

    def disparar(self, jogo, dono):
        self.disparos += 1
        return True


class Soco(ArmaDeContato):
    NOME = "Soco"
    MELHORIAS = ("a", "b", "c", "d", "e", "f")

    def atualizar(self, dt, jogo, dono):
        pass


class Amuleto(Item):
    NOME = "Amuleto"
    MELHORIAS = ("x", "y")

    def aplicar(self, jogador):
        jogador.sorte += self.nivel


class Grito(Especial):
    NOME = "Grito"
    RECARGA = 10.0

    def ativar(self, dono, jogo):
        dono.gritou = True


def dono_falso():
    return SimpleNamespace(mult_cafe=1.0, mult_recarga=1.0, multiplicador_recarga=1.0, multiplicador_dano=1.0)


def test_arma_e_abstrata():
    with pytest.raises(TypeError):
        Arma()
    with pytest.raises(TypeError):
        ArmaDeDisparo()


def test_nivel_da_arma_validado():
    s = Soco()
    assert s.nivel == 1
    with pytest.raises(ValueError):
        s.nivel = 0
    with pytest.raises(ValueError):
        s.nivel = 8
    with pytest.raises(TypeError):
        s.nivel = 2.0
    for _ in range(6):
        s.subir_nivel()
    assert s.no_maximo
    with pytest.raises(ValueError):
        s.subir_nivel()


def test_descricao_do_proximo_nivel_e_str():
    s = Soco()
    assert s.descricao_proxima() == "a"
    s.subir_nivel()
    assert s.descricao_proxima() == "b"
    assert str(s) == "Soco (nível 2)"
    assert s.fracao_cafe is None


def test_municao_validada():
    e = Estilingue()
    assert e.municao == e.municao_maxima == 12
    with pytest.raises(ValueError):
        e.municao = -1
    e.municao = 500
    assert e.municao == 12
    e.municao = 0
    assert not e.tem_cafe
    e.encher()
    assert e.municao == 12


def test_disparo_gasta_cafe_e_sem_cafe_atira_mais_devagar():
    e = Estilingue()
    dono = dono_falso()
    e.atualizar(0.0, None, dono)
    assert e.disparos == 1
    assert e.municao == 11
    e.municao = 0
    e.atualizar(1.0, None, dono)
    assert e.disparos == 2
    e.atualizar(1.5, None, dono)
    assert e.disparos == 2
    assert e.fracao_cafe == pytest.approx(e.municao / 12)


def test_item_nivel_ate_3_e_aplicar():
    a = Amuleto()
    jogador = SimpleNamespace(sorte=0)
    a.subir_nivel()
    a.subir_nivel()
    assert a.no_maximo
    with pytest.raises(ValueError):
        a.subir_nivel()
    a.aplicar(jogador)
    assert jogador.sorte == 3


def test_especial_recarga():
    g = Grito()
    dono = SimpleNamespace(gritou=False)
    assert g.pronto
    assert g.usar(dono, None) is True
    assert dono.gritou
    assert not g.pronto
    assert g.usar(dono, None) is False
    g.atualizar(5.0)
    assert g.progresso == pytest.approx(0.5)
    g.atualizar(2.5, mult_recarga=0.5)
    assert g.pronto


def test_bonus_temporario_expira():
    b = BonusTemporario("ssj", "dano", 2.0, 1.0)
    assert b.ativo
    b.atualizar(1.0)
    assert not b.ativo
