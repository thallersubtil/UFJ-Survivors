import pygame

from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import ControleRicochete


class Controle(ArmaDeDisparo):
    """Arma inicial do Gamer: arremessa o controle, que ricocheteia de inimigo em inimigo."""
    NOME = "Controle"
    ICONE = "icones/controle.png"
    DESCRICAO = "Arremessa o controle, que ricocheteia de um inimigo para outro."
    ATRIBUTOS = {
        "dano": (13, 15, 17, 19, 21, 24, 28),
        "ricochetes": (2, 2, 3, 3, 4, 4, 6),
        "quantidade": (1, 1, 1, 2, 2, 2, 2),
        "recarga": (0.9, 0.85, 0.85, 0.8, 0.75, 0.7, 0.6),
    }
    MELHORIAS = (
        "Mais dano e recarga menor.",
        "Mais 1 ricochete.",
        "Mais 1 controle (modo cooperativo).",
        "Mais 1 ricochete e mais dano.",
        "Mais dano e recarga menor.",
        "Combo infinito: muito mais ricochetes.",
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
            jogo.adicionar(ControleRicochete(dono.posicao, direcao * self.VELOCIDADE,
                                             self.valor("dano") * dono.multiplicador_dano, self.valor("ricochetes")))
        Recursos.tocar("disparo", 0.12)
        return True
