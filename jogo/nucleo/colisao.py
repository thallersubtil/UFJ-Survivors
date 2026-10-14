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

    @staticmethod
    def ponto_no_poligono(ponto, poligono):
        """Teste do raio: conta quantas arestas uma semirreta horizontal cruza."""
        x, y = ponto
        dentro = False
        j = len(poligono) - 1
        for i in range(len(poligono)):
            xi, yi = poligono[i]
            xj, yj = poligono[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                dentro = not dentro
            j = i
        return dentro

    @staticmethod
    def ponto_mais_proximo_na_borda(ponto, poligono):
        ponto = pygame.Vector2(ponto)
        melhor, melhor_d2 = None, float("inf")
        for i in range(len(poligono)):
            a = pygame.Vector2(poligono[i])
            b = pygame.Vector2(poligono[(i + 1) % len(poligono)])
            trecho = b - a
            comprimento2 = trecho.length_squared()
            t = 0.0 if comprimento2 == 0 else max(0.0, min(1.0, (ponto - a).dot(trecho) / comprimento2))
            candidato = a + trecho * t
            d2 = candidato.distance_squared_to(ponto)
            if d2 < melhor_d2:
                melhor, melhor_d2 = candidato, d2
        return melhor

    @staticmethod
    def circulo_poligono(centro, raio, poligono):
        if Colisao.ponto_no_poligono(centro, poligono):
            return True
        borda = Colisao.ponto_mais_proximo_na_borda(centro, poligono)
        return borda.distance_squared_to(centro) < raio * raio

    @staticmethod
    def empurrar_para_fora(centro, raio, poligono):
        """Nova posição do círculo encostado por fora do polígono, ou None se não há contato."""
        centro = pygame.Vector2(centro)
        dentro = Colisao.ponto_no_poligono(centro, poligono)
        borda = Colisao.ponto_mais_proximo_na_borda(centro, poligono)
        distancia = borda.distance_to(centro)
        if not dentro and distancia >= raio:
            return None
        if distancia == 0:
            meio = sum((pygame.Vector2(p) for p in poligono), pygame.Vector2()) / len(poligono)
            direcao = borda - meio
        else:
            direcao = (borda - centro) if dentro else (centro - borda)
        if direcao.length_squared() == 0:
            direcao = pygame.Vector2(0, 1)
        return borda + direcao.normalize() * raio
