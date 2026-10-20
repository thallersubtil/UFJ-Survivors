from jogo.ajudantes.ajudantes import FuscaVeiculo
from jogo.armas.arma import ArmaDeContato
from jogo.nucleo.recursos import Recursos


class FuscaAzul(ArmaDeContato):
    NOME = "Fusca Azul"
    ICONE = "sprites/fusca.png"
    DESCRICAO = "Um fusca azul atravessa a tela. Quem é atropelado sai socando os outros inimigos."
    ATRIBUTOS = {
        "recarga": (7.0, 6.5, 6.0, 5.5, 5.0, 4.5, 3.5),
        "quantidade": (1, 1, 2, 2, 2, 3, 3),
        "possessao": (3.0, 3.5, 3.5, 4.0, 4.5, 5.0, 6.0),
        "dano": (8, 10, 12, 14, 16, 18, 22),
    }
    MELHORIAS = (
        "Possessão mais longa e recarga menor.",
        "Mais 1 fusca.",
        "Possessão mais longa e recarga menor.",
        "Possessão mais longa e recarga menor.",
        "Mais 1 fusca e possessão mais longa.",
        "Possessão bem mais longa e recarga menor.",
    )

    def __init__(self):
        super().__init__()
        self._espera = 2.0

    def atualizar(self, dt, jogo, dono):
        self._espera -= dt
        if self._espera <= 0:
            self._soltar(jogo, dono)
            self._espera = self.valor("recarga") * dono.multiplicador_recarga

    def _soltar(self, jogo, dono):
        tela = jogo.camera.retangulo
        for _ in range(self.valor("quantidade")):
            da_esquerda = jogo.rng.random() < 0.5
            y = jogo.rng.uniform(tela.top + 60, tela.bottom - 40)
            x = tela.left - 120 if da_esquerda else tela.right + 120
            jogo.adicionar(FuscaVeiculo((x, y), 1 if da_esquerda else -1, self.valor("possessao"),
                                        self.valor("dano") * dono.multiplicador_dano))
        Recursos.tocar("buzina", 0.5)
