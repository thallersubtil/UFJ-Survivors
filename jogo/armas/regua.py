"""Régua de 1 Metro: golpe corpo a corpo em arco, na direção da mira."""
from jogo.ajudantes.golpes import ArcoDaRegua
from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos


class ReguaDeUmMetro(ArmaDeDisparo):
    NOME = "Régua de 1 Metro"
    ICONE = "icones/regua.png"
    DESCRICAO = "Uma régua de madeira que varre um arco na frente do aluno, na direção da mira."
    ATRIBUTOS = {
        "dano": (18, 24, 31, 50),
        "alcance": (110, 120, 135, 150),
        "abertura": (100, 110, 120, 130),      # graus do arco
        "recarga": (1.1, 1.0, 0.9, 0.75),
    }
    MELHORIAS = (
        "Mais dano e mais alcance.",
        "Arco mais largo, mais dano e recarga menor.",
        "IDA E VOLTA: a régua bate na frente e, no mesmo golpe, atrás de você.",
    )

    def disparar(self, jogo, dono):
        alcance = self.valor("alcance")
        if jogo.inimigo_mais_proximo(dono.posicao, alcance) is None:
            return False                       # não gasta o golpe no vazio
        direcoes = [dono.direcao_mira]
        if self.no_maximo:
            direcoes.append(-dono.direcao_mira)
        for direcao in direcoes:
            self.lancar(jogo, ArcoDaRegua(dono, direcao, alcance, self.valor("abertura"),
                                          self.valor("dano") * dono.multiplicador_dano))
        Recursos.tocar("disparo", 0.12)
        return True
