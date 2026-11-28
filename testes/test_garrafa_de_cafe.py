"""A munição do jogo: a Garrafa de Café da Virada de Noite (Programador), com @property e validação."""
import pygame
import pytest

from jogo.coletaveis.coletaveis import CopoDeCafe
from jogo.jogador.classes import MestreDeRPG, Programador
from jogo.jogador.especiais import CodigoDisparado, ViradaDeNoite
from jogo.jogador.garrafa_de_cafe import GarrafaDeCafe


def test_municao_so_aceita_inteiro_dentro_da_capacidade():
    garrafa = GarrafaDeCafe(100)
    for errado in (True, 1.5, "10", None):
        with pytest.raises(TypeError):
            garrafa.municao = errado
    for errado in (-1, 101):
        with pytest.raises(ValueError):
            garrafa.municao = errado
    assert garrafa.municao == 0                  # valor inválido não muda nada
    garrafa.municao = 100
    assert garrafa.municao == 100


def test_capacidade_tambem_e_validada_e_corta_a_municao():
    garrafa = GarrafaDeCafe(100)
    garrafa.encher()
    with pytest.raises(TypeError):
        garrafa.capacidade = 50.5
    with pytest.raises(ValueError):
        garrafa.capacidade = 0
    garrafa.capacidade = 60
    assert garrafa.municao == 60


def test_gastar_tira_uma_dose_e_nao_fica_negativa():
    garrafa = GarrafaDeCafe(2)
    garrafa.encher()
    assert garrafa.gastar() and garrafa.municao == 1
    assert garrafa.gastar() and garrafa.vazia
    assert not garrafa.gastar() and garrafa.municao == 0


def jogo_do_programador(jogo_limpo):
    jogo = jogo_limpo(Programador)
    jogo.jogador.imortal = True
    jogo.jogador.armas = []
    return jogo


def tiros(jogo):
    jogo._incorporar_novas()
    return sum(isinstance(e, CodigoDisparado) for e in jogo.entidades)


def rodar(jogo, segundos):
    for _ in range(round(30 * segundos)):
        jogo.atualizar(1 / 30)


def test_virada_atira_sozinha_ate_o_cafe_acabar(jogo_limpo):
    jogo = jogo_do_programador(jogo_limpo)
    heroi, virada = jogo.jogador, jogo.jogador.especial
    assert heroi.usar_especial(jogo) and virada.disparando and virada.garrafa.municao == 100
    rodar(jogo, 1)                                    # sem apertar nada: a rajada segue sozinha
    assert 0 < virada.garrafa.municao < 100 and tiros(jogo) > 0
    rodar(jogo, 100 / ViradaDeNoite.TIROS_POR_SEGUNDO)
    assert not virada.disparando
    rodar(jogo, 2)                                    # tiros antigos somem; rajada acabou: nenhum novo
    assert tiros(jogo) == 0


def test_durante_a_rajada_espaco_nao_faz_nada(jogo_limpo):
    jogo = jogo_do_programador(jogo_limpo)
    heroi, virada = jogo.jogador, jogo.jogador.especial
    heroi.usar_especial(jogo)
    virada.cargas = 1                                 # mesmo com outra carga (Pendrive)
    assert not virada.pronto and not heroi.usar_especial(jogo) and virada.cargas == 1


def test_a_garrafa_enche_aos_poucos_depois_da_rajada(jogo_limpo):
    jogo = jogo_do_programador(jogo_limpo)
    heroi, virada = jogo.jogador, jogo.jogador.especial
    heroi.usar_especial(jogo)
    rodar(jogo, 100 / ViradaDeNoite.TIROS_POR_SEGUNDO + 0.5)
    assert not virada.disparando and virada.restante == pytest.approx(virada.RECARGA, abs=1)   # recarga parada na rajada
    rodar(jogo, virada.RECARGA / 2)
    meio = virada.garrafa.municao
    assert 30 < meio < 70 and not virada.pronto
    rodar(jogo, virada.RECARGA / 2 + 1)
    assert virada.pronto and virada.garrafa.municao == virada.garrafa.capacidade


def test_cafe_na_rajada_vira_mais_tiros_e_fora_dela_adianta_a_garrafa(jogo_limpo):
    jogo = jogo_do_programador(jogo_limpo)
    heroi, virada = jogo.jogador, jogo.jogador.especial
    heroi.usar_especial(jogo)
    rodar(jogo, 2)
    antes = virada.garrafa.municao
    CopoDeCafe(heroi.posicao).ao_coletar(jogo)
    assert virada.garrafa.municao == antes + ViradaDeNoite.DOSES_DO_COPO
    rodar(jogo, 15)
    assert not virada.disparando
    antes = virada.garrafa.municao
    CopoDeCafe(heroi.posicao).ao_coletar(jogo)
    assert virada.garrafa.municao >= antes + ViradaDeNoite.DOSES_DO_COPO - 1
    assert virada.garrafa.municao <= virada.garrafa.capacidade


def test_para_as_outras_classes_o_cafe_adianta_o_especial(jogo_limpo):
    jogo = jogo_limpo(MestreDeRPG)
    especial = jogo.jogador.especial
    especial.restante = especial.RECARGA
    CopoDeCafe(jogo.jogador.posicao).ao_coletar(jogo)
    assert especial.restante == pytest.approx(especial.RECARGA * (1 - especial.CARGA_DO_CAFE))


def test_cafeinado_aumenta_a_garrafa(jogo_limpo):
    jogo = jogo_do_programador(jogo_limpo)
    heroi = jogo.jogador
    heroi.adicionar_habilidade(heroi.habilidades_da_classe[1])
    heroi.usar_especial(jogo)
    assert heroi.especial.garrafa.capacidade == 100 + heroi.habilidades[0].DOSES[0]


def test_hud_mostra_a_barra_de_cafe_so_para_quem_tem_garrafa(jogo_limpo):
    from jogo.cenas.hud import Hud
    jogo = jogo_do_programador(jogo_limpo)
    assert jogo.jogador.especial.medidor_extra[1] == 100
    assert MestreDeRPG((0, 0)).especial.medidor_extra is None
    Hud().desenhar(pygame.Surface((1280, 720)), jogo)
