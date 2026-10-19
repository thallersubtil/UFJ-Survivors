"""Chefe da 2ª prova: o professor de Arquitetura de Computadores e de Estrutura de Dados em C.

Duas fases: primeiro Arquitetura possui o professor; ao ser derrotada, Estrutura
de Dados em C (mais difícil) toma o lugar.
"""
from jogo.inimigos.chefe_possuido import ChefePossuido
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.materias.arquitetura import ArquiteturaDeComputadores
from jogo.inimigos.materias.estrutura_de_dados import EstruturaDeDadosEmC


@FabricaDeInimigos.registrar("chefe_arquitetura_ed")
class ProfessorDeArquiteturaEED(ChefePossuido):
    NOME = "Professor de Arquitetura e ED"
    NOME_PROFESSOR = "o Professor"
    MATERIAS = (ArquiteturaDeComputadores, EstruturaDeDadosEmC)
