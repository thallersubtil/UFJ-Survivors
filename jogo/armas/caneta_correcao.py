"""Caneta de Correção: a arma exclusiva do Monitor. Estocadas que marcam o inimigo com um X."""
from jogo.ajudantes.golpes import EstocadaDaCaneta, XDeCorrecao
from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos


class CanetaDeCorrecao(ArmaDeDisparo):
    NOME = "Caneta de Correção"
    ICONE = "icones/caneta_vermelha.png"
    DESCRICAO = "Estocadas da caneta vermelha na direção da mira: quem leva fica marcado com um X e apanha mais."
    EXCLUSIVA = True
    ATRIBUTOS = {
        "dano": (8, 10, 13, 22),
        "estocadas": (3, 4, 5, 6),
        "alcance": (100, 110, 120, 135),
        "marca": (0.20, 0.25, 0.30, 0.40),     # dano a mais em quem está marcado com o X
        "recarga": (0.9, 0.85, 0.75, 0.6),
    }
    MELHORIAS = (
        "Mais 1 estocada, mais dano e o X pesa mais.",
        "Mais 1 estocada, mais alcance e recarga menor.",
        "CORREÇÃO EM MASSA: a última estocada risca no chão um X gigante, que fere quem está nele.",
    )
    DURACAO_DA_MARCA = 4.0
    RAIO_DO_X = 70
    DANO_DO_X = 0.6                            # fração do dano da estocada, a cada toque do X
    DURACAO_DO_X = 2.5

    def disparar(self, jogo, dono):
        alcance = self.valor("alcance")
        if jogo.inimigo_mais_proximo(dono.posicao, alcance) is None:
            return False
        dano = self.valor("dano") * dono.multiplicador_dano
        rastro = None
        if self.no_maximo:
            def rastro(ponta):
                return XDeCorrecao(ponta, self.RAIO_DO_X, dano * self.DANO_DO_X, self.DURACAO_DO_X)
        self.lancar(jogo, EstocadaDaCaneta(dono, dono.direcao_mira, alcance, dano, self.valor("estocadas"),
                                           (self.DURACAO_DA_MARCA, self.valor("marca")), rastro))
        Recursos.tocar("disparo", 0.1)
        return True
