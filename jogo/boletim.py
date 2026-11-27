"""Boletim do semestre: uma nota por prova, calculada a partir do que aconteceu na partida."""
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
        self.linhas = [self._linha(jogo, i, fase) for i, fase in enumerate(jogo.fases)]

    @staticmethod
    def nota_de_aprovacao(jogador):
        """Passou na prova: 6 a 10, conforme a vida que sobrou quando o chefe caiu."""
        return round(Boletim.MEDIA_PARA_PASSAR + 4 * max(0.0, jogador.vida / jogador.vida_maxima), 1)

    @staticmethod
    def nota_contra_o_chefe(chefe):
        """Caiu com o chefe da prova em campo: de 4 a 5,9, pelo dano que já tinha feito nele."""
        return round(4 + (Boletim.NOTA_MAXIMA_REPROVADO - 4) * (1 - chefe.vida / chefe.vida_maxima), 1)

    @staticmethod
    def nota_pelo_tempo(fase):
        """Caiu antes de o chefe chegar: até 4, pelo tempo de prova que aguentou."""
        return round(4 * min(1.0, fase.tempo / fase.DURACAO), 1)

    @classmethod
    def _linha(cls, jogo, i, fase):
        """A linha da prova `i`. Como os chefes chegam no relógio, pode haver mais de uma prova em
        aberto: toda prova cujo chefe está vivo conta como reprovada, e a que ainda corria também."""
        disciplina = (getattr(fase, "ROTULO", "") or fase.MATERIA or fase.NOME).replace(" -> ", " e ")
        if i in jogo.notas:
            return LinhaDoBoletim(disciplina, jogo.notas[i], "APROVADO")
        chefe = jogo.chefe_da_prova(i)
        if chefe is not None:
            return LinhaDoBoletim(disciplina, cls.nota_contra_o_chefe(chefe), "REPROVADO")
        if fase is jogo.fase:
            return LinhaDoBoletim(disciplina, cls.nota_pelo_tempo(fase), "REPROVADO")
        return LinhaDoBoletim(disciplina, None, "NÃO CURSOU")

    @property
    def media(self):
        notas = [linha.nota for linha in self.linhas if linha.nota is not None]
        return round(sum(notas) / len(notas), 1) if notas else 0.0
