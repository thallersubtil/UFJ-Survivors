"""As armas do semestre: as comuns novas (Régua de 1 Metro, Corrente de WhatsApp), a colab Fake News e as armas
exclusivas das classes (Dado de 20 Lados; Lightstick, Teclado Mecânico, Caneta de Correção e Mapa do Campus são
testadas em test_armas_exclusivas.py)."""
import pygame
import pytest

from jogo.ajudantes.golpes import ArcoDaRegua, DadoArremessado, ElosDaCorrente
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.colabs import Colab, FakeNews
from jogo.armas.corrente_whatsapp import CorrenteDeWhatsApp
from jogo.armas.dado import DadoDeVinteLados
from jogo.armas.regua import ReguaDeUmMetro
from jogo.inimigos.bug import Bug
from jogo.jogador.classes import MestreDeRPG
from jogo.progressao import Progressao

NOVAS = [ReguaDeUmMetro, CorrenteDeWhatsApp]


def jogo_com_bugs(jogo_limpo, *deslocamentos, classe=None):
    jogo = jogo_limpo(classe) if classe else jogo_limpo()
    jogo.jogador.armas = []
    bugs = []
    for deslocamento in deslocamentos:
        bug = Bug(jogo.jogador.posicao + deslocamento)
        bug.velocidade = 0
        bug.vida_maxima = 10_000           # aguenta todos os golpes do teste
        bug.vida = 10_000
        bugs.append(bug)
        jogo.adicionar(bug)
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    return jogo, bugs


def novas(jogo, tipo):
    jogo._incorporar_novas()
    return [e for e in jogo.entidades if isinstance(e, tipo)]


def no_maximo(arma):
    arma.nivel = arma.NIVEL_MAXIMO
    return arma


@pytest.mark.parametrize("classe", NOVAS)
def test_tabelas_de_atributos(classe):
    for valores in classe.ATRIBUTOS.values():
        assert len(valores) == classe.NIVEL_MAXIMO
    assert len(classe.MELHORIAS) == classe.NIVEL_MAXIMO - 1
    assert classe.NOME and classe.DESCRICAO and classe.ICONE
    assert classe in Progressao.ARMAS


def test_mestre_de_rpg_comeca_com_o_dado_e_o_gemini_vira_arma_comum():
    from jogo.armas.gemini import Gemini
    assert [type(a) for a in MestreDeRPG((0, 0)).armas] == [DadoDeVinteLados]
    assert DadoDeVinteLados.EXCLUSIVA and DadoDeVinteLados not in Progressao.ARMAS
    assert Gemini in Progressao.ARMAS


# ------------------------------------------------------------------ Dado de 20 Lados

def test_dano_do_dado_e_o_numero_tirado_com_20_triplo_e_1_errando():
    dado, heroi = DadoDeVinteLados(), MestreDeRPG((0, 0))
    por_ponto = dado.valor("dano") * heroi.multiplicador_dano
    assert dado.dano_da_rolagem(1, heroi) == 0
    assert dado.dano_da_rolagem(12, heroi) == pytest.approx(12 * por_ponto)
    assert dado.dano_da_rolagem(20, heroi) == pytest.approx(20 * por_ponto * 3)


class RngFixo:
    def __init__(self, *numeros):
        self.numeros = list(numeros)

    def randint(self, a, b):
        return self.numeros.pop(0)


def test_no_maximo_o_dado_rola_com_vantagem():
    dado = DadoDeVinteLados()
    assert dado.rolar(RngFixo(4, 17)) == 4                # nível 1: o primeiro número vale
    no_maximo(dado)
    assert dado.rolar(RngFixo(4, 17)) == 17               # vantagem: fica com o maior
    assert dado.rolar(RngFixo(19, 2)) == 19


