"""Classes Monitor, Gamer, Calouro e Cara da Carona, com armas, habilidades e especiais."""
import pygame
import pytest

from jogo.ajudantes.ajudantes import FuscaVeiculo, QuadroBrancoNoChao
from jogo.armas.apostila import Apostila
from jogo.armas.controle import Controle
from jogo.armas.fusca import FuscaAzul
from jogo.armas.quadro_branco import QuadroBranco
from jogo.coletaveis.coletaveis import Moeda, Nota
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.jogador.classes import CLASSES, CaraDaCarona, Calouro, Gamer, Monitor, Programador
from jogo.projeteis.projeteis import ControleRicochete


def inimigo(jogo, deslocamento, nome="pente_ram"):
    e = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + pygame.Vector2(deslocamento), 1.0)
    jogo.adicionar(e)
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    return e


def test_sete_classes_com_arma_inicial_certa():
    assert len(CLASSES) == 7
    assert isinstance(Monitor((0, 0)).armas[0], QuadroBranco)
    assert isinstance(Gamer((0, 0)).armas[0], Controle)
    assert isinstance(Calouro((0, 0)).armas[0], Apostila)
    assert isinstance(CaraDaCarona((0, 0)).armas[0], FuscaAzul)


def test_habilidades_de_atributo_melhoram_com_a_carta():
    for classe, atributo in ((Monitor, "regeneracao"), (Calouro, "mult_experiencia")):
        heroi = classe((0, 0))
        antes = getattr(heroi, atributo)
        heroi.adicionar_habilidade(heroi.habilidades_da_classe[0])
        assert getattr(heroi, atributo) > antes
    gamer = Gamer((0, 0))
    gamer.adicionar_habilidade(gamer.habilidades_da_classe[0])
    assert gamer.mult_rolamento < 1
    assert Calouro.VIDA < Programador.VIDA + 10  # começa fraco


def test_revisao_para_prova_puxa_notas_e_cura(jogo_limpo):
    jogo = jogo_limpo(Monitor)
    heroi = jogo.jogador
    nota = Nota(heroi.posicao + (900, 0), 1)
    jogo.adicionar(nota)
    jogo._incorporar_novas()
    heroi.vida = heroi.vida_maxima / 2
    assert heroi.usar_especial(jogo)
    assert nota.atraido
    assert heroi.vida == pytest.approx(heroi.vida_maxima * 0.8)


def test_tela_azul_e_o_especial_do_gamer(jogo_limpo):
    from jogo.jogador.especiais import TelaAzul
    jogo = jogo_limpo(Gamer)
    assert isinstance(jogo.jogador.especial, TelaAzul)
    alvo = inimigo(jogo, (200, 0), "calculadora")
    jogo.jogador.usar_especial(jogo)
    assert alvo.travado > 0


def test_calourada_vira_parte_dos_inimigos_e_enfraquece_os_outros(jogo_limpo):
    jogo = jogo_limpo(Calouro)
    alvos = [inimigo(jogo, (120 + 20 * i, 0), "calculadora") for i in range(20)]
    jogo.jogador.usar_especial(jogo)
    aliados = [a for a in alvos if a.possuido > 0]
    fracos = [a for a in alvos if a.fraqueza > 0]
    assert aliados and fracos and len(aliados) + len(fracos) == len(alvos)
    assert fracos[0].dano_de_contato < fracos[0].DANO


def test_lotacao_solta_quatro_fuscas(jogo_limpo):
    jogo = jogo_limpo(CaraDaCarona)
    jogo.jogador.usar_especial(jogo)
    jogo._incorporar_novas()
    assert sum(isinstance(e, FuscaVeiculo) for e in jogo.entidades) == 4


def test_carona_solidaria_solta_moeda_de_quem_morre_possuido(jogo_limpo):
    jogo = jogo_limpo(CaraDaCarona)
    jogo.jogador.chance_carona = 1.0
    alvo = inimigo(jogo, (300, 0), "bug")
    alvo.possuir(3)
    jogo.causar_dano(alvo, 9999)
    jogo._incorporar_novas()
    assert any(isinstance(e, Moeda) for e in jogo.entidades)
