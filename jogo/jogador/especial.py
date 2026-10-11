"""Base dos ataques especiais (tecla Espaço)."""
from abc import ABC, abstractmethod


class Especial(ABC):
    NOME = "Especial"
    DESCRICAO = ""
    ICONE = ""
    RECARGA = 60.0

    def __init__(self):
        self.restante = 0.0

    @property
    def pronto(self):
        return self.restante <= 0

    @property
    def progresso(self):
        return max(0.0, min(1.0, 1 - self.restante / self.RECARGA))

    def atualizar(self, dt, mult_recarga=1.0):
        self.restante = max(0.0, self.restante - dt / mult_recarga)

    def usar(self, dono, jogo):
        if not self.pronto:
            return False
        self.ativar(dono, jogo)
        self.restante = self.RECARGA
        return True

    @abstractmethod
    def ativar(self, dono, jogo):
        """Efeito do especial."""
