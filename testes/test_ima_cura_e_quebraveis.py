"""Ímã no lugar da lata de energético, inimigos sem cura (ela vem de um item e dos objetos quebráveis do mapa)."""
from types import SimpleNamespace

import pygame
import pytest

from jogo.coletaveis.coletaveis import Ima, Moeda, Nota, PocaoDeVida
from jogo.inimigos.bug import Bug
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo
from jogo.inimigos.quebraveis import QUEBRAVEIS, ObjetoQuebravel
from jogo.itens.itens import ITENS, KitDePrimeirosSocorros
from jogo.jogador.classes import Monitor
from jogo.jogo import Jogo


def coletaveis(jogo, classe):
    jogo._incorporar_novas()
    return [e for e in jogo.grupos["coletavel"] if isinstance(e, classe) and e.ativo]


def rng_fixo(valor):
    return SimpleNamespace(random=lambda: valor, uniform=lambda a, b: a, randint=lambda a, b: a,
                           choice=lambda lista: lista[0])


# ---------------------------------------------------------------- ímã

def test_ima_puxa_toda_a_experiencia_do_mapa_e_so_ela(jogo_limpo):
    jogo = jogo_limpo()
    heroi = jogo.jogador
    heroi.imortal = True
    longe = [Nota(heroi.posicao + pygame.Vector2(1500, 0).rotate(90 * i), 3) for i in range(4)]
    moeda = Moeda(heroi.posicao + (900, 0), 5)
    for entidade in longe + [moeda, Ima(heroi.posicao)]:
        jogo.adicionar(entidade)
    jogo.atualizar(1 / 60)
    assert all(nota.atraido for nota in longe) and not moeda.atraido
    for _ in range(60 * 5):
        jogo.atualizar(1 / 60)
    assert not any(nota.ativo for nota in longe) and moeda.ativo
    assert heroi.nivel > 1 or heroi.experiencia >= 12


def test_ima_cai_bem_raramente_e_a_lata_de_energetico_nao_existe_mais(jogo_limpo):
    import jogo.coletaveis.coletaveis as modulo
    assert not hasattr(modulo, "LataDeEnergetico") and not hasattr(Inimigo, "CHANCE_ENERGETICO")
    assert 0 < Inimigo.CHANCE_IMA <= 0.003
    jogo = jogo_limpo()
    jogo.rng = rng_fixo(Inimigo.CHANCE_IMA / 2)
    Bug(jogo.jogador.posicao + (300, 0)).ao_morrer(jogo)
    assert len(coletaveis(jogo, Ima)) == 1
    jogo.rng = rng_fixo(Inimigo.CHANCE_IMA * 2)
    Bug(jogo.jogador.posicao + (300, 0)).ao_morrer(jogo)
    assert len(coletaveis(jogo, Ima)) == 1


def test_chefes_e_lacaios_de_mini_chefe_nao_soltam_ima():
    from jogo.inimigos.chefe import Chefe
    from jogo.inimigos.lacaios_do_campus import LacaioDoCampus
    assert Chefe.CHANCE_IMA == 0 and LacaioDoCampus.CHANCE_IMA == 0


def test_revisao_para_prova_usa_o_mesmo_puxao_do_ima(jogo_limpo):
    jogo = jogo_limpo(Monitor)
    nota = Nota(jogo.jogador.posicao + (1200, 0), 1)
    jogo.adicionar(nota)
    jogo._incorporar_novas()
    assert jogo.jogador.usar_especial(jogo)
    assert nota.atraido


# ---------------------------------------------------------------- inimigos sem cura; o item que devolve

def test_inimigo_nao_solta_mais_cura_sozinho(jogo_limpo):
    assert not hasattr(Inimigo, "CHANCE_POCAO")
    jogo = jogo_limpo()
    jogo.rng = rng_fixo(0.0)                       # a melhor sorte possível
    for i in range(50):
        Bug(jogo.jogador.posicao + (300 + i, 0)).ao_morrer(jogo)
    assert coletaveis(jogo, PocaoDeVida) == []


def test_kit_de_primeiros_socorros_faz_um_inimigo_soltar_cura_de_tempos_em_tempos(jogo_limpo):
    jogo = jogo_limpo()
    heroi = jogo.jogador
    heroi.imortal = True
    heroi.armas = []
    kit = KitDePrimeirosSocorros()
    heroi.adicionar_item(kit)

    def eliminar():
        bug = Bug(heroi.posicao + (400, 0))
        jogo.adicionar(bug)
        jogo._incorporar_novas()
        jogo.causar_dano(bug, 10 ** 6)

    eliminar()                                    # o kit começa carregado: a primeira eliminação já solta
    assert len(coletaveis(jogo, PocaoDeVida)) == 1 and not kit.pronto
    eliminar()
    assert len(coletaveis(jogo, PocaoDeVida)) == 1
    for _ in range(round(60 * kit.intervalo) + 2):
        jogo.atualizar(1 / 60)
    assert kit.pronto
    eliminar()
    assert len(coletaveis(jogo, PocaoDeVida)) == 2


