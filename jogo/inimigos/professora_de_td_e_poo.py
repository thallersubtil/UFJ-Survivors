"""Chefe da 3ª e última prova: a professora de Transformação Digital e de POO.

Duas fases: primeiro Transformação Digital (mais fácil); ao ser derrotada,
Programação Orientada a Objetos possui a professora para a luta final.
"""
from jogo.inimigos.chefe_possuido import ChefePossuido
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.materias.poo import ProgramacaoOrientadaAObjetos
from jogo.inimigos.materias.transformacao_digital import TransformacaoDigital


@FabricaDeInimigos.registrar("chefe_td_poo")
class ProfessoraDeTDEPOO(ChefePossuido):
    NOME = "Professora de TD e POO"
    NOME_PROFESSOR = "a Professora"
    PASTA_SPRITE = "professora"            # sem a pasta, usa a imagem abaixo (provisória)
    IMAGEM = "sprites/professor.png"
    MATERIAS = (TransformacaoDigital, ProgramacaoOrientadaAObjetos)
