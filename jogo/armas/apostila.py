from jogo.ajudantes.ajudantes import FolhaDaApostila
from jogo.armas.arma import ArmaSemMunicao

from jogo.formas_supremas import BolaDeConteudo


class Apostila(ArmaSemMunicao):
    """Folhas que giram em volta do aluno por alguns segundos, somem e voltam."""
    NOME = "Apostila"
    ICONE = "icones/apostila.png"
    DESCRICAO = "Folhas da apostila giram em volta de você de tempos em tempos e ferem quem encosta."
    ATRIBUTOS = {
        "folhas": (1, 2, 2, 2),
        "dano": (11, 13, 17, 34),
        "raio": (70, 80, 90, 120),
        "duracao": (3.0, 3.5, 4.0, 3.4),
        "pausa": (2.0, 1.8, 1.5, 1.8),
    }
    MELHORIAS = (
        "Mais uma folha, mais dano e folhas mais afastadas.",
        "Mais dano; giram por mais tempo e voltam mais rápido.",
        "BOLA DE NEVE DE CONTEÚDO: a matéria acumulada vira duas bolas de papel que rolam pela tela crescendo e atropelando tudo.",
    )

    def __init__(self):
        super().__init__()
        self.folhas = []
        self._espera = 0.0

    def atualizar(self, dt, jogo, dono):
        if any(f.ativo for f in self.folhas):
            return
        self._espera -= dt / dono.multiplicador_recarga
        if self._espera > 0:
            return
        total = self.valor("folhas")
        if self.no_maximo:                      # bola de neve de conteúdo: rola pela tela crescendo
            dano = self.valor("dano") * dono.multiplicador_dano
            for i in range(total):
                direcao = dono.direcao_mira.rotate(i * 360 / total)
                self.lancar(jogo, BolaDeConteudo(dono.posicao, direcao, dano, self.valor("duracao")))
            self._espera = self.valor("pausa")
            return
        self.folhas = [FolhaDaApostila(dono, self, i, total, self.valor("duracao")) for i in range(total)]
        for folha in self.folhas:
            self.lancar(jogo, folha)
        self._espera = self.valor("pausa")

    def ao_remover(self, jogo):
        for folha in self.folhas:
            folha.remover()
        self.folhas = []
