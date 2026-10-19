import pygame
import pytest

from jogo.efeitos import FaiscaExplosao, TextoFlutuante
from jogo.inimigos.caixinha import Caixinha, CaixinhaPequena
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo
from jogo.inimigos.mouse_de_bolinha import MouseDeBolinha

LACAIOS = ["bug", "calculadora", "mouse", "caixinha", "pi", "ponteiro", "pilha", "pente_ram"]


def novos(jogo):
    jogo._incorporar_novas()
    return jogo.entidades


def test_todos_os_lacaios_estao_registrados_e_herdam_de_inimigo():
    for nome in LACAIOS + ["chefe_calculo", "chefe_arquitetura_ed", "chefe_td_poo"]:
        assert issubclass(FabricaDeInimigos.classe(nome), Inimigo)


@pytest.mark.parametrize("nome", LACAIOS + ["chefe_calculo", "chefe_arquitetura_ed", "chefe_td_poo"])
def test_cada_inimigo_anda_e_desenha_sem_erro(jogo_limpo, nome):
    jogo = jogo_limpo()
    inimigo = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + (250, 120))
    jogo.adicionar(inimigo)
    tela = pygame.Surface((1280, 720))
    inicio = pygame.Vector2(inimigo.posicao)
    for _ in range(90):
        jogo.atualizar(1 / 60)
    jogo.desenhar(tela)
    assert inimigo.posicao != inicio


def test_mouse_fica_parado_e_depois_dispara(jogo_limpo):
    jogo = jogo_limpo()
    mouse = MouseDeBolinha(jogo.jogador.posicao + (400, 0))
    jogo.adicionar(mouse)
    jogo.atualizar(0.2)
    assert mouse.posicao.x == pytest.approx(jogo.jogador.posicao.x + 400, abs=1)
    for _ in range(20):
        jogo.atualizar(1 / 60)
    assert mouse.correndo
    assert mouse.posicao.x < jogo.jogador.posicao.x + 400 - 20


def test_caixinha_se_divide_em_duas_que_nao_se_dividem(jogo_limpo):
    jogo = jogo_limpo()
    caixa = Caixinha(jogo.jogador.posicao + (300, 0))
    jogo.adicionar(caixa)
    jogo._incorporar_novas()
    jogo.causar_dano(caixa, 1000)
    pequenas = [e for e in novos(jogo) if isinstance(e, CaixinhaPequena)]
    assert len(pequenas) == 2
    jogo.causar_dano(pequenas[0], 1000)
    assert len([e for e in novos(jogo) if isinstance(e, CaixinhaPequena) and e.ativo]) == 1


def test_pi_mostra_3_14_ao_morrer(jogo_limpo):
    jogo = jogo_limpo()
    pi = FabricaDeInimigos.criar("pi", jogo.jogador.posicao + (300, 0))
    jogo.adicionar(pi)
    jogo._incorporar_novas()
    jogo.causar_dano(pi, 1000)
    assert any(isinstance(e, TextoFlutuante) for e in novos(jogo))


def test_pilha_explode_e_fere_quem_estiver_perto(jogo_limpo):
    jogo = jogo_limpo()
    pilha = FabricaDeInimigos.criar("pilha", jogo.jogador.posicao + (40, 0))
    jogo.adicionar(pilha)
    jogo._incorporar_novas()
    jogo.causar_dano(pilha, 1000)
    assert any(isinstance(e, FaiscaExplosao) for e in novos(jogo))
    jogo.atualizar(1 / 60)
    assert jogo.jogador.vida < jogo.jogador.vida_maxima


def test_ponteiro_mergulha_em_linha_reta(jogo_limpo):
    jogo = jogo_limpo()
    ponteiro = FabricaDeInimigos.criar("ponteiro", jogo.jogador.posicao + (500, 0))
    jogo.adicionar(ponteiro)
    jogo.atualizar(1 / 60)
    direcao = pygame.Vector2(ponteiro.direcao)
    jogo.jogador.posicao.y += 200
    jogo.atualizar(1 / 60)
    assert ponteiro.direcao == direcao


def test_chefe_nao_e_possuido_pelo_fusca(jogo_limpo):
    jogo = jogo_limpo()
    chefe = FabricaDeInimigos.criar("chefe_calculo", jogo.jogador.posicao + (300, 0))
    jogo.iniciar_chefe(chefe)
    jogo._incorporar_novas()
    chefe.possuir(5)
    assert chefe.possuido == 0
