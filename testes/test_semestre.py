"""O semestre de 20 minutos: uma fase só, chefes às 5, 10 e 15 min, relógio que não para e a reta final
que mata todo mundo por volta dos 20:00. O resultado vem dos chefes derrotados."""
import time

import pygame
import pytest

from jogo.boletim import Boletim
from jogo.coletaveis.coletaveis import Nota
from jogo.config import DURACAO_SEMESTRE, MAX_INIMIGOS
from jogo.efeitos import AvisoDeFormacao
from jogo.fase import CALENDARIO, Fase, Semestre
from jogo.inimigos.bug import Bug
from jogo.inimigos.chefe_possuido import ChefePossuido
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.quebraveis import CaixaDePapelao
from jogo.jogador.classes import Programador
from jogo.jogo import Jogo
from jogo.opcoes import OpcoesDePartida


def partida(imortal=True):
    jogo = Jogo(Programador, semente=11)
    jogo.jogador.imortal = imortal
    return jogo


def pular_para(jogo, segundos):
    """Leva o relógio até `segundos` (o que tinha hora antes disso acontece neste quadro)."""
    jogo.fase.tempo = segundos - 0.01
    jogo.placar.tempo = segundos - 0.01
    jogo.atualizar(0.02)
    jogo._incorporar_novas()


def derrubar(jogo, chefe):
    """Zera todas as matérias do chefe (cada uma é uma barra de vida)."""
    for _ in range(chefe.total_de_fases):
        chefe.troca = 0
        chefe.escudo = 0
        jogo.causar_dano(chefe, 10 ** 8)
    assert not chefe.ativo


def vencer_os_tres_chefes(jogo):
    for prova in CALENDARIO:
        pular_para(jogo, prova.hora)
    for chefe in list(jogo.chefes):
        derrubar(jogo, chefe)


# ---------------------------------------------------------------- calendário

def test_uma_fase_so_com_tres_chefes_as_5_10_e_15_minutos():
    assert DURACAO_SEMESTRE == 20 * 60
    jogo = partida()
    assert isinstance(jogo.fase, Semestre)
    assert [p.hora for p in jogo.fase.provas] == [5 * 60, 10 * 60, 15 * 60]
    assert [p.chefe for p in jogo.fase.provas] == ["chefe_calculo", "chefe_arquitetura_ed", "chefe_td_poo"]


def test_chefes_chegam_na_hora_certa_com_aviso_de_perigo():
    jogo = partida()
    pular_para(jogo, 5 * 60 - 1)
    assert jogo.chefe is None and jogo.perigo > 0
    pular_para(jogo, 5 * 60)
    assert isinstance(jogo.chefe, ChefePossuido) and jogo.chefe.nome == "Cálculo I"
    assert jogo.chefe_a_apresentar is jogo.chefe
    pular_para(jogo, 10 * 60)
    assert [c.nome for c in jogo.chefes] == ["Cálculo I", "Arquitetura de Computadores"]


def test_o_relogio_nao_para_durante_a_luta():
    jogo = partida()
    pular_para(jogo, 5 * 60)
    antes = jogo.fase.tempo
    for _ in range(90):
        jogo.atualizar(1 / 30)
    assert jogo.chefe is not None and jogo.fase.tempo == pytest.approx(antes + 3, abs=0.01)
    pular_para(jogo, 10 * 60)               # o 1º ainda vivo: o 2º vem mesmo assim
    assert len(jogo.chefes) == 2


def test_na_chegada_do_chefe_saem_so_os_lacaios_comuns():
    jogo = partida()
    lacaio = Bug(jogo.jogador.posicao + (300, 0))
    caixa = CaixaDePapelao(jogo.jogador.posicao + (330, 0))
    mini = FabricaDeInimigos.criar("tia_da_cantina", jogo.jogador.posicao + (360, 0))
    for e in (lacaio, caixa, mini):
        jogo.adicionar(e)
    jogo._incorporar_novas()
    pular_para(jogo, 5 * 60)
    primeiro = jogo.chefe
    assert not lacaio.ativo and caixa.ativo and mini.ativo
    pular_para(jogo, 10 * 60)
    assert primeiro.ativo and mini.ativo


def test_gigantes_e_possuidos_ficam_na_chegada_do_chefe():
    jogo = partida()
    gigante = FabricaDeInimigos.criar_gigante("calculadora", jogo.jogador.posicao + (300, 0))
    passageiro = Bug(jogo.jogador.posicao + (330, 0))
    passageiro.possuir(10)
    comum = Bug(jogo.jogador.posicao + (360, 0))
    for e in (gigante, passageiro, comum):
        jogo.adicionar(e)
    jogo._incorporar_novas()
    assert gigante.solta_bau and passageiro.possuido > 0
    pular_para(jogo, 5 * 60)
    assert gigante.ativo and passageiro.ativo and not comum.ativo


