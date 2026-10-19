"""Arquitetura de Computadores: pulsos de clock, barramento de bits e interrupções."""
from jogo.inimigos.materias.materia import Materia


class ArquiteturaDeComputadores(Materia):
    NOME = "Arquitetura de Computadores"
    COR = (90, 200, 255)
    SIMBOLO = "1"
    VIDA = 2400
    INTERVALO_ATAQUE = 2.6
    INTERVALO_FURIOSO = 1.7
    LACAIOS = ("mouse", "pente_ram", "bug")

    def ataques(self):
        return [self.clock, self.barramento, self.busca, self.interrupcao]

    def clock(self, chefe, jogo):
        """Anéis de bits em pulsos, como o sinal de clock: 0, 1, 0..."""
        vezes = 4 if chefe.furioso else 3
        self.rajada(chefe, vezes, 0.45,
                    lambda i: self.anel(chefe, jogo, 8, giro=i * 22.5, simbolo="01"[i % 2], velocidade=240))

    def barramento(self, chefe, jogo):
        """Uma fileira de bits lado a lado, viajando juntos na direção do herói."""
        quantidade = 13 if chefe.furioso else 9
        direcao = chefe.mirar(jogo)
        lado = direcao.rotate(90)
        for i in range(quantidade):
            origem = chefe.posicao + lado * (i - (quantidade - 1) / 2) * 30
            self.lancar(chefe, jogo, direcao, simbolo="01"[i % 2], origem=origem, velocidade=260)

    def busca(self, chefe, jogo):
        """Ciclo de busca: avança até o herói como quem vai buscar a próxima instrução."""
        chefe.investir(2 if chefe.furioso else 1)

    def interrupcao(self, chefe, jogo):
        self.chamada(chefe, jogo, 8 if chefe.furioso else 6, "INTERRUPÇÃO!")
