"""Conquistas: metas que pagam moedas uma vez só, conferidas no fim de cada partida (fora do treino).

Cada conquista herda de Conquista e diz em `alcancada` se a partida que acabou a cumpriu.
Algumas olham o placar; outras, os marcos que a partida anotou em `jogo.marcos`
(pego colando, greve, colab, bigorna).
"""
from abc import ABC, abstractmethod


class Conquista(ABC):
    CHAVE = ""
    NOME = "Conquista"
    DESCRICAO = ""
    PREMIO = 50

    @abstractmethod
    def alcancada(self, jogo, progresso):
        """Se a partida `jogo` cumpriu esta conquista."""


class PassouEmCalculo(Conquista):
    CHAVE = "primeira_prova"
    NOME = "Passou em Cálculo"
    DESCRICAO = "Vença a primeira prova."
    PREMIO = 50

    def alcancada(self, jogo, progresso):
        return jogo.provas_vencidas >= 1


class SemestreAprovado(Conquista):
    CHAVE = "semestre"
    NOME = "Semestre Aprovado"
    DESCRICAO = "Vença as três provas."
    PREMIO = 300

    def alcancada(self, jogo, progresso):
        return jogo.venceu


class Combo67(Conquista):
    CHAVE = "combo_67"
    NOME = "67!"
    DESCRICAO = "Faça um combo 67."
    PREMIO = 67

    def alcancada(self, jogo, progresso):
        return jogo.placar.combos_67 >= 1


class MilBugsDepois(Conquista):
    CHAVE = "mil_eliminacoes"
    NOME = "Mil Bugs Depois"
    DESCRICAO = "Elimine 1000 inimigos numa partida."
    PREMIO = 100

    def alcancada(self, jogo, progresso):
        return jogo.placar.eliminacoes >= 1000


class Veterano(Conquista):
    CHAVE = "nivel_40"
    NOME = "Veterano"
    DESCRICAO = "Chegue ao nível 25 numa partida."
    PREMIO = 100

    def alcancada(self, jogo, progresso):
        return jogo.jogador.nivel >= 25


class ConquistaDeMarco(Conquista):
    """Conquista cumprida quando a partida anotou o marco de mesma CHAVE."""

    def alcancada(self, jogo, progresso):
        return self.CHAVE in jogo.marcos


class TrabalhoEmGrupo(ConquistaDeMarco):
    CHAVE = "colab"
    NOME = "Trabalho em Grupo"
    DESCRICAO = "Faça uma colab."
    PREMIO = 80


class PegoNoFlagra(ConquistaDeMarco):
    CHAVE = "pego_colando"
    NOME = "Pego no Flagra"
    DESCRICAO = "Seja pego colando."
    PREMIO = 30


class GreveGeral(ConquistaDeMarco):
    CHAVE = "greve"
    NOME = "Greve Geral"
    DESCRICAO = "Chegue ao fim de uma greve."
    PREMIO = 40


class ArmaLendaria(ConquistaDeMarco):
    CHAVE = "bigorna_max"
    NOME = "Arma Lendária"
    DESCRICAO = "Afie a mesma arma 3 vezes na Bigorna."
    PREMIO = 120


class TodoMundoNaSala(Conquista):
    CHAVE = "todas_as_classes"
    NOME = "Todo Mundo na Sala"
    DESCRICAO = "Jogue com todas as classes (conta entre as partidas)."
    PREMIO = 150

    def alcancada(self, jogo, progresso):
        from jogo.jogador.classes import CLASSES
        return {c.__name__ for c in CLASSES} <= progresso.classes_jogadas


CONQUISTAS = (PassouEmCalculo, SemestreAprovado, Combo67, MilBugsDepois, Veterano, TrabalhoEmGrupo, PegoNoFlagra,
              GreveGeral, ArmaLendaria, TodoMundoNaSala)


class Conquistas:
    @staticmethod
    def verificar(jogo, progresso):
        """Registra a classe jogada, marca as conquistas novas, paga os prêmios e devolve as novas."""
        progresso.registrar_classe(type(jogo.jogador).__name__)
        novas = [c() for c in CONQUISTAS if c.CHAVE not in progresso.conquistas and c().alcancada(jogo, progresso)]
        for conquista in novas:
            progresso.registrar_conquista(conquista.CHAVE)
            progresso.ganhar(conquista.PREMIO)
        return novas