def test_derrotar_um_chefe_aprova_a_prova_dele():
    jogo = partida()
    pular_para(jogo, 5 * 60)
    pular_para(jogo, 10 * 60)
    calculo, arquitetura = jogo.chefes
    jogo.jogador.vida = jogo.jogador.vida_maxima / 2
    derrubar(jogo, arquitetura)                     # o segundo cai antes do primeiro
    assert jogo.chefes_derrotados == 1 and jogo.chefes == [calculo]
    assert jogo.baus_pendentes == 1 and jogo.placar.moedas > 0
    assert jogo.jogador.vida > jogo.jogador.vida_maxima / 2
    assert any("Aprovado em Arquitetura" in texto for texto, _ in jogo.anuncios)
    assert not jogo.terminou and not jogo.venceu
    assert [linha.situacao for linha in Boletim(jogo).linhas] == ["REPROVADO", "APROVADO", "REPROVADO"]


def test_lacaios_entram_perto_do_chefe_da_materia():
    jogo = partida()
    pular_para(jogo, 80)
    assert jogo.fase.ativos == ["bug", "calculadora", "pi"]
    pular_para(jogo, 430)
    assert {"pente_ram", "ponteiro", "pilha"} <= set(jogo.fase.ativos)


def test_no_maximo_tres_gigantes_com_hora_marcada():
    assert len(Semestre.GIGANTES) <= 3
    jogo = partida()
    pular_para(jogo, Semestre.GIGANTES[0][0])
    gigantes = [e for e in jogo.inimigos if e.gigante]
    assert len(gigantes) == 1 and gigantes[0].CHAVE == Semestre.GIGANTES[0][1]


def test_formacao_com_aviso_antes():
    jogo = partida()
    tempo, _ = Semestre.FORMACOES[0]
    antes = len(jogo.inimigos)
    pular_para(jogo, tempo - Semestre.AVISO)
    assert any(isinstance(e, AvisoDeFormacao) for e in jogo.entidades)
    for _ in range(round(60 * (Semestre.AVISO + 0.1))):
        jogo.atualizar(1 / 60)
    assert len(jogo.inimigos) >= antes + 20
    intervalos = [b[0] - a[0] for a, b in zip(Semestre.FORMACOES, Semestre.FORMACOES[1:])]
    assert all(80 <= i <= 120 for i in intervalos)


def test_avisos_da_reta_final_e_dos_30_segundos():
    jogo = partida()
    pular_para(jogo, 15 * 60 + 0.5)
    assert any("Reta final" in texto for texto, _ in jogo.anuncios)
    pular_para(jogo, 19 * 60 + 30)
    assert any("Faltam 30 s" in texto for texto, _ in jogo.anuncios)


def test_hud_conta_para_tras_ate_os_20_minutos():
    fase = Semestre()
    assert fase.restante == 20 * 60
    fase.tempo = 19 * 60 + 45
    assert fase.restante == pytest.approx(15)
    fase.tempo = 21 * 60
    assert fase.restante == 0 and fase.titulo == "Reta final"


# ---------------------------------------------------------------- dificuldade

def test_quanto_mais_tarde_mais_inimigos_e_nascimento_mais_rapido():
    fase = Semestre()
    alvos, intervalos = [], []
    for tempo in (0, 120, 300, 600, 840):
        fase.tempo = tempo
        alvos.append(fase.alvo_de_inimigos())
        intervalos.append(fase.intervalo_de_nascimento())
    assert alvos == sorted(alvos) and alvos[-1] > 3 * alvos[0]
    assert intervalos == sorted(intervalos, reverse=True) and intervalos[-1] < intervalos[0] / 2
    assert max(alvos) <= MAX_INIMIGOS


def test_com_chefe_em_campo_nascem_menos_inimigos():
    jogo = partida()
    pular_para(jogo, 5 * 60)
    jogo.fase.tempo = 400
    cheio = jogo.fase.alvo_de_inimigos()
    assert jogo.fase.alvo_com(jogo) == int(cheio * jogo.fase.ALIVIO_COM_CHEFE)
    derrubar(jogo, jogo.chefe)
    assert jogo.fase.alvo_com(jogo) == cheio


def test_a_reta_final_comeca_suave_e_aperta_depois_das_18():
    fase = Semestre()
    fase.tempo = 15 * 60
    inicio = fase.escala_dificuldade
    fase.tempo = 16 * 60
    um_minuto = fase.escala_dificuldade
    fase.tempo = 18 * 60
    aperto = fase.escala_dificuldade
    fase.tempo = 19 * 60
    depois = fase.escala_dificuldade
    assert inicio < um_minuto < 2.1 * inicio                  # quem ainda luta com o 3º chefe às 16:00 aguenta
    assert depois / aperto > um_minuto / inicio               # das 18:00 em diante cresce mais depressa


