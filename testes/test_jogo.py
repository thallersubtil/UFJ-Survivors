import pygame
import pytest

from jogo.coletaveis.coletaveis import Nota
from jogo.config import COMBO_ESPECIAL, LIMITE_COLETAVEIS
from jogo.inimigos.bug import Bug
from jogo.jogador.alunos import AlunoAgil, AlunoResistente
from jogo.jogo import Jogo
from jogo.nucleo.entidade import Entidade


class Espiao(Entidade):
    def __init__(self):
        super().__init__((0, 0), 1)
        self.chamadas = 0

    def atualizar(self, dt, jogo):
        self.chamadas += 1

    def desenhar(self, tela, camera):
        pass


def jogo_sem_decoracao(classe=AlunoAgil):
    jogo = Jogo(classe, semente=1)
    for e in jogo.entidades:
        if e.grupo == "decoracao":
            e.remover()
    jogo._limpar()
    return jogo


def test_jogo_contem_jogador_fase_e_placar():
    jogo = Jogo(AlunoAgil, semente=1)
    assert jogo.jogador in jogo.entidades
    assert jogo.fase is not None and jogo.placar is not None
    assert jogo.jogador.posicao == pygame.Vector2(jogo.arena.center)


def test_laco_unico_atualiza_qualquer_entidade():
    jogo = jogo_sem_decoracao()
    espiao = Espiao()
    jogo.adicionar(espiao)
    jogo.atualizar(1 / 60)
    jogo.atualizar(1 / 60)
    assert espiao.chamadas == 2


def test_entidade_removida_sai_das_listas():
    jogo = jogo_sem_decoracao()
    bug = Bug(jogo.jogador.posicao + (300, 0))
    jogo.adicionar(bug)
    jogo.atualizar(0.001)
    assert bug in jogo.inimigos
    bug.remover()
    jogo.atualizar(0.001)
    assert bug not in jogo.inimigos and bug not in jogo.entidades


def test_causar_dano_mata_pontua_e_solta_nota():
    jogo = jogo_sem_decoracao()
    bug = Bug(jogo.jogador.posicao + (300, 0))
    jogo.adicionar(bug)
    jogo.atualizar(0.001)
    assert jogo.causar_dano(bug, 1000) is True
    assert not bug.ativo
    assert jogo.placar.eliminacoes == 1
    assert jogo.placar.pontos == Bug.PONTOS
    assert jogo.causar_dano(bug, 1000) is False
    jogo.atualizar(0.001)
    assert any(isinstance(e, Nota) for e in jogo.entidades)


def test_combo_67_toca_bonus_de_velocidade():
    jogo = jogo_sem_decoracao()
    base = jogo.jogador.velocidade
    for _ in range(COMBO_ESPECIAL):
        bug = Bug(jogo.jogador.posicao + (500, 0))
        jogo.adicionar(bug)
        jogo._incorporar_novas()
        jogo.causar_dano(bug, 1000)
    assert jogo.jogador.tem_bonus("combo67")
    assert jogo.jogador.velocidade == pytest.approx(base * 1.5)
    assert any(texto == "67!" for texto, _ in jogo.anuncios)


def test_ferir_jogador_respeita_invencibilidade_e_zera_combo():
    jogo = jogo_sem_decoracao()
    jogo.placar.combo = 10
    assert jogo.ferir_jogador(5) is True
    assert jogo.placar.combo == 0
    assert jogo.ferir_jogador(5) is False
    assert jogo.jogador.vida == jogo.jogador.vida_maxima - 5


def test_bug_encosta_e_fere_o_heroi():
    jogo = jogo_sem_decoracao()
    jogo.adicionar(Bug(jogo.jogador.posicao + (5, 0)))
    jogo.atualizar(1 / 60)
    assert jogo.jogador.vida < jogo.jogador.vida_maxima


def test_cobra_acerta_bug_na_frente():
    jogo = jogo_sem_decoracao()
    bug = Bug(jogo.jogador.posicao + (120, 0))
    bug.VELOCIDADE = 0
    bug.velocidade = 0
    jogo.adicionar(bug)
    for _ in range(40):
        jogo.atualizar(1 / 60)
    assert not bug.ativo or bug.vida < bug.vida_maxima


def test_caramelo_morde_bug_por_perto():
    jogo = jogo_sem_decoracao(AlunoResistente)
    bug = Bug(jogo.jogador.posicao + (70, 0), escala=50)
    bug.velocidade = 0
    jogo.adicionar(bug)
    for _ in range(90):
        jogo.atualizar(1 / 60)
    assert bug.vida < bug.vida_maxima


def test_notas_viram_experiencia_e_niveis_pendentes():
    jogo = jogo_sem_decoracao()
    jogo.adicionar(Nota(jogo.jogador.posicao, 500))
    jogo.atualizar(1 / 60)
    assert jogo.niveis_pendentes > 1


def test_notas_se_acumulam_quando_passa_do_limite():
    jogo = jogo_sem_decoracao()
    longe = jogo.jogador.posicao + (1000, 0)
    for _ in range(LIMITE_COLETAVEIS + 50):
        jogo.soltar_nota(longe, 1)
        jogo._incorporar_novas()
    notas = [e for e in jogo.entidades if isinstance(e, Nota)]
    assert len(notas) == LIMITE_COLETAVEIS
    assert sum(n.valor for n in notas) == LIMITE_COLETAVEIS + 50


def test_morte_do_heroi_termina_a_partida():
    jogo = jogo_sem_decoracao()
    jogo.jogador.vida = 0
    jogo.atualizar(1 / 60)
    assert jogo.terminou and not jogo.venceu


def test_partida_de_um_minuto_com_jogador_automatico():
    jogo = Jogo(AlunoAgil, semente=7)
    jogo.jogador.vida_maxima = 10 ** 9
    jogo.jogador.vida = 10 ** 9
    tela = pygame.Surface((1280, 720))
    passos = 60 * 60
    for i in range(passos):
        jogo.entrada.direcao = pygame.Vector2(1, 0).rotate(i * 0.5)
        jogo.atualizar(1 / 60)
        if i % 60 == 0:
            jogo.desenhar(tela)
    assert jogo.placar.tempo == pytest.approx(60, abs=0.1)
    assert len(jogo.inimigos) > 10
    assert jogo.placar.eliminacoes > 0


def test_resultado_vira_registro_de_ranking():
    jogo = jogo_sem_decoracao()
    jogo.placar.adicionar_pontos(100)
    jogo.placar.tempo = 10
    jogo.terminar(True)
    r = jogo.resultado("Ana")
    assert r.nome == "Ana" and r.heroi == "Aluno 1" and r.venceu
    assert r.pontos == 100 + 20 + 5000
