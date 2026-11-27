"""Ritmo da partida: chefes no relógio (4, 8 e 12 min), modo sem fim depois do último e mais inimigos com o tempo."""
import pytest

from jogo.boletim import Boletim
from jogo.config import DURACAO_PROVA, MAX_INIMIGOS
from jogo.fase import ModoSemFim, ProvaDeArquiteturaEED, ProvaDeCalculo, ProvaDeTDEPOO, semestre
from jogo.inimigos.chefe_possuido import ChefePossuido
from jogo.jogador.classes import Programador
from jogo.jogo import Jogo
from jogo.opcoes import OpcoesDePartida


def partida(**opcoes):
    jogo = Jogo(Programador, semente=11, **opcoes)
    jogo.jogador.imortal = True
    return jogo


def fim_da_prova(jogo):
    """Leva o relógio da prova atual até a hora do chefe dela."""
    jogo.fase.tempo = jogo.fase.DURACAO - 0.01
    jogo.atualizar(0.02)
    jogo._incorporar_novas()


def derrubar(jogo, chefe):
    """Zera todas as matérias do chefe (cada uma é uma barra de vida)."""
    for _ in range(chefe.total_de_fases):
        chefe.troca = 0
        chefe.escudo = 0
        jogo.causar_dano(chefe, 10 ** 8)
    assert not chefe.ativo


# ---------------------------------------------------------------- chefes no relógio

def test_as_provas_duram_quatro_minutos_e_os_chefes_chegam_aos_4_8_e_12():
    assert DURACAO_PROVA == 4 * 60
    provas = semestre()
    chegadas = [prova.INICIO_DIFICULDADE + prova.DURACAO for prova in provas]
    assert chegadas == [4 * 60, 8 * 60, 12 * 60]


def test_segundo_chefe_chega_com_o_primeiro_ainda_vivo():
    jogo = partida()
    fim_da_prova(jogo)
    primeiro = jogo.chefe
    assert isinstance(primeiro, ChefePossuido) and primeiro.nome == "Cálculo I"
    assert isinstance(jogo.fase, ProvaDeArquiteturaEED) and jogo.fase.tempo < 1     # a 2ª prova começou no relógio
    fim_da_prova(jogo)
    assert primeiro.ativo
    assert [c.nome for c in jogo.chefes] == ["Cálculo I", "Arquitetura de Computadores"]
    assert jogo.chefe is primeiro                       # a barra principal é a do mais antigo
    assert isinstance(jogo.fase, ProvaDeTDEPOO)


def test_a_passagem_de_prova_nao_limpa_o_campo_nem_cura():
    from jogo.inimigos.bug import Bug
    jogo = partida()
    lacaio = Bug(jogo.jogador.posicao + (300, 0))
    jogo.adicionar(lacaio)
    fim_da_prova(jogo)
    assert lacaio.ativo and jogo.baus_pendentes == 0


def test_aviso_de_perigo_e_apresentacao_continuam_valendo_para_cada_chefe():
    jogo = partida()
    for _ in range(2):
        jogo.fase.tempo = jogo.fase.DURACAO - jogo.fase.AVISO_DO_CHEFE - 0.01
        jogo.atualizar(0.02)
        assert jogo.perigo > 0
        jogo.chefe_a_apresentar = None
        fim_da_prova(jogo)
        assert jogo.perigo == 0 and jogo.chefe_a_apresentar is jogo.chefes[-1]


def test_derrotar_um_chefe_aprova_a_prova_dele_sem_trocar_de_fase():
    jogo = partida()
    fim_da_prova(jogo)
    fim_da_prova(jogo)
    calculo, arquitetura = jogo.chefes
    jogo.jogador.vida = jogo.jogador.vida_maxima / 2
    derrubar(jogo, arquitetura)                         # o segundo cai antes do primeiro
    assert set(jogo.notas) == {1} and jogo.provas_vencidas == 1
    assert jogo.chefes == [calculo] and isinstance(jogo.fase, ProvaDeTDEPOO)
    assert jogo.baus_pendentes == 1 and jogo.placar.moedas > 0
    assert jogo.jogador.vida > jogo.jogador.vida_maxima / 2
    assert not jogo.terminou and not jogo.venceu
    linhas = Boletim(jogo).linhas
    assert [linha.situacao for linha in linhas] == ["REPROVADO", "APROVADO", "REPROVADO"]


