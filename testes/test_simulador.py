"""O robô do simulador (ferramentas/simular_partida.py): desvia, escolhe cartas, caça mini-chefes e monta a loja."""
import random
import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))
import simular_partida as simulador  # noqa: E402

from jogo.armas.colabs import CarameloNoFusca  # noqa: E402
from jogo.invocacao import LocalDeInvocacao  # noqa: E402
from jogo.jogador.classes import CLASSES, Otaku, Programador  # noqa: E402
from jogo.loja.melhorias import MELHORIAS  # noqa: E402
from jogo.progressao import Opcao  # noqa: E402
from jogo.projeteis.projeteis import ProjetilDaMateria  # noqa: E402


def carta(tipo, origem):
    return Opcao(origem.NOME if origem else tipo, "", "", "", tipo, lambda j, jogo: None, origem=origem)


def test_cartas_seguem_a_prioridade_colab_arma_inicial_armas_itens():
    from jogo.armas.chatgpt import MascoteChatGPT
    from jogo.itens.itens import ITENS
    from jogo.armas.cobra_python import CobraPython
    heroi = Programador((0, 0))
    item, outra_arma = carta("nova", ITENS[0]), carta("nova", MascoteChatGPT)
    inicial, colab = carta("melhoria", CobraPython), carta("colab", CarameloNoFusca)
    assert simulador.escolher_carta([item, outra_arma, inicial], heroi) is inicial
    assert simulador.escolher_carta([item, outra_arma], heroi) is outra_arma
    assert simulador.escolher_carta([item, colab, inicial], heroi) is colab
    vida = carta("maximo", None)
    assert simulador.escolher_carta([vida], heroi) is vida


def test_loja_nada_metade_e_cheia():
    assert simulador.montar_loja("nada") == ((), frozenset())
    melhorias, desbloqueios = simulador.montar_loja("cheia")
    assert {type(m) for m in melhorias} == set(MELHORIAS) and all(m.nivel == m.NIVEL_MAXIMO for m in melhorias)
    assert desbloqueios == simulador.tudo_desbloqueavel()
    assert simulador.custo_da_loja("metade") <= simulador.ORCAMENTO_METADE < simulador.custo_da_loja("cheia")
    assert simulador.custo_da_loja("metade") > simulador.ORCAMENTO_METADE * 0.9


def jogo_de_teste(classe=Otaku):
    from jogo.jogo import Jogo
    jogo = Jogo(classe, semente=5)
    for e in jogo.inimigos + jogo.grupos["invocacao"] + jogo.grupos["quebravel"]:
        e.remover()
    jogo._limpar()
    return jogo


def test_rola_quando_um_projetil_vem_na_direcao_dele():
    jogo = jogo_de_teste()
    heroi = jogo.jogador
    tiro = ProjetilDaMateria(heroi.posicao + (70, 0), (-400, 0), 5, "dx", (255, 255, 255))
    jogo.adicionar(tiro)
    jogo._incorporar_novas()
    robo = simulador.Robo(jogo)
    robo.agir(1 / 30)
    assert heroi.rolamento.rolando
    assert abs(heroi.rolamento.direcao.x) < 0.5          # rola de lado, para fora da linha do tiro


def test_sem_chefe_vai_ao_circulo_mais_perto_e_invoca():
    jogo = jogo_de_teste()
    jogo.jogador.imortal = True
    longe = LocalDeInvocacao(jogo.jogador.posicao + (1500, 0), "vigilante")
    perto = LocalDeInvocacao(jogo.mapa.empurrar(jogo.jogador.posicao + (0, 350), 100), "tia_da_cantina")
    for local in (longe, perto):
        jogo.adicionar(local)
    jogo._incorporar_novas()
    robo = simulador.Robo(jogo)
    assert not robo.pronto_para_cacar                     # nível 1: ainda não vai
    jogo.jogador.nivel = simulador.Robo.NIVEL_PARA_CACAR
    assert robo.pronto_para_cacar
    for _ in range(30 * 12):
        robo.agir(1 / 30)
        jogo.atualizar(1 / 30)
        if not perto.ativo:
            break
    assert not perto.ativo and longe.ativo                 # invocou o de perto, não o de longe
    assert any(getattr(e, "CHAVE", "") == "tia_da_cantina" for e in jogo.inimigos)


