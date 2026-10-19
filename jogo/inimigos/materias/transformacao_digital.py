"""Transformação Digital: a matéria mais tranquila. E-mails em massa, nuvem e reuniões."""
from jogo.inimigos.materias.materia import Materia


class TransformacaoDigital(Materia):
    NOME = "Transformação Digital"
    COR = (190, 140, 255)
    SIMBOLO = "@"
    VIDA = 2200
    INTERVALO_ATAQUE = 2.9
    INTERVALO_FURIOSO = 2.0
    DANO_PROJETIL = 10
    VELOCIDADE_PROJETIL = 220
    LACAIOS = ("bug", "mouse", "caixinha")

    def ataques(self):
        return [self.email_em_massa, self.nuvem, self.reuniao]

    def email_em_massa(self, chefe, jogo):
        """Leque largo e lento de "@"."""
        self.leque(chefe, jogo, 11 if chefe.furioso else 9, abertura=16)

    def nuvem(self, chefe, jogo):
        """Tudo vai para a nuvem: um anel lento de "www"."""
        self.anel(chefe, jogo, 12 if chefe.furioso else 10, simbolo="www", velocidade=160)

    def reuniao(self, chefe, jogo):
        self.chamada(chefe, jogo, 6 if chefe.furioso else 5, "REUNIÃO!")
