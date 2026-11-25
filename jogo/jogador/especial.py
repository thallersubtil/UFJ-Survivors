"""Base dos ataques especiais (tecla Espaço)."""
from abc import ABC, abstractmethod


class Especial(ABC):
    NOME = "Especial"
    DESCRICAO = ""
    ICONE = ""
    RECARGA = 60.0

    def __init__(self):
        self.restante = 0.0          # tempo até a próxima carga
        self.cargas = 1
        self._cargas_maximas = 1     # o Pendrive guarda mais cargas

    @property
    def cargas_maximas(self):
        return self._cargas_maximas

    @cargas_maximas.setter
    def cargas_maximas(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:
            raise ValueError("o especial guarda pelo menos 1 carga")
        self._cargas_maximas = valor
        self.cargas = min(self.cargas, valor)

    @property
    def pronto(self):
        return self.cargas > 0

    @property
    def progresso(self):
        """Quanto falta para a próxima carga (1 quando não há nada recarregando)."""
        return max(0.0, min(1.0, 1 - self.restante / self.RECARGA))

    def atualizar(self, dt, mult_recarga=1.0):
        if self.cargas < self._cargas_maximas and self.restante <= 0:
            self.restante = self.RECARGA
        if self.restante <= 0:
            return
        self.restante = max(0.0, self.restante - dt / mult_recarga)
        if self.restante <= 0 and self.cargas < self._cargas_maximas:
            self.cargas += 1
            if self.cargas < self._cargas_maximas:
                self.restante = self.RECARGA

    def usar(self, dono, jogo):
        if not self.pronto:
            return False
        self.ativar(dono, jogo)
        self.cargas -= 1
        if self.restante <= 0:
            self.restante = self.RECARGA
        return True

    @abstractmethod
    def ativar(self, dono, jogo):
        """Efeito do especial."""
