from jogo.ajudantes.ajudantes import QuadroBrancoNoChao
from jogo.armas.arma import ArmaContinua

from jogo.formas_supremas import AulaMagna


class QuadroBranco(ArmaContinua):
    """Arma inicial do Monitor: desenha uma área no chão que atrasa e fere os inimigos."""
    NOME = "Quadro Branco"
    ICONE = "icones/quadro_branco.png"
    DESCRICAO = "Desenha uma área no chão, onde está o inimigo mais perto: quem entra anda devagar e leva dano."
    ATRIBUTOS = {
        "dano": (4, 6, 8, 15),
        "raio": (70, 80, 95, 135),
        "duracao": (3.0, 3.5, 4.0, 6.0),
        "recarga": (4.5, 4.1, 3.6, 2.4),
        "quantidade": (1, 1, 2, 3),
    }
    MELHORIAS = (
        "Mais dano, área maior e dura mais.",
        "Mais 1 área; mais dano e volta mais rápido.",
        "AULA MAGNA: as áreas viram redemoinhos de matéria que puxam os inimigos para o centro e não deixam sair.",
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
            self.lancar(jogo, (AulaMagna if self.no_maximo else QuadroBrancoNoChao)(dono, self, alvo))
