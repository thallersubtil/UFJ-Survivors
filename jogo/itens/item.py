"""Base dos itens passivos."""
from abc import ABC, abstractmethod


class Item(ABC):
    NOME = "Item"
    DESCRICAO = ""
    ICONE = ""
    NIVEL_MAXIMO = 3
    MELHORIAS = ()

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

    @abstractmethod
    def aplicar(self, jogador):
        """Soma o efeito deste item (no nível atual) aos atributos do jogador."""

    def __str__(self):
        return f"{self.NOME} (nível {self._nivel})"
