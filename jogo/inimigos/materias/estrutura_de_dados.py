"""Estrutura de Dados em C: ponteiros selvagens, segmentation fault e pilhas."""
from jogo.inimigos.materias.materia import Materia


class EstruturaDeDadosEmC(Materia):
    NOME = "Estrutura de Dados em C"
    COR = (110, 240, 130)
    SIMBOLO = "*p"
    VIDA = 3400
    INTERVALO_ATAQUE = 2.2
    INTERVALO_FURIOSO = 1.3
    DANO_PROJETIL = 14
    VELOCIDADE_PROJETIL = 340
    LACAIOS = ("ponteiro", "pilha", "pente_ram")

    def ataques(self):
        return [self.ponteiro_selvagem, self.segmentation_fault, self.empilhar, self.alocar]

    def ponteiro_selvagem(self, chefe, jogo):
        """Investidas seguidas, mudando de direção, como um ponteiro sem rumo."""
        chefe.investir(4 if chefe.furioso else 3, carga=0.6, velocidade=820)

    def segmentation_fault(self, chefe, jogo):
        """Explode um anel de NULL e manda um leque rápido de ponteiros no herói."""
        self.anel(chefe, jogo, 16 if chefe.furioso else 12, simbolo="NULL", velocidade=230)
        self.leque(chefe, jogo, 5, abertura=10, velocidade=420)

    def empilhar(self, chefe, jogo):
        """Uma fila de "[]" sempre mirada no herói: cada novo vai para o topo da pilha."""
        vezes = 9 if chefe.furioso else 6
        self.rajada(chefe, vezes, 0.12, lambda i: self.lancar(chefe, jogo, chefe.mirar(jogo), simbolo="[]"))

    def alocar(self, chefe, jogo):
        self.chamada(chefe, jogo, 9 if chefe.furioso else 7, "MALLOC!")