def test_sem_caca_nao_vai_aos_circulos():
    jogo = jogo_de_teste()
    jogo.jogador.imortal = True
    perto = LocalDeInvocacao(jogo.mapa.empurrar(jogo.jogador.posicao + (0, 350), 100), "tia_da_cantina")
    jogo.adicionar(perto)
    jogo._incorporar_novas()
    robo = simulador.Robo(jogo, cacar=False)
    for _ in range(30 * 8):
        robo.agir(1 / 30)
        jogo.atualizar(1 / 30)
    assert perto.ativo


def test_uma_partida_curta_devolve_a_linha_com_o_que_a_tabela_precisa():
    resultado = simulador.jogar(CLASSES[0], semente=2, loja="nada", cacar=True, minutos=1.0)
    for campo in ("classe", "semente", "niveis_nos_chefes", "chefes_caidos", "mini_chefes", "resultado",
                  "moedas", "tempo", "pior_quadro_ms", "pico_inimigos"):
        assert hasattr(resultado, campo)
    assert resultado.tempo >= 59 and resultado.eliminacoes >= 5     # o Otaku começa sem o crítico (vem nas cartas)
    linha = simulador.linha_da_partida(resultado)
    assert resultado.classe in linha and "nível" in linha
    tabela = simulador.tabela_por_classe([resultado, resultado])
    assert resultado.classe in tabela


def test_ferido_vai_quebrar_o_objeto_mais_perto_atras_de_cura():
    from jogo.inimigos.quebraveis import QUEBRAVEIS
    jogo = jogo_de_teste()
    heroi = jogo.jogador
    heroi.imortal = True
    objeto = QUEBRAVEIS[0](jogo.mapa.empurrar(heroi.posicao + (300, 0), 40))
    jogo.adicionar(objeto)
    jogo._incorporar_novas()
    robo = simulador.Robo(jogo)
    robo.agir(1 / 30)
    assert jogo.entrada.mira is None or jogo.entrada.mira != objeto.posicao      # com vida cheia, ignora
    heroi.vida = heroi.vida_maxima * 0.3
    robo.agir(1 / 30)
    assert jogo.entrada.mira == objeto.posicao and jogo.entrada.direcao.dot(objeto.posicao - heroi.posicao) > 0


def test_distancia_de_combate_vem_da_arma_principal():
    from jogo.jogador.classes import Otaku, MestreDeRPG
    otaku, mestre = simulador.Robo(jogo_de_teste(Otaku)), simulador.Robo(jogo_de_teste(MestreDeRPG))
    assert otaku.distancia_de_combate < 80                # o Caramelo morde em volta do aluno
    assert mestre.distancia_de_combate == simulador.Robo.DISTANCIA_DE_TIRO      # o Dado é jogado de longe


def test_projetil_com_rapidez_em_numero_nao_quebra_o_robo():
    jogo = jogo_de_teste()
    tiro = ProjetilDaMateria(jogo.jogador.posicao + (70, 0), (-400, 0), 5, "dx", (255, 255, 255))
    tiro.velocidade = 300                       # como os bumerangues e golpes dos mini-chefes
    jogo.adicionar(tiro)
    jogo._incorporar_novas()
    simulador.Robo(jogo).agir(1 / 30)


def test_tabela_separa_fim_do_semestre_de_honras():
    fim = simulador.Resultado("Otaku", 1, "nada", True, chefes_caidos=[300, 600, 900], resultado="FIM", tempo=1000)
    honras = simulador.Resultado("Otaku", 2, "nada", True, chefes_caidos=[300, 600, 900], resultado="HONRAS",
                                 tempo=1210)
    reprovado = simulador.Resultado("Otaku", 3, "nada", True, chefes_caidos=[300], resultado="REPROVADO", tempo=400)
    assert fim.fim_do_semestre and not fim.honras
    assert honras.fim_do_semestre and honras.honras
    assert not reprovado.fim_do_semestre
    tabela = simulador.tabela_por_classe([fim, honras, reprovado])
    assert "fim sem." in tabela.splitlines()[0]
    total = tabela.splitlines()[-1].split()
    assert total[0] == "TOTAL" and total[4:6] == ["67%", "33%"]     # fim do semestre 2 de 3, honras 1 de 3
