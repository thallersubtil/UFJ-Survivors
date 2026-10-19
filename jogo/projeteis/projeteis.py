"""Projéteis do herói e dos inimigos."""
import math
from abc import ABC, abstractmethod

import pygame

from jogo.nucleo.colisao import Colisao
from jogo.nucleo.animacao import Animador
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Projetil(Entidade, ABC):
    grupo = "projetil"
    camada = 2
    IMAGEM = ""
    ALTURA = 24
    DURACAO = 2.0
    PASTA_SPRITE = None

    def __init__(self, posicao, velocidade, dano, raio=10):
        super().__init__(posicao, raio)
        self.velocidade = pygame.Vector2(velocidade)
        self.dano = dano
        self.tempo = 0.0
        self.animador = Animador(Recursos.animacoes_ou_imagem(self.PASTA_SPRITE, self.IMAGEM, self.ALTURA))

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.animador.atualizar(dt)
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
        imagem = self.animador.quadro_atual
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
    grupo = "projetil_inimigo"

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
    PASTA_SPRITE = "cobra"
    ALTURA = 22
    DURACAO = 1.6


class ProjetilDaMateria(ProjetilInimigo):
    """Símbolo da matéria lançado pelo chefe ("dx" no Cálculo, "*p" em ED...)."""

    DURACAO = 4.5
    _imagens = {}

    def __init__(self, posicao, velocidade, dano, simbolo, cor, raio=12):
        super().__init__(posicao, velocidade, dano, raio)
        self.simbolo = simbolo
        self.cor = tuple(cor)

    @classmethod
    def imagem_do_simbolo(cls, simbolo, cor, raio):
        """Bolinha escura com borda na cor da matéria e o símbolo no meio (guardada em cache)."""
        chave = (simbolo, tuple(cor), raio)
        if chave not in cls._imagens:
            texto = Recursos.fonte(max(10, raio)).render(simbolo, True, cor)
            largura = max(raio * 2, texto.get_width() + 10)
            imagem = pygame.Surface((largura + 4, raio * 2 + 4), pygame.SRCALPHA)
            caixa = imagem.get_rect().inflate(-4, -4)
            pygame.draw.rect(imagem, (24, 18, 34), caixa, border_radius=raio)
            pygame.draw.rect(imagem, cor, caixa, 2, border_radius=raio)
            imagem.blit(texto, texto.get_rect(center=caixa.center))
            cls._imagens[chave] = imagem
        return cls._imagens[chave]

    def desenhar(self, tela, camera):
        imagem = self.imagem_do_simbolo(self.simbolo, self.cor, round(self.raio))
        tela.blit(imagem, imagem.get_rect(center=camera.para_tela(self.posicao)))


class TiroChatGPT(ProjetilDoHeroi):
    """Bolinha de energia do mascote. Quando alucinado, é rosa e com '?'."""

    DURACAO = 1.4

    def __init__(self, posicao, velocidade, dano, alucinado=False):
        super().__init__(posicao, velocidade, dano, raio=8)
        self.alucinado = alucinado

    def desenhar(self, tela, camera):
        c = camera.para_tela(self.posicao)
        cor = (255, 110, 200) if self.alucinado else (120, 240, 200)
        pygame.draw.circle(tela, (*cor, 255), (round(c.x), round(c.y)), 8)
        pygame.draw.circle(tela, (255, 255, 255), (round(c.x), round(c.y)), 4)
        if self.alucinado:
            marca = Recursos.fonte(14).render("?", True, (255, 255, 255))
            tela.blit(marca, marca.get_rect(center=(round(c.x), round(c.y - 14))))


class EstrelaGemini(ProjetilDivisivel):
    IMAGEM = "sprites/estrela_gemini.png"
    ALTURA = 26
    DURACAO = 1.8

    def angulo_desenho(self):
        return self.tempo * 540


class CobraGemea(MovimentoSerpente, ProjetilDivisivel):
    IMAGEM = "sprites/cobra.png"
    PASTA_SPRITE = "cobra"
    ALTURA = 22
    DURACAO = 1.6
