"""Projéteis do herói e dos inimigos."""
import math
from abc import ABC, abstractmethod

import pygame

from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Projetil(Entidade, ABC):
    grupo = "projetil"
    camada = 2
    IMAGEM = ""
    ALTURA = 24
    DURACAO = 2.0

    def __init__(self, posicao, velocidade, dano, raio=10):
        super().__init__(posicao, raio)
        self.velocidade = pygame.Vector2(velocidade)
        self.dano = dano
        self.tempo = 0.0

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if self.tempo >= self.DURACAO or not jogo.arena.collidepoint(self.posicao):
            self.remover()
            return
        self.mover(dt)
        self.verificar_colisao(jogo)

    def mover(self, dt):
        self.posicao += self.velocidade * dt

    @abstractmethod
    def verificar_colisao(self, jogo):
        """Testa se acertou alguém e aplica o dano."""

    def angulo_desenho(self):
        return -math.degrees(math.atan2(self.velocidade.y, self.velocidade.x))

    def desenhar(self, tela, camera):
        imagem = Recursos.imagem(self.IMAGEM, self.ALTURA)
        desenhar_sprite(tela, camera, imagem, self.posicao, angulo=self.angulo_desenho(), sombra=False)


class ProjetilDoHeroi(Projetil):
    def __init__(self, posicao, velocidade, dano, perfuracao=1, raio=10, atingidos=None):
        super().__init__(posicao, velocidade, dano, raio)
        self.perfuracao = perfuracao
        self.atingidos = set(atingidos or ())

    def verificar_colisao(self, jogo):
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if id(inimigo) in self.atingidos:
                continue
            self.atingidos.add(id(inimigo))
            jogo.causar_dano(inimigo, self.dano, self.velocidade)
            self.ao_acertar(inimigo, jogo)
            self.perfuracao -= 1
            if self.perfuracao <= 0:
                self.remover()
                return

    def ao_acertar(self, inimigo, jogo):
        """Gancho para projéteis com efeito extra ao acertar."""


class ProjetilDivisivel(ProjetilDoHeroi):
    """Ao acertar, se divide em duas cópias de si mesmo (Gemini, Cobras Gêmeas)."""

    DESVIO = 35
    FATOR_DANO = 0.7

    def __init__(self, posicao, velocidade, dano, geracoes=1, perfuracao=1, raio=10, atingidos=None):
        super().__init__(posicao, velocidade, dano, perfuracao, raio, atingidos)
        self.geracoes = geracoes

    def ao_acertar(self, inimigo, jogo):
        if self.geracoes <= 0:
            return
        for desvio in (-self.DESVIO, self.DESVIO):
            jogo.adicionar(type(self)(self.posicao, self.velocidade.rotate(desvio), self.dano * self.FATOR_DANO,
                                      geracoes=self.geracoes - 1, raio=self.raio, atingidos=self.atingidos))


class ProjetilInimigo(Projetil):
    def verificar_colisao(self, jogo):
        if Colisao.circulos_colidem(self, jogo.jogador):
            jogo.ferir_jogador(self.dano)
            self.remover()


class MovimentoSerpente:
    """Mixin: avança ondulando para os lados, como uma cobra."""

    AMPLITUDE = 14
    FREQUENCIA = 12

    def mover(self, dt):
        if not hasattr(self, "_base"):
            self._base = pygame.Vector2(self.posicao)
        self._base += self.velocidade * dt
        lado = pygame.Vector2(-self.velocidade.y, self.velocidade.x)
        if lado.length_squared() > 0:
            lado.scale_to_length(math.sin(self.tempo * self.FREQUENCIA) * self.AMPLITUDE)
        self.posicao = self._base + lado


class CobraProjetil(MovimentoSerpente, ProjetilDoHeroi):
    IMAGEM = "sprites/cobra.png"
    ALTURA = 22
    DURACAO = 1.6
