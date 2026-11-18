"""Convite da Atlética, Pendrive e Apostila."""
import pygame
import pytest

from jogo.armas.apostila import Apostila
from jogo.ajudantes.ajudantes import FolhaDaApostila
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.itens.itens import ConviteDaAtletica, Pendrive
from jogo.jogador.classes import Otaku, Programador


def inimigo_perto(jogo, distancia=80):
    inimigo = FabricaDeInimigos.criar("pente_ram", jogo.jogador.posicao + (distancia, 0), 1.0)
    jogo.adicionar(inimigo)
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    return inimigo


def test_grito_da_atletica_fere_e_empurra_de_tempos_em_tempos(jogo_limpo):
    jogo = jogo_limpo()
    convite = ConviteDaAtletica()
    jogo.jogador.adicionar_item(convite)
    inimigo = inimigo_perto(jogo)
    vida = inimigo.vida
    for _ in range(round(60 * (convite.intervalo - 0.5))):
        jogo.jogador.atualizar(1 / 60, jogo)
    assert inimigo.vida == vida                    # ainda não gritou
    for _ in range(60):
        jogo.jogador.atualizar(1 / 60, jogo)
    assert inimigo.vida < vida
    assert inimigo.empurrao.x > 0                  # para longe do aluno


def test_atletica_grita_mais_vezes_e_mais_longe_por_nivel():
    convite = ConviteDaAtletica()
    intervalo, raio = convite.intervalo, convite.raio
    convite.subir_nivel()
    assert convite.intervalo < intervalo and convite.raio > raio


def test_pendrive_guarda_um_especial_a_mais():
    heroi = Otaku((0, 0))
    assert heroi.especial.cargas == 1
    heroi.adicionar_item(Pendrive())
    assert heroi.especial.cargas_maximas == 2
    heroi.especial.atualizar(heroi.especial.RECARGA + 1)
    assert heroi.especial.cargas == 2


def test_especial_com_duas_cargas_usa_duas_vezes_seguidas(jogo_limpo):
    jogo = jogo_limpo(Programador)
    heroi = jogo.jogador
    heroi.adicionar_item(Pendrive())
    heroi.especial.atualizar(heroi.especial.RECARGA + 1)
    assert heroi.usar_especial(jogo)
    assert heroi.usar_especial(jogo)
    assert not heroi.usar_especial(jogo)
    heroi.especial.atualizar(heroi.especial.RECARGA + 0.1)
    assert heroi.especial.cargas == 1


def test_apostila_ganha_folhas_e_alterna_entre_girar_e_sumir(jogo_limpo):
    jogo = jogo_limpo()
    apostila = Apostila()
    jogo.jogador.adicionar_arma(apostila)
    assert apostila.valor("folhas") == 1
    while not apostila.no_maximo:
        apostila.subir_nivel()
    assert apostila.valor("folhas") == 3
    apostila.atualizar(1 / 60, jogo, jogo.jogador)
    jogo._incorporar_novas()
    folhas = [e for e in jogo.entidades if isinstance(e, FolhaDaApostila)]
    assert len(folhas) == 3
    tempo = 0.0
    while folhas[0].ativo and tempo < 30:
        apostila.atualizar(1 / 60, jogo, jogo.jogador)
        for f in folhas:
            f.atualizar(1 / 60, jogo)
        tempo += 1 / 60
    assert not folhas[0].ativo                          # as folhas somem depois de um tempo
    for _ in range(round(60 * (apostila.valor("pausa") + 0.2))):
        apostila.atualizar(1 / 60, jogo, jogo.jogador)
    jogo._incorporar_novas()
    assert sum(isinstance(e, FolhaDaApostila) and e.ativo for e in jogo.entidades) == 3


def test_folha_fere_quem_encosta_uma_vez_por_volta(jogo_limpo):
    jogo = jogo_limpo()
    apostila = Apostila()
    jogo.jogador.adicionar_arma(apostila)
    apostila.atualizar(1 / 60, jogo, jogo.jogador)
    jogo._incorporar_novas()
    folha = next(e for e in jogo.entidades if isinstance(e, FolhaDaApostila))
    inimigo = inimigo_perto(jogo, 0)
    inimigo.posicao = pygame.Vector2(folha.posicao)
    jogo.grade.reconstruir(jogo.inimigos)
    vida = inimigo.vida
    folha.atualizar(0, jogo)
    folha.atualizar(0, jogo)
    assert vida - inimigo.vida == pytest.approx(apostila.valor("dano") * jogo.jogador.multiplicador_dano, abs=1)
