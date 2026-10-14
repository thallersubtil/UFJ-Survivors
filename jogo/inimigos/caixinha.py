import math

import pygame

from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("caixinha")
class Caixinha(Inimigo):
    """Caixa de papelão com etiqueta "class". Anda aos pulos; ao morrer solta duas menores."""

    NOME = "Caixinha"
    IMAGEM = "sprites/caixinha.png"
    PASTA_SPRITE = "caixinha"
    ALTURA = 42
    RAIO = 17
    VIDA = 22
    VELOCIDADE = 230
    DANO = 7
    PONTOS = 12
    EXPERIENCIA = 2
    CICLO = 1.0
    PULO = 0.35

    def _no_ar(self):
        return self.tempo % self.CICLO < self.PULO

    def mover(self, dt, jogo):
        if self._no_ar():
            self.ir_em_direcao(jogo.jogador.posicao, dt)

    def balanco(self):
        fase = self.tempo % self.CICLO
        return math.sin(math.pi * fase / self.PULO) * 14 if fase < self.PULO else 0

    def ao_morrer(self, jogo):
        super().ao_morrer(jogo)
        for lado in (-1, 1):
            jogo.adicionar(CaixinhaPequena(self.posicao + pygame.Vector2(lado * 16, 0), self.escala))


@FabricaDeInimigos.registrar("caixinha_pequena")
class CaixinhaPequena(Caixinha):
    """A caixinha que sai de dentro da Caixinha. Esta não se divide."""

    PASTA_SPRITE = "caixinha_pequena"
    ALTURA = 26
    RAIO = 11
    VIDA = 8
    PONTOS = 4
    EXPERIENCIA = 1
    CHANCE_CAFE = 0.0

    def ao_morrer(self, jogo):
        Inimigo.ao_morrer(self, jogo)
