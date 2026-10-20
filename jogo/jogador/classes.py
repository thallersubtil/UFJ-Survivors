"""Classes de personagem. Cada classe tem uma arma inicial (ativa), uma passiva e um especial.

A aparência (masculino ou feminino, cabelo, roupas, cores) não depende da classe:
é escolhida na personalização e fica no boneco do aluno.
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
    APARENCIA = {"penteado": "Espetado", "cabelo": "Preto", "olhos": "Anime", "cor_cima": "Laranja",
                 "acessorio": "Fone"}

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
    APARENCIA = {"acessorio": "Óculos", "cima": "Camiseta", "cor_cima": "Preto"}

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
    APARENCIA = {"penteado": "Rabo de cavalo", "cabelo": "Castanho claro", "cima": "Jaqueta", "cor_cima": "Roxo"}

    def criar_arma_inicial(self):
        return Gemini()

    def criar_passiva(self):
        return RolagemDeIniciativa()

    def criar_especial(self):
        return Zoltraak()


CLASSES = (Otaku, Programador, MestreDeRPG)
