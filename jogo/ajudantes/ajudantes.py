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


class MascoteFlutuante(Ajudante):
    """Mascote que flutua perto do herói (ChatGPT, Claude). Pode mostrar uma barrinha."""

    camada = 2

    def __init__(self, dono, imagem, altura, deslocamento, barra=None):
        super().__init__(dono.posicao + deslocamento, 14)
        self.dono = dono
        self.imagem = imagem
        self.altura = altura
        self.deslocamento = pygame.Vector2(deslocamento)
        self.barra = barra
        self.tempo = 0.0

    def atualizar(self, dt, jogo):
        self.tempo += dt
        alvo = self.dono.posicao + self.deslocamento + pygame.Vector2(0, math.sin(self.tempo * 3) * 6)
        self.posicao += (alvo - self.posicao) * min(1.0, dt * 8)

    def desenhar(self, tela, camera):
        imagem = Recursos.imagem(self.imagem, self.altura)
        desenhar_sprite(tela, camera, imagem, self.posicao, sombra=False)
        if self.barra is not None:
            c = camera.para_tela(self.posicao)
            fundo = pygame.Rect(0, 0, 34, 5)
            fundo.midtop = (round(c.x), round(c.y - self.altura / 2 - 10))
            pygame.draw.rect(tela, (20, 16, 30), fundo.inflate(2, 2))
            cheio = fundo.copy()
            cheio.width = round(fundo.width * self.barra())
            pygame.draw.rect(tela, (240, 140, 70), cheio)


class FuscaVeiculo(Ajudante):
    """Fusca azul que atravessa a tela buzinando e possui quem atropela."""

    IMAGEM = "sprites/fusca.png"
    ALTURA = 56
    VELOCIDADE = 650

    def __init__(self, posicao, sentido, possessao, dano):
        super().__init__(posicao, 34)
        self.sentido = sentido
        self.possessao = possessao
        self.dano = dano
        self.tempo = 0.0
        self._atingidos = set()

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.posicao.x += self.sentido * self.VELOCIDADE * dt
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if id(inimigo) in self._atingidos:
                continue
            self._atingidos.add(id(inimigo))
            inimigo.possuir(self.possessao)
            jogo.causar_dano(inimigo, self.dano, pygame.Vector2(self.sentido, -0.3))
        if self.tempo > 0.5 and not jogo.camera.visivel(self.posicao, 300):
            self.remover()

    def desenhar(self, tela, camera):
        imagem = Recursos.imagem(self.IMAGEM, self.ALTURA)
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.sentido < 0,
                        deslocamento_y=abs(math.sin(self.tempo * 30)) * 2)
