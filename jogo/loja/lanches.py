"""Lanches da Cantina: comprados no Centro Acadêmico, valem só para a próxima partida (um por vez).

Têm a mesma interface das melhorias (`aplicar(jogador)`), então o Jogador recebe o lanche
junto com elas e não precisa saber qual é (polimorfismo).
"""
from abc import ABC, abstractmethod


class Lanche(ABC):
    CHAVE = ""                 # nome guardado no arquivo de progresso
    NOME = "Lanche"
    DESCRICAO = ""
    ICONE = ""
    PRECO = 60

    @abstractmethod
    def aplicar(self, jogador):
        """Soma o efeito do lanche aos atributos do jogador durante a partida."""


class PaoDeQueijo(Lanche):
    CHAVE = "pao_de_queijo"
    NOME = "Pão de Queijo"
    DESCRICAO = "Próxima partida: +20 de vida máxima."
    ICONE = "icones/pao_de_queijo.png"
    VIDA = 20

    def aplicar(self, jogador):
        jogador.vida_maxima_extra += self.VIDA


class Coxinha(Lanche):
    CHAVE = "coxinha"
    NOME = "Coxinha"
    DESCRICAO = "Próxima partida: +15% de experiência."
    ICONE = "sprites/nota.png"
    PRECO = 80

    def aplicar(self, jogador):
        jogador.mult_experiencia += 0.15


class CafeCoado(Lanche):
    CHAVE = "cafe_coado"
    NOME = "Café Coado"
    DESCRICAO = "Próxima partida: armas recarregam 10% mais rápido."
    ICONE = "icones/garrafa.png"
    PRECO = 70

    def aplicar(self, jogador):
        jogador.mult_recarga *= 0.9


class Acai(Lanche):
    CHAVE = "acai"
    NOME = "Açaí"
    DESCRICAO = "Próxima partida: +10% de velocidade."
    ICONE = "icones/energetico.png"

    def aplicar(self, jogador):
        jogador.mult_velocidade += 0.10


class Pastel(Lanche):
    CHAVE = "pastel"
    NOME = "Pastel de Feira"
    DESCRICAO = "Próxima partida: +10% de dano."
    ICONE = "icones/caderno.png"
    PRECO = 80

    def aplicar(self, jogador):
        jogador.mult_dano += 0.10


LANCHES = (PaoDeQueijo, Coxinha, CafeCoado, Acai, Pastel)
