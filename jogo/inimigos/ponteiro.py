import math

import pygame

from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.recursos import Recursos


@FabricaDeInimigos.registrar("ponteiro")
class Ponteiro(Inimigo):
    """A setinha do mouse: mergulha em linha reta, passa do ponto e mira de novo."""

    NOME = "Ponteiro"
    IMAGEM = "sprites/ponteiro.png"
    PASTA_SPRITE = "ponteiro"
    ALTURA = 34
    RAIO = 13
    VIDA = 9
    VELOCIDADE = 380
    DANO = 6
    PONTOS = 10
    TEMPO_MERGULHO = 1.8
    ANGULO_DA_PONTA = 135   # a ponta do cursor aponta para cima e para a esquerda

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.direcao = pygame.Vector2(1, 0)
        self._timer = 0.0

    def mover(self, dt, jogo):
        self._timer -= dt
        if self._timer <= 0:
            falta = jogo.jogador.posicao - self.posicao
            if falta.length_squared() > 0:
                self.direcao = falta.normalize()
            self._timer = self.TEMPO_MERGULHO
        self.posicao += self.direcao * self.velocidade * dt

    def desenhar_corpo(self, tela, camera):
        imagem = self.animador.quadro_atual
        angulo = math.degrees(math.atan2(-self.direcao.y, self.direcao.x)) - self.ANGULO_DA_PONTA
        desenhar_sprite(tela, camera, imagem, self.posicao, piscar=self.piscar > 0, angulo=angulo or 0.01)
