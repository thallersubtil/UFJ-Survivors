"""Base das passivas de classe: um efeito permanente que cresce com o nível do aluno."""
from abc import ABC, abstractmethod


class Passiva(ABC):
    NOME = "Passiva"
    DESCRICAO = ""

    @abstractmethod
    def aplicar(self, jogador):
        """Soma o efeito desta passiva (no nível atual do jogador) aos atributos dele."""

    def __str__(self):
        return self.NOME
