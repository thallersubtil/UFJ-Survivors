import math

from jogo.ajudantes.ajudantes import CachorroCaramelo
from jogo.armas.arma import ArmaDeContato


class Caramelo(ArmaDeContato):
    NOME = "Caramelo"
    ICONE = "sprites/caramelo.png"
    DESCRICAO = "Um vira-lata caramelo corre em volta de você e morde quem chega perto."
    ATRIBUTOS = {
        "quantidade": (1, 2, 2, 3, 3, 4, 4),
        "dano": (7, 8, 9, 10, 12, 13, 16),
        "raio": (70, 75, 80, 90, 95, 100, 115),
        "velocidade": (3.0, 3.0, 3.4, 3.4, 3.8, 3.8, 4.3),
    }
    MELHORIAS = (
        "Mais 1 caramelo.",
        "Voltas mais rápidas e mais dano.",
        "Mais 1 caramelo.",
        "Voltas mais rápidas e maiores.",
        "Mais 1 caramelo.",
        "Mais dano, voltas maiores e mais rápidas.",
    )

    def __init__(self):
        super().__init__()
        self.cachorros = []

    def atualizar(self, dt, jogo, dono):
        if len(self.cachorros) != self.valor("quantidade"):
            self._recriar(jogo, dono)

    def _recriar(self, jogo, dono):
        self.ao_remover(jogo)
        quantidade = self.valor("quantidade")
        self.cachorros = [CachorroCaramelo(dono, 2 * math.pi * i / quantidade, self) for i in range(quantidade)]
        for cachorro in self.cachorros:
            jogo.adicionar(cachorro)

    def ao_remover(self, jogo):
        for cachorro in self.cachorros:
            cachorro.remover()
        self.cachorros = []
