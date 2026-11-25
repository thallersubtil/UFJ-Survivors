import pygame

from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import PequiArremessado


class PequiExplosivo(ArmaDeDisparo):
    NOME = "Pequi Explosivo"
    ICONE = "icones/pequi.png"
    DESCRICAO = "Arremessa um pequi no inimigo mais perto. Ele estoura e espalha espinhos em volta."
    PRECO_DESBLOQUEIO = 400
    ATRIBUTOS = {
        "dano": (14, 16, 18, 21, 24, 27, 32),
        "raio": (70, 75, 85, 90, 100, 110, 125),
        "quantidade": (1, 1, 1, 2, 2, 2, 3),
        "recarga": (1.6, 1.5, 1.4, 1.4, 1.3, 1.2, 1.1),
    }
    MELHORIAS = (
        "Mais dano e recarga menor.",
        "Estouro maior.",
        "Mais 1 pequi.",
        "Mais dano e estouro maior.",
        "Mais dano e recarga menor.",
        "Mais 1 pequi e estouro bem maior.",
    )
    VELOCIDADE = 420
    ALCANCE = 450

    def disparar(self, jogo, dono):
        alvo = jogo.inimigo_mais_proximo(dono.posicao, self.ALCANCE)
        if alvo is None:
            return False
        rumo = alvo.posicao - dono.posicao
        rumo = rumo.normalize() if rumo.length_squared() > 0 else pygame.Vector2(1, 0)
        quantidade = self.valor("quantidade")
        for i in range(quantidade):
            direcao = rumo.rotate((i - (quantidade - 1) / 2) * 25)
            jogo.adicionar(PequiArremessado(dono.posicao, direcao * self.VELOCIDADE,
                                            self.valor("dano") * dono.multiplicador_dano, self.valor("raio")))
        Recursos.tocar("disparo", 0.12)
        return True
