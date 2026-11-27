"""Joga uma partida inteira sem janela, com um jogador automático, e mostra um resumo.

Uso: python ferramentas/simular_partida.py [--heroi 1..7] (a ordem de CLASSES: 1 Otaku, 2 Programador, 3 Mestre de RPG...)
     [--imortal] [--semente N] [--minutos N]

Os chefes chegam aos 5, 10 e 15 minutos; das 15:00 em diante a dificuldade dispara até ninguém passar
muito dos 20:00. `--minutos` diz quando parar (com --imortal ela não acaba sozinha). O resumo mostra
também o maior número de inimigos em campo e o quadro mais lento, para conferir o desempenho.
"""
import argparse
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

from jogo.jogador.classes import CLASSES  # noqa: E402
from jogo.jogo import Jogo  # noqa: E402
from jogo.progressao import Progressao  # noqa: E402


TROCA_DE_OBJETIVO = 5.0     # segundos perseguindo o chefe, depois o mesmo tanto recolhendo notas


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--heroi", type=int, default=1)
    p.add_argument("--imortal", action="store_true")
    p.add_argument("--semente", type=int, default=1)
    p.add_argument("--minutos", type=float, default=21)
    a = p.parse_args()
    pygame.init()
    pygame.display.set_mode((1, 1))
    jogo = Jogo(CLASSES[a.heroi - 1], semente=a.semente)
    jogo.jogador.imortal = a.imortal       # imortal de verdade: nem um golpe maior que a vida inteira derruba
    dt = 1 / 30
    inicio = time.perf_counter()
    quadro = 0
    titulo_anterior, chefes_vistos, derrotados = None, set(), 0
    pico_inimigos, pior_quadro, pior_cpu, soma_quadros = 0, 0.0, 0.0, 0.0
    while not jogo.terminou and jogo.placar.tempo < a.minutos * 60:
        if jogo.fase.titulo != titulo_anterior:
            titulo_anterior = jogo.fase.titulo
            print(f">>> {jogo.placar.tempo_formatado}  {titulo_anterior} (nível {jogo.jogador.nivel})")
        for chefe in jogo.chefes:
            if chefe not in chefes_vistos:
                chefes_vistos.add(chefe)
                print(f">>> {jogo.placar.tempo_formatado}  chefe {chefe.nome} (nível {jogo.jogador.nivel}; "
                      f"{len(jogo.chefes)} em campo)")
        if jogo.chefes_derrotados != derrotados:
            derrotados = jogo.chefes_derrotados
            print(f">>> {jogo.placar.tempo_formatado}  chefe derrotado: {derrotados} de 3")
        fuga = pygame.Vector2()
        for inimigo in jogo.inimigos_proximos(jogo.jogador.posicao, 220):
            fuga += jogo.jogador.posicao - inimigo.posicao
        cercado = bool(jogo.inimigos_proximos(jogo.jogador.posicao, 90))     # tem inimigo quase encostando
        circulo = pygame.Vector2(1, 0).rotate(quadro * 0.3)
        centro = pygame.Vector2(jogo.arena.center) - jogo.jogador.posicao
        fuga += centro * 0.15   # foge sem se encurralar nas bordas
        # Com os chefes no relógio a luta não para a partida: o bot alterna entre encostar no chefe e
        # buscar as notas caídas (senão a experiência fica toda no chão e ele para de subir de nível).
        buscando_notas = int(jogo.placar.tempo / TROCA_DE_OBJETIVO) % 2 == 1
        if jogo.chefe is not None and jogo.chefe.ativo and not buscando_notas:
            if jogo.chefe.posicao.distance_to(jogo.jogador.posicao) > 120:
                fuga = jogo.chefe.posicao - jogo.jogador.posicao
        elif buscando_notas or fuga.length_squared() < 1:
            notas = [c for c in jogo.grupos["coletavel"] if c.MAGNETICO]
            if notas:
                perto = min(notas, key=lambda c: c.posicao.distance_squared_to(jogo.jogador.posicao))
                rumo = perto.posicao - jogo.jogador.posicao
                if cercado and rumo.length_squared() > 0:      # com inimigo perto, fugir pesa mais que a nota
                    fuga = fuga.normalize() + rumo.normalize() * 0.6
                else:
                    fuga = rumo
        jogo.entrada.direcao = fuga.normalize() if fuga.length_squared() > 0 else circulo
        alvo = jogo.inimigo_mais_proximo(jogo.jogador.posicao, 700)
        jogo.entrada.mira = pygame.Vector2(alvo.posicao) if alvo is not None else None
        if jogo.jogador.especial.pronto:
            jogo.jogador.usar_especial(jogo)
        antes, antes_cpu = time.perf_counter(), time.thread_time()
        jogo.atualizar(dt)
        gasto = time.perf_counter() - antes
        soma_quadros += gasto
        pior_quadro = max(pior_quadro, gasto)
        pior_cpu = max(pior_cpu, time.thread_time() - antes_cpu)     # sem as pausas que o sistema dá no processo
        pico_inimigos = max(pico_inimigos, len(jogo.inimigos))
        while jogo.niveis_pendentes > 0:
            Progressao.gerar_opcoes(jogo.jogador, jogo.rng)[0].aplicar(jogo.jogador, jogo)
            jogo.niveis_pendentes -= 1
        while jogo.baus_pendentes > 0:
            Progressao.premio_bau(jogo.jogador, jogo.rng).aplicar(jogo.jogador, jogo)
            jogo.baus_pendentes -= 1
        quadro += 1
        if quadro % (30 * 60) == 0:
            print(f"{jogo.placar.tempo_formatado}  nível {jogo.jogador.nivel:>2}  vida {jogo.jogador.vida:>7.0f}  "
                  f"inimigos {len(jogo.inimigos):>3}  eliminações {jogo.placar.eliminacoes}  "
                  f"dificuldade {jogo.fase.escala_dificuldade:.1f}  {jogo.fase.titulo}")
    print("---")
    situacao = "HONRAS" if jogo.venceu else "REPROVADO"
    print(f"resultado: {situacao}, {'caiu' if jogo.terminou else 'simulação parada'} em {jogo.placar.tempo_formatado} "
          f"({jogo.fase.titulo}); chefes derrotados: {jogo.chefes_derrotados}; "
          f"mini-chefes: {jogo.mini_chefes_derrotados}; moedas: {jogo.moedas_ganhas()}")
    print(f"desempenho: pico de {pico_inimigos} inimigos; quadro médio {soma_quadros / max(1, quadro) * 1000:.1f} ms, "
          f"pior {pior_cpu * 1000:.1f} ms de CPU ({pior_quadro * 1000:.1f} ms de relógio; a diferença são pausas "
          f"do sistema, não do jogo). Só a lógica, sem desenhar.")
    print(f"nível {jogo.jogador.nivel}; armas: {', '.join(str(x) for x in jogo.jogador.armas)}")
    print(f"itens: {', '.join(str(x) for x in jogo.jogador.itens)}")
    print(f"placar: {jogo.placar}; combos 67: {jogo.placar.combos_67}")
    print(f"tempo real da simulação: {time.perf_counter() - inicio:.0f} s")


if __name__ == "__main__":
    main()
