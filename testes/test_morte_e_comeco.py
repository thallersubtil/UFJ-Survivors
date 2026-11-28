"""Reação a dano, corpo caindo na morte, golpes à frente do corpo e o começo da partida com inimigos na tela."""
import pygame
import pytest

from jogo.ajudantes.golpes import AVANCO_DO_GOLPE, ArcoDaRegua
from jogo.config import ALTURA, LARGURA
from jogo.efeitos import CorpoCaindo, NumeroDeDano
from jogo.fase import Semestre
from jogo.inimigos.bug import Bug
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.quebraveis import QUEBRAVEIS


def colocar(jogo, inimigo):
    jogo.adicionar(inimigo)
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos + jogo.grupos["quebravel"])
    return inimigo


def novos(jogo, classe):
    jogo._incorporar_novas()
    return [e for e in jogo.entidades if isinstance(e, classe) and e.ativo]


def test_inimigo_morto_sai_do_jogo_na_hora_e_deixa_so_o_corpo(jogo_limpo):
    jogo = jogo_limpo()
    bug = colocar(jogo, Bug(jogo.jogador.posicao + (150, 0)))
    assert jogo.causar_dano(bug, 10 ** 6, pygame.Vector2(1, 0))
    assert not bug.ativo                                  # saiu na hora: não leva golpe...
    jogo._limpar()
    assert bug not in jogo.inimigos                       # ...nem pesa no alvo da fase
    [corpo] = novos(jogo, CorpoCaindo)
    assert corpo.direcao.x > 0                            # escorrega para onde o golpe empurrou
    assert corpo.duracao == pytest.approx(Bug.DURACAO_DO_CORPO)


def test_corpo_escorrega_apaga_e_some(jogo_limpo):
    jogo = jogo_limpo()
    bug = colocar(jogo, Bug(jogo.jogador.posicao + (150, 0)))
    jogo.causar_dano(bug, 10 ** 6)
    [corpo] = novos(jogo, CorpoCaindo)
    tela = pygame.Surface((LARGURA, ALTURA))
    for _ in range(round(corpo.duracao * 60) + 2):
        corpo.atualizar(1 / 60, jogo)
        corpo.desenhar(tela, jogo.camera)
    assert not corpo.ativo


def test_mini_chefe_cai_mais_devagar_e_treme(jogo_limpo):
    jogo = jogo_limpo()
    tia = colocar(jogo, FabricaDeInimigos.criar("tia_da_cantina", jogo.jogador.posicao + (300, 0)))
    tia.receber_dano(1)
    assert tia.tremendo                                   # treme no golpe
    corpo = tia.criar_corpo(jogo)
    assert corpo.duracao > Bug.DURACAO_DO_CORPO and len(corpo.poeira) > Bug.POEIRA_DO_CORPO


def test_objeto_quebravel_nao_deixa_corpo(jogo_limpo):
    jogo = jogo_limpo()
    caixa = colocar(jogo, QUEBRAVEIS[0](jogo.jogador.posicao + (150, 0)))
    assert caixa.criar_corpo(jogo) is None


def test_lacaio_comum_pisca_mas_nao_treme(jogo_limpo):
    jogo = jogo_limpo()
    bug = colocar(jogo, Bug(jogo.jogador.posicao + (150, 0), escala=50))
    jogo.causar_dano(bug, 1)
    assert bug.piscar > 0 and not bug.tremendo


def test_numero_de_dano_salta_e_cai(jogo_limpo):
    numero = NumeroDeDano(12, pygame.Vector2(0, 0))
    alturas = []
    for _ in range(30):
        numero.tempo += 1 / 60
        alturas.append(numero.deslocamento.y)
    topo = alturas.index(min(alturas))
    assert 0 < topo < len(alturas) - 1                    # sobe, chega no alto e volta a cair
    assert alturas[-1] > alturas[topo]


def test_critico_sai_maior_e_com_exclamacao():
    comum, critico = NumeroDeDano(12, pygame.Vector2()), NumeroDeDano(12, pygame.Vector2(), critico=True)
    assert critico.imagem.get_height() > comum.imagem.get_height()
    assert critico.imagem.get_width() > comum.imagem.get_width()          # "12!" é mais largo que "12"


def test_golpe_em_arco_nasce_a_frente_do_corpo(jogo_limpo):
    jogo = jogo_limpo()
    heroi = jogo.jogador
    arco = ArcoDaRegua(heroi, pygame.Vector2(1, 0), 120, 100, 10)
    assert arco.centro.distance_to(heroi.posicao) == pytest.approx(AVANCO_DO_GOLPE)
    longe = colocar(jogo, Bug(heroi.posicao + (AVANCO_DO_GOLPE + 110, 0), escala=50))
    vida = longe.vida
    jogo.adicionar(arco)
    jogo._incorporar_novas()
    arco.atualizar(1 / 60, jogo)
    assert longe.vida < vida                              # alcança além do que alcançaria colado no corpo


def test_inimigos_nascem_logo_fora_da_borda_da_tela(jogo_limpo):
    jogo = jogo_limpo()
    jogo.mapa.bloqueado = lambda posicao, raio: False
    centro = jogo.jogador.posicao
    for _ in range(200):
        p = Semestre.posicao_de_nascimento(jogo) - centro
        fora_x, fora_y = abs(p.x) - LARGURA / 2, abs(p.y) - ALTURA / 2
        assert max(fora_x, fora_y) == pytest.approx(Semestre.FORA_DA_TELA)   # na borda, não num círculo largo


def test_partida_comeca_com_uma_turma_na_tela(jogo_limpo):
    jogo = jogo_limpo()
    fase = Semestre()
    fase.atualizar(1 / 60, jogo)
    jogo._incorporar_novas()
    assert len(jogo.inimigos) >= Semestre.TURMA_INICIAL
    fase.atualizar(1 / 60, jogo)
    jogo._incorporar_novas()
    assert len(jogo.inimigos) < Semestre.TURMA_INICIAL * 2          # a turma sai uma vez só
