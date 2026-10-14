from jogo.ajudantes.ajudantes import MascoteFlutuante
from jogo.armas.arma import ArmaDeContato
from jogo.efeitos import GolpeClaude
from jogo.nucleo.recursos import Recursos


class MascoteClaude(ArmaDeContato):
    NOME = "Mascote do Claude"
    ICONE = "sprites/claude.png"
    DESCRICAO = "Pensa por um instante e acerta um golpe forte no inimigo com mais vida."
    ATRIBUTOS = {
        "pensar": (3.0, 2.7, 2.4, 2.1, 1.8, 1.6, 1.3),
        "dano": (45, 55, 65, 80, 95, 115, 150),
        "area": (0, 0, 0, 70, 80, 95, 120),
    }
    MELHORIAS = (
        "Pensa mais rápido e bate mais forte.",
        "Pensa mais rápido e bate mais forte.",
        "O golpe passa a causar dano em área.",
        "Pensa mais rápido e área maior.",
        "Pensa mais rápido e área maior.",
        "Pensa bem mais rápido, área e dano maiores.",
    )
    ALCANCE = 600
    DESLOCAMENTO = (38, -46)

    def __init__(self):
        super().__init__()
        self.progresso = 0.0
        self.mascote = None

    def atualizar(self, dt, jogo, dono):
        if self.mascote is None:
            self.mascote = MascoteFlutuante(dono, self.ICONE, 34, self.DESLOCAMENTO, barra=lambda: self.progresso,
                                            pasta="claude")
            jogo.adicionar(self.mascote)
        self.progresso = min(1.0, self.progresso + dt / (self.valor("pensar") * dono.mult_recarga))
        if self.progresso < 1.0:
            return
        alvo = jogo.inimigo_com_mais_vida(dono.posicao, self.ALCANCE)
        if alvo is not None:
            self._golpear(jogo, dono, alvo)
            self.progresso = 0.0

    def _golpear(self, jogo, dono, alvo):
        dano = self.valor("dano") * dono.multiplicador_dano
        area = self.valor("area")
        centro = alvo.posicao.copy()
        jogo.causar_dano(alvo, dano, forte=True)
        jogo.adicionar(GolpeClaude(centro, max(area, 40)))
        if area:
            for outro in jogo.inimigos_proximos(centro, area):
                if outro is not alvo:
                    jogo.causar_dano(outro, dano * 0.5, outro.posicao - centro)
        Recursos.tocar("claude", 0.4)

    def ao_remover(self, jogo):
        if self.mascote is not None:
            self.mascote.remover()
            self.mascote = None
