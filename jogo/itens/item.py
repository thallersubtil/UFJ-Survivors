"""Base dos itens passivos."""
from abc import ABC, abstractmethod


class Item(ABC):
    NOME = "Item"
    DESCRICAO = ""
    ICONE = ""
    NIVEL_MAXIMO = 3
    MELHORIAS = ()
    PRECO_DESBLOQUEIO = 0      # > 0: só aparece nas cartas depois de comprado no Centro Acadêmico
    SO_AO_SUBIR_DE_NIVEL = False   # True: só nas cartas de nível, nunca como prêmio do baú

    def __init__(self):
        self._nivel = 1

    @classmethod
    def liberada(cls, desbloqueios):
        """Se pode aparecer nas cartas, dado o conjunto de nomes de classes desbloqueadas."""
        return cls.PRECO_DESBLOQUEIO <= 0 or cls.__name__ in desbloqueios

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

    def atualizar(self, dt, jogador, jogo):
        """Chamado a cada quadro. Só itens com efeito ativo (ex.: Convite da Atlética) usam."""

    def ao_subir_de_nivel(self, jogador, jogo):
        """Chamado a cada nível que o herói sobe. A maioria dos itens não faz nada."""

    @abstractmethod
    def aplicar(self, jogador):
        """Soma o efeito deste item (no nível atual) aos atributos do jogador."""

    def __str__(self):
        return f"{self.NOME} (nível {self._nivel})"
