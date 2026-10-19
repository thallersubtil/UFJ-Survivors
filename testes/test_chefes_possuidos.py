import pygame
import pytest

from jogo.inimigos.acoes_do_chefe import Investida, Rajada
from jogo.inimigos.chefe_possuido import ChefePossuido
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.materias.materia import Materia
from jogo.projeteis.projeteis import ProjetilDaMateria


def novos(jogo):
    jogo._incorporar_novas()
    return jogo.entidades


def projeteis(jogo):
    return [e for e in novos(jogo) if isinstance(e, ProjetilDaMateria) and e.ativo]


def colocar_chefe(jogo, nome):
    chefe = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + (300, 0))
    jogo.iniciar_chefe(chefe)
    jogo._incorporar_novas()
    return chefe


def test_materia_e_abstrata():
    with pytest.raises(TypeError):
        Materia()


def test_chefe_possuido_sem_materia_e_recusado():
    class SemMateria(ChefePossuido):
        MATERIAS = ()

    with pytest.raises(ValueError):
        SemMateria((0, 0))


def test_nome_do_chefe_e_o_nome_da_materia(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_calculo")
    assert chefe.nome == "Cálculo I"
    assert str(chefe.materia) == "Cálculo I"
    assert chefe.vida == chefe.vida_maxima == chefe.materia.VIDA
    assert any("Cálculo I" in texto for texto, _ in jogo.anuncios)


def test_calculo_tem_uma_fase_e_derrota_vence(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_calculo")
    assert chefe.total_de_fases == 1 and not chefe.tem_proxima_materia
    assert jogo.causar_dano(chefe, 10 ** 7)
    assert jogo.terminou and jogo.venceu


def test_ataques_de_calculo_lancam_simbolos_investem_e_chamam(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_calculo")
    materia = chefe.materia
    materia.limite(chefe, jogo)
    assert len(projeteis(jogo)) == 7
    chefe.vida = chefe.vida_maxima * 0.4
    materia.limite(chefe, jogo)
    assert len(projeteis(jogo)) == 7 + 11
    antes = len(jogo.inimigos)
    materia.chamar_lacaios(chefe, jogo)
    novos(jogo)
    assert len(jogo.inimigos) > antes
    materia.derivada(chefe, jogo)
    assert isinstance(chefe.acao_atual, Investida)
    inicio = pygame.Vector2(chefe.posicao)
    for _ in range(150):
        jogo.atualizar(1 / 60)
    assert chefe.posicao.distance_to(inicio) > 150


def test_integral_dispara_aneis_em_sequencia(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_calculo")
    chefe.materia.integral(chefe, jogo)
    assert isinstance(chefe.acao_atual, Rajada)
    contagens = []
    for _ in range(80):
        chefe.mover(1 / 60, jogo)
        contagens.append(len(projeteis(jogo)))
    assert contagens[0] > 0
    assert contagens[-1] >= 3 * contagens[0]
    assert chefe.acao_atual is None


def test_chefe_ataca_sozinho_na_partida(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_calculo")
    jogo.jogador.vida_maxima = 10 ** 9
    jogo.jogador.vida = 10 ** 9
    for _ in range(60 * 8):
        jogo.atualizar(1 / 60)
    assert chefe._indice >= 2   # já usou pelo menos dois ataques da matéria


def test_projetil_da_materia_fere_o_heroi(jogo_limpo):
    jogo = jogo_limpo()
    jogo.adicionar(ProjetilDaMateria(jogo.jogador.posicao, (0, 0), 9, "dx", (255, 170, 60)))
    vida = jogo.jogador.vida
    jogo.atualizar(1 / 60)
    assert jogo.jogador.vida == vida - 9


def test_projetil_da_materia_desenha_o_simbolo():
    a = ProjetilDaMateria.imagem_do_simbolo("dx", (255, 170, 60), 12)
    b = ProjetilDaMateria.imagem_do_simbolo("dx", (255, 170, 60), 12)
    assert a is b and a.get_width() >= 24
