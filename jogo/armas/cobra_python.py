from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import CobraProjetil


class CobraPython(ArmaDeDisparo):
    NOME = "Cobra Python"
    ICONE = "sprites/cobra.png"
    DESCRICAO = "Dispara cobrinhas que avançam serpenteando na direção da mira."
    ATRIBUTOS = {
        "dano": (10, 12, 14, 14, 17, 17, 22),
        "quantidade": (1, 1, 2, 2, 3, 3, 4),
        "perfuracao": (1, 2, 2, 3, 3, 4, 5),
        "recarga": (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.65),
    }
    MELHORIAS = (
        "Atravessa mais 1 inimigo.",
        "Mais 1 cobra por disparo.",
        "Atravessa mais 1 inimigo.",
        "Mais 1 cobra e mais dano.",
        "Atravessa mais 1 inimigo.",
        "Mais 1 cobra, mais dano e recarga menor.",
    )
    VELOCIDADE = 430
    ABERTURA = 12

    def disparar(self, jogo, dono):
        quantidade = self.valor("quantidade")
        dano = self.valor("dano") * dono.multiplicador_dano
        for i in range(quantidade):
            direcao = dono.direcao_mira.rotate((i - (quantidade - 1) / 2) * self.ABERTURA)
            jogo.adicionar(CobraProjetil(dono.posicao, direcao * self.VELOCIDADE, dano,
                                         perfuracao=self.valor("perfuracao")))
        Recursos.tocar("disparo", 0.15)
        return True
