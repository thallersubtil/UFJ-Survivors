import time

import pygame

from jogo.coletaveis.coletaveis import Nota
from jogo.config import DURACAO_PROVA
from jogo.fase import PROVAS, ProvaDeArquiteturaEED, ProvaDeCalculo, ProvaDeTDEPOO, semestre
from jogo.inimigos.bug import Bug
from jogo.inimigos.chefe_possuido import ChefePossuido
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.jogador.alunos import AlunoAgil
from jogo.jogo import Jogo
from jogo.projeteis.projeteis import ProjetilDaMateria


def jogo_imortal(**opcoes):
    jogo = Jogo(AlunoAgil, semente=11, **opcoes)
    jogo.jogador.vida_maxima = 10 ** 9
    jogo.jogador.vida = 10 ** 9
    return jogo


def pular_para(jogo, segundos):
    jogo.fase.tempo = segundos - 0.01
    jogo.atualizar(0.02)


def test_semestre_tem_as_tres_provas_na_ordem():
    assert PROVAS == (ProvaDeCalculo, ProvaDeArquiteturaEED, ProvaDeTDEPOO)
    jogo = jogo_imortal()
    assert [type(f) for f in jogo.fases] == list(PROVAS)
    assert isinstance(jogo.fase, ProvaDeCalculo)
    assert [f.CHEFE for f in semestre()] == ["chefe_calculo", "chefe_arquitetura_ed", "chefe_td_poo"]


def test_cada_prova_dura_cinco_minutos_e_comeca_mais_dificil():
    assert DURACAO_PROVA == 300
    provas = semestre()
    assert all(p.DURACAO == 300 for p in provas)
    escalas = [p.escala_dificuldade for p in provas]
    assert escalas == sorted(escalas) and escalas[0] < escalas[-1]


def test_lacaios_sao_apresentados_na_ordem():
    jogo = jogo_imortal()
    pular_para(jogo, 80)
    assert jogo.fase.ativos == ["bug", "calculadora", "pi"]


def test_mini_chefe_da_prova_de_calculo():
    jogo = jogo_imortal()
    pular_para(jogo, 150)
    jogo._incorporar_novas()
    gigantes = [e for e in jogo.inimigos if e.gigante]
    assert len(gigantes) == 1 and gigantes[0].CHAVE == "calculadora"


def test_formacao_a_cada_minuto():
    jogo = jogo_imortal()
    antes = len(jogo.inimigos)
    pular_para(jogo, 60)
    assert len(jogo.inimigos) >= antes + 20


def test_chefe_chega_no_fim_da_prova():
    jogo = jogo_imortal()
    pular_para(jogo, DURACAO_PROVA - 1)
    assert jogo.chefe is None
    pular_para(jogo, DURACAO_PROVA)
    assert isinstance(jogo.chefe, ChefePossuido)
    assert jogo.chefe.nome == "Cálculo I"
    assert jogo.fase.chefe_apareceu
    assert any("Cálculo I chegou" in texto for texto, _ in jogo.anuncios)


def test_derrotar_o_chefe_passa_para_a_proxima_prova():
    jogo = jogo_imortal()
    pular_para(jogo, DURACAO_PROVA)
    jogo._incorporar_novas()
    lacaio = Bug(jogo.jogador.posicao + (200, 0))
    tiro = ProjetilDaMateria(jogo.jogador.posicao + (400, 0), (0, 0), 5, "dx", (255, 255, 255))
    jogo.adicionar(lacaio)
    jogo.adicionar(tiro)
    jogo._incorporar_novas()
    jogo.jogador.vida_maxima = 100
    jogo.jogador.vida = 10
    assert jogo.causar_dano(jogo.chefe, 10 ** 7)
    assert not jogo.terminou
    assert isinstance(jogo.fase, ProvaDeArquiteturaEED) and jogo.indice_fase == 1
    assert jogo.chefe is None
    assert not lacaio.ativo and not tiro.ativo
    assert jogo.jogador.vida == 60
    assert jogo.baus_pendentes == 1
    assert any("2ª prova" in texto for texto, _ in jogo.anuncios)
    assert jogo.fase.tempo == 0


def test_derrotar_o_ultimo_chefe_vence_o_jogo():
    jogo = jogo_imortal(fases=[ProvaDeTDEPOO()])
    pular_para(jogo, DURACAO_PROVA)
    jogo._incorporar_novas()
    chefe = jogo.chefe
    jogo.causar_dano(chefe, chefe.vida)
    chefe.troca = 0
    chefe.escudo = 0
    assert jogo.causar_dano(chefe, 10 ** 7)
    assert jogo.terminou and jogo.venceu


def test_treino_pode_comecar_perto_do_chefe():
    fase = ProvaDeArquiteturaEED()
    fase.adiantar_para_o_chefe()
    jogo = jogo_imortal(fases=[fase])
    for _ in range(4 * 60):
        jogo.atualizar(1 / 60)
    assert jogo.chefe is not None and jogo.chefe.nome == "Arquitetura de Computadores"
    assert not any(e.gigante for e in jogo.inimigos if e is not jogo.chefe)


def test_quadro_continua_rapido_com_muitas_entidades():
    jogo = jogo_imortal()
    for i in range(300):
        jogo.adicionar(Bug(jogo.jogador.posicao + pygame.Vector2(200 + (i % 30) * 25, 0).rotate(i * 7)))
    for i in range(400):
        jogo.adicionar(Nota(jogo.jogador.posicao + pygame.Vector2(600, 0).rotate(i), 1))
    jogo._incorporar_novas()
    tela = pygame.Surface((1280, 720))
    inicio = time.perf_counter()
    for _ in range(30):
        jogo.atualizar(1 / 60)
        jogo.desenhar(tela)
    media_ms = (time.perf_counter() - inicio) / 30 * 1000
    assert media_ms < 33, f"quadro médio de {media_ms:.1f} ms"


def test_prova_e_chefe_possuido_sao_abstratos():
    import pytest
    from jogo.fase import Prova
    with pytest.raises(TypeError):
        Prova()
    with pytest.raises(TypeError):
        ChefePossuido((0, 0))


def test_lacaio_criado_no_mesmo_quadro_nao_passa_para_a_proxima_prova():
    jogo = jogo_imortal()
    pular_para(jogo, DURACAO_PROVA)
    jogo._incorporar_novas()
    atrasado = Bug(jogo.jogador.posicao + (200, 0))
    jogo.adicionar(atrasado)          # ainda na fila de novas entidades
    jogo.causar_dano(jogo.chefe, 10 ** 7)
    assert not atrasado.ativo


def test_reprovado_mostra_a_materia_do_chefe_atual():
    from jogo.cenas.fim import CenaFimDeJogo
    jogo = jogo_imortal(fases=[ProvaDeArquiteturaEED()])
    assert CenaFimDeJogo.motivo(jogo) == "Reprovado em Arquitetura de Computadores e Estrutura de Dados em C."
    pular_para(jogo, DURACAO_PROVA)
    jogo._incorporar_novas()
    chefe = jogo.chefe
    jogo.causar_dano(chefe, chefe.vida)
    assert CenaFimDeJogo.motivo(jogo) == "Reprovado em Estrutura de Dados em C."
