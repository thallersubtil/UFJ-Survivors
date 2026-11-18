"""Classes Monitor, Gamer, Calouro e Cara da Carona, com armas, passivas e especiais."""
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


def test_passivas_crescem_com_o_nivel():
    for classe, atributo in ((Monitor, "regeneracao"), (Calouro, "mult_experiencia")):
        heroi = classe((0, 0))
        antes = getattr(heroi, atributo)
        heroi.nivel = 20
        heroi.recalcular_atributos()
        assert getattr(heroi, atributo) > antes
    gamer = Gamer((0, 0))
    antes = gamer.mult_rolamento
    gamer.nivel = 20
    gamer.recalcular_atributos()
    assert gamer.mult_rolamento < antes < 1
    assert Calouro.VIDA < Programador.VIDA + 10  # começa fraco


def test_quadro_branco_deixa_inimigo_lento_e_fere(jogo_limpo):
    jogo = jogo_limpo(Monitor)
    alvo = inimigo(jogo, (150, 0))
    quadro = QuadroBrancoNoChao(jogo.jogador, jogo.jogador.armas[0], alvo.posicao)
    vida = alvo.vida
    quadro.atualizar(0.01, jogo)
    assert alvo.lento > 0 and alvo.vida < vida
    antes = pygame.Vector2(alvo.posicao)
    alvo.atualizar(0.1, jogo)
    lento = alvo.posicao.distance_to(antes)
    alvo.lento = 0
    antes = pygame.Vector2(alvo.posicao)
    alvo.atualizar(0.1, jogo)
    assert lento < alvo.posicao.distance_to(antes)


def test_controle_ricocheteia_para_outro_inimigo(jogo_limpo):
    jogo = jogo_limpo(Gamer)
    a = inimigo(jogo, (100, 0))
    b = inimigo(jogo, (100, 150))
    controle = ControleRicochete(a.posicao, (300, 0), 10, ricochetes=2)
    vida_b = b.vida
    controle.verificar_colisao(jogo)
    assert controle.ativo and controle.ricochetes == 1
    controle.posicao = pygame.Vector2(b.posicao)
    controle.verificar_colisao(jogo)
    assert b.vida < vida_b


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


def test_speedrun_deixa_rapido_e_invencivel(jogo_limpo):
    jogo = jogo_limpo(Gamer)
    heroi = jogo.jogador
    velocidade = heroi.velocidade
    heroi.usar_especial(jogo)
    assert heroi.velocidade > velocidade and not heroi.pode_levar_dano


def test_trote_reverso_faz_os_inimigos_fugirem(jogo_limpo):
    jogo = jogo_limpo(Calouro)
    alvo = inimigo(jogo, (120, 0), "calculadora")
    jogo.jogador.usar_especial(jogo)
    assert alvo.assustado > 0
    distancia = alvo.posicao.distance_to(jogo.jogador.posicao)
    alvo.atualizar(0.2, jogo)
    assert alvo.posicao.distance_to(jogo.jogador.posicao) > distancia


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
