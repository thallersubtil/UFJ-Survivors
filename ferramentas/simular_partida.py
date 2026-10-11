"""Joga uma partida inteira sem janela, com um jogador automático, e mostra um resumo.

Uso: python ferramentas/simular_partida.py [--heroi 1|2] [--imortal] [--semente N]
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

from jogo.jogador.alunos import HEROIS  # noqa: E402
from jogo.jogo import Jogo  # noqa: E402
from jogo.progressao import Progressao  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--heroi", type=int, default=1)
    p.add_argument("--imortal", action="store_true")
    p.add_argument("--semente", type=int, default=1)
    a = p.parse_args()
    pygame.init()
    pygame.display.set_mode((1, 1))
    jogo = Jogo(HEROIS[a.heroi - 1], semente=a.semente)
    dt = 1 / 30
    inicio = time.perf_counter()
    quadro = 0
    while not jogo.terminou and jogo.placar.tempo < 20 * 60:
        fuga = pygame.Vector2()
        for inimigo in jogo.inimigos_proximos(jogo.jogador.posicao, 220):
            fuga += jogo.jogador.posicao - inimigo.posicao
        circulo = pygame.Vector2(1, 0).rotate(quadro * 0.3)
        centro = pygame.Vector2(jogo.arena.center) - jogo.jogador.posicao
        fuga += centro * 0.15   # foge sem se encurralar nas bordas
        if jogo.chefe is not None and jogo.chefe.ativo and jogo.chefe.posicao.distance_to(jogo.jogador.posicao) > 350:
            fuga = jogo.chefe.posicao - jogo.jogador.posicao
        jogo.entrada.direcao = fuga.normalize() if fuga.length_squared() > 0 else circulo
        alvo = jogo.inimigo_mais_proximo(jogo.jogador.posicao, 700)
        jogo.entrada.mira = pygame.Vector2(alvo.posicao) if alvo is not None else None
        if a.imortal:
            jogo.jogador.vida = jogo.jogador.vida_maxima
        if jogo.jogador.especial.pronto:
            jogo.jogador.usar_especial(jogo)
        jogo.atualizar(dt)
        while jogo.niveis_pendentes > 0:
            Progressao.gerar_opcoes(jogo.jogador, jogo.rng)[0].aplicar(jogo.jogador, jogo)
            jogo.niveis_pendentes -= 1
        while jogo.baus_pendentes > 0:
            Progressao.premio_bau(jogo.jogador, jogo.rng).aplicar(jogo.jogador, jogo)
            jogo.baus_pendentes -= 1
        quadro += 1
        if quadro % (30 * 60) == 0:
            print(f"{jogo.placar.tempo_formatado}  nível {jogo.jogador.nivel:>2}  vida {jogo.jogador.vida:>7.0f}  "
                  f"inimigos {len(jogo.inimigos):>3}  eliminações {jogo.placar.eliminacoes}")
    print("---")
    print(f"resultado: {'VITÓRIA' if jogo.venceu else 'DERROTA' if jogo.terminou else 'SEM FIM'} em {jogo.placar.tempo_formatado}")
    print(f"nível {jogo.jogador.nivel}; armas: {', '.join(str(x) for x in jogo.jogador.armas)}")
    print(f"itens: {', '.join(str(x) for x in jogo.jogador.itens)}")
    print(f"placar: {jogo.placar}; combos 67: {jogo.placar.combos_67}")
    print(f"tempo real da simulação: {time.perf_counter() - inicio:.0f} s")


if __name__ == "__main__":
    main()
