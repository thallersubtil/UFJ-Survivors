"""Efeitos visuais de curta duração: números de dano, explosões, raios."""
import math
from abc import ABC

import pygame

from jogo.config import Cor
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Efeito(Entidade, ABC):
    grupo = "efeito"
    camada = 3

    def __init__(self, posicao, duracao, raio=0):
        super().__init__(posicao, raio)
        self.duracao = duracao
        self.tempo = 0.0

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.ao_atualizar(dt, jogo)
        if self.tempo >= self.duracao:
            self.remover()

    def ao_atualizar(self, dt, jogo):
        """Gancho para efeitos que interagem com o jogo enquanto duram."""

    @property
    def fracao(self):
        return min(1.0, self.tempo / self.duracao) if self.duracao > 0 else 1.0


class TextoFlutuante(Efeito):
    def __init__(self, texto, posicao, cor=Cor.DANO, tamanho=16, duracao=0.7, subida=36):
        super().__init__(posicao, duracao)
        self.subida = subida
        fonte = Recursos.fonte(tamanho)
        frente = fonte.render(texto, True, cor)
        contorno = fonte.render(texto, True, Cor.BORDA_ESCURA)
        self.imagem = pygame.Surface((frente.get_width() + 2, frente.get_height() + 2), pygame.SRCALPHA)
        for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
            self.imagem.blit(contorno, (dx, dy))
        self.imagem.blit(frente, (1, 1))

    def desenhar(self, tela, camera):
        p = camera.para_tela(self.posicao)
        p.y -= self.subida * self.fracao
        alfa = 255 if self.fracao < 0.6 else int(255 * (1 - self.fracao) / 0.4)
        self.imagem.set_alpha(alfa)
        tela.blit(self.imagem, self.imagem.get_rect(center=(round(p.x), round(p.y))))


class FaiscaExplosao(Efeito):
    """Explosão da Pilha AA: fere o herói uma vez se ele estiver perto."""

    def __init__(self, posicao, raio=70, dano=10):
        super().__init__(posicao, 0.35, raio)
        self.dano = dano
        self._feriu = False

    def ao_atualizar(self, dt, jogo):
        if not self._feriu:
            self._feriu = True
            if Colisao.circulos_colidem(self, jogo.jogador):
                jogo.ferir_jogador(self.dano)

    def desenhar(self, tela, camera):
        lado = int(self.raio * 2.4)
        sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
        centro = pygame.Vector2(lado / 2, lado / 2)
        r = self.raio * (0.4 + 0.6 * self.fracao)
        alfa = int(255 * (1 - self.fracao))
        pygame.draw.circle(sup, (255, 220, 80, alfa // 2), centro, int(r))
        pygame.draw.circle(sup, (255, 255, 200, alfa), centro, int(r), 3)
        for i in range(8):
            direcao = pygame.Vector2(1, 0).rotate(i * 45 + self.fracao * 60)
            pygame.draw.line(sup, (255, 240, 120, alfa), centro + direcao * r * 0.5, centro + direcao * r * 1.15, 3)
        c = camera.para_tela(self.posicao)
        tela.blit(sup, sup.get_rect(center=(round(c.x), round(c.y))))


class AuraSSJ(Efeito):
    """Aura dourada do Super Saiyajin, desenhada logo atrás do herói."""

    camada = 1

    def __init__(self, dono, duracao):
        super().__init__(dono.posicao, duracao)
        self.dono = dono

    def ao_atualizar(self, dt, jogo):
        self.posicao = self.dono.posicao - pygame.Vector2(0, 0.5)

    def desenhar(self, tela, camera):
        c = camera.para_tela(self.dono.posicao)
        largura, altura = 70, 96
        sup = pygame.Surface((largura + 20, altura + 30), pygame.SRCALPHA)
        base = pygame.Vector2(sup.get_width() / 2, sup.get_height() - 6)
        brilho = 0.85 + 0.15 * math.sin(self.tempo * 25)
        pygame.draw.ellipse(sup, (255, 210, 60, int(70 * brilho)), (10, 20, largura, altura))
        for i in range(7):
            x = 14 + i * (largura - 8) / 6
            topo = 8 + 10 * (1 + math.sin(self.tempo * 18 + i * 1.7))
            pygame.draw.polygon(sup, (255, 236, 120, int(110 * brilho)),
                                [(x - 7, base.y - 20), (x, topo), (x + 7, base.y - 20)])
        tela.blit(sup, sup.get_rect(midbottom=(round(c.x), round(c.y + 34))))


class RaioZoltraak(Efeito):
    """Raio mágico que sai do herói na direção da mira e atravessa tudo."""

    COMPRIMENTO = 950
    LARGURA = 70
    INTERVALO = 0.1

    def __init__(self, dono, dano, duracao=1.5):
        super().__init__(dono.posicao, duracao)
        self.dono = dono
        self.dano = dano
        self.direcao = pygame.Vector2(dono.direcao_mira)
        self._espera = 0.0

    def ao_atualizar(self, dt, jogo):
        self.posicao = pygame.Vector2(self.dono.posicao)
        self.direcao = pygame.Vector2(self.dono.direcao_mira)
        self._espera -= dt
        if self._espera > 0:
            return
        self._espera = self.INTERVALO
        fim = self.posicao + self.direcao * self.COMPRIMENTO
        meio = (self.posicao + fim) / 2
        for inimigo in jogo.inimigos_proximos(meio, self.COMPRIMENTO / 2 + self.LARGURA):
            if Colisao.segmento_acerta_circulo(self.posicao, fim, self.LARGURA, inimigo.posicao, inimigo.raio):
                jogo.causar_dano(inimigo, self.dano, self.direcao)

    def desenhar(self, tela, camera):
        inicio = camera.para_tela(self.posicao)
        fim = inicio + self.direcao * self.COMPRIMENTO
        sumindo = 1.0 if self.fracao < 0.85 else (1 - self.fracao) / 0.15
        largura = self.LARGURA * (1 + 0.12 * math.sin(self.tempo * 40)) * sumindo
        for cor, fator in (((140, 80, 255), 1.0), ((210, 190, 255), 0.55), ((255, 255, 255), 0.25)):
            espessura = max(1, int(largura * fator))
            pygame.draw.line(tela, cor, inicio, fim, espessura)
            pygame.draw.circle(tela, cor, inicio, espessura // 2 + 4)
