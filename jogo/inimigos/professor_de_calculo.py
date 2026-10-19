"""Chefe da 1ª prova: o professor de Cálculo I, possuído pela própria matéria."""
from jogo.inimigos.chefe_possuido import ChefePossuido
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.materias.calculo import CalculoI


@FabricaDeInimigos.registrar("chefe_calculo")
class ProfessorDeCalculo(ChefePossuido):
    NOME = "Professor de Cálculo"
    NOME_PROFESSOR = "o Professor de Cálculo"
    MATERIAS = (CalculoI,)
