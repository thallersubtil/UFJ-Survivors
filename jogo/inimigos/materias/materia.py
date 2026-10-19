"""Matéria: o que possui um professor e o transforma em chefe.

A matéria decide o nome do chefe, a cor da aura, a vida e os ataques. O chefe
(ChefePossuido) só contém uma ou mais matérias e usa os ataques da matéria atual.
"""
from abc import ABC, abstractmethod

import pygame

from jogo.config import Cor
from jogo.efeitos import TextoFlutuante
from jogo.inimigos.acoes_do_chefe import Rajada
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.projeteis.projeteis import ProjetilDaMateria


class Materia(ABC):
    NOME = "Matéria"
    COR = (255, 255, 255)        # aura do chefe e borda dos projéteis
    SIMBOLO = "?"                # símbolo padrão dos projéteis
    VIDA = 3000
    INTERVALO_ATAQUE = 2.6
    INTERVALO_FURIOSO = 1.6
    DANO_PROJETIL = 12
    VELOCIDADE_PROJETIL = 300
    LACAIOS = ("bug",)           # quem aparece na chamada

    @abstractmethod
    def ataques(self):
        """Métodos `(chefe, jogo)` que o chefe usa em sequência."""

    def __str__(self):
        return self.NOME

    # Ataques prontos que cada matéria combina do seu jeito

    def lancar(self, chefe, jogo, direcao, simbolo=None, velocidade=None, dano=None, origem=None):
        velocidade = velocidade or self.VELOCIDADE_PROJETIL
        jogo.adicionar(ProjetilDaMateria(origem if origem is not None else chefe.posicao,
                                         pygame.Vector2(direcao) * velocidade,
                                         dano or self.DANO_PROJETIL, simbolo or self.SIMBOLO, self.COR))

    def leque(self, chefe, jogo, quantidade, abertura=12, **opcoes):
        """Projéteis em leque, centrados na direção do herói."""
        base = chefe.mirar(jogo)
        for i in range(quantidade):
            self.lancar(chefe, jogo, base.rotate((i - (quantidade - 1) / 2) * abertura), **opcoes)

    def anel(self, chefe, jogo, quantidade, giro=0.0, **opcoes):
        """Projéteis em círculo, para todos os lados."""
        for i in range(quantidade):
            self.lancar(chefe, jogo, pygame.Vector2(1, 0).rotate(giro + 360 * i / quantidade), **opcoes)

    def rajada(self, chefe, vezes, intervalo, disparo):
        """O chefe para e executa `disparo(i)` várias vezes seguidas."""
        chefe.executar(Rajada(vezes, intervalo, disparo))

    def chamada(self, chefe, jogo, quantidade, texto="CHAMADA!"):
        """Lacaios da matéria aparecem em volta do chefe."""
        for i in range(quantidade):
            posicao = chefe.posicao + pygame.Vector2(140, 0).rotate(360 * i / quantidade)
            nome = jogo.rng.choice(self.LACAIOS)
            jogo.adicionar(FabricaDeInimigos.criar(nome, posicao, jogo.fase.escala_dificuldade))
        self.gritar(chefe, jogo, texto)

    def gritar(self, chefe, jogo, texto):
        jogo.adicionar(TextoFlutuante(texto, chefe.posicao - (0, 80), Cor.DESTAQUE, 22, duracao=1.2))
