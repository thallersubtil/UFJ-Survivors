"""Cálculo I: limites em leque, derivada (investida pela tangente) e integral em espiral."""
from jogo.inimigos.materias.materia import Materia


class CalculoI(Materia):
    NOME = "Cálculo I"
    COR = (255, 168, 60)
    SIMBOLO = "dx"
    VIDA = 2600
    INTERVALO_ATAQUE = 2.6
    INTERVALO_FURIOSO = 1.7
    LACAIOS = ("calculadora", "pi", "bug")

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
        self.rajada(chefe, 3, 0.3, lambda i: self.anel(chefe, jogo, quantidade, giro=i * 10, velocidade=220))

    def chamar_lacaios(self, chefe, jogo):
        self.chamada(chefe, jogo, 8 if chefe.furioso else 6, "LISTA DE EXERCÍCIOS!")
