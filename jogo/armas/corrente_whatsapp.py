"""Corrente de WhatsApp: acerta o inimigo mais perto e é encaminhada de inimigo em inimigo."""
from jogo.ajudantes.golpes import ElosDaCorrente, corrente
from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos


class CorrenteDeWhatsApp(ArmaDeDisparo):
    NOME = "Corrente de WhatsApp"
    ICONE = "icones/wifi.png"
    DESCRICAO = "\"Encaminhe para 10 amigos\": acerta o inimigo mais perto e pula para os vizinhos, sem repetir."
    ATRIBUTOS = {
        "dano": (14, 18, 23, 37),
        "saltos": (3, 4, 5, 8),
        "recarga": (1.4, 1.3, 1.15, 0.9),
    }
    MELHORIAS = (
        "Mais 1 encaminhamento e mais dano.",
        "Mais 1 encaminhamento, mais dano e recarga menor.",
        "VIRALIZOU: oito encaminhamentos, e cada um bate 10% mais forte que o anterior.",
    )
    ALCANCE = 380
    ALCANCE_DO_SALTO = 200
    CRESCIMENTO = 0.10                         # no nível máximo, quanto cada encaminhamento cresce

    def disparar(self, jogo, dono):
        dano = self.valor("dano") * dono.multiplicador_dano
        cresce = self.CRESCIMENTO if self.no_maximo else 0.0
        acertos = []

        def acertar(inimigo):
            jogo.causar_dano(inimigo, dano * (1 + cresce * len(acertos)), inimigo.posicao - dono.posicao)
            acertos.append(inimigo)

        pontos = corrente(jogo, dono.posicao, self.ALCANCE, self.valor("saltos"), self.ALCANCE_DO_SALTO, acertar)
        if not pontos:
            return False
        elos = ElosDaCorrente(pontos)
        self.lancar(jogo, elos)
        Recursos.tocar("disparo", 0.12)
        return True
