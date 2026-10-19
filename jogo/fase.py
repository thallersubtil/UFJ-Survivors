"""Fases: linha do tempo de inimigos, mini-chefes e chefe."""
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

import pygame

from jogo.config import ALTURA, DURACAO_PROVA, LARGURA, MAX_INIMIGOS
from jogo.inimigos.fabrica import FabricaDeInimigos


@dataclass
class EventoDaFase:
    tempo: float
    acao: Callable
    descricao: str = ""
    executado: bool = field(default=False)


class Fase(ABC):
    NOME = "Fase"
    MATERIA = "Semana de Provas"   # o que aparece em "Aprovado em ..." e "Reprovado em ..."
    DURACAO = DURACAO_PROVA
    APRESENTACOES = ()
    INTERVALO_NASCIMENTO = 0.5
    INICIO_DIFICULDADE = 0        # segundos "já jogados": provas seguintes começam mais difíceis
    PASSO_DIFICULDADE = 180       # segundos para a dificuldade subir 1 ponto

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
        return 1 + (self.INICIO_DIFICULDADE + self.tempo) / self.PASSO_DIFICULDADE

    def alvo_de_inimigos(self):
        alvo = 10 + (self.INICIO_DIFICULDADE + self.tempo) * 0.5
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

    def adiantar_para(self, tempo):
        """Pula a linha do tempo até `tempo` sem executar o que ficou para trás (modo treino)."""
        self.tempo = tempo
        for evento in self.eventos:
            if evento.tempo < tempo:
                evento.executado = True

    def nascer(self, jogo, nome, quantidade=None):
        classe = FabricaDeInimigos.classe(nome)
        quantidade = quantidade or classe.TAMANHO_GRUPO
        centro = self.posicao_de_nascimento(jogo)
        for _ in range(quantidade):
            espalhar = pygame.Vector2(jogo.rng.uniform(-40, 40), jogo.rng.uniform(-40, 40))
            jogo.adicionar(FabricaDeInimigos.criar(nome, centro + espalhar, self.escala_dificuldade))

    @staticmethod
    def posicao_de_nascimento(jogo):
        """Um ponto logo fora da tela, em volta do herói, dentro da arena e fora dos prédios."""
        distancia = math.hypot(LARGURA, ALTURA) / 2 + 80
        p = pygame.Vector2(jogo.jogador.posicao)
        for tentativa in range(30):
            angulo = jogo.rng.uniform(0, 2 * math.pi)
            p = jogo.jogador.posicao + pygame.Vector2(math.cos(angulo), math.sin(angulo)) * (distancia + tentativa * 10)
            p.x = max(jogo.arena.left + 30, min(p.x, jogo.arena.right - 30))
            p.y = max(jogo.arena.top + 30, min(p.y, jogo.arena.bottom - 30))
            if not jogo.mapa.bloqueado(p, 30):
                return p
        return jogo.mapa.empurrar(p, 30)

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


class Prova(Fase, ABC):
    """Fase descrita só por dados: quem aparece e quando, formações, mini-chefes e o chefe.

    Cada prova do semestre é uma subclasse que só preenche as constantes abaixo.
    """

    CHEFE = ""                   # nome do chefe na FabricaDeInimigos
    ROTULO = ""                  # nome curto, para o menu de treino
    FORMACOES = ()               # um lacaio por minuto, alternando círculo e parede
    MINI_CHEFES = ()             # (segundos, nome do lacaio que vira gigante)

    def criar_eventos(self):
        eventos = [EventoDaFase(tempo, lambda jogo, n=nome: self.chamar_mini_chefe(jogo, n), f"{nome} gigante")
                   for tempo, nome in self.MINI_CHEFES]
        eventos.append(EventoDaFase(self.DURACAO, lambda jogo: self.chamar_chefe(jogo, self.CHEFE), "Chefe"))
        for i, nome in enumerate(self.FORMACOES):
            if i % 2 == 0:
                acao = lambda jogo, n=nome: self.formacao_circulo(jogo, n, 24)
            else:
                acao = lambda jogo, n=nome: self.formacao_parede(jogo, n, 20)
            eventos.append(EventoDaFase(60 * (i + 1), acao, f"Formação de {nome}"))
        return eventos

    def adiantar_para_o_chefe(self):
        """Modo treino: começa a prova poucos segundos antes do chefe chegar."""
        self.adiantar_para(self.DURACAO - 3)


class ProvaDeCalculo(Prova):
    NOME = "1ª prova: Cálculo I"
    MATERIA = "Cálculo I"
    CHEFE = "chefe_calculo"
    ROTULO = "Cálculo I"
    INICIO_DIFICULDADE = 0
    APRESENTACOES = (
        (0, "bug"),
        (30, "calculadora"),
        (70, "pi"),
        (110, "caixinha"),
        (170, "mouse"),
    )
    FORMACOES = ("bug", "calculadora", "pi", "calculadora")
    MINI_CHEFES = ((150, "calculadora"),)


class ProvaDeArquiteturaEED(Prova):
    NOME = "2ª prova: Arquitetura e Estrutura de Dados"
    MATERIA = "Arquitetura de Computadores e Estrutura de Dados em C"
    CHEFE = "chefe_arquitetura_ed"
    ROTULO = "Arquitetura -> Estrutura de Dados em C"
    INICIO_DIFICULDADE = 240
    APRESENTACOES = (
        (0, "bug"),
        (0, "mouse"),
        (30, "pente_ram"),
        (70, "ponteiro"),
        (110, "pilha"),
        (170, "calculadora"),
    )
    FORMACOES = ("mouse", "ponteiro", "pente_ram", "pilha")
    MINI_CHEFES = ((150, "pente_ram"),)


class ProvaDeTDEPOO(Prova):
    NOME = "3ª prova: Transformação Digital e POO"
    MATERIA = "Transformação Digital e Programação Orientada a Objetos"
    CHEFE = "chefe_td_poo"
    ROTULO = "Transformação Digital -> POO"
    INICIO_DIFICULDADE = 480
    APRESENTACOES = (
        (0, "bug"),
        (0, "caixinha"),
        (30, "pi"),
        (60, "ponteiro"),
        (90, "pilha"),
        (120, "mouse"),
        (150, "pente_ram"),
        (180, "calculadora"),
    )
    FORMACOES = ("caixinha", "bug", "ponteiro", "caixinha")
    MINI_CHEFES = ((120, "caixinha"), (210, "ponteiro"))


PROVAS = (ProvaDeCalculo, ProvaDeArquiteturaEED, ProvaDeTDEPOO)


def semestre():
    """As três provas em ordem, cada uma uma instância nova."""
    return [classe() for classe in PROVAS]
