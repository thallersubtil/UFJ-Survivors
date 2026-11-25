from jogo.ajudantes.ajudantes import QuadroBrancoNoChao
from jogo.armas.arma import ArmaSemMunicao


class QuadroBranco(ArmaSemMunicao):
    """Arma inicial do Monitor: desenha uma área no chão que atrasa e fere os inimigos."""
    NOME = "Quadro Branco"
    ICONE = "icones/quadro_branco.png"
    DESCRICAO = "Desenha uma área no chão, onde está o inimigo mais perto: quem entra anda devagar e leva dano."
    ATRIBUTOS = {
        "dano": (4, 5, 6, 7, 8, 9, 11),
        "raio": (70, 75, 80, 85, 95, 100, 115),
        "duracao": (3.0, 3.5, 3.5, 4.0, 4.0, 4.5, 5.0),
        "recarga": (4.5, 4.3, 4.1, 3.9, 3.6, 3.4, 3.0),
        "quantidade": (1, 1, 1, 1, 2, 2, 2),
    }
    MELHORIAS = (
        "Mais dano e área maior.",
        "Dura mais.",
        "Mais dano e área maior.",
        "Mais dano e área maior.",
        "Mais 1 área; dura mais e volta mais rápido.",
        "Mais dano, área maior e dura mais.",
    )
    ALCANCE = 450

    def __init__(self):
        super().__init__()
        self._espera = 0.5

    def atualizar(self, dt, jogo, dono):
        self._espera -= dt
        if self._espera > 0:
            return
        self._espera = self.valor("recarga") * dono.multiplicador_recarga
        perto = sorted(jogo.inimigos_proximos(dono.posicao, self.ALCANCE),
                       key=lambda e: e.posicao.distance_squared_to(dono.posicao))
        alvos = [e.posicao for e in perto[:self.valor("quantidade")]] or [dono.posicao]
        for alvo in alvos:
            jogo.adicionar(QuadroBrancoNoChao(dono, self, alvo))
