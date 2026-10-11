"""Câmera que segue o herói sem mostrar fora da arena."""
import pygame


class Camera:
    def __init__(self, largura, altura, arena):
        self.largura = largura
        self.altura = altura
        self.arena = arena
        self.deslocamento = pygame.Vector2(0, 0)

    def seguir(self, posicao):
        x = posicao[0] - self.largura / 2
        y = posicao[1] - self.altura / 2
        x = max(self.arena.left, min(x, self.arena.right - self.largura))
        y = max(self.arena.top, min(y, self.arena.bottom - self.altura))
        self.deslocamento.update(x, y)

    def para_tela(self, posicao):
        return pygame.Vector2(posicao) - self.deslocamento

    def para_mundo(self, posicao_tela):
        return pygame.Vector2(posicao_tela) + self.deslocamento

    @property
    def retangulo(self):
        return pygame.Rect(round(self.deslocamento.x), round(self.deslocamento.y), self.largura, self.altura)

    def visivel(self, posicao, margem=64):
        return self.retangulo.inflate(margem * 2, margem * 2).collidepoint(posicao)
