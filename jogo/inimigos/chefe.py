"""Base dos chefes: alternam ataques e ficam furiosos com pouca vida."""
from abc import ABC, abstractmethod

from jogo.inimigos.inimigo import Inimigo


class Chefe(Inimigo, ABC):
    CHANCE_CAFE = 0.0
    CHANCE_POCAO = 0.0
    INTERVALO_ATAQUE = 2.6
    INTERVALO_FURIOSO = 1.6
    DISTANCIA_PREFERIDA = 260

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, 1.0)
        self.reposiciona = False
        self._espera_ataque = 2.0
        self._indice = 0
        self.acao_atual = None

    @property
    def furioso(self):
        return self.vida < self.vida_maxima / 2

    @abstractmethod
    def ataques(self):
        """Lista de ataques (métodos que recebem o jogo), usados em sequência."""

    def mover(self, dt, jogo):
        if self.acao_atual is not None:
            if self.acao_atual(dt, jogo):
                self.acao_atual = None
            return
        if self.posicao.distance_to(jogo.jogador.posicao) > self.DISTANCIA_PREFERIDA:
            self.ir_em_direcao(jogo.jogador.posicao, dt)
        self._espera_ataque -= dt
        if self._espera_ataque <= 0:
            lista = self.ataques()
            lista[self._indice % len(lista)](jogo)
            self._indice += 1
            self._espera_ataque = self.INTERVALO_FURIOSO if self.furioso else self.INTERVALO_ATAQUE

    def possuir(self, duracao):
        """Chefes não são possuídos pelo Fusca."""

    def empurrar(self, direcao, forca=180):
        super().empurrar(direcao, forca * 0.1)
