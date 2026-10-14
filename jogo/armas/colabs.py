"""Colabs: duas armas no nível máximo se juntam numa arma nova."""
from abc import ABC

import pygame

from jogo.ajudantes.ajudantes import FuscaCircular, MascoteFlutuante
from jogo.armas.arma import Arma, ArmaDeContato, ArmaDeDisparo
from jogo.armas.caramelo import Caramelo
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.claude import MascoteClaude
from jogo.armas.cobra_python import CobraPython
from jogo.armas.fusca import FuscaAzul
from jogo.armas.gemini import Gemini
from jogo.efeitos import RaioDebate
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import CobraGemea


class Colab(Arma, ABC):
    NIVEL_MAXIMO = 1
    MELHORIAS = ()
    INGREDIENTES = ()
    RECEITAS = []

    @staticmethod
    def colabs_disponiveis(armas):
        """Receitas cujas duas armas estão no nível máximo."""
        disponiveis = []
        for receita in Colab.RECEITAS:
            if all(any(type(a) is ingrediente and a.no_maximo for a in armas) for ingrediente in receita.INGREDIENTES):
                disponiveis.append(receita)
        return disponiveis

    @staticmethod
    def ingredientes_em(receita, armas):
        return [a for a in armas if type(a) in receita.INGREDIENTES]


class CarameloNoFusca(ArmaDeContato, Colab):
    NOME = "Caramelo no Fusca"
    ICONE = "sprites/caramelo_no_fusca.png"
    DESCRICAO = "O Caramelo assume o volante e dá voltas na arena atropelando e possuindo inimigos."
    INGREDIENTES = (Caramelo, FuscaAzul)
    ATRIBUTOS = {"dano": (30,), "possessao": (5.0,)}

    def __init__(self):
        super().__init__()
        self.fusca = None

    def atualizar(self, dt, jogo, dono):
        if self.fusca is None:
            self.fusca = FuscaCircular(dono, self)
            jogo.adicionar(self.fusca)

    def ao_remover(self, jogo):
        if self.fusca is not None:
            self.fusca.remover()
            self.fusca = None


class CobrasGemeas(ArmaDeDisparo, Colab):
    NOME = "Cobras Gêmeas"
    ICONE = "icones/cobras_gemeas.png"
    DESCRICAO = "Quatro cobras por disparo, e cada uma se divide em duas ao acertar."
    INGREDIENTES = (CobraPython, Gemini)
    ATRIBUTOS = {"dano": (24,), "quantidade": (4,), "geracoes": (2,), "recarga": (0.7,)}
    MUNICAO_BASE = 16
    VELOCIDADE = 430

    def disparar(self, jogo, dono):
        quantidade = self.valor("quantidade")
        for i in range(quantidade):
            direcao = dono.direcao_mira.rotate((i - (quantidade - 1) / 2) * 14)
            jogo.adicionar(CobraGemea(dono.posicao, direcao * self.VELOCIDADE,
                                      self.valor("dano") * dono.multiplicador_dano, geracoes=self.valor("geracoes")))
        Recursos.tocar("disparo", 0.15)
        return True


class DebateDasIAs(ArmaDeContato, Colab):
    NOME = "Debate das IAs"
    ICONE = "icones/debate.png"
    DESCRICAO = "ChatGPT e Claude discutem em volta de você, e o raio entre eles acerta tudo no meio."
    INGREDIENTES = (MascoteChatGPT, MascoteClaude)
    ATRIBUTOS = {"dano": (14,), "raio": (150,), "velocidade": (1.6,)}
    INTERVALO = 0.15

    def __init__(self):
        super().__init__()
        self.mascotes = None
        self.raio_visual = None
        self.angulo = 0.0
        self._espera = 0.0

    def atualizar(self, dt, jogo, dono):
        if self.mascotes is None:
            self.mascotes = (MascoteFlutuante(dono, MascoteChatGPT.ICONE, 34, (0, 0), pasta="chatgpt"),
                             MascoteFlutuante(dono, MascoteClaude.ICONE, 34, (0, 0), pasta="claude"))
            self.raio_visual = RaioDebate(*self.mascotes)
            for e in (*self.mascotes, self.raio_visual):
                jogo.adicionar(e)
        self.angulo += self.valor("velocidade") * dt
        braco = pygame.Vector2(self.valor("raio"), 0).rotate_rad(self.angulo)
        self.mascotes[0].deslocamento = braco
        self.mascotes[1].deslocamento = -braco
        self._espera -= dt
        if self._espera > 0:
            return
        self._espera = self.INTERVALO
        inicio, fim = self.mascotes[0].posicao, self.mascotes[1].posicao
        for inimigo in jogo.inimigos_proximos(dono.posicao, self.valor("raio") + 20):
            if Colisao.segmento_acerta_circulo(inicio, fim, 16, inimigo.posicao, inimigo.raio):
                jogo.causar_dano(inimigo, self.valor("dano") * dono.multiplicador_dano)

    def ao_remover(self, jogo):
        if self.mascotes is not None:
            for e in (*self.mascotes, self.raio_visual):
                e.remover()
            self.mascotes = None


Colab.RECEITAS = [CarameloNoFusca, CobrasGemeas, DebateDasIAs]
