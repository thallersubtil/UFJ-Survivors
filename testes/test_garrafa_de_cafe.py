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


def test_virada_atira_enquanto_ha_cafe_e_para_quando_acaba(jogo_limpo):
    jogo = jogo_do_programador(jogo_limpo)
    heroi, virada = jogo.jogador, jogo.jogador.especial
    assert heroi.usar_especial(jogo) and virada.garrafa.municao == 100
    jogo.entrada.segurando_especial = True
    for _ in range(round(30 * 12)):                   # 12 s segurando: 100 doses a 10 por segundo acabam
        jogo.atualizar(1 / 30)
    assert virada.garrafa.vazia
    assert heroi.tem_bonus("sem_cafe")
    for _ in range(60):                               # tiros antigos somem; garrafa vazia: nenhum novo
        jogo.atualizar(1 / 30)
    assert tiros(jogo) == 0


def test_soltar_o_botao_guarda_as_doses(jogo_limpo):
    jogo = jogo_do_programador(jogo_limpo)
    virada = jogo.jogador.especial
    jogo.jogador.usar_especial(jogo)
    jogo.entrada.segurando_especial = True
    for _ in range(15):
        jogo.atualizar(1 / 30)
    jogo.entrada.segurando_especial = False
    sobrou = virada.garrafa.municao
    for _ in range(60):
        jogo.atualizar(1 / 30)
    assert 0 < sobrou < 100 and virada.garrafa.municao == sobrou


def test_com_cafe_na_garrafa_espaco_nao_gasta_o_especial(jogo_limpo):
    jogo = jogo_do_programador(jogo_limpo)
    heroi = jogo.jogador
    heroi.usar_especial(jogo)
    heroi.especial.cargas = 1
    assert not heroi.usar_especial(jogo) and heroi.especial.cargas == 1


def test_cafe_coletado_enche_a_garrafa_sem_passar_da_capacidade(jogo_limpo):
    jogo = jogo_do_programador(jogo_limpo)
    heroi, garrafa = jogo.jogador, jogo.jogador.especial.garrafa
    CopoDeCafe(heroi.posicao).ao_coletar(jogo)
    assert garrafa.municao == ViradaDeNoite.DOSES_DO_COPO
    garrafa.municao = garrafa.capacidade - 3
    CopoDeCafe(heroi.posicao).ao_coletar(jogo)
    assert garrafa.municao == garrafa.capacidade


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
