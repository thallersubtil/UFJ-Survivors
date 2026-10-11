"""Chão do pátio e decorações da arena."""
import pygame

from jogo.config import Cor
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Decoracao(Entidade):
    """Enfeite parado (árvore, banco, poste). Só existe para ser visto."""

    grupo = "decoracao"
    camada = 1

    def __init__(self, posicao, imagem, altura):
        super().__init__(posicao, 0)
        self.imagem = imagem
        self.altura = altura

    def atualizar(self, dt, jogo):
        pass

    def desenhar(self, tela, camera):
        desenhar_sprite(tela, camera, Recursos.imagem(self.imagem, self.altura), self.posicao)


class Cenario:
    TIPOS = (
        ("cenario/arvore.png", 140, 0.35),
        ("cenario/banco.png", 46, 0.25),
        ("cenario/poste.png", 100, 0.2),
        ("cenario/canteiro.png", 52, 0.2),
    )
    CHAO = "cenario/chao.png"

    def __init__(self, arena):
        self.arena = arena

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