# ---------------------------------------------------------------- modo sem fim

def vencer_o_semestre(jogo):
    for _ in range(len(jogo.fases)):
        fim_da_prova(jogo)
    for chefe in list(jogo.chefes):
        derrubar(jogo, chefe)


def test_derrotado_o_ultimo_chefe_a_partida_continua_sem_fim():
    jogo = partida()
    vencer_o_semestre(jogo)
    assert jogo.venceu and not jogo.terminou
    assert isinstance(jogo.fase, ModoSemFim) and jogo.chefe is None
    assert len(jogo.notas) == 3
    antes = len(jogo.inimigos)
    for _ in range(120):
        jogo.atualizar(1 / 30)
    assert not jogo.terminou and len(jogo.inimigos) > antes


def test_dificuldade_do_modo_sem_fim_multiplica_a_cada_15_segundos():
    fase = ModoSemFim(inicio=720)
    base = fase.escala_dificuldade
    assert base == pytest.approx(ProvaDeTDEPOO().escala_dificuldade + ProvaDeTDEPOO.DURACAO / ProvaDeTDEPOO.PASSO_DIFICULDADE)
    fase.tempo = 14.9
    assert fase.escala_dificuldade == pytest.approx(base) and fase.onda == 1
    fase.tempo = 15
    assert fase.escala_dificuldade == pytest.approx(base * ModoSemFim.FATOR_POR_ONDA) and fase.onda == 2
    fase.tempo = 60
    assert fase.escala_dificuldade == pytest.approx(base * ModoSemFim.FATOR_POR_ONDA ** 4)


def test_projeto_de_extensao_nao_anuncia_as_ondas():
    jogo = partida()
    vencer_o_semestre(jogo)
    anunciados = []
    jogo.anunciar = lambda texto, duracao=2.5: anunciados.append(texto)     # grava tudo (os anúncios somem em 2 s)
    for _ in range(round(30 * 50)):               # 50 s: três viradas de dificuldade e a 1ª formação (45 s)
        jogo.atualizar(1 / 30)
    assert jogo.fase.escala_dificuldade > ModoSemFim(inicio=jogo.fase.INICIO_DIFICULDADE).escala_dificuldade
    assert anunciados and not any("onda" in texto.lower() for texto in anunciados)
    assert ModoSemFim.INTERVALO_DE_ONDA == 15 and ModoSemFim.FATOR_POR_ONDA > 1


def test_morrer_no_modo_sem_fim_termina_como_aprovado():
    jogo = partida()
    vencer_o_semestre(jogo)
    jogo.placar.tempo = 800
    jogo.jogador.imortal = False
    jogo.jogador.vida = 0
    jogo.atualizar(1 / 30)
    assert jogo.terminou and jogo.venceu
    registro = jogo.resultado("Ana")
    assert registro.venceu and registro.pontos >= jogo.placar.BONUS_VITORIA + 1600
    boletim = Boletim(jogo)
    assert all(linha.aprovado for linha in boletim.linhas)


def test_morrer_antes_de_vencer_reprova_na_prova_do_chefe_vivo():
    jogo = partida()
    fim_da_prova(jogo)
    jogo.chefe.vida = jogo.chefe.vida_maxima / 2
    jogo.jogador.imortal = False
    jogo.jogador.vida = 0
    jogo.atualizar(1 / 30)
    assert jogo.terminou and not jogo.venceu
    linhas = Boletim(jogo).linhas
    assert linhas[0].situacao == "REPROVADO" and 4 < linhas[0].nota <= Boletim.NOTA_MAXIMA_REPROVADO
    assert linhas[1].situacao == "REPROVADO" and linhas[1].nota < 4          # a 2ª prova mal tinha começado
    assert linhas[2].situacao == "NÃO CURSOU"


def test_treino_acaba_quando_o_chefe_cai():
    opcoes = OpcoesDePartida.treino_contra(ProvaDeCalculo, direto_no_chefe=True, imortal=True)
    jogo = Jogo.a_partir_de(Programador, opcoes, semente=3)
    for _ in range(4 * 60):
        jogo.atualizar(1 / 60)
    derrubar(jogo, jogo.chefe)
    assert jogo.terminou and jogo.venceu and not isinstance(jogo.fase, ModoSemFim)


