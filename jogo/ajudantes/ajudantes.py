"""Ajudantes: coisas que as armas colocam na arena (cachorro, fusca, mascotes)."""
import math
from abc import ABC

import pygame

from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Ajudante(Entidade, ABC):
    grupo = "ajudante"
    camada = 2


class CachorroCaramelo(Ajudante):
    """Vira-lata caramelo que corre em volta do herói e morde quem encosta."""

    IMAGEM = "sprites/caramelo.png"
    ALTURA = 40
    ESPERA_MORDIDA = 0.5

    def __init__(self, dono, angulo, arma):
        super().__init__(dono.posicao, 18)
        self.dono = dono
        self.angulo = angulo
        self.arma = arma
        self.tempo = 0.0
        self.olhando_esquerda = False
        self._mordidos = {}

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.angulo += self.arma.valor("velocidade") * dt
        raio = self.arma.valor("raio")
        nova = self.dono.posicao + pygame.Vector2(math.cos(self.angulo), math.sin(self.angulo)) * raio
        if abs(nova.x - self.posicao.x) > 0.5:
            self.olhando_esquerda = nova.x < self.posicao.x
        self.posicao = nova
        for chave in list(self._mordidos):
            self._mordidos[chave] -= dt
            if self._mordidos[chave] <= 0:
                del self._mordidos[chave]
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if id(inimigo) in self._mordidos:
                continue
            self._mordidos[id(inimigo)] = self.ESPERA_MORDIDA
            jogo.causar_dano(inimigo, self.arma.valor("dano") * self.dono.multiplicador_dano,
                             inimigo.posicao - self.dono.posicao)

    def desenhar(self, tela, camera):
        imagem = Recursos.imagem(self.IMAGEM, self.ALTURA)
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.olhando_esquerda,
                        deslocamento_y=abs(math.sin(self.tempo * 14)) * 4)
