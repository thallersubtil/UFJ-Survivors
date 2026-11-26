"""Passivas das classes. Cada uma soma seu efeito em Jogador.recalcular_atributos()."""
from jogo.jogador.passiva import Passiva


class InstintoOtaku(Passiva):
    NOME = "Instinto Otaku"
    DESCRICAO = "Chance de acerto crítico (dano em dobro) que cresce a cada nível."
    BASE = 0.03
    POR_NIVEL = 0.016
    MAXIMO = 0.5

    def aplicar(self, jogador):
        jogador.chance_critico += min(self.MAXIMO, self.BASE + self.POR_NIVEL * (jogador.nivel - 1))


class Cafeinado(Passiva):
    NOME = "Cafeinado"
    DESCRICAO = "Armas recarregam 1,6% mais rápido por nível (até 30%) e o café rende mais."
    POR_NIVEL = 0.016
    MAXIMO = 0.30
    CAFE = 1.25

    def aplicar(self, jogador):
        jogador.mult_recarga *= 1 - min(self.MAXIMO, self.POR_NIVEL * (jogador.nivel - 1))
        jogador.mult_cafe *= self.CAFE


class RolagemDeIniciativa(Passiva):
    NOME = "Rolagem de Iniciativa"
    DESCRICAO = "O especial recarrega 3,2% mais rápido por nível (até 60%)."
    POR_NIVEL = 0.032
    MAXIMO = 0.60

    def aplicar(self, jogador):
        jogador.mult_especial *= 1 - min(self.MAXIMO, self.POR_NIVEL * (jogador.nivel - 1))


class PlantaoDeDuvidas(Passiva):
    NOME = "Plantão de Dúvidas"
    DESCRICAO = "Recupera vida aos poucos e puxa as notas de mais longe; os dois crescem a cada nível."
    REGENERACAO_BASE = 0.1
    REGENERACAO_POR_NIVEL = 0.032
    REGENERACAO_MAXIMA = 0.7
    COLETA_POR_NIVEL = 0.032
    COLETA_MAXIMA = 0.6

    def aplicar(self, jogador):
        n = jogador.nivel - 1
        jogador.regeneracao += min(self.REGENERACAO_MAXIMA, self.REGENERACAO_BASE + self.REGENERACAO_POR_NIVEL * n)
        jogador.alcance_coleta *= 1 + min(self.COLETA_MAXIMA, self.COLETA_POR_NIVEL * n)


class Reflexo(Passiva):
    NOME = "Reflexo"
    DESCRICAO = "O rolamento recarrega 10% mais rápido, e mais 2,4% a cada nível (até 55%)."
    BASE = 0.10
    POR_NIVEL = 0.024
    MAXIMO = 0.55

    def aplicar(self, jogador):
        jogador.mult_rolamento *= 1 - min(self.MAXIMO, self.BASE + self.POR_NIVEL * (jogador.nivel - 1))


class SedeDeAprender(Passiva):
    NOME = "Sede de Aprender"
    DESCRICAO = "+10% de experiência, e mais 1,6% a cada nível (até +40%)."
    BASE = 0.10
    POR_NIVEL = 0.016
    MAXIMO = 0.40

    def aplicar(self, jogador):
        jogador.mult_experiencia += min(self.MAXIMO, self.BASE + self.POR_NIVEL * (jogador.nivel - 1))


class CaronaSolidaria(Passiva):
    NOME = "Carona Solidária"
    DESCRICAO = "Inimigo que morre possuído (atropelado) pode deixar uma moeda: 10%, e mais 1,6% por nível (até 40%)."
    BASE = 0.10
    POR_NIVEL = 0.016
    MAXIMO = 0.40

    def aplicar(self, jogador):
        jogador.chance_carona += min(self.MAXIMO, self.BASE + self.POR_NIVEL * (jogador.nivel - 1))
