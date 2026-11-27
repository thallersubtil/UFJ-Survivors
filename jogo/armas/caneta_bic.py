"""Caneta Bic: estocadas rápidas na direção da mira."""
from jogo.ajudantes.golpes import EstocadaDaCaneta
from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos


class CanetaBic(ArmaDeDisparo):
    NOME = "Caneta Bic"
    ICONE = "icones/caneta_vermelha.png"
    DESCRICAO = "Estocadas rápidas de caneta na direção da mira. Curta, mas não para."
    ATRIBUTOS = {
        "dano": (7, 9, 12, 20),
        "estocadas": (3, 4, 5, 6),
        "alcance": (95, 105, 115, 130),
        "recarga": (0.9, 0.85, 0.75, 0.6),
    }
    MELHORIAS = (
        "Mais 1 estocada e mais dano.",
        "Mais 1 estocada, mais alcance e recarga menor.",
        "TINTA VAZOU: a última estocada de cada série deixa no chão uma poça de tinta que fere quem pisa.",
    )
    RAIO_DA_POCA = 48
    DANO_DA_POCA = 0.6                         # fração do dano da estocada, a cada toque da poça
    DURACAO_DA_POCA = 2.5

    def disparar(self, jogo, dono):
        alcance = self.valor("alcance")
        if jogo.inimigo_mais_proximo(dono.posicao, alcance) is None:
            return False
        dano = self.valor("dano") * dono.multiplicador_dano
        poca = (self.RAIO_DA_POCA, dano * self.DANO_DA_POCA, self.DURACAO_DA_POCA) if self.no_maximo else None
        self.lancar(jogo, EstocadaDaCaneta(dono, dono.direcao_mira, alcance, dano, self.valor("estocadas"), poca))
        Recursos.tocar("disparo", 0.1)
        return True
