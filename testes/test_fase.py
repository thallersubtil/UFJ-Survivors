import time

import pygame

from jogo.coletaveis.coletaveis import Nota
from jogo.fase import SemanaDeProvas
from jogo.inimigos.bug import Bug
from jogo.inimigos.professor import Professor
from jogo.jogador.alunos import AlunoAgil
from jogo.jogo import Jogo


def jogo_imortal():
    jogo = Jogo(AlunoAgil, semente=11)
    jogo.jogador.vida_maxima = 10 ** 9
    jogo.jogador.vida = 10 ** 9
    return jogo


def pular_para(jogo, segundos):
    jogo.fase.tempo = segundos - 0.01
    jogo.atualizar(0.02)


def test_lacaios_sao_apresentados_na_ordem():
    fase = SemanaDeProvas()
    nomes = [nome for _, nome in fase.APRESENTACOES]
    assert nomes == ["bug", "calculadora", "mouse", "caixinha", "pi", "ponteiro", "pilha", "pente_ram"]
    jogo = jogo_imortal()
    pular_para(jogo, 150)
    assert jogo.fase.ativos == ["bug", "calculadora", "mouse", "caixinha"]
    assert [t for t, _ in fase.APRESENTACOES] == [0, 40, 80, 120, 160, 200, 240, 280]


def test_mini_chefes_aos_2min40_e_aos_5min20():
    jogo = jogo_imortal()
    pular_para(jogo, 160)
    jogo._incorporar_novas()
    gigantes = [e for e in jogo.inimigos if e.gigante]
    assert len(gigantes) == 1 and gigantes[0].CHAVE == "calculadora"
    pular_para(jogo, 320)
    gigantes = [e for e in jogo.inimigos if e.gigante]
    assert {g.CHAVE for g in gigantes} == {"calculadora", "pente_ram"}


def test_formacao_a_cada_minuto():
    jogo = jogo_imortal()
    antes = len(jogo.inimigos)
    pular_para(jogo, 60)
    assert len(jogo.inimigos) >= antes + 20


def test_professor_aos_8_minutos():
    from jogo.config import DURACAO_FASE
    assert DURACAO_FASE == 480 == SemanaDeProvas.DURACAO
    jogo = jogo_imortal()
    pular_para(jogo, 479)
    assert jogo.chefe is None
    pular_para(jogo, 480)
    assert isinstance(jogo.chefe, Professor)
    assert jogo.fase.chefe_apareceu
    assert any("Professor" in texto for texto, _ in jogo.anuncios)


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
