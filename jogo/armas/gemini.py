import pygame

from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import EstrelaGemini


class Gemini(ArmaDeDisparo):
    NOME = "Gemini"
    ICONE = "sprites/estrela_gemini.png"
    DESCRICAO = "Atira uma estrela que se divide em duas ao acertar. Gêmeos, entendeu?"
    ATRIBUTOS = {
        "dano": (12, 14, 16, 18, 20, 23, 27),
        "quantidade": (1, 1, 1, 2, 2, 2, 3),
        "geracoes": (1, 1, 2, 2, 2, 3, 3),
        "recarga": (1.3, 1.2, 1.2, 1.1, 1.0, 1.0, 0.9),
    }
    MELHORIAS = (
        "Mais dano e recarga menor.",
        "As estrelas se dividem mais uma vez.",
        "Mais 1 estrela.",
        "Mais dano e recarga menor.",
        "As estrelas se dividem mais uma vez.",
        "Mais 1 estrela e mais dano.",
    )
    VELOCIDADE = 380
    ALCANCE = 600

    def disparar(self, jogo, dono):
        alvo = jogo.inimigo_mais_proximo(dono.posicao, self.ALCANCE)
        rumo = (alvo.posicao - dono.posicao) if alvo is not None else pygame.Vector2(dono.direcao_mira)
        rumo = rumo.normalize() if rumo.length_squared() > 0 else pygame.Vector2(1, 0)
        quantidade = self.valor("quantidade")
        for i in range(quantidade):
            direcao = rumo.rotate((i - (quantidade - 1) / 2) * 20)
            jogo.adicionar(EstrelaGemini(dono.posicao, direcao * self.VELOCIDADE,
                                         self.valor("dano") * dono.multiplicador_dano, geracoes=self.valor("geracoes")))
        Recursos.tocar("disparo", 0.12)
        return True
