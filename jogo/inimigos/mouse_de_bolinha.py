import math

import pygame

from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("mouse")
class MouseDeBolinha(Inimigo):
    """Mouse bege antigo que corre como rato: para, mira e dispara em linha reta."""

    NOME = "Mouse de Bolinha"
    IMAGEM = "sprites/mouse.png"
    PASTA_SPRITE = "mouse"
    ALTURA = 34
    RAIO = 16
    VIDA = 12
    VELOCIDADE = 320
    DANO = 7
    PONTOS = 10
    TEMPO_PARADO = 0.7
    TEMPO_CORRENDO = 0.9

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.correndo = False
        self._timer = 0.4
        self._direcao = pygame.Vector2(1, 0)

    def mover(self, dt, jogo):
        self._timer -= dt
        if self.correndo:
            self.posicao += self._direcao * self.velocidade * dt
            if self._timer <= 0:
                self.correndo = False
                self._timer = self.TEMPO_PARADO
        elif self._timer <= 0:
            falta = jogo.jogador.posicao - self.posicao
            if falta.length_squared() > 0:
                self._direcao = falta.normalize()
                self.olhando_esquerda = self._direcao.x < 0
            self.correndo = True
            self._timer = self.TEMPO_CORRENDO

    def escolher_animacao(self):
        return "andar" if self.correndo else "parado"

    def balanco(self):
        return abs(math.sin(self.tempo * 22)) * 2 if self.correndo else 0
