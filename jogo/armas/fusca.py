import pygame

from jogo.ajudantes.ajudantes import FuscaVeiculo
from jogo.ajudantes.golpes import mais_cheio
from jogo.armas.arma import ArmaContinua
from jogo.nucleo.recursos import Recursos

from jogo.formas_supremas import FuscaMonstro


class FuscaAzul(ArmaContinua):
    NOME = "Fusca Azul"
    ICONE = "sprites/fusca.png"
    DESCRICAO = "Um fusca azul atravessa a tela pelo meio da muvuca (ou em cima do chefe). Quem é atropelado sai socando os outros inimigos."
    EXCLUSIVA = True
    ATRIBUTOS = {
        "recarga": (5.0, 4.5, 4.0, 2.5),
        "quantidade": (1, 2, 2, 2),
        "possessao": (3.0, 3.5, 4.5, 7.0),
        "dano": (14, 18, 24, 39),            # a suprema com pelo menos 1,6x o dano do nível 3
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

    FOLGA_DO_BOLO = 60           # o fusca cruza até esta distância (para cima ou para baixo) da altura do alvo

    def _soltar(self, jogo, dono):
        """Cruza a tela na altura do chefe ou mini-chefe na tela mais perto do aluno; sem nenhum, na do maior bolo
        de inimigos (com um sorteio pequeno em volta); sem ninguém na tela, numa altura qualquer dela."""
        tela = jogo.camera.retangulo
        bolo = self._altura_do_alvo(jogo, tela)
        for _ in range(self.valor("quantidade")):
            da_esquerda = jogo.rng.random() < 0.5
            if bolo is None:
                y = jogo.rng.uniform(tela.top + 60, tela.bottom - 40)
            else:
                y = bolo.y + jogo.rng.uniform(-self.FOLGA_DO_BOLO, self.FOLGA_DO_BOLO)
                y = max(tela.top + 60, min(tela.bottom - 40, y))
            x = tela.left - 120 if da_esquerda else tela.right + 120
            self.lancar(jogo, (FuscaMonstro if self.no_maximo else FuscaVeiculo)((x, y), 1 if da_esquerda else -1, self.valor("possessao"),
                                        self.valor("dano") * dono.multiplicador_dano))
        Recursos.tocar("buzina", 0.5)

    @staticmethod
    def _altura_do_alvo(jogo, tela):
        """O ponto que o fusca mira: o chefe ou mini-chefe visível mais perto do aluno, senão o maior bolo."""
        chefes = [e for e in jogo.inimigos if e.ativo and e.CHEFE and tela.collidepoint(e.posicao)]
        if chefes:
            return min(chefes, key=lambda e: e.posicao.distance_squared_to(jogo.jogador.posicao)).posicao
        return mais_cheio(jogo, pygame.Vector2(tela.center), max(tela.width, tela.height) / 2)
