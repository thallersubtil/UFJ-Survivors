import pygame

from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import ControleRicochete

from jogo.formas_supremas import ControleLendario


class Controle(ArmaDeDisparo):
    """Arma inicial do Gamer: arremessa o controle, que ricocheteia de inimigo em inimigo."""
    NOME = "Controle"
    ICONE = "icones/controle.png"
    DESCRICAO = "Arremessa o controle, que ricocheteia de um inimigo para outro."
    EXCLUSIVA = True
    ATRIBUTOS = {
        "dano": (13, 17, 22, 38),
        "ricochetes": (2, 3, 4, 9),
        "quantidade": (1, 1, 2, 3),
        "recarga": (0.9, 0.85, 0.75, 0.5),
    }
    MELHORIAS = (
        "Mais 1 ricochete, mais dano e recarga menor.",
        "Mais 1 controle (modo cooperativo), mais 1 ricochete e mais dano.",
        "COMBO INFINITO: cada ricochete aumenta o dano em 20% (são 9) e o último acerto explode.",
    )
    VELOCIDADE = 520
    ALCANCE = 600

    def disparar(self, jogo, dono):
        alvo = jogo.inimigo_mais_proximo(dono.posicao, self.ALCANCE)
        rumo = (alvo.posicao - dono.posicao) if alvo is not None else pygame.Vector2(dono.direcao_mira)
        rumo = rumo.normalize() if rumo.length_squared() > 0 else pygame.Vector2(1, 0)
        quantidade = self.valor("quantidade")
        for i in range(quantidade):
            direcao = rumo.rotate((i - (quantidade - 1) / 2) * 25)
            self.lancar(jogo, (ControleLendario if self.no_maximo else ControleRicochete)(dono.posicao, direcao * self.VELOCIDADE,
                                             self.valor("dano") * dono.multiplicador_dano, self.valor("ricochetes")))
        Recursos.tocar("disparo", 0.12)
        return True
