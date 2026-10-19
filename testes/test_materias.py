import pytest

from jogo.inimigos.acoes_do_chefe import Investida, Rajada
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.projeteis.projeteis import ProjetilDaMateria


def novos(jogo):
    jogo._incorporar_novas()
    return jogo.entidades


def simbolos(jogo):
    return [e.simbolo for e in novos(jogo) if isinstance(e, ProjetilDaMateria) and e.ativo]


def colocar_chefe(jogo, nome):
    chefe = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + (300, 0))
    jogo.iniciar_chefe(chefe)
    jogo._incorporar_novas()
    return chefe


def derrotar_fase(jogo, chefe):
    jogo.causar_dano(chefe, chefe.vida)
    chefe.mover(1 / 60, jogo)


def test_professor_tem_arquitetura_e_depois_estrutura_de_dados(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_arquitetura_ed")
    assert chefe.nome == "Arquitetura de Computadores"
    assert chefe.rotulo_da_barra.endswith("(FASE 1/2)")
    assert chefe.total_de_fases == 2 and chefe.fase_da_luta == 1
    derrotar_fase(jogo, chefe)
    assert chefe.ativo and not jogo.terminou
    assert chefe.nome == "Estrutura de Dados em C"
    assert chefe.fase_da_luta == 2
    assert chefe.vida == chefe.vida_maxima
    assert any("Estrutura de Dados em C possuiu" in texto for texto, _ in jogo.anuncios)


def test_professora_tem_transformacao_digital_e_depois_poo(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_td_poo")
    assert chefe.nome == "Transformação Digital"
    derrotar_fase(jogo, chefe)
    assert chefe.nome == "Programação Orientada a Objetos"
    assert "Professora" in chefe.NOME_PROFESSOR


def test_segunda_fase_e_mais_dificil_que_a_primeira():
    for nome in ("chefe_arquitetura_ed", "chefe_td_poo"):
        primeira, segunda = FabricaDeInimigos.criar(nome, (0, 0)).materias
        assert segunda.VIDA > primeira.VIDA
        assert segunda.INTERVALO_ATAQUE < primeira.INTERVALO_ATAQUE


def test_fica_invulneravel_durante_a_troca_de_materia(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_td_poo")
    derrotar_fase(jogo, chefe)
    vida = chefe.vida
    assert not jogo.causar_dano(chefe, 10 ** 7)
    assert chefe.vida == vida
    for _ in range(120):
        chefe.mover(1 / 60, jogo)
    assert not chefe.invulneravel


def test_so_a_ultima_materia_vence_a_luta(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_arquitetura_ed")
    derrotar_fase(jogo, chefe)
    chefe.troca = 0
    assert jogo.causar_dano(chefe, 10 ** 7)
    assert jogo.terminou and jogo.venceu


@pytest.mark.parametrize("nome", ["chefe_calculo", "chefe_arquitetura_ed", "chefe_td_poo"])
def test_todos_os_ataques_de_todas_as_materias_funcionam(jogo_limpo, nome):
    jogo = jogo_limpo()
    jogo.jogador.vida_maxima = 10 ** 9
    jogo.jogador.vida = 10 ** 9
    chefe = colocar_chefe(jogo, nome)
    for indice in range(chefe.total_de_fases):
        for ataque in chefe.ataques():
            ataque(jogo)
            for _ in range(240):
                jogo.atualizar(1 / 60)
                if chefe.acao_atual is None:
                    break
            assert chefe.acao_atual is None
        if chefe.tem_proxima_materia:
            derrotar_fase(jogo, chefe)
            chefe.troca = 0


def test_arquitetura_barramento_e_clock(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_arquitetura_ed")
    materia = chefe.materia
    materia.barramento(chefe, jogo)
    assert len(simbolos(jogo)) == 9
    materia.clock(chefe, jogo)
    assert isinstance(chefe.acao_atual, Rajada)


def test_estrutura_de_dados_ponteiro_selvagem_investe_varias_vezes(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_arquitetura_ed")
    derrotar_fase(jogo, chefe)
    chefe.materia.ponteiro_selvagem(chefe, jogo)
    assert isinstance(chefe.acao_atual, Investida) and chefe.acao_atual.vezes >= 3
    chefe.materia.segmentation_fault(chefe, jogo)
    assert "NULL" in simbolos(jogo)


def test_poo_encapsulamento_protege_e_polimorfismo_alterna(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_td_poo")
    derrotar_fase(jogo, chefe)
    chefe.troca = 0
    poo = chefe.materia
    poo.encapsulamento(chefe, jogo)
    assert chefe.escudo > 0
    vida = chefe.vida
    jogo.causar_dano(chefe, 100)
    assert chefe.vida == vida
    poo.polimorfismo(chefe, jogo)
    primeiro = set(simbolos(jogo))
    poo.polimorfismo(chefe, jogo)
    assert set(simbolos(jogo)) != primeiro


def test_golpe_no_chefe_invulneravel_nao_mostra_dano(jogo_limpo):
    from jogo.efeitos import TextoFlutuante
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_td_poo")
    chefe.proteger(2)
    jogo._incorporar_novas()
    antes = sum(isinstance(e, TextoFlutuante) for e in jogo.entidades)
    assert not jogo.causar_dano(chefe, 50)
    assert sum(isinstance(e, TextoFlutuante) for e in novos(jogo)) == antes


def test_chefe_nao_machuca_por_contato_durante_a_troca(jogo_limpo):
    jogo = jogo_limpo()
    chefe = colocar_chefe(jogo, "chefe_td_poo")
    derrotar_fase(jogo, chefe)
    chefe.posicao = jogo.jogador.posicao.copy()
    vida = jogo.jogador.vida
    chefe.tocar_jogador(jogo)
    assert jogo.jogador.vida == vida
