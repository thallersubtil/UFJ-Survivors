"""Área clicável desenhada por cima de uma arte do jogo (Centro Acadêmico, estante da loja).

Cinza = dá para usar; amarelo piscando = em cima ou selecionada (antes de entrar).
"""
import pygame

from jogo.ui.pixel import piscar


class AreaInterativa:
    CINZA = (210, 210, 220)
    AMARELO = (255, 214, 92)

    def __init__(self, nome, pontos, descricao=""):
        self.nome = nome
        self.pontos = [tuple(p) for p in pontos]       # contorno em coordenadas da tela (1280x720)
        self.descricao = descricao
        xs, ys = [p[0] for p in self.pontos], [p[1] for p in self.pontos]
        self.caixa = pygame.Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    @classmethod
    def retangulo(cls, nome, rect, descricao=""):
        r = pygame.Rect(rect)
        return cls(nome, [r.topleft, r.topright, r.bottomright, r.bottomleft], descricao)

    def contem(self, pos):
        """Ponto dentro do polígono (regra do número de cruzamentos; aceita formas em L)."""
        x, y = pos
        dentro = False
        for (x1, y1), (x2, y2) in zip(self.pontos, self.pontos[1:] + self.pontos[:1]):
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                dentro = not dentro
        return dentro

    @property
    def centro(self):
        return self.caixa.center

    def desenhar(self, tela, selecionada, tempo, largura=3, preencher=True):
        veu = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
        if selecionada:
            p = piscar(tempo)
            if preencher:
                pygame.draw.polygon(veu, (*self.AMARELO, int(40 * p)), self.pontos)
            pygame.draw.polygon(veu, (*self.AMARELO, int(255 * p)), self.pontos, largura + 2)
            pygame.draw.polygon(veu, (255, 250, 200, int(120 * p)), self.pontos, 1)
        else:
            pygame.draw.polygon(veu, (*self.CINZA, 200), self.pontos, largura)
        tela.blit(veu, (0, 0))
