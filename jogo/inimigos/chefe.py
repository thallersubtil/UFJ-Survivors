"""Base dos chefes: alternam ataques e ficam furiosos com pouca vida."""
from abc import ABC, abstractmethod

import pygame

from jogo.inimigos.acoes_do_chefe import Investida
from jogo.inimigos.inimigo import Inimigo


class Chefe(Inimigo, ABC):
    CHANCE_CAFE = 0.0
    CHANCE_POCAO = 0.0
    INTERVALO_ATAQUE = 2.6
    INTERVALO_FURIOSO = 1.6
    DISTANCIA_PREFERIDA = 260

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, 1.0)
        self.reposiciona = False
        self._espera_ataque = 2.0
        self._indice = 0
        self.acao_atual = None

    @property
    def furioso(self):
        return self.vida < self.vida_maxima / 2

    @property
    def intervalo_ataque(self):
        """Segundos entre um ataque e o próximo (menos quando furioso)."""
        return self.INTERVALO_FURIOSO if self.furioso else self.INTERVALO_ATAQUE

    @abstractmethod
    def ataques(self):
        """Lista de ataques (funções que recebem o jogo), usados em sequência."""

    def mirar(self, jogo):
        """Direção (vetor unitário) do chefe até o herói."""
        falta = jogo.jogador.posicao - self.posicao
        return falta.normalize() if falta.length_squared() > 0 else pygame.Vector2(1, 0)

    def investir(self, vezes=1, **ajustes):
        """Começa uma investida (ou várias seguidas) em direção ao herói."""
        self.acao_atual = Investida(self, vezes, **ajustes)

    def mover(self, dt, jogo):
        if self.acao_atual is not None:
            if self.acao_atual(dt, jogo):
                self.acao_atual = None
            return
        if self.posicao.distance_to(jogo.jogador.posicao) > self.DISTANCIA_PREFERIDA:
            self.ir_em_direcao(jogo.jogador.posicao, dt)
        self._espera_ataque -= dt
        if self._espera_ataque <= 0:
            lista = self.ataques()
            lista[self._indice % len(lista)](jogo)
            self._indice += 1
            self._espera_ataque = self.intervalo_ataque

    def possuir(self, duracao):
        """Chefes não são possuídos pelo Fusca."""

    def empurrar(self, direcao, forca=180):
        super().empurrar(direcao, forca * 0.1)

    def desenhar_corpo(self, tela, camera):
        if self.acao_atual is not None:
            self.acao_atual.desenhar_aviso(tela, camera)
        super().desenhar_corpo(tela, camera)
