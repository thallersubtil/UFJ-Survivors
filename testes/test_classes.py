"""Classes de personagem: cada uma com arma inicial (ativa), três habilidades e especial próprios."""
import random

import pytest

from jogo.armas.lightstick import Lightstick
from jogo.armas.teclado import TecladoMecanico
from jogo.armas.dado import DadoDeVinteLados
from jogo.inimigos.bug import Bug
from jogo.jogador.classes import CLASSES, MestreDeRPG, Otaku, Programador
from jogo.jogador.especiais import SuperSaiyajin, ViradaDeNoite, Zoltraak
from jogo.jogador.habilidade import Habilidade
from jogo.jogador.habilidades import (Bis, Cafeinado, Compilar, FichaDePersonagem, HypeDoShow, LacoDeRepeticao,
                                      RolagemDeIniciativa, TesteDeResistencia, Wotagei)


def test_habilidade_e_abstrata():
    with pytest.raises(TypeError):
        Habilidade()


@pytest.mark.parametrize("classe, arma, habilidades, especial", [
    (Otaku, Lightstick, (Wotagei, Bis, HypeDoShow), SuperSaiyajin),
    (Programador, TecladoMecanico, (LacoDeRepeticao, Cafeinado, Compilar), ViradaDeNoite),
    (MestreDeRPG, DadoDeVinteLados, (RolagemDeIniciativa, FichaDePersonagem, TesteDeResistencia), Zoltraak),
])
def test_cada_classe_tem_ativa_habilidades_e_especial_proprios(classe, arma, habilidades, especial):
    j = classe((0, 0))
    assert [type(a) for a in j.armas] == [arma]
    assert tuple(type(h) for h in j.habilidades_da_classe) == habilidades
    assert j.habilidades == []                      # começa sem nenhuma: elas vêm nas cartas
    assert isinstance(j.especial, especial)
    assert classe in CLASSES


def test_classes_tem_nome_descricao_e_tres_habilidades():
    for classe in CLASSES:
        j = classe((0, 0))
        assert classe.NOME and classe.DESCRICAO
        assert len(j.habilidades_da_classe) == 3
        for h in j.habilidades_da_classe:
            assert h.NOME and h.DESCRICAO and h.ICONE and len(h.MELHORIAS) == h.NIVEL_MAXIMO - 1


def test_wotagei_da_critico_e_cresce_com_a_carta():
    j = Otaku((0, 0))
    assert j.chance_critico == 0
    wotagei = j.habilidades_da_classe[0]
    j.adicionar_habilidade(wotagei)
    primeiro = j.chance_critico
    j.subir_nivel_habilidade(wotagei)
    assert j.chance_critico > primeiro > 0


def test_outras_classes_nao_tem_critico():
    assert Programador((0, 0)).chance_critico == 0
    assert MestreDeRPG((0, 0)).chance_critico == 0


def test_laco_de_repeticao_repete_disparos():
    j = Programador((0, 0))
    assert j.chance_repeticao == 0
    j.adicionar_habilidade(j.habilidades_da_classe[0])
    assert j.chance_repeticao > 0


def test_rolagem_de_iniciativa_recarrega_o_especial_mais_rapido():
    j = MestreDeRPG((0, 0))
    j.adicionar_habilidade(j.habilidades_da_classe[0])
    assert j.mult_especial < 1
    j.especial.restante = j.especial.RECARGA
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
    assert 9 <= vida - bug.vida <= 11            # variação de ±10%, sem crítico


def test_especial_do_programador_enche_a_garrafa_e_nao_mexe_na_recarga_das_armas(jogo_limpo):
    jogo = jogo_limpo(Programador)
    j = jogo.jogador
    assert j.usar_especial(jogo)
    assert j.especial.garrafa.municao == j.especial.garrafa.capacidade
    assert not j.especial.pronto
    assert j.multiplicador_recarga == j.mult_recarga


def test_otaku_vira_super_saiyajin_no_especial(jogo_limpo):
    jogo = jogo_limpo(Otaku)
    jogo.jogador.usar_especial(jogo)
    assert jogo.jogador.tem_bonus("ssj")
    assert jogo.jogador.multiplicador_dano == pytest.approx(SuperSaiyajin.DANO[0])


def test_cartas_de_nivel_funcionam_com_todas_as_classes(jogo_limpo):
    from jogo.progressao import Progressao
    for classe in CLASSES:
        jogo = jogo_limpo(classe)
        for _ in range(30):
            Progressao.gerar_opcoes(jogo.jogador, random.Random(1))[0].aplicar(jogo.jogador, jogo)
        assert len(jogo.jogador.armas) <= jogo.jogador.MAX_ARMAS
