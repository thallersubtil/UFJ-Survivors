"""O robô do simulador (ferramentas/simular_partida.py): desvia, escolhe cartas, caça mini-chefes e monta a loja."""
import random
import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))
import simular_partida as simulador  # noqa: E402

from jogo.armas.colabs import Caramelo5G  # noqa: E402
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
    from jogo.armas.teclado import TecladoMecanico
    heroi = Programador((0, 0))
    item, outra_arma = carta("nova", ITENS[0]), carta("nova", MascoteChatGPT)
    inicial, colab = carta("melhoria", TecladoMecanico), carta("colab", Caramelo5G)
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
    jogo.fase.atualizar(0.0, jogo)               # solta a turma do começo agora, para o campo começar vazio
    jogo._incorporar_novas()
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
    from jogo.jogador.classes import Monitor, MestreDeRPG
    monitor, mestre = simulador.Robo(jogo_de_teste(Monitor)), simulador.Robo(jogo_de_teste(MestreDeRPG))
    assert monitor.distancia_de_combate < 80              # a Caneta de Correção estoca de perto
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


def test_itens_de_risco_ficam_por_ultimo_nas_cartas():
    from jogo.itens.itens import (ITENS, MensalidadeDaAtletica, NoiteSemDormir, ParcelarNoCartao,
                                  PreTreinoDuvidoso)
    heroi = Programador((0, 0))
    comum = next(classe for classe in ITENS if classe not in simulador.ITENS_DE_RISCO)
    for risco in (PreTreinoDuvidoso, NoiteSemDormir, ParcelarNoCartao, MensalidadeDaAtletica):
        assert risco in simulador.ITENS_DE_RISCO
        arriscado, seguro = carta("nova", risco), carta("nova", comum)
        assert simulador.escolher_carta([arriscado, seguro], heroi) is seguro
        assert simulador.escolher_carta([carta("melhoria", risco), seguro], heroi) is seguro
        assert simulador.escolher_carta([arriscado], heroi) is arriscado


def test_lutas_contra_mini_chefe_ficam_registradas_com_nivel_vida_e_desfecho():
    vencida = simulador.Luta("Vigilante", inicio=200, nivel=6, vida=0.9, fim=240, venceu=True)
    perdida = simulador.Luta("Reitor", inicio=500, nivel=9, vida=1.0, fim=510)
    assert vencida.duracao == 40 and perdida.duracao == 10 and not perdida.venceu
    com = simulador.Resultado("Otaku", 1, "nada", True, resultado="REPROVADO", tempo=510, lutas=[vencida, perdida])
    sem = simulador.Resultado("Otaku", 2, "nada", True, resultado="REPROVADO", tempo=100)
    assert "1º mini-chefe no nível 6" in simulador.linha_da_partida(com)
    perdeu = simulador.Resultado("Otaku", 3, "nada", True, resultado="REPROVADO", tempo=300, lutas=[perdida])
    cabecalho, _, *_, total = simulador.tabela_por_classe([com, sem, perdeu]).splitlines()
    for coluna in ("nível 1º mini", "vence 1º mini", "perde 1º mini", "sem luta"):
        assert coluna in cabecalho
    # nível médio da 1ª luta; e cada partida cai em um dos três: venceu a 1ª, perdeu a 1ª, morreu sem lutar
    assert total.split()[-4:] == ["7.5", "33%", "33%", "33%"]


def test_a_partida_registra_a_luta_quando_o_mini_chefe_aparece_e_quando_ele_cai():
    from jogo.inimigos.mini_chefes import Vigilante
    jogo = jogo_de_teste()
    heroi = jogo.jogador
    heroi.nivel, heroi.vida = 6, heroi.vida_maxima * 0.5
    r, lutas = simulador.Resultado("Otaku", 1, "nada", True), {}
    vigilante = Vigilante(heroi.posicao + (300, 0))
    jogo.adicionar(vigilante)
    jogo._incorporar_novas()
    simulador._acompanhar_lutas(jogo, lutas, r)
    simulador._acompanhar_lutas(jogo, lutas, r)          # o mesmo mini-chefe não abre duas lutas
    assert len(r.lutas) == 1 and r.lutas[0].nivel == 6 and r.lutas[0].vida == 0.5 and r.lutas[0].fim is None
    jogo.placar.tempo += 30
    jogo.causar_dano(vigilante, vigilante.vida * 2)
    simulador._acompanhar_lutas(jogo, lutas, r)
    assert r.lutas[0].venceu and r.lutas[0].duracao == 30 and not lutas and r.lutas[0].vida_do_mini_chefe == 0


def test_quem_nao_vai_cacar_sai_do_circulo_em_vez_de_invocar_sem_querer():
    jogo = jogo_de_teste(Programador)
    jogo.jogador.imortal = True
    jogo.jogador.posicao = jogo.mapa.empurrar(pygame.Vector2(jogo.arena.center), 100)   # sem inimigos, ele vai ao centro
    jogo.fase.alvo_com = lambda jogo: 0                  # e ninguém nasce para tirá-lo de lá
    circulo = LocalDeInvocacao(pygame.Vector2(jogo.jogador.posicao), "tia_da_cantina")
    jogo.adicionar(circulo)
    jogo._incorporar_novas()
    robo = simulador.Robo(jogo, cacar=False)
    for _ in range(30 * 4):
        robo.agir(1 / 30)
        jogo.atualizar(1 / 30)
    assert circulo.ativo and jogo.jogador.posicao.distance_to(circulo.posicao) > circulo.raio


def test_a_mesma_semente_da_a_mesma_partida_em_processos_diferentes():
    """A ordem de um set de objetos ou textos muda de um processo para outro (PYTHONHASHSEED): nada da lógica
    do jogo pode depender dela, senão a mesma semente não repete a partida."""
    import os
    import subprocess
    raiz = Path(__file__).resolve().parent.parent
    codigo = ("import sys; sys.path[:0] = ['ferramentas', '.']; import simular_partida as s; "
              "from jogo.jogador.classes import CLASSES; "
              "r = s.jogar(CLASSES[1], 1, 'nada', True, 1.5); "
              "print(round(r.tempo, 3), r.eliminacoes, r.nivel_final, r.moedas, len(r.lutas))")
    saidas = set()
    for semente_do_hash in ("1", "2", "3"):
        ambiente = dict(os.environ, PYTHONHASHSEED=semente_do_hash, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        saida = subprocess.run([sys.executable, "-c", codigo], cwd=raiz, env=ambiente, capture_output=True,
                               text=True, timeout=300, check=True).stdout.strip().splitlines()[-1]
        saidas.add(saida)
    assert len(saidas) == 1, saidas
