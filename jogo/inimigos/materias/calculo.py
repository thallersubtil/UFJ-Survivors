"""Cálculo I (limites, derivada e integral) e Cálculo II (séries, integral dupla e convergência)."""
import pygame

from jogo.inimigos.materias.materia import Materia


class CalculoI(Materia):
    NOME = "Cálculo I"
    COR = (255, 168, 60)
    SIMBOLO = "dx"
    VIDA = 3400
    INTERVALO_ATAQUE = 2.6
    INTERVALO_FURIOSO = 1.7
    LACAIOS = ("calculadora", "pi", "bug")
    ARTES = {"lim": "lim", "dx": "dx", "∫": "integral", "π": "pi"}
    ARTE_DA_CHAMADA = "esquadro"

    def ataques(self):
        return [self.limite, self.derivada, self.integral, self.chamar_lacaios]

    def limite(self, chefe, jogo):
        """Leque de "lim" na direção do herói."""
        self.leque(chefe, jogo, 11 if chefe.furioso else 7, simbolo="lim")

    def derivada(self, chefe, jogo):
        """Investida em linha reta, como uma reta tangente; duas seguidas quando furioso."""
        chefe.investir(2 if chefe.furioso else 1)

    def integral(self, chefe, jogo):
        """Três anéis de "dx", cada um girado um pouco: forma uma espiral."""
        quantidade = 12 if chefe.furioso else 10
        self.rajada(chefe, 3, 0.3, lambda i: self.anel(chefe, jogo, quantidade, giro=i * 10, velocidade=220,
                                                       simbolo=("dx", "∫", "dx")[i]))

    def chamar_lacaios(self, chefe, jogo):
        self.chamada(chefe, jogo, 8 if chefe.furioso else 6, "LISTA DE EXERCÍCIOS!")


class CalculoII(Materia):
    """A segunda matéria do professor de Cálculo: séries, integral dupla e a convergência que fecha o cerco."""

    NOME = "Cálculo II"
    COR = (240, 90, 50)
    SIMBOLO = "Σ"                # os termos da série (desenhados como um gráfico subindo)
    VIDA = 4200
    INTERVALO_ATAQUE = 2.2
    INTERVALO_FURIOSO = 1.4
    DANO_PROJETIL = 13
    VELOCIDADE_PROJETIL = 320
    LACAIOS = ("calculadora", "pi")
    ARTES = {"Σ": "grafico", "lim": "lim", "∫": "integral", "π": "pi"}
    ARTE_DA_CHAMADA = "esquadro"
    RAIO_DA_CONVERGENCIA = 430      # a que distância do aluno nascem os termos da série que converge nele

    def ataques(self):
        return [self.serie_de_taylor, self.integral_dupla, self.convergencia, self.derivada_segunda,
                self.prova_substitutiva]

    def serie_de_taylor(self, chefe, jogo):
        """Leques cada vez mais abertos, como os termos de uma série: 3, 5, 7 (e 9 quando furioso)."""
        termos = (3, 5, 7, 9) if chefe.furioso else (3, 5, 7)
        self.rajada(chefe, len(termos), 0.35, lambda i: self.leque(chefe, jogo, termos[i], abertura=9, simbolo="Σ"))

    def integral_dupla(self, chefe, jogo):
        """Anéis de integrais girando para lados opostos, um depois do outro: forma uma trama."""
        quantidade = 12 if chefe.furioso else 10
        self.rajada(chefe, 4, 0.3, lambda i: self.anel(chefe, jogo, quantidade, giro=(1 if i % 2 else -1) * i * 9,
                                                       velocidade=210, simbolo="∫"))

    def convergencia(self, chefe, jogo):
        """Os termos nascem num círculo em volta do aluno e convergem para ele: é preciso sair pelo vão."""
        quantidade = 16 if chefe.furioso else 12
        vao = jogo.rng.uniform(0, 360)
        for i in range(quantidade):
            direcao = pygame.Vector2(1, 0).rotate(vao + 360 * (i + 0.5) / (quantidade + 1))
            origem = jogo.jogador.posicao + direcao * self.RAIO_DA_CONVERGENCIA
            self.lancar(chefe, jogo, -direcao, simbolo="lim", velocidade=170, origem=origem)
        self.gritar(chefe, jogo, "CONVERGE!")

    def derivada_segunda(self, chefe, jogo):
        """Investidas seguidas: a derivada da derivada muda de direção mais vezes."""
        chefe.investir(4 if chefe.furioso else 3)

    def prova_substitutiva(self, chefe, jogo):
        self.chamada(chefe, jogo, 8 if chefe.furioso else 6, "PROVA SUBSTITUTIVA!")
