"""Sorte, baús por raridade, mini-chefes invocáveis e mini-mapa."""
import random

import pygame
import pytest

from jogo.aplicacao import Aplicacao
from jogo.cenas.chefe import CenaChefe
from jogo.cenas.minimapa import CenaMiniMapa
from jogo.cenas.partida import CenaPartida
from jogo.fase import PROVAS, ProvaDeCalculo
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.lacaios_do_campus import LacaioDoCampus
from jogo.inimigos.mini_chefes import MINI_CHEFES, MiniChefe
from jogo.invocacao import LocalDeInvocacao
from jogo.itens.itens import JogoDeCintura, MoedaDaSorte
from jogo.jogador.classes import Programador
from jogo.jogo import Jogo
from jogo.loja.melhorias import SorteDeCalouro
from jogo.loja.progresso import Progresso
from jogo.mapa import MapaUFJ
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.do_campus import FeixeDeAbducao, Multa, VeiculoDesgovernado
from jogo.ranking import Ranking
from jogo.tesouro import COMUM, EPICO, LENDARIO, Tesouro


# ---------------------------------------------------------------- sorte
def test_sorte_multiplica_as_chances(jogo_limpo):
    heroi = jogo_limpo().jogador
    assert heroi.sorte == 0 and heroi.chance(0.2) == pytest.approx(0.2)
    heroi.adicionar_item(MoedaDaSorte())
    assert heroi.sorte == pytest.approx(0.15)
    assert heroi.chance(0.2) == pytest.approx(0.23)


def test_melhoria_da_loja_da_sorte(jogo_limpo):
    heroi = jogo_limpo().jogador
    heroi.receber_melhorias([SorteDeCalouro(4)])
    assert heroi.sorte == pytest.approx(0.20)


def test_sorte_aumenta_as_moedas_dos_monstros(jogo_limpo):
    def moedas_soltas(sorte):
        jogo = jogo_limpo()
        jogo.jogador.sorte = sorte
        for _ in range(400):
            bug = FabricaDeInimigos.criar("bug", jogo.jogador.posicao + (300, 0))
            bug.ao_morrer(jogo)
        jogo._incorporar_novas()
        return sum(type(e).__name__ == "Moeda" for e in jogo.entidades)

    assert moedas_soltas(4.0) > moedas_soltas(0.0) * 2