def test_um_natural_nao_joga_o_dado_e_vinte_joga_com_dano_triplo(jogo_limpo, monkeypatch):
    jogo, _ = jogo_com_bugs(jogo_limpo, (200, 0))
    dado, heroi = DadoDeVinteLados(), jogo.jogador
    monkeypatch.setattr(jogo.rng, "randint", lambda a, b: 1)
    assert dado.disparar(jogo, heroi)                     # jogou, mas errou
    assert novas(jogo, DadoArremessado) == []
    monkeypatch.setattr(jogo.rng, "randint", lambda a, b: 20)
    dado.disparar(jogo, heroi)
    [voando] = novas(jogo, DadoArremessado)
    assert voando.numero == 20 and voando.dano == pytest.approx(dado.dano_da_rolagem(20, heroi))
    assert voando.velocidade.x > 0                        # vai no bug, à direita


def test_dado_sem_alvo_nao_joga(jogo_limpo):
    jogo, _ = jogo_com_bugs(jogo_limpo)
    assert not DadoDeVinteLados().disparar(jogo, jogo.jogador)


def test_dado_supremo_joga_tres_dados(jogo_limpo, monkeypatch):
    jogo, _ = jogo_com_bugs(jogo_limpo, (200, 0))
    monkeypatch.setattr(jogo.rng, "randint", lambda a, b: 10)
    no_maximo(DadoDeVinteLados()).disparar(jogo, jogo.jogador)
    assert len(novas(jogo, DadoArremessado)) == 3


# ------------------------------------------------------------------ Régua de 1 Metro

def test_regua_acerta_o_arco_da_frente_e_nao_o_de_tras(jogo_limpo):
    jogo, (frente, atras) = jogo_com_bugs(jogo_limpo, (80, 0), (-80, 0))
    jogo.jogador.direcao_mira = pygame.Vector2(1, 0)
    vida = frente.vida
    assert ReguaDeUmMetro().disparar(jogo, jogo.jogador)
    for arco in novas(jogo, ArcoDaRegua):
        arco.atualizar(1 / 30, jogo)
    assert frente.vida < vida and atras.vida == vida


def test_regua_suprema_bate_na_frente_e_atras(jogo_limpo):
    jogo, (frente, atras) = jogo_com_bugs(jogo_limpo, (80, 0), (-80, 0))
    jogo.jogador.direcao_mira = pygame.Vector2(1, 0)
    vida = frente.vida
    no_maximo(ReguaDeUmMetro()).disparar(jogo, jogo.jogador)
    arcos = novas(jogo, ArcoDaRegua)
    for arco in arcos:
        arco.atualizar(1 / 30, jogo)
    assert len(arcos) == 2 and frente.vida < vida and atras.vida < vida


def test_regua_nao_gasta_o_golpe_no_vazio(jogo_limpo):
    jogo, _ = jogo_com_bugs(jogo_limpo, (400, 0))
    assert not ReguaDeUmMetro().disparar(jogo, jogo.jogador)


def test_arco_fere_cada_inimigo_uma_vez_so(jogo_limpo):
    jogo, (bug,) = jogo_com_bugs(jogo_limpo, (80, 0))
    jogo.jogador.direcao_mira = pygame.Vector2(1, 0)
    ReguaDeUmMetro().disparar(jogo, jogo.jogador)
    [arco] = novas(jogo, ArcoDaRegua)
    arco.atualizar(1 / 30, jogo)
    depois_do_golpe = bug.vida
    for _ in range(5):
        arco.atualizar(1 / 30, jogo)
    assert bug.vida == depois_do_golpe


# ------------------------------------------------------------------ Corrente de WhatsApp

def test_corrente_pula_de_inimigo_em_inimigo_sem_repetir(jogo_limpo, monkeypatch):
    jogo, bugs = jogo_com_bugs(jogo_limpo, (150, 0), (300, 0), (450, 0), (600, 0), (750, 0), (900, 0))
    golpes = []
    original = jogo.causar_dano
    monkeypatch.setattr(jogo, "causar_dano", lambda alvo, *a, **k: golpes.append(alvo) or original(alvo, *a, **k))
    corrente = CorrenteDeWhatsApp()
    assert corrente.disparar(jogo, jogo.jogador)
    assert golpes == bugs[:corrente.valor("saltos") + 1]                     # do mais perto para longe, sem repetir
    [elos] = novas(jogo, ElosDaCorrente)
    assert len(elos.pontos) == len(golpes) + 1                               # começa no aluno


