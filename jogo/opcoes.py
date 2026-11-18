"""Como a partida vai ser: quais provas, se é treino, a aparência do aluno e o que ele comprou na loja."""
from dataclasses import dataclass, replace
from typing import Optional

from jogo.fase import PROVAS


@dataclass(frozen=True)
class OpcoesDePartida:
    provas: tuple = PROVAS            # classes de Prova, na ordem
    treino: bool = False              # treino não entra no ranking
    direto_no_chefe: bool = False     # começa a prova poucos segundos antes do chefe
    imortal: bool = False             # o herói não leva dano
    aparencia: Optional["Aparencia"] = None   # noqa: F821  (jogo.jogador.aparencia)
    melhorias: tuple = ()             # Melhorias permanentes compradas (jogo.loja.melhorias)
    desbloqueios: frozenset = frozenset()   # nomes das armas e itens comprados na loja

    @classmethod
    def treino_contra(cls, prova, direto_no_chefe=False, imortal=False):
        """Opções do modo treino: só a prova escolhida."""
        return cls(provas=(prova,), treino=True, direto_no_chefe=direto_no_chefe, imortal=imortal)

    def com_aparencia(self, aparencia):
        return replace(self, aparencia=aparencia)

    def com_progresso(self, progresso):
        """As mesmas opções, com o que o aluno comprou no Centro Acadêmico."""
        return replace(self, melhorias=tuple(progresso.melhorias_compradas()), desbloqueios=progresso.desbloqueios)

    def criar_fases(self):
        fases = [classe() for classe in self.provas]
        if self.direto_no_chefe:
            for fase in fases:
                fase.adiantar_para_o_chefe()
        return fases