def test_jogo_de_cintura_desvia_de_golpes(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.adicionar_item(JogoDeCintura())
    jogo.jogador.sorte = 100.0                       # desvio no teto
    levados = 0
    for _ in range(200):
        jogo.jogador.invencivel = 0.0
        levados += jogo.ferir_jogador(1)
    assert 0 < levados < 200 * (1 - Jogo.DESVIO_MAXIMO) * 1.5


def test_sem_desvio_todo_golpe_acerta(jogo_limpo):
    jogo = jogo_limpo()
    assert jogo.ferir_jogador(5) is True


# ---------------------------------------------------------------- baús
def test_chances_do_bau_crescem_com_a_sorte(jogo_limpo):
    heroi = jogo_limpo().jogador
    comum, epico, lendario = Tesouro.chances(heroi)
    assert comum + epico + lendario == pytest.approx(1) and lendario < epico < comum
    heroi.sorte = 1.0
    _, epico_sortudo, lendario_sortudo = Tesouro.chances(heroi)
    assert epico_sortudo == pytest.approx(epico * 2) and lendario_sortudo == pytest.approx(lendario * 2)


def test_raridade_define_itens_e_moedas(jogo_limpo):
    assert (COMUM.itens, EPICO.itens, LENDARIO.itens) == (1, 3, 5)
    assert COMUM.moedas[1] < EPICO.moedas[0] and EPICO.moedas[1] < LENDARIO.moedas[0]
    jogo = jogo_limpo()
    tesouro = Tesouro(LENDARIO, 200)
    premios = tesouro.abrir(jogo)
    assert len(premios) == 5 and jogo.placar.moedas == tesouro.moedas_ganhas >= 200
    assert "bau_lendario" in jogo.marcos


def test_moedas_do_bau_podem_critar(jogo_limpo):
    heroi = jogo_limpo().jogador
    rng = random.Random(1)
    tesouros = [Tesouro.sortear(heroi, rng) for _ in range(600)]
    criticos = [t for t in tesouros if t.moedas_criticas]
    assert 40 < len(criticos) < 160
    assert all(t.moedas >= t.raridade.moedas[0] * Tesouro.MULT_MOEDAS_CRITICAS for t in criticos)
    assert any(t.raridade is EPICO for t in tesouros) and sum(t.raridade is COMUM for t in tesouros) > 450


# ---------------------------------------------------------------- mini-chefes
def test_todas_as_provas_tem_invocacoes_validas():
    usados = set()
    for prova in PROVAS:
        assert prova.INVOCACOES
        for tempo, nome in prova.INVOCACOES:
            assert 0 < tempo < prova.DURACAO and nome in MINI_CHEFES
            assert issubclass(FabricaDeInimigos.classe(nome), MiniChefe)
            usados.add(nome)
    assert usados == set(MINI_CHEFES)                 # todo mini-chefe aparece em alguma prova


@pytest.mark.parametrize("nome", MINI_CHEFES)
def test_mini_chefe_tem_arte_lugar_e_lacaio(nome):
    classe = FabricaDeInimigos.classe(nome)
    for caminho in (f"sprites/{classe.PASTA_SPRITE}/andar-8.png", f"rostos/{classe.PASTA_SPRITE}.png",
                    f"chefes/{classe.PASTA_SPRITE}.png"):
        assert (Recursos.pasta / caminho).is_file(), caminho
    assert classe.GRITO and classe.ONDE and (classe.LOCAL or classe.PONTO)
    assert issubclass(FabricaDeInimigos.classe(classe.LACAIO), LacaioDoCampus)
    mapa = MapaUFJ.carregar()
    if mapa is not None:
        ponto = mapa.local_de(classe.LOCAL) if classe.LOCAL else pygame.Vector2(classe.PONTO)
        assert ponto is not None and mapa.arena.collidepoint(ponto) and not mapa.bloqueado(ponto, 60)


def test_tia_da_cantina_e_enorme_e_o_reitor_muito_alto(jogo_limpo):
    jogo = jogo_limpo()
    aluno = jogo.jogador.animador.quadro_atual.get_height()
    tia = FabricaDeInimigos.criar("tia_da_cantina", (0, 0))
    reitor = FabricaDeInimigos.criar("reitor", (0, 0))
    assert tia.altura_sprite >= 2.5 * aluno and tia.raio >= 3 * jogo.jogador.raio
    assert reitor.altura_sprite >= 3.3 * aluno


def test_centro_de_aulas_secreto_51_existe_no_mapa():
    mapa = MapaUFJ.carregar()
    if mapa is None:
        pytest.skip("sem o mapa da UFJ")
    (secreto,) = [p for p in mapa.predios if p.nome == "CENTRO DE AULAS SECRETO 51"]
    outros = [p for p in mapa.predios if p is not secreto]
    assert all(not secreto.contorno.inflate(600, 600).colliderect(p.contorno) for p in outros)   # afastado de tudo
    assert FabricaDeInimigos.classe("et_de_varginha").LOCAL == secreto.nome


def test_circulo_aparece_perto_do_predio_na_hora_marcada():
    jogo = Jogo(Programador, fase=ProvaDeCalculo(), semente=1)
    jogo.jogador.imortal = True
    tempo, nome = next(i for i in ProvaDeCalculo.INVOCACOES if i[1] == "tia_da_cantina")
    assert jogo.marcadores() == []
    jogo.fase.adiantar_para(tempo - 0.01)
    jogo.atualizar(0.05)
    (local,) = jogo.marcadores()
    assert isinstance(local, LocalDeInvocacao) and not local.invocado and local.NOME == "Tia da Cantina"
    esperado = jogo.mapa.local_de("RU")
    if esperado is not None:
        assert local.posicao.distance_to(esperado) < 1 and not jogo.mapa.bloqueado(local.posicao, 60)
    assert jogo.fase.abrir_invocacao(jogo, nome) is None          # não repete enquanto o primeiro existe


def test_culto_secreto_so_entra_no_mapa_quando_o_aluno_chega_perto(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.imortal = True
    anuncios = len(jogo.anuncios)
    local = jogo.fase.abrir_invocacao(jogo, "grao_mestre_do_culto")
    jogo.jogador.posicao = local.posicao - (local.DISTANCIA_PARA_DESCOBRIR + 300, 0)
    jogo.atualizar(0.05)
    assert local.ativo and jogo.marcadores() == [] and len(jogo.anuncios) == anuncios      # nem aviso, nem mapa
    jogo.jogador.posicao = local.posicao - (local.DISTANCIA_PARA_DESCOBRIR - 50, 0)
    jogo.atualizar(0.05)
    assert jogo.marcadores() == [local] and "segredo" in jogo.marcos


def test_ficar_no_circulo_invoca_apresenta_e_sair_esvazia(jogo_limpo):
    jogo = jogo_limpo()
    local = LocalDeInvocacao(jogo.jogador.posicao + (30, 0), "tia_da_cantina")
    jogo.adicionar(local)
    jogo.jogador.imortal = True
    for _ in range(30):
        jogo.atualizar(1 / 30)
    assert 0.3 < local.progresso < 0.5
    jogo.jogador.posicao += (600, 0)
    for _ in range(30):
        jogo.atualizar(1 / 30)
    assert local.progresso == 0 and local.ativo
    jogo.jogador.posicao = pygame.Vector2(local.posicao)
    for _ in range(90):
        jogo.atualizar(1 / 30)
    assert not local.ativo
    (chefe,) = jogo.marcadores()
    assert isinstance(chefe, MiniChefe) and chefe.invocado and chefe.solta_bau
    assert jogo.chefe_a_apresentar is chefe                       # a cena de apresentação vai entrar
    assert sum(type(e).__name__ == "Coxinha" for e in jogo.inimigos) == chefe.LACAIOS_NA_CHEGADA


def test_invocar_na_partida_mostra_a_apresentacao(tmp_path):
    app = Aplicacao(pygame.Surface((1280, 720)))
    app.ranking = Ranking(tmp_path / "ranking.json")
    app.progresso = Progresso(tmp_path / "progresso.json")
    partida = CenaPartida(app, Programador)
    app.trocar(partida)
    partida.jogo.jogador.imortal = True
    local = LocalDeInvocacao(partida.jogo.jogador.posicao, "bibliotecaria")
    partida.jogo.adicionar(local)
    local.progresso = 0.999
    for _ in range(4):
        app.passo(1 / 30, [])
    assert isinstance(app.cena_atual, CenaChefe) and app.cena_atual.chefe.NOME == "Bibliotecária"
    assert app.cena_atual.frase == "Uma Bibliotecária selvagem apareceu!"
    app.passo(1.5, [])                                            # desenha a ilustração, a faixa e a fala
    app.passo(2.0, [])
    assert app.cena_atual is partida


@pytest.mark.parametrize("nome", MINI_CHEFES)
def test_mini_chefe_ataca_guarda_o_posto_e_deixa_bau(jogo_limpo, nome):
    jogo = jogo_limpo()
    jogo.jogador.imortal = True
    chefe = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + (260, 0))
    jogo.adicionar(chefe)
    chefe.ao_chegar(jogo)
    jogo._incorporar_novas()
    assert sum(isinstance(e, LacaioDoCampus) for e in jogo.inimigos) == chefe.LACAIOS_NA_CHEGADA
    for _ in range(300):
        jogo.atualizar(1 / 30)
    assert chefe.ataques >= 2
    chefe.assustar(5)
    chefe.possuir(5)
    assert chefe.assustado == 0 and chefe.possuido == 0
    chefe.vida = chefe.vida_maxima / 2
    jogo.jogador.posicao = chefe.posto + (chefe.GUARDA + 900, 0)      # o aluno foge: ele volta e se cura
    for _ in range(120):
        jogo.atualizar(1 / 30)
    assert chefe.vida > chefe.vida_maxima / 2
    jogo.marcados.add(chefe.NOME)
    assert jogo.causar_dano(chefe, 10 ** 6)
    jogo._incorporar_novas()
    assert any(type(e).__name__ == "Bau" for e in jogo.entidades)
    assert "mini_chefe" in jogo.marcos and chefe.NOME not in jogo.marcados


def test_multa_da_bibliotecaria_tira_moedas(jogo_limpo):
    jogo = jogo_limpo()
    jogo.placar.adicionar_moedas(20)
    jogo.adicionar(Multa(jogo.jogador.posicao, (0, 0), 2, 8, (200, 130, 230)))
    jogo.atualizar(1 / 30)
    assert jogo.placar.moedas == 12 and jogo.jogador.vida < jogo.jogador.vida_maxima
    assert jogo.multar(100) == 12 and jogo.placar.moedas == 0          # nunca fica negativo


def test_hb20_avisa_antes_e_atropela_depois(jogo_limpo):
    jogo = jogo_limpo()
    carro = VeiculoDesgovernado(jogo.jogador.posicao - (400, 0), (1, 0), "hb20", 600, 10, 30, aviso=0.5)
    jogo.adicionar(carro)
    inicio = pygame.Vector2(carro.posicao)
    for _ in range(12):
        jogo.atualizar(1 / 30)
    assert carro.posicao == inicio and jogo.jogador.vida == jogo.jogador.vida_maxima    # ainda buzinando
    for _ in range(30):
        jogo.atualizar(1 / 30)
    assert jogo.jogador.vida < jogo.jogador.vida_maxima and carro.posicao.x > jogo.jogador.posicao.x


def test_feixe_de_abducao_so_pega_quem_fica_no_circulo(jogo_limpo):
    jogo = jogo_limpo()
    jogo.adicionar(FeixeDeAbducao(jogo.jogador.posicao, 90, 10))
    jogo.adicionar(FeixeDeAbducao(jogo.jogador.posicao + (400, 0), 90, 1000))
    for _ in range(45):
        jogo.atualizar(1 / 30)
    assert jogo.jogador.vida == jogo.jogador.vida_maxima - 10
    assert not jogo.grupos["projetil_inimigo"]


@pytest.mark.parametrize("nome", ["coxinha", "morcego", "livro_atrasado", "cobaia", "carimbo", "lobinho", "dente",
                                  "cultista", "mini_ovni", "boi", "gato_alienigena"])
def test_lacaio_do_campus_tem_arte_e_chega_no_aluno(jogo_limpo, nome):
    jogo = jogo_limpo()
    jogo.jogador.imortal = True
    lacaio = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + (420, 0))
    assert len(lacaio.animador.animacao.quadros) >= 4                 # tem tira animada de verdade
    jogo.adicionar(lacaio)
    perto = 10 ** 9
    for _ in range(360):
        jogo.atualizar(1 / 30)
        perto = min(perto, lacaio.posicao.distance_to(jogo.jogador.posicao))
    assert perto < 330