def test_depois_dos_20_minutos_furia_spawn_no_teto_e_dano_acima_de_qualquer_vida():
    fase = Semestre()
    fase.tempo = 19 * 60
    assert fase.furia == 1
    fase.tempo = 20 * 60 + 20
    assert fase.alvo_de_inimigos() == MAX_INIMIGOS
    bug = fase.criar("bug", (0, 0))
    comum = FabricaDeInimigos.criar("bug", (0, 0))
    assert bug.velocidade >= comum.velocidade * 2
    assert bug.dano_de_contato > 10_000                       # muito mais que a vida máxima de qualquer aluno


def morre_antes_de(jogo, limite):
    """Põe o aluno parado aos 19:30 e avança o relógio; devolve a hora em que ele caiu (ou None)."""
    jogo.fase.adiantar_para(19 * 60 + 30)
    jogo.placar.tempo = jogo.fase.tempo
    jogo.invocacoes_abertas = True
    while jogo.fase.tempo < limite and not jogo.terminou:
        jogo.entrada.direcao = pygame.Vector2()
        jogo.atualizar(1 / 20)
        jogo.niveis_pendentes = 0
        jogo.baus_pendentes = 0
    return jogo.fase.tempo if jogo.terminou else None


def test_reta_final_mata_o_aluno_mais_forte_antes_de_20_30():
    jogo = partida(imortal=False)
    jogo.jogador.vida_maxima = 5000                           # bem acima da loja cheia com itens de vida
    jogo.jogador.vida = 5000
    jogo.jogador.regeneracao = 200                            # e regeneração enorme
    caiu = morre_antes_de(jogo, 20 * 60 + 30)
    assert caiu is not None, "o aluno passou das 20:30"


def test_reta_final_mata_mesmo_com_desvio_alto():
    jogo = partida(imortal=False)
    jogo.jogador.vida_maxima = 3000
    jogo.jogador.vida = 3000
    jogo.jogador.sorte = 10                                   # desvio no máximo (60%)
    jogo.jogador.chance_desvio = 1.0
    assert min(Jogo.DESVIO_MAXIMO, jogo.jogador.chance(jogo.jogador.chance_desvio)) == Jogo.DESVIO_MAXIMO
    caiu = morre_antes_de(jogo, 20 * 60 + 30)
    assert caiu is not None, "o aluno passou das 20:30"


# ---------------------------------------------------------------- resultado

def test_morrer_depois_dos_tres_chefes_da_honras_e_bonus():
    jogo = partida()
    vencer_os_tres_chefes(jogo)
    assert jogo.venceu and not jogo.terminou and jogo.chefe is None
    jogo.contar_mini_chefe()
    jogo.contar_mini_chefe()
    jogo.jogador.imortal = False
    jogo.jogador.vida = 0
    jogo.atualizar(1 / 30)
    assert jogo.terminou and jogo.venceu
    esperado = round((Jogo.BONUS_HONRAS + 2 * Jogo.MOEDAS_POR_MINI_CHEFE) * jogo.jogador.mult_moedas)
    assert jogo.bonus_de_honras == esperado
    assert jogo.moedas_ganhas() >= jogo.placar.moedas + esperado
    registro = jogo.resultado("Ana")
    assert registro.venceu and registro.chefes == 3
    assert all(linha.aprovado for linha in Boletim(jogo).linhas)
    from jogo.cenas.fim import CenaFimDeJogo
    assert CenaFimDeJogo.motivo(jogo).startswith("Fim do semestre com honras!")


def test_morrer_com_chefe_de_pe_reprova_sem_bonus():
    jogo = partida()
    pular_para(jogo, 5 * 60)
    pular_para(jogo, 10 * 60)
    derrubar(jogo, jogo.chefes[1])
    jogo.chefe.vida = jogo.chefe.vida_maxima / 2
    jogo.jogador.imortal = False
    jogo.jogador.vida = 0
    jogo.atualizar(1 / 30)
    assert jogo.terminou and not jogo.venceu
    assert jogo.bonus_de_honras == 0
    linhas = Boletim(jogo).linhas
    assert linhas[0].situacao == "REPROVADO" and 4 < linhas[0].nota <= Boletim.NOTA_MAXIMA_REPROVADO
    assert linhas[1].aprovado
    assert linhas[2].situacao == "REPROVADO" and linhas[2].nota < 4      # a 3ª prova mal tinha começado
    from jogo.cenas.fim import CenaFimDeJogo
    assert CenaFimDeJogo.motivo(jogo) == "Reprovado em Cálculo I."


