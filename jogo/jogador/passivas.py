"""Passivas das classes. Cada uma soma seu efeito em Jogador.recalcular_atributos()."""
from jogo.jogador.passiva import Passiva


class InstintoOtaku(Passiva):
    NOME = "Instinto Otaku"
    DESCRICAO = "Chance de acerto crítico (dano em dobro) que cresce a cada nível."
    BASE = 0.03
    POR_NIVEL = 0.01
    MAXIMO = 0.5

    def aplicar(self, jogador):
        jogador.chance_critico += min(self.MAXIMO, self.BASE + self.POR_NIVEL * (jogador.nivel - 1))


class Cafeinado(Passiva):
    NOME = "Cafeinado"
    DESCRICAO = "Armas recarregam 1% mais rápido por nível (até 30%) e o café rende mais."
    POR_NIVEL = 0.01
    MAXIMO = 0.30
    CAFE = 1.25

    def aplicar(self, jogador):
        jogador.mult_recarga *= 1 - min(self.MAXIMO, self.POR_NIVEL * (jogador.nivel - 1))
        jogador.mult_cafe *= self.CAFE


class RolagemDeIniciativa(Passiva):
    NOME = "Rolagem de Iniciativa"
    DESCRICAO = "O especial recarrega 2% mais rápido por nível (até 60%)."
    POR_NIVEL = 0.02
    MAXIMO = 0.60

    def aplicar(self, jogador):
        jogador.mult_especial *= 1 - min(self.MAXIMO, self.POR_NIVEL * (jogador.nivel - 1))
