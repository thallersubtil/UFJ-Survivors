from jogo.ajudantes.ajudantes import FolhaDaApostila
from jogo.armas.arma import ArmaSemMunicao


class Apostila(ArmaSemMunicao):
    """Folhas que giram em volta do aluno por alguns segundos, somem e voltam."""
    NOME = "Apostila"
    ICONE = "icones/apostila.png"
    DESCRICAO = "Folhas da apostila giram em volta de você de tempos em tempos e ferem quem encosta."
    ATRIBUTOS = {
        "folhas": (1, 1, 2, 2, 2, 3, 3),
        "dano": (8, 9, 10, 12, 13, 15, 18),
        "raio": (70, 75, 80, 85, 90, 95, 105),
        "duracao": (3.0, 3.0, 3.5, 3.5, 4.0, 4.0, 5.0),
        "pausa": (3.0, 3.0, 2.5, 2.5, 2.0, 2.0, 1.5),
    }
    MELHORIAS = (
        "Mais dano e folhas mais afastadas.",
        "Mais uma folha.",
        "Mais dano; as folhas giram por mais tempo.",
        "Mais dano; voltam mais rápido.",
        "Mais uma folha.",
        "Edição revisada: mais dano, mais tempo girando e menos pausa.",
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
        self.folhas = [FolhaDaApostila(dono, self, i, total, self.valor("duracao")) for i in range(total)]
        for folha in self.folhas:
            jogo.adicionar(folha)
        self._espera = self.valor("pausa")

    def ao_remover(self, jogo):
        for folha in self.folhas:
            folha.remover()
        self.folhas = []
