"""Ações de várias etapas que um chefe executa enquanto fica parado (investida, rajada)."""
from abc import ABC, abstractmethod

import pygame


class AcaoDoChefe(ABC):
    """Ação que dura alguns quadros. O chefe chama a ação a cada quadro até ela terminar."""

    @abstractmethod
    def __call__(self, dt, jogo):
        """Avança a ação um quadro. Retorna True quando terminou."""

    def desenhar_aviso(self, tela, camera):
        """Aviso visual da ação (por padrão nenhum)."""


class Investida(AcaoDoChefe):
    """O chefe mira no herói (carga), avança em linha reta e repete `vezes` vezes."""

    CARGA_REPETICAO = 0.45

    def __init__(self, chefe, vezes=1, carga=0.8, duracao=0.6, velocidade=720):
        self.chefe = chefe
        self.vezes = vezes
        self.carga = carga
        self.duracao = duracao
        self.velocidade = velocidade
        self._restante = duracao
        self.direcao = pygame.Vector2(1, 0)

    @property
    def em_carga(self):
        return self.carga > 0

    def __call__(self, dt, jogo):
        if self.carga > 0:
            self.carga -= dt
            self.direcao = self.chefe.mirar(jogo)
            return False
        self._restante -= dt
        self.chefe.posicao += self.direcao * self.velocidade * dt
        if self._restante > 0:
            return False
        self.vezes -= 1
        if self.vezes <= 0:
            return True
        self.carga = self.CARGA_REPETICAO
        self._restante = self.duracao
        return False

    def desenhar_aviso(self, tela, camera):
        if not self.em_carga:
            return
        inicio = camera.para_tela(self.chefe.posicao)
        fim = inicio + self.direcao * self.velocidade * self.duracao
        pygame.draw.line(tela, (230, 60, 60), inicio, fim, 6)


class Rajada(AcaoDoChefe):
    """Chama `disparo(i)` `vezes` vezes, uma a cada `intervalo` segundos (a primeira na hora)."""

    def __init__(self, vezes, intervalo, disparo):
        self.vezes = vezes
        self.intervalo = intervalo
        self.disparo = disparo
        self.feitas = 0
        self._espera = 0.0

    def __call__(self, dt, jogo):
        self._espera -= dt
        if self._espera <= 0:
            self.disparo(self.feitas)
            self.feitas += 1
            self._espera = self.intervalo
        return self.feitas >= self.vezes
