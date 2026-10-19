"""Programação Orientada a Objetos: a fase final. Herança, polimorfismo, encapsulamento e new."""
from jogo.inimigos.materias.materia import Materia


class ProgramacaoOrientadaAObjetos(Materia):
    NOME = "Programação Orientada a Objetos"
    COR = (255, 96, 128)
    SIMBOLO = "{}"
    VIDA = 3800
    INTERVALO_ATAQUE = 2.2
    INTERVALO_FURIOSO = 1.3
    DANO_PROJETIL = 14
    VELOCIDADE_PROJETIL = 320
    LACAIOS = ("caixinha", "bug")
    DURACAO_ESCUDO = 2.5

    def __init__(self):
        self._forma = 0

    def ataques(self):
        return [self.polimorfismo, self.heranca, self.encapsulamento, self.instanciar, self.polimorfismo]

    def polimorfismo(self, chefe, jogo):
        """O mesmo ataque muda de forma a cada vez: ora leque de "new", ora anel de "self"."""
        if self._forma == 0:
            self.leque(chefe, jogo, 11 if chefe.furioso else 7, simbolo="new")
        else:
            self.anel(chefe, jogo, 14 if chefe.furioso else 10, simbolo="self", velocidade=250)
        self._forma = 1 - self._forma

    def heranca(self, chefe, jogo):
        """Caixinhas que, ao morrer, deixam caixinhas filhas."""
        self.chamada(chefe, jogo, 8 if chefe.furioso else 6, "HERANÇA!")

    def encapsulamento(self, chefe, jogo):
        """Fica protegido (atributo privado!) e solta um anel de chaves."""
        chefe.proteger(self.DURACAO_ESCUDO)
        self.anel(chefe, jogo, 12, velocidade=240)
        self.gritar(chefe, jogo, "PRIVADO!")

    def instanciar(self, chefe, jogo):
        """Uma sequência de "new" mirada no herói."""
        vezes = 8 if chefe.furioso else 5
        self.rajada(chefe, vezes, 0.15, lambda i: self.lancar(chefe, jogo, chefe.mirar(jogo), simbolo="new"))
