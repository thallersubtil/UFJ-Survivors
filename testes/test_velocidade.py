"""Velocidade que evolui aos poucos: inimigos pela dificuldade da prova, o herói pelo nível."""
import pytest

from jogo.inimigos.bug import Bug
from jogo.inimigos.inimigo import Inimigo
from jogo.jogador.classes import CLASSES, Otaku, Programador


def test_inimigo_ganha_velocidade_com_a_dificuldade_ate_um_teto():
    assert Inimigo.fator_de_velocidade(1.0) == pytest.approx(1.0)
    assert Inimigo.fator_de_velocidade(3.0) > Inimigo.fator_de_velocidade(2.0) > 1.0
    assert Inimigo.fator_de_velocidade(1000) == pytest.approx(Inimigo.TETO_VELOCIDADE)
    assert Bug((0, 0), escala=3.0).velocidade == pytest.approx(Bug.VELOCIDADE * Inimigo.fator_de_velocidade(3.0))


def test_no_comeco_o_heroi_mais_lento_ainda_corre_mais_que_o_bug():
    heroi_mais_lento = min(c.VELOCIDADE for c in CLASSES)
    assert Bug((0, 0)).velocidade < heroi_mais_lento


def test_heroi_fica_um_pouco_mais_rapido_a_cada_nivel_ate_um_teto():
    j = Programador((0, 0))
    base = j.velocidade
    j.ganhar_experiencia(sum(6 + n * 3 for n in range(10)))
    assert j.nivel == 11
    assert j.velocidade == pytest.approx(base * (1 + 10 * Programador.GANHO_VELOCIDADE_POR_NIVEL))
    j.ganhar_experiencia(10 ** 6)
    assert j.velocidade == pytest.approx(base * (1 + Programador.TETO_GANHO_VELOCIDADE))


def test_no_fim_do_semestre_o_otaku_evoluido_alcanca_o_bug_mais_rapido():
    otaku = Otaku((0, 0))
    otaku.ganhar_experiencia(10 ** 6)
    assert otaku.velocidade >= Bug.VELOCIDADE * Inimigo.TETO_VELOCIDADE
