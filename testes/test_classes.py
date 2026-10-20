"""Classes de personagem: cada uma com arma inicial (ativa), passiva e especial próprios."""
import random

import pytest

from jogo.armas.caramelo import Caramelo
from jogo.armas.cobra_python import CobraPython
from jogo.armas.gemini import Gemini
from jogo.inimigos.bug import Bug
from jogo.jogador.classes import CLASSES, MestreDeRPG, Otaku, Programador
from jogo.jogador.especiais import SuperSaiyajin, ViradaDeNoite, Zoltraak
from jogo.jogador.passiva import Passiva
from jogo.jogador.passivas import Cafeinado, InstintoOtaku, RolagemDeIniciativa


def subir_ate(jogador, nivel):
    while jogador.nivel < nivel:
        jogador.ganhar_experiencia(jogador.experiencia_necessaria - jogador.experiencia)


def test_passiva_e_abstrata():
    with pytest.raises(TypeError):
        Passiva()


@pytest.mark.parametrize("classe, arma, passiva, especial", [
    (Otaku, Caramelo, InstintoOtaku, SuperSaiyajin),
    (Programador, CobraPython, Cafeinado, ViradaDeNoite),
    (MestreDeRPG, Gemini, RolagemDeIniciativa, Zoltraak),
])
def test_cada_classe_tem_ativa_passiva_e_especial_proprios(classe, arma, passiva, especial):
    j = classe((0, 0))
    assert [type(a) for a in j.armas] == [arma]
    assert isinstance(j.passiva, passiva)
    assert isinstance(j.especial, especial)
    assert classe in CLASSES


def test_classes_tem_nome_e_descricao():
    for classe in CLASSES:
        j = classe((0, 0))
        assert classe.NOME and classe.DESCRICAO
        assert j.passiva.NOME and j.passiva.DESCRICAO


def test_otaku_ganha_chance_de_critico_a_cada_nivel():
    j = Otaku((0, 0))
    inicial = j.chance_critico
    assert inicial > 0
    subir_ate(j, 10)
    assert j.chance_critico > inicial
    subir_ate(j, 200)
    assert j.chance_critico == pytest.approx(InstintoOtaku.MAXIMO)


def test_outras_classes_nao_tem_critico():
    assert Programador((0, 0)).chance_critico == 0
    assert MestreDeRPG((0, 0)).chance_critico == 0


def test_programador_recarrega_mais_rapido_conforme_sobe_de_nivel():
    j = Programador((0, 0))
    antes = j.mult_recarga
    subir_ate(j, 11)
    assert j.mult_recarga < antes


def test_mestre_de_rpg_recarrega_o_especial_mais_rapido():
    j = MestreDeRPG((0, 0))
    j.especial.restante = j.especial.RECARGA
    subir_ate(j, 20)
    assert j.mult_especial < 1
    restante = j.especial.restante
    j.especial.atualizar(1.0, j.mult_recarga * j.mult_especial)
    assert restante - j.especial.restante > 1.0


def test_critico_dobra_o_dano(jogo_limpo):
    jogo = jogo_limpo(Otaku)
    jogo.jogador.chance_critico = 1.0
    bug = Bug(jogo.jogador.posicao + (300, 0), escala=100)
    jogo.adicionar(bug)
    jogo._incorporar_novas()
    vida = bug.vida
    jogo.causar_dano(bug, 10)
    assert vida - bug.vida == 10 * jogo.jogador.MULT_CRITICO


def test_sem_chance_de_critico_o_dano_e_o_normal(jogo_limpo):
    jogo = jogo_limpo(Programador)
    bug = Bug(jogo.jogador.posicao + (300, 0), escala=100)
    jogo.adicionar(bug)
    jogo._incorporar_novas()
    vida = bug.vida
    jogo.causar_dano(bug, 10)
    assert vida - bug.vida == 10


def test_virada_de_noite_enche_o_cafe_e_acelera_as_armas(jogo_limpo):
    jogo = jogo_limpo(Programador)
    j = jogo.jogador
    j.armas[0].municao = 0
    assert j.usar_especial(jogo)
    assert j.armas[0].municao == j.armas[0].municao_maxima
    assert j.multiplicador_recarga < j.mult_recarga


def test_otaku_vira_super_saiyajin_no_especial(jogo_limpo):
    jogo = jogo_limpo(Otaku)
    jogo.jogador.usar_especial(jogo)
    assert jogo.jogador.tem_bonus("ssj")
    assert jogo.jogador.multiplicador_dano == pytest.approx(2.0)


def test_cartas_de_nivel_funcionam_com_todas_as_classes(jogo_limpo):
    from jogo.progressao import Progressao
    for classe in CLASSES:
        jogo = jogo_limpo(classe)
        for _ in range(30):
            Progressao.gerar_opcoes(jogo.jogador, random.Random(1))[0].aplicar(jogo.jogador, jogo)
        assert len(jogo.jogador.armas) <= jogo.jogador.MAX_ARMAS
