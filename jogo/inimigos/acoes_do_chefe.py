"""Ações de várias etapas que um chefe executa enquanto fica parado (investida, rajada)."""
import math
from abc import ABC, abstractmethod

import pygame

from jogo.nucleo.desenho import desenhar_faixa_de_aviso


class AcaoDoChefe(ABC):
    """Ação que dura alguns quadros. O chefe chama a ação a cada quadro até ela terminar."""

    POR_CIMA = False             # True: o aviso é desenhado na frente do chefe (o que sai do corpo dele)

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
        desenhar_faixa_de_aviso(tela, inicio, fim, self.chefe.raio * 1.4, tempo=self.carga)


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


class RaiosPelosOlhos(AcaoDoChefe):
    """O chefe para, encara o herói e solta dois feixes vermelhos pelos olhos.

    Primeiro vem a mira: dois fios finos acompanham o herói e, no fim, travam (ficam grossos e piscando).
    Só então os feixes saem, na direção travada: quem saiu da linha escapa. Repete `vezes` vezes.
    """

    POR_CIMA = True
    MIRA = 0.85                  # segundos acompanhando o herói
    TRAVA = 0.35                 # segundos com a direção já travada, antes do disparo
    DISPARO = 0.45               # segundos de feixe aceso
    ALCANCE = 900
    LARGURA = 6                  # espessura de cada feixe
    SEPARACAO = 9                # distância entre os dois feixes
    VERMELHO = (255, 40, 40)

    def __init__(self, chefe, dano, vezes=1):
        self.chefe = chefe
        self.dano = dano
        self.vezes = vezes
        self.tempo = 0.0
        self.direcao = pygame.Vector2(1, 0)
        self._acertou = False

    @property
    def travado(self):
        return self.tempo >= self.MIRA

    @property
    def disparando(self):
        return self.tempo >= self.MIRA + self.TRAVA

    def feixes(self):
        """Um segmento (origem, fim) por olho, em coordenadas do mundo. Os dois nascem exatamente nos olhos
        e vão se abrindo um pouco pelo caminho, para se ver que são dois."""
        lado = self.direcao.rotate(90) * self.SEPARACAO / 2
        return [(olho, olho + desvio + self.direcao * self.ALCANCE)
                for olho, desvio in zip(self.chefe.olhos(), (-lado, lado))]

    def acerta(self, alvo):
        """Se o círculo do alvo encosta em algum dos feixes."""
        for origem, fim in self.feixes():
            ao_longo = max(0.0, min(self.ALCANCE, (alvo.posicao - origem).dot(self.direcao)))
            if alvo.posicao.distance_to(origem + self.direcao * ao_longo) <= alvo.raio + self.LARGURA / 2:
                return True
        return False

    def __call__(self, dt, jogo):
        if not self.travado:
            self.chefe.olhando_esquerda = jogo.jogador.posicao.x < self.chefe.posicao.x
            olhos = self.chefe.olhos()
            falta = jogo.jogador.posicao - sum(olhos, pygame.Vector2()) / len(olhos)     # a mira parte dos olhos
            if falta.length_squared() > 0:
                self.direcao = falta.normalize()
        self.tempo += dt
        if self.disparando and not self._acertou and self.acerta(jogo.jogador):
            self._acertou = jogo.ferir_jogador(self.dano)
        if self.tempo < self.MIRA + self.TRAVA + self.DISPARO:
            return False
        self.vezes -= 1
        self.tempo = self.MIRA * 0.5                       # as repetições miram mais depressa
        self._acertou = False
        return self.vezes <= 0

    def desenhar_aviso(self, tela, camera):
        camada = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
        for origem, fim in self.feixes():
            a, b = camera.para_tela(origem), camera.para_tela(fim)
            if self.disparando:                             # o feixe: halo, vermelho vivo e miolo branco
                pygame.draw.line(camada, (*self.VERMELHO, 90), a, b, self.LARGURA + 8)
                pygame.draw.line(camada, (*self.VERMELHO, 255), a, b, self.LARGURA)
                pygame.draw.line(camada, (255, 225, 210, 255), a, b, 2)
                pygame.draw.circle(camada, (255, 225, 210, 255), a, 2)
            elif self.travado:                              # travou: fio grosso piscando
                pisca = 120 + round(120 * abs(math.sin(self.tempo * 30)))
                pygame.draw.line(camada, (*self.VERMELHO, pisca), a, b, 3)
                pygame.draw.circle(camada, (*self.VERMELHO, 255), a, 2)
            else:                                           # mirando: fio fino que acompanha o herói
                pygame.draw.line(camada, (*self.VERMELHO, 110), a, b, 2)
                pygame.draw.circle(camada, (*self.VERMELHO, 220), a, 1 + round(self.tempo / self.MIRA))
        tela.blit(camada, (0, 0))