def test_partida_normal_e_sem_fim_e_o_treino_nao():
    assert Jogo.a_partir_de(Programador, OpcoesDePartida(), semente=3).sem_fim
    assert not Jogo.a_partir_de(Programador, OpcoesDePartida.treino_contra(ProvaDeCalculo), semente=3).sem_fim


# ---------------------------------------------------------------- inimigos com o tempo

def test_quanto_mais_tarde_mais_inimigos_e_nascimento_mais_rapido():
    provas = semestre()
    alvos, intervalos = [], []
    for prova in provas:
        for tempo in (0, 120, 239):
            prova.tempo = tempo
            alvos.append(prova.alvo_de_inimigos())
            intervalos.append(prova.intervalo_de_nascimento())
    assert alvos == sorted(alvos) and alvos[-1] > 3 * alvos[0]
    assert intervalos == sorted(intervalos, reverse=True) and intervalos[-1] < intervalos[0] / 2
    assert max(alvos) <= MAX_INIMIGOS


def test_modo_sem_fim_respeita_o_teto_de_inimigos():
    fase = ModoSemFim(inicio=720)
    fase.tempo = 3600
    assert fase.alvo_de_inimigos() == MAX_INIMIGOS
    assert fase.intervalo_de_nascimento() >= fase.INTERVALO_MINIMO


def test_com_chefe_em_campo_nascem_menos_inimigos():
    jogo = partida()
    fim_da_prova(jogo)
    jogo.fase.tempo = 120
    cheio = jogo.fase.alvo_de_inimigos()
    assert jogo.fase.alvo_com(jogo) == int(cheio * jogo.fase.ALIVIO_COM_CHEFE)
    derrubar(jogo, jogo.chefe)
    assert jogo.fase.alvo_com(jogo) == cheio


def test_greve_e_formacoes_acabam_antes_de_o_chefe_chegar():
    for prova in semestre():
        assert prova.GREVE + prova.DURACAO_GREVE < prova.DURACAO - prova.AVISO_DO_CHEFE
        assert 60 * len(prova.FORMACOES) <= prova.DURACAO - 60


# ---------------------------------------------------------------- telas

def test_hud_nivel_e_fim_desenham_com_dois_chefes_e_no_modo_sem_fim(tmp_path, monkeypatch):
    import pygame
    from jogo.cenas.hud import Hud
    tela = pygame.Surface((1280, 720))
    jogo = partida()
    fim_da_prova(jogo)
    fim_da_prova(jogo)
    hud = Hud()
    hud.atualizar(1 / 60, jogo)
    hud.desenhar(tela, jogo)                     # duas barras de chefe
    for chefe in list(jogo.chefes):
        derrubar(jogo, chefe)
    fim_da_prova(jogo)
    derrubar(jogo, jogo.chefe)
    assert isinstance(jogo.fase, ModoSemFim) and jogo.fase.titulo == "Projeto de extensão"     # sem número de onda
    hud.atualizar(1 / 60, jogo)
    hud.desenhar(tela, jogo)


def test_chamada_do_chefe_nao_passa_do_teto_de_inimigos(jogo_limpo):
    from jogo.inimigos.bug import Bug
    from jogo.inimigos.fabrica import FabricaDeInimigos
    jogo = jogo_limpo()
    chefe = FabricaDeInimigos.criar("chefe_calculo", jogo.jogador.posicao + (300, 0))
    jogo.adicionar(chefe)
    jogo._incorporar_novas()
    chefe.materia.chamada(chefe, jogo, 4)
    jogo._incorporar_novas()
    assert len(jogo.inimigos) == 5 and not jogo.campo_cheio
    for i in range(MAX_INIMIGOS):
        jogo.adicionar(Bug(jogo.jogador.posicao + (400 + i, 0)))
    jogo._incorporar_novas()
    cheio = len(jogo.inimigos)
    chefe.materia.chamada(chefe, jogo, 4)
    jogo._incorporar_novas()
    assert jogo.campo_cheio and len(jogo.inimigos) == cheio