def test_morrer_depois_do_fim_com_chefe_de_pe_e_o_semestre_acabou():
    from jogo.cenas.fim import CenaFimDeJogo
    jogo = partida()
    jogo.fase.adiantar_para(20 * 60 + 5)
    assert not jogo.venceu
    assert CenaFimDeJogo.motivo(jogo) == "Reprovado: o semestre acabou."


def test_morrer_antes_do_primeiro_chefe_reprova_em_calculo():
    from jogo.cenas.fim import CenaFimDeJogo
    jogo = partida()
    pular_para(jogo, 150)
    linhas = Boletim(jogo).linhas
    assert linhas[0].situacao == "REPROVADO" and linhas[0].nota == pytest.approx(2.0)
    assert [linha.situacao for linha in linhas[1:]] == ["NÃO CURSOU", "NÃO CURSOU"]
    assert CenaFimDeJogo.motivo(jogo) == "Reprovado em Cálculo I."


def test_ranking_desempata_por_chefes_e_depois_por_tempo():
    from jogo.ranking import RegistroRanking
    menos_chefes = RegistroRanking("A", "Otaku", 1000, 600, chefes=1)
    mais_chefes = RegistroRanking("B", "Otaku", 1000, 900, chefes=2)
    mais_rapido = RegistroRanking("C", "Otaku", 1000, 800, chefes=2)
    assert sorted([menos_chefes, mais_chefes, mais_rapido], reverse=True) == [mais_rapido, mais_chefes, menos_chefes]
    assert RegistroRanking.de_dict(mais_chefes.para_dict()) == mais_chefes


# ---------------------------------------------------------------- treino

def test_treino_direto_no_chefe_comeca_3_s_antes_e_acaba_quando_ele_cai():
    prova = CALENDARIO[1]
    opcoes = OpcoesDePartida.treino_contra(prova, direto_no_chefe=True, imortal=True)
    jogo = Jogo.a_partir_de(Programador, opcoes, semente=3)
    assert jogo.fase.tempo == pytest.approx(prova.hora - Semestre.AVISO_DO_CHEFE)
    assert jogo.jogador.nivel == prova.nivel_treino
    for _ in range(4 * 60):
        jogo.atualizar(1 / 60)
    assert [c.nome for c in jogo.chefes] == ["Arquitetura de Computadores"]
    derrubar(jogo, jogo.chefe)
    assert jogo.terminou and jogo.venceu and jogo.moedas_ganhas() == 0


# ---------------------------------------------------------------- mira e desempenho

def test_a_mira_ignora_objetos_quebraveis(jogo_limpo):
    jogo = jogo_limpo()
    caixa = CaixaDePapelao(jogo.jogador.posicao + (60, 0))
    bug = Bug(jogo.jogador.posicao + (200, 0))
    jogo.adicionar(caixa)
    jogo.adicionar(bug)
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos + jogo.grupos["quebravel"])
    assert jogo.inimigo_mais_proximo(jogo.jogador.posicao, 700) is bug
    assert jogo.inimigo_com_mais_vida(jogo.jogador.posicao, 700) is bug
    assert caixa in jogo.inimigos_proximos(caixa.posicao, 10)       # mas um golpe que passa por ela acerta


def test_quadro_continua_rapido_com_muitas_entidades():
    jogo = partida()
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


def test_o_primeiro_quadro_nao_carrega_o_chao_do_mapa():
    """O chão do mapa é lido ao montar a partida, não no primeiro quadro (era o pior quadro do simulador)."""
    jogo = partida()
    inicio = time.perf_counter()
    jogo.atualizar(1 / 30)
    assert (time.perf_counter() - inicio) * 1000 < 33


def test_fase_e_chefe_possuido_sao_abstratos():
    with pytest.raises(TypeError):
        Fase()
    with pytest.raises(TypeError):
        ChefePossuido((0, 0))


def test_chamada_do_chefe_nao_passa_do_teto_de_inimigos(jogo_limpo):
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


def test_hud_e_pausa_desenham_com_dois_chefes_e_na_reta_final(jogo_limpo):
    from jogo.cenas.hud import Hud
    tela = pygame.Surface((1280, 720))
    jogo = partida()
    pular_para(jogo, 5 * 60)
    pular_para(jogo, 10 * 60)
    hud = Hud()
    hud.atualizar(1 / 60, jogo)
    hud.desenhar(tela, jogo)                     # duas barras de chefe
    pular_para(jogo, 19 * 60 + 40)
    hud.atualizar(1 / 60, jogo)
    hud.desenhar(tela, jogo)                     # relógio vermelho
