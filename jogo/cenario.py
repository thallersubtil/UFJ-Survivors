"""Pátio genérico: o mapa usado quando o mapa da UFJ não está disponível."""
import pygame

from jogo.config import ARENA_ALTURA, ARENA_LARGURA, Cor
from jogo.mapa import Decoracao, Mapa
from jogo.nucleo.recursos import Recursos

__all__ = ["Cenario", "Decoracao"]


class Cenario(Mapa):
    TIPOS = (
        ("cenario/arvore.png", 140, 0.35),
        ("cenario/banco.png", 46, 0.25),
        ("cenario/poste.png", 100, 0.2),
        ("cenario/canteiro.png", 52, 0.2),
    )
    CHAO = "cenario/chao.png"

    def __init__(self, arena=None, rng=None):
        arena = arena or pygame.Rect(0, 0, ARENA_LARGURA, ARENA_ALTURA)
        super().__init__(arena, arena.center)
        self.decoracoes = self.gerar_decoracoes(arena, rng) if rng is not None else []

    def entidades(self):
        return list(self.decoracoes)

    @staticmethod
    def gerar_decoracoes(arena, rng, quantidade=70):
        imagens = [t[0] for t in Cenario.TIPOS]
        alturas = {t[0]: t[1] for t in Cenario.TIPOS}
        pesos = [t[2] for t in Cenario.TIPOS]
        centro = pygame.Vector2(arena.center)
        decoracoes = []
        while len(decoracoes) < quantidade:
            p = pygame.Vector2(rng.uniform(arena.left + 80, arena.right - 80),
                               rng.uniform(arena.top + 80, arena.bottom - 80))
            if p.distance_to(centro) < 300:
                continue
            imagem = rng.choices(imagens, pesos)[0]
            decoracoes.append(Decoracao(p, imagem, alturas[imagem]))
        return decoracoes

    def desenhar_chao(self, tela, camera):
        tela.fill(Cor.GRAMA_FORA)
        chao = Recursos.imagem(self.CHAO)
        largura, altura = chao.get_size()
        visivel = camera.retangulo.clip(self.arena)
        x0 = visivel.left - (visivel.left - self.arena.left) % largura
        y0 = visivel.top - (visivel.top - self.arena.top) % altura
        for y in range(int(y0), visivel.bottom, altura):
            for x in range(int(x0), visivel.right, largura):
                tela.blit(chao, camera.para_tela((x, y)))
        borda = self.arena.move(-camera.deslocamento.x, -camera.deslocamento.y)
        pygame.draw.rect(tela, Cor.BORDA_ESCURA, borda, 6)
