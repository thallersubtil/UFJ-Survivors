import pygame
import pytest

from jogo.ajudantes.ajudantes import FuscaVeiculo
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.claude import MascoteClaude
from jogo.armas.fusca import FuscaAzul
from jogo.armas.gemini import Gemini
from jogo.inimigos.bug import Bug
from jogo.projeteis.projeteis import EstrelaGemini, TiroChatGPT

NOVAS = [MascoteChatGPT, MascoteClaude, Gemini, FuscaAzul]


def parado(bug):
    bug.velocidade = 0
    return bug


@pytest.mark.parametrize("classe", NOVAS)
def test_tabelas_de_atributos(classe):
    for valores in classe.ATRIBUTOS.values():
        assert len(valores) == classe.NIVEL_MAXIMO
    assert len(classe.MELHORIAS) == classe.NIVEL_MAXIMO - 1
    assert classe.NOME and classe.DESCRICAO and classe.ICONE


def test_chatgpt_atira_no_mais_proximo_e_nao_atira_sem_alvo(jogo_limpo, monkeypatch):
    monkeypatch.setattr(MascoteChatGPT, "CHANCE_ALUCINAR", 0.0)
    jogo = jogo_limpo()
    arma = MascoteChatGPT()
    arma.atualizar(0.0, jogo, jogo.jogador)
    jogo._incorporar_novas()
    assert not any(isinstance(e, TiroChatGPT) for e in jogo.entidades)
    jogo.adicionar(parado(Bug(jogo.jogador.posicao + (200, 0))))
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    assert arma.disparar(jogo, jogo.jogador)
    jogo._incorporar_novas()
    tiros = [e for e in jogo.entidades if isinstance(e, TiroChatGPT)]
    assert len(tiros) == 1 and tiros[0].velocidade.x > 0


def test_chatgpt_alucinado_da_dano_dobrado(jogo_limpo, monkeypatch):
    jogo = jogo_limpo()
    monkeypatch.setattr(MascoteChatGPT, "CHANCE_ALUCINAR", 1.0)
    arma = MascoteChatGPT()
    arma.atualizar(0.0, jogo, jogo.jogador)
    jogo.adicionar(parado(Bug(jogo.jogador.posicao + (200, 0))))
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    arma.disparar(jogo, jogo.jogador)
    jogo._incorporar_novas()
    tiro = [e for e in jogo.entidades if isinstance(e, TiroChatGPT)][0]
    assert tiro.alucinado and tiro.dano == pytest.approx(arma.valor("dano") * 2)


def test_claude_pensa_e_golpeia_o_inimigo_com_mais_vida(jogo_limpo):
    jogo = jogo_limpo()
    fraco = parado(Bug(jogo.jogador.posicao + (200, 0)))
    forte = parado(Bug(jogo.jogador.posicao + (-200, 0), escala=40))
    jogo.adicionar(fraco)
    jogo.adicionar(forte)
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    arma = MascoteClaude()
    arma.atualizar(1.0, jogo, jogo.jogador)
    assert 0 < arma.progresso < 1
    arma.atualizar(5.0, jogo, jogo.jogador)
    assert arma.progresso == 0
    assert forte.vida < forte.vida_maxima
    assert fraco.vida == fraco.vida_maxima


def test_estrela_gemini_se_divide_ao_acertar(jogo_limpo):
    jogo = jogo_limpo()
    jogo.adicionar(parado(Bug(jogo.jogador.posicao + (100, 0), escala=20)))
    jogo.adicionar(EstrelaGemini(jogo.jogador.posicao + (60, 0), (380, 0), 10, geracoes=1))
    for _ in range(10):
        jogo.atualizar(1 / 60)
    assert sum(isinstance(e, EstrelaGemini) for e in jogo.entidades) == 2


def test_gemini_dispara_estrela_com_geracoes_do_nivel(jogo_limpo):
    jogo = jogo_limpo()
    arma = Gemini()
    assert arma.disparar(jogo, jogo.jogador)
    jogo._incorporar_novas()
    estrela = [e for e in jogo.entidades if isinstance(e, EstrelaGemini)][0]
    assert estrela.geracoes == arma.valor("geracoes")


def test_fusca_atravessa_a_tela_e_possui_inimigos(jogo_limpo):
    jogo = jogo_limpo()
    bug = parado(Bug(jogo.jogador.posicao + (0, 150), escala=50))
    jogo.adicionar(bug)
    tela = jogo.camera.retangulo
    jogo.adicionar(FuscaVeiculo((tela.left - 100, bug.posicao.y), 1, possessao=3.0, dano=8))
    for _ in range(200):
        jogo.atualizar(1 / 60)
    assert bug.possuido > 0
    assert not any(isinstance(e, FuscaVeiculo) for e in jogo.entidades)


def test_arma_fusca_solta_fuscas_de_tempos_em_tempos(jogo_limpo):
    jogo = jogo_limpo()
    arma = FuscaAzul()
    arma.atualizar(10.0, jogo, jogo.jogador)
    jogo._incorporar_novas()
    assert sum(isinstance(e, FuscaVeiculo) for e in jogo.entidades) == arma.valor("quantidade")


def test_possuido_soca_outro_inimigo(jogo_limpo):
    jogo = jogo_limpo()
    possuido = Bug(jogo.jogador.posicao + (300, 0))
    vitima = parado(Bug(jogo.jogador.posicao + (330, 0), escala=10))
    jogo.adicionar(possuido)
    jogo.adicionar(vitima)
    possuido.possuir(3)
    for _ in range(60):
        jogo.atualizar(1 / 60)
    assert vitima.vida < vitima.vida_maxima
