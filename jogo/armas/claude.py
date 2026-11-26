from jogo.ajudantes.ajudantes import MascoteFlutuante
from jogo.armas.arma import ArmaSemMunicao
from jogo.efeitos import GolpeClaude
from jogo.formas_supremas import golpe_em_cadeia
from jogo.nucleo.recursos import Recursos


class MascoteClaude(ArmaSemMunicao):
    NOME = "Mascote do Claude"
    ICONE = "sprites/claude.png"
    DESCRICAO = "Pensa por um instante e acerta um golpe forte no inimigo com mais vida."
    ATRIBUTOS = {
        "pensar": (3.0, 2.4, 1.8, 1.0),
        "dano": (45, 65, 100, 200),
        "area": (0, 0, 80, 150),
    }
    MELHORIAS = (
        "Pensa mais rápido e bate mais forte.",
        "O golpe passa a causar dano em área; pensa mais rápido.",
        "RACIOCÍNIO EM CADEIA: o golpe salta do alvo para até 4 inimigos vizinhos, um depois do outro, e ele pensa em 1 segundo.",
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
            self.lancar(jogo, self.mascote)
        self.mascote.aura = self.aura
        self.progresso = min(1.0, self.progresso + dt / (self.valor("pensar") * dono.multiplicador_recarga))
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
        self.lancar(jogo, GolpeClaude(centro, max(area, 40), origem=self.mascote.posicao if self.mascote else None))
        if area:
            for outro in jogo.inimigos_proximos(centro, area):
                if outro is not alvo:
                    jogo.causar_dano(outro, dano * 0.5, outro.posicao - centro)
        if self.no_maximo:                      # raciocínio em cadeia: o golpe salta para os vizinhos
            golpe_em_cadeia(jogo, self, dono, alvo, dano, centro)
        Recursos.tocar("claude", 0.4)

    def ao_remover(self, jogo):
        if self.mascote is not None:
            self.mascote.remover()
            self.mascote = None
