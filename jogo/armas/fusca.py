from jogo.ajudantes.ajudantes import FuscaVeiculo
from jogo.armas.arma import ArmaContinua
from jogo.nucleo.recursos import Recursos

from jogo.formas_supremas import FuscaMonstro


class FuscaAzul(ArmaContinua):
    NOME = "Fusca Azul"
    ICONE = "sprites/fusca.png"
    DESCRICAO = "Um fusca azul atravessa a tela. Quem é atropelado sai socando os outros inimigos."
    ATRIBUTOS = {
        "recarga": (7.0, 6.0, 5.0, 2.8),
        "quantidade": (1, 2, 2, 2),
        "possessao": (3.0, 3.5, 4.5, 7.0),
        "dano": (8, 12, 17, 30),
    }
    MELHORIAS = (
        "Mais 1 fusca, possessão mais longa e recarga menor.",
        "Mais dano, possessão mais longa e recarga menor.",
        "FUSCA MONSTRO: dois fuscas de rodas gigantes cruzam a tela esmagando várias vezes quem fica embaixo; possessão de 7 s.",
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
            self.lancar(jogo, (FuscaMonstro if self.no_maximo else FuscaVeiculo)((x, y), 1 if da_esquerda else -1, self.valor("possessao"),
                                        self.valor("dano") * dono.multiplicador_dano))
        Recursos.tocar("buzina", 0.5)