def test_intervalo_do_kit_diminui_com_o_nivel():
    kit = KitDePrimeirosSocorros()
    intervalos = []
    for nivel in range(1, kit.NIVEL_MAXIMO + 1):
        kit.nivel = nivel
        intervalos.append(kit.intervalo)
    assert intervalos == sorted(intervalos, reverse=True) and len(set(intervalos)) == kit.NIVEL_MAXIMO
    assert KitDePrimeirosSocorros in ITENS and len(KitDePrimeirosSocorros.MELHORIAS) == kit.NIVEL_MAXIMO - 1


# ---------------------------------------------------------------- objetos quebráveis

def test_partida_comeca_com_objetos_quebraveis_espalhados_fora_dos_predios():
    jogo = Jogo(Monitor, semente=7)
    objetos = jogo.grupos["quebravel"]
    assert len(objetos) == jogo.QUEBRAVEIS_NO_INICIO
    assert {type(o) for o in objetos} <= set(QUEBRAVEIS) and len({type(o) for o in objetos}) > 1
    for objeto in objetos:
        assert jogo.arena.collidepoint(objeto.posicao) and not jogo.mapa.bloqueado(objeto.posicao, objeto.raio)
    assert not jogo.inimigos                       # não contam como inimigos (não pesam no alvo da fase)


def test_quebraveis_ficam_longe_uns_dos_outros_e_do_aluno():
    jogo = Jogo(Monitor, semente=7)
    objetos = jogo.grupos["quebravel"]
    for i, um in enumerate(objetos):
        assert um.posicao.distance_to(jogo.jogador.posicao) >= jogo.LONGE_DO_ALUNO
        for outro in objetos[i + 1:]:
            assert um.posicao.distance_to(outro.posicao) >= jogo.ESPACO_ENTRE_QUEBRAVEIS


def test_cada_partida_espalha_os_quebraveis_num_lugar_diferente():
    lugares = [{(round(o.posicao.x), round(o.posicao.y)) for o in Jogo(Monitor).grupos["quebravel"]}
               for _ in range(2)]                  # sem semente, como no jogo de verdade
    assert lugares[0] != lugares[1]


def test_quebravel_quebrado_nao_volta_e_nenhum_aparece_depois_do_comeco():
    jogo = Jogo(Monitor, semente=7)
    jogo.jogador.imortal = True
    jogo.jogador.armas = []
    antes = len(jogo.grupos["quebravel"])
    alvo = jogo.grupos["quebravel"][0]
    jogo.causar_dano(alvo, 10 ** 6)
    for _ in range(60 * 60):                       # um minuto inteiro de partida
        jogo.atualizar(1 / 60)
    assert len(jogo.grupos["quebravel"]) == antes - 1
    assert not hasattr(jogo, "MAX_QUEBRAVEIS") and not hasattr(jogo, "INTERVALO_DE_QUEBRAVEL")


def test_objeto_quebravel_e_um_inimigo_que_nao_anda_nao_fere_e_nao_vai_para_a_fabrica(jogo_limpo):
    jogo = jogo_limpo()
    heroi = jogo.jogador
    heroi.armas = []
    objeto = QUEBRAVEIS[0](heroi.posicao)          # em cima do aluno
    jogo.adicionar(objeto)
    assert isinstance(objeto, Inimigo) and isinstance(objeto, ObjetoQuebravel)
    vida, lugar = heroi.vida, pygame.Vector2(objeto.posicao)
    objeto.empurrar((1, 0))
    objeto.possuir(5)
    objeto.assustar(5)
    for _ in range(60):
        jogo.atualizar(1 / 60)
    assert heroi.vida == vida and objeto.posicao == lugar and objeto.possuido == 0
    nomes_na_fabrica = {FabricaDeInimigos.classe(nome) for nome in FabricaDeInimigos.nomes()}
    assert not nomes_na_fabrica & set(QUEBRAVEIS)


def test_as_armas_acertam_o_objeto_e_ele_solta_cura_ou_moedas_sem_contar_no_placar(jogo_limpo):
    jogo = jogo_limpo()
    heroi = jogo.jogador
    heroi.imortal = True
    for sorteio, classe in ((0.0, PocaoDeVida), (0.99, Moeda)):
        objeto = QUEBRAVEIS[0](heroi.posicao + (150, 0))
        jogo.adicionar(objeto)
        jogo.entrada.mira = pygame.Vector2(objeto.posicao)
        for _ in range(60 * 6):                    # a Cobra Python do Programador dá conta sozinha
            jogo.atualizar(1 / 60)
            if not objeto.ativo:
                break
        assert not objeto.ativo
    assert jogo.placar.eliminacoes == 0 and jogo.placar.combo == 0 and jogo.placar.pontos == 0
    jogo.rng = rng_fixo(0.0)
    QUEBRAVEIS[0](heroi.posicao + (600, 0)).ao_morrer(jogo)
    assert len(coletaveis(jogo, PocaoDeVida)) >= 1
    antes = len(coletaveis(jogo, Moeda))
    jogo.rng = rng_fixo(0.99)
    QUEBRAVEIS[0](heroi.posicao + (700, 0)).ao_morrer(jogo)
    assert len(coletaveis(jogo, Moeda)) == antes + 1
