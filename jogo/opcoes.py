"""Como a partida vai ser: semestre inteiro ou treino contra um chefe, e o que o aluno comprou na loja."""
from dataclasses import dataclass, replace
from typing import Optional

from jogo.fase import Semestre


@dataclass(frozen=True)
class OpcoesDePartida:
    prova: Optional[object] = None    # treino: a ProvaMarcada escolhida (None: o semestre inteiro)
    treino: bool = False              # treino não entra no ranking
    direto_no_chefe: bool = False     # começa a prova poucos segundos antes do chefe
    imortal: bool = False             # o herói não leva dano
    melhorias: tuple = ()             # Melhorias permanentes compradas (jogo.loja.melhorias)
    desbloqueios: frozenset = frozenset()   # nomes das armas e itens comprados na loja
    lanche: Optional[type] = None     # classe do Lanche da Cantina guardado (só fora do treino)
    mini_chefes_conhecidos: frozenset = frozenset()   # CHAVEs dos mini-chefes já invocados alguma vez

    @classmethod
    def treino_contra(cls, prova, direto_no_chefe=False, imortal=False):
        """Opções do modo treino: só o chefe da `prova` (uma ProvaMarcada do calendário)."""
        return cls(prova=prova, treino=True, direto_no_chefe=direto_no_chefe, imortal=imortal)

    def com_progresso(self, progresso):
        """As mesmas opções, com o que o aluno comprou no Centro Acadêmico."""
        return replace(self, melhorias=tuple(progresso.melhorias_compradas()), desbloqueios=progresso.desbloqueios,
                       lanche=None if self.treino else progresso.lanche_reservado,
                       mini_chefes_conhecidos=frozenset(progresso.mini_chefes_conhecidos))

    def criar_fase(self):
        """O Semestre: inteiro, ou no treino só com a prova escolhida (e, se pedido, já perto do chefe)."""
        if self.prova is None:
            return Semestre()
        fase = Semestre(provas=(self.prova,))
        if self.direto_no_chefe:
            fase.adiantar_para_a_prova(self.prova)
        return fase
