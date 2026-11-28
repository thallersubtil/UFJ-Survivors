from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import CobraProjetil

from jogo.formas_supremas import CobraRei


class CobraPython(ArmaDeDisparo):
    NOME = "Cobra Python"
    ICONE = "sprites/cobra.png"
    DESCRICAO = "Dispara cobrinhas que avançam serpenteando na direção da mira."
    ATRIBUTOS = {
        "dano": (10, 14, 18, 30),
        "quantidade": (1, 2, 3, 5),
        "perfuracao": (1, 2, 3, 8),
        "recarga": (1.0, 0.9, 0.8, 0.55),
    }
    MELHORIAS = (
        "Mais 1 cobra, mais dano e atravessa mais 1 inimigo.",
        "Mais 1 cobra, mais dano e atravessa mais 1 inimigo.",
        "COBRA-REI: 5 cobras coroadas, bem maiores e 60% mais rápidas, que atravessam 8 inimigos com muito mais dano.",
    )
    VELOCIDADE = 430
    FATOR_COBRA_REI = 1.6          # a Cobra-Rei voa bem mais rápido (e mais longe)
    ABERTURA = 12

    def disparar(self, jogo, dono):
        quantidade = self.valor("quantidade")
        dano = self.valor("dano") * dono.multiplicador_dano
        for i in range(quantidade):
            direcao = dono.direcao_mira.rotate((i - (quantidade - 1) / 2) * self.ABERTURA)
            classe = CobraRei if self.no_maximo else CobraProjetil      # no máximo: maiores e mais rápidas
            velocidade = self.VELOCIDADE * (self.FATOR_COBRA_REI if self.no_maximo else 1)
            self.lancar(jogo, classe(dono.posicao, direcao * velocidade, dano,
                                     perfuracao=self.valor("perfuracao")))
        Recursos.tocar("disparo", 0.15)
