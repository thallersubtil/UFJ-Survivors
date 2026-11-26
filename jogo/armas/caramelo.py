import math

from jogo.ajudantes.ajudantes import CachorroCaramelo
from jogo.armas.arma import ArmaSemMunicao

from jogo.formas_supremas import CachorroDaMatilha


class Caramelo(ArmaSemMunicao):
    NOME = "Caramelo"
    ICONE = "sprites/caramelo.png"
    DESCRICAO = "Um vira-lata caramelo corre em volta de você e morde quem chega perto."
    ATRIBUTOS = {
        "quantidade": (1, 2, 3, 5),
        "dano": (7, 9, 12, 22),
        "raio": (70, 80, 95, 125),
        "velocidade": (3.0, 3.4, 3.8, 6.0),
    }
    MELHORIAS = (
        "Mais 1 caramelo, voltas mais rápidas e mais dano.",
        "Mais 1 caramelo, voltas maiores e mais dano.",
        "MATILHA DOURADA: 5 caramelos bem maiores, que mordem mais longe, dão voltas maiores e muito mais rápidas.",
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
        classe = CachorroDaMatilha if self.no_maximo else CachorroCaramelo      # no máximo: maiores e mais rápidos
        self.cachorros = [classe(dono, 2 * math.pi * i / quantidade, self) for i in range(quantidade)]
        for cachorro in self.cachorros:
            self.lancar(jogo, cachorro)

    def ao_remover(self, jogo):
        for cachorro in self.cachorros:
            cachorro.remover()
        self.cachorros = []
