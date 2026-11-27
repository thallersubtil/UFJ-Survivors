"""Boletim do semestre: uma nota por prova do calendário, calculada a partir do que aconteceu na partida."""
from dataclasses import dataclass


@dataclass
class LinhaDoBoletim:
    disciplina: str
    nota: object          # float de 0 a 10, ou None se a prova não chegou a acontecer
    situacao: str         # APROVADO, REPROVADO ou NÃO CURSOU

    @property
    def aprovado(self):
        return self.situacao == "APROVADO"

    @property
    def nota_texto(self):
        return "-" if self.nota is None else f"{self.nota:.1f}".replace(".", ",")


class Boletim:
    MEDIA_PARA_PASSAR = 6.0
    NOTA_MAXIMA_REPROVADO = 5.9

    def __init__(self, jogo):
        self.linhas = [self._linha(jogo, prova) for prova in jogo.fase.provas]

    @staticmethod
    def nota_de_aprovacao(jogador):
        """Passou na prova: 6 a 10, conforme a vida que sobrou quando o chefe caiu."""
        return round(Boletim.MEDIA_PARA_PASSAR + 4 * max(0.0, jogador.vida / jogador.vida_maxima), 1)

    @staticmethod
    def nota_contra_o_chefe(chefe):
        """Caiu com o chefe da prova em campo: de 4 a 5,9, pelo dano que já tinha feito nele."""
        return round(4 + (Boletim.NOTA_MAXIMA_REPROVADO - 4) * (1 - chefe.vida / chefe.vida_maxima), 1)

    @staticmethod
    def nota_pelo_tempo(prova, tempo):
        """Caiu antes de o chefe chegar: até 4, pelo tempo daquela prova que aguentou."""
        duracao = max(1.0, prova.hora - prova.inicio)
        return round(4 * min(1.0, max(0.0, tempo - prova.inicio) / duracao), 1)

    @classmethod
    def _linha(cls, jogo, prova):
        """A linha da `prova`. Como os chefes chegam no relógio, pode haver mais de uma em aberto: toda
        prova cujo chefe está vivo conta como reprovada, e a que ainda corria também."""
        disciplina = prova.rotulo.replace(" -> ", " e ")
        if prova in jogo.notas:
            return LinhaDoBoletim(disciplina, jogo.notas[prova], "APROVADO")
        chefe = jogo.chefe_da_prova(prova)
        if chefe is not None:
            return LinhaDoBoletim(disciplina, cls.nota_contra_o_chefe(chefe), "REPROVADO")
        if prova.inicio <= jogo.fase.tempo < prova.hora:
            return LinhaDoBoletim(disciplina, cls.nota_pelo_tempo(prova, jogo.fase.tempo), "REPROVADO")
        return LinhaDoBoletim(disciplina, None, "NÃO CURSOU")

    @property
    def media(self):
        notas = [linha.nota for linha in self.linhas if linha.nota is not None]
        return round(sum(notas) / len(notas), 1) if notas else 0.0
