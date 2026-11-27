"""Base das habilidades de classe: aparecem nas cartas de nível, como armas e itens, e têm 3 níveis.

Cada classe oferece três (`Jogador.criar_habilidades`) e o aluno começa sem nenhuma. Uma habilidade soma um
efeito fixo em `aplicar` (chamado com os itens ao recalcular os atributos) e reage à partida pelos ganchos de
`ReageAoJogo` (acertar, eliminar, ser atingido, rolar, a cada quadro).
"""
from abc import ABC, abstractmethod

from jogo.jogador.reacao import ReageAoJogo


class Habilidade(ReageAoJogo, ABC):
    NOME = "Habilidade"
    DESCRICAO = ""
    ICONE = ""
    NIVEL_MAXIMO = 3
    MELHORIAS = ()               # o que muda no nível 2 e no 3
    PESO = 1.0                   # chance relativa de aparecer nas cartas

    def __init__(self):
        self._nivel = 1

    @property
    def nivel(self):
        return self._nivel

    @nivel.setter
    def nivel(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("o nível deve ser um número inteiro")
        if not 1 <= valor <= self.NIVEL_MAXIMO:
            raise ValueError(f"o nível de {self.NOME} vai de 1 a {self.NIVEL_MAXIMO}")
        self._nivel = valor

    @property
    def no_maximo(self):
        return self._nivel >= self.NIVEL_MAXIMO

    def subir_nivel(self):
        self.nivel = self._nivel + 1

    def descricao_proxima(self):
        return "" if self.no_maximo else self.MELHORIAS[self._nivel - 1]

    def valor(self, por_nivel):
        """O número deste nível numa tupla de três (um por nível)."""
        return por_nivel[self._nivel - 1]

    @abstractmethod
    def aplicar(self, jogador):
        """Soma o efeito fixo desta habilidade (no nível atual) aos atributos do jogador. Quem só reage a
        eventos não soma nada aqui."""

    @property
    def contador(self):
        """Um texto curto para o HUD (ex.: "COMBO 23/50"), ou None."""
        return None

    def __str__(self):
        return f"{self.NOME} (nível {self._nivel})"