def test_corrente_nao_pula_longe_demais(jogo_limpo):
    jogo, (perto, longe) = jogo_com_bugs(jogo_limpo, (150, 0), (150 + CorrenteDeWhatsApp.ALCANCE_DO_SALTO + 80, 0))
    vida = longe.vida
    CorrenteDeWhatsApp().disparar(jogo, jogo.jogador)
    assert perto.vida < 10_000 and longe.vida == vida


def test_corrente_suprema_cresce_a_cada_encaminhamento(jogo_limpo, monkeypatch):
    jogo, _ = jogo_com_bugs(jogo_limpo, (150, 0), (300, 0), (450, 0))
    danos = []
    monkeypatch.setattr(jogo, "causar_dano", lambda alvo, dano, *a, **k: danos.append(dano))
    no_maximo(CorrenteDeWhatsApp()).disparar(jogo, jogo.jogador)
    assert danos[1] == pytest.approx(danos[0] * 1.1) and danos[2] == pytest.approx(danos[0] * 1.2)


def test_corrente_sem_alvo_nao_dispara(jogo_limpo):
    jogo, _ = jogo_com_bugs(jogo_limpo)
    assert not CorrenteDeWhatsApp().disparar(jogo, jogo.jogador)


# ------------------------------------------------------------------ Fake News

def test_fake_news_e_a_colab_da_corrente_com_o_chatgpt():
    assert FakeNews in Colab.RECEITAS
    armas = [no_maximo(CorrenteDeWhatsApp()), no_maximo(MascoteChatGPT())]
    assert FakeNews in Colab.colabs_disponiveis(armas)
    assert FakeNews not in Colab.colabs_disponiveis([CorrenteDeWhatsApp(), no_maximo(MascoteChatGPT())])


def test_fake_news_espalha_e_quem_acredita_luta_do_seu_lado(jogo_limpo, monkeypatch):
    jogo, bugs = jogo_com_bugs(jogo_limpo, (100, 0), (250, 0), (400, 0))
    monkeypatch.setattr(jogo.rng, "random", lambda: 0.0)     # todo mundo acredita
    fake = FakeNews()
    fake.atualizar(1 / 30, jogo, jogo.jogador)
    assert all(b.vida < 10_000 for b in bugs)
    assert all(b.possuido == pytest.approx(fake.valor("possessao")) for b in bugs)
    assert novas(jogo, ElosDaCorrente)


def test_fake_news_nao_engana_chefe(jogo_limpo, monkeypatch):
    jogo, (bug,) = jogo_com_bugs(jogo_limpo, (100, 0))
    monkeypatch.setattr(type(bug), "CHEFE", True)
    monkeypatch.setattr(jogo.rng, "random", lambda: 0.0)
    FakeNews().atualizar(1 / 30, jogo, jogo.jogador)
    assert bug.possuido == 0


# ------------------------------------------------------------------ desenho

@pytest.mark.parametrize("suprema", [False, True])
def test_golpes_desenham_sem_erro(jogo_limpo, monkeypatch, suprema):
    jogo, _ = jogo_com_bugs(jogo_limpo, (70, 0), (220, 0), (370, 0))
    jogo.jogador.direcao_mira = pygame.Vector2(1, 0)
    monkeypatch.setattr(jogo.rng, "randint", lambda a, b: 20)
    for classe in NOVAS + [DadoDeVinteLados]:
        arma = classe()
        if suprema:
            no_maximo(arma)
        assert arma.disparar(jogo, jogo.jogador)
    fake = FakeNews()
    fake.atualizar(1 / 30, jogo, jogo.jogador)
    tela = pygame.Surface((1280, 720))
    jogo._incorporar_novas()
    for _ in range(4):                                   # alguns quadros: golpe no meio e a poça no chão
        for entidade in list(jogo.entidades):
            if isinstance(entidade, (DadoArremessado, ArcoDaRegua, ElosDaCorrente)):
                entidade.atualizar(1 / 30, jogo)
        jogo._incorporar_novas()
        jogo.desenhar(tela)
