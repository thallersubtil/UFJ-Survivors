"""Fases: linha do tempo de inimigos, mini-chefes e chefe."""
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

import pygame

from jogo.config import ALTURA, LARGURA, MAX_INIMIGOS
from jogo.inimigos.fabrica import FabricaDeInimigos


@dataclass
class EventoDaFase:
    tempo: float
    acao: Callable
    descricao: str = ""
    executado: bool = field(default=False)


class Fase(ABC):
    NOME = "Fase"
    DURACAO = 900
    APRESENTACOES = ()
    INTERVALO_NASCIMENTO = 0.5

    def __init__(self):
        self.tempo = 0.0
        self.ativos = []
        self._apresentados = 0
        self._espera = 0.0
        self.chefe_apareceu = False
        self.eventos = sorted(self.criar_eventos(), key=lambda e: e.tempo)

    @abstractmethod
    def criar_eventos(self):
        """Lista de EventoDaFase (mini-chefes, formações, chefe)."""

    @property
    def escala_dificuldade(self):
        return 1 + self.tempo / 300

    def alvo_de_inimigos(self):
        alvo = 18 + self.tempo * 0.26
        if self.chefe_apareceu:
            alvo *= 0.5
        return min(MAX_INIMIGOS, int(alvo))

    def atualizar(self, dt, jogo):
        self.tempo += dt
        while self._apresentados < len(self.APRESENTACOES) and \
                self.APRESENTACOES[self._apresentados][0] <= self.tempo:
            self.ativos.append(self.APRESENTACOES[self._apresentados][1])
            self._apresentados += 1
        for evento in self.eventos:
            if not evento.executado and evento.tempo <= self.tempo:
                evento.executado = True
                evento.acao(jogo)
        self._espera -= dt
        if self._espera <= 0 and self.ativos:
            self._espera = self.INTERVALO_NASCIMENTO
            if len(jogo.inimigos) < self.alvo_de_inimigos():
                self.nascer(jogo, jogo.rng.choice(self.ativos))

    def nascer(self, jogo, nome, quantidade=None):
        classe = FabricaDeInimigos.classe(nome)
        quantidade = quantidade or classe.TAMANHO_GRUPO
        centro = self.posicao_de_nascimento(jogo)
        for _ in range(quantidade):
            espalhar = pygame.Vector2(jogo.rng.uniform(-40, 40), jogo.rng.uniform(-40, 40))
            jogo.adicionar(FabricaDeInimigos.criar(nome, centro + espalhar, self.escala_dificuldade))

    @staticmethod
    def posicao_de_nascimento(jogo):
        """Um ponto logo fora da tela, em volta do herói, dentro da arena."""
        angulo = jogo.rng.uniform(0, 2 * math.pi)
        distancia = math.hypot(LARGURA, ALTURA) / 2 + 80
        p = jogo.jogador.posicao + pygame.Vector2(math.cos(angulo), math.sin(angulo)) * distancia
        p.x = max(jogo.arena.left + 30, min(p.x, jogo.arena.right - 30))
        p.y = max(jogo.arena.top + 30, min(p.y, jogo.arena.bottom - 30))
        return p

    def formacao_circulo(self, jogo, nome, quantidade, raio=560):
        for i in range(quantidade):
            direcao = pygame.Vector2(1, 0).rotate(360 * i / quantidade)
            jogo.adicionar(FabricaDeInimigos.criar(nome, jogo.jogador.posicao + direcao * raio,
                                                   self.escala_dificuldade))
        jogo.anunciar("Cercado!", 1.5)

    def formacao_parede(self, jogo, nome, quantidade):
        lado = jogo.rng.choice((-1, 1))
        x = jogo.jogador.posicao.x + lado * (LARGURA / 2 + 60)
        for i in range(quantidade):
            y = jogo.jogador.posicao.y + (i - (quantidade - 1) / 2) * 36
            jogo.adicionar(FabricaDeInimigos.criar(nome, (x, y), self.escala_dificuldade))
        jogo.anunciar("Lá vem a turma!", 1.5)

    def chamar_mini_chefe(self, jogo, nome):
        gigante = FabricaDeInimigos.criar_gigante(nome, self.posicao_de_nascimento(jogo), self.escala_dificuldade)
        jogo.adicionar(gigante)
        jogo.anunciar(f"Mini-chefe: {gigante.NOME} Gigante!", 3)

    def chamar_chefe(self, jogo, nome):
        self.chefe_apareceu = True
        jogo.iniciar_chefe(FabricaDeInimigos.criar(nome, self.posicao_de_nascimento(jogo)))


class SemanaDeProvas(Fase):
    NOME = "Semana de Provas"
    DURACAO = 900
    APRESENTACOES = ((0, "bug"),)

    def criar_eventos(self):
        return []
