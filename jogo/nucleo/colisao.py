"""Utilitário de colisão. Todas as entidades colidem como círculos."""
import pygame


class Colisao:
    @staticmethod
    def circulos_colidem(a, b):
        soma = a.raio + b.raio
        return a.posicao.distance_squared_to(b.posicao) <= soma * soma

    @staticmethod
    def ponto_no_circulo(ponto, centro, raio):
        return pygame.Vector2(ponto).distance_squared_to(centro) <= raio * raio

    @staticmethod
    def segmento_acerta_circulo(inicio, fim, largura, centro, raio):
        """True se o círculo encosta na faixa de `largura` que vai de inicio a fim."""
        inicio = pygame.Vector2(inicio)
        trecho = pygame.Vector2(fim) - inicio
        centro = pygame.Vector2(centro)
        comprimento2 = trecho.length_squared()
        t = 0.0 if comprimento2 == 0 else max(0.0, min(1.0, (centro - inicio).dot(trecho) / comprimento2))
        mais_proximo = inicio + trecho * t
        limite = raio + largura / 2
        return mais_proximo.distance_squared_to(centro) <= limite * limite