# ---------------------------------------------------------------- mini-mapa
def test_mini_mapa_mostra_so_o_lugar_e_o_clique_marca(tmp_path):
    app = Aplicacao(pygame.Surface((1280, 720)))
    app.ranking = Ranking(tmp_path / "ranking.json")
    app.progresso = Progresso(tmp_path / "progresso.json")
    partida = CenaPartida(app, Programador)
    app.trocar(partida)
    jogo = partida.jogo
    local = LocalDeInvocacao(jogo.jogador.posicao + (2000, 900), "bibliotecaria")
    jogo.adicionar(local)
    tecla_m = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m, mod=0, unicode="m", scancode=0)
    app.passo(1 / 60, [tecla_m])
    cena = app.cena_atual
    assert isinstance(cena, CenaMiniMapa)
    tempo = jogo.placar.tempo
    app.passo(1 / 60, [])                                     # desenha o mapa e os rostos; a partida fica parada
    assert jogo.placar.tempo == tempo
    area = pygame.Rect(100, 50, 300, 500)
    assert cena.ponto_no_mapa(jogo.arena.topleft, area) == area.topleft
    assert cena.ponto_no_mapa(jogo.arena.bottomright, area) == area.bottomright

    def clique(ponto):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=ponto)

    assert jogo.marcados == set()
    app.passo(1 / 60, [clique(cena.ponto_no_mapa(local.posicao))])
    assert jogo.marcados == {"Bibliotecária"} and app.cena_atual is cena      # clicar não fecha o mapa
    app.passo(1 / 60, [clique(cena.ponto_no_mapa(local.posicao))])
    assert jogo.marcados == set()                                              # clicar de novo desmarca
    app.passo(1 / 60, [clique((5, 5))])
    assert jogo.marcados == set() and app.cena_atual is cena
    app.passo(1 / 60, [tecla_m])
    assert app.cena_atual is partida
