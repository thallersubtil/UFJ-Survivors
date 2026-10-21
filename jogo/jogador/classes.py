"""Classes de personagem. Cada classe tem uma arma inicial (ativa), uma passiva e um especial.

A aparência (gênero e cores) é escolhida na personalização, ANTES da classe, e vale para
todas: cada classe tem a sua arte (pastas masculina e feminina), recolorida com as
cores escolhidas.
"""
from jogo.armas.caramelo import Caramelo
from jogo.armas.cobra_python import CobraPython
from jogo.armas.gemini import Gemini
from jogo.jogador.especiais import SuperSaiyajin, ViradaDeNoite, Zoltraak
from jogo.jogador.jogador import Jogador
from jogo.jogador.passivas import Cafeinado, InstintoOtaku, RolagemDeIniciativa


class Otaku(Jogador):
    NOME = "Otaku"
    DESCRICAO = "Resistente e lento. O Caramelo luta junto."
    VIDA = 130
    VELOCIDADE = 180
    IMAGEM = "sprites/aluno2.png"
    PASTA_SPRITE = "aluno2"
    PASTA_SPRITE_FEMININA = "aluna2"
    MOLETOM_ORIGINAL = "laranja"
    PASTA_TRANSFORMADO = "aluno2_ssj"
    PASTA_TRANSFORMADO_FEMININA = "aluna2_ssj"
    IMAGEM_TRANSFORMADO = "sprites/aluno2_ssj.png"

    def criar_arma_inicial(self):
        return Caramelo()

    def criar_passiva(self):
        return InstintoOtaku()

    def criar_especial(self):
        return SuperSaiyajin()


class Programador(Jogador):
    NOME = "Programador"
    DESCRICAO = "Ágil e frágil. Ataca de longe à base de café."
    VIDA = 80
    VELOCIDADE = 230
    IMAGEM = "sprites/aluno1.png"
    PASTA_SPRITE = "aluno1"
    PASTA_SPRITE_FEMININA = "aluna1"

    def criar_arma_inicial(self):
        return CobraPython()

    def criar_passiva(self):
        return Cafeinado()

    def criar_especial(self):
        return ViradaDeNoite()


class MestreDeRPG(Jogador):
    NOME = "Mestre de RPG"
    DESCRICAO = "Equilibrado. O especial volta logo."
    VIDA = 100
    VELOCIDADE = 205
    IMAGEM = "sprites/aluno1.png"
    PASTA_SPRITE = "aluno1"
    PASTA_SPRITE_FEMININA = "aluna1"

    def criar_arma_inicial(self):
        return Gemini()

    def criar_passiva(self):
        return RolagemDeIniciativa()

    def criar_especial(self):
        return Zoltraak()


CLASSES = (Otaku, Programador, MestreDeRPG)
