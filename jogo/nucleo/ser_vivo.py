"""Entidades com vida."""
from abc import ABC
from numbers import Real

from jogo.nucleo.entidade import Entidade


def exigir_numero(valor, nome):
    """Recusa o que não for número (bool também é recusado)."""
    if isinstance(valor, bool) or not isinstance(valor, Real):
        raise TypeError(f"{nome} deve ser um número, recebeu {valor!r}")


class SerVivo(Entidade, ABC):
    """Entidade com vida. A vida nunca fica abaixo de 0 nem acima do máximo."""

    DURACAO_PISCAR = 0.12

    def __init__(self, posicao, raio, vida_maxima):
        super().__init__(posicao, raio)
        self._vida = None
        self.vida_maxima = vida_maxima
        self._vida = self._vida_maxima
        self.piscar = 0.0

    @property
    def vida_maxima(self):
        return self._vida_maxima

    @vida_maxima.setter
    def vida_maxima(self, valor):
        exigir_numero(valor, "vida_maxima")
        if valor <= 0:
            raise ValueError("vida_maxima deve ser positiva")
        self._vida_maxima = valor
        if self._vida is not None:
            self._vida = min(self._vida, valor)

    @property
    def vida(self):
        return self._vida

    @vida.setter
    def vida(self, valor):
        exigir_numero(valor, "vida")
        self._vida = max(0, min(valor, self._vida_maxima))

    @property
    def esta_vivo(self):
        return self._vida > 0

    def receber_dano(self, quantidade):
        """Tira vida. Retorna True só no golpe que matou."""
        exigir_numero(quantidade, "dano")
        if quantidade < 0:
            raise ValueError("dano não pode ser negativo")
        estava_vivo = self.esta_vivo
        self.vida = self._vida - quantidade
        self.piscar = self.DURACAO_PISCAR
        return estava_vivo and not self.esta_vivo

    def curar(self, quantidade):
        exigir_numero(quantidade, "cura")
        if quantidade < 0:
            raise ValueError("cura não pode ser negativa")
        self.vida = self._vida + quantidade
