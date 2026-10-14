"""Os dois heróis jogáveis (arte provisória de aluno genérico)."""
from jogo.armas.caramelo import Caramelo
from jogo.armas.cobra_python import CobraPython
from jogo.jogador.especiais import SuperSaiyajin, Zoltraak
from jogo.jogador.jogador import Jogador


class AlunoAgil(Jogador):
    NOME = "Aluno 1"
    DESCRICAO = "Ágil e frágil. Ataca de longe."
    VIDA = 80
    VELOCIDADE = 230
    IMAGEM = "sprites/aluno1.png"
    PASTA_SPRITE = "aluno1"

    def criar_arma_inicial(self):
        return CobraPython()

    def criar_especial(self):
        return Zoltraak()


class AlunoResistente(Jogador):
    NOME = "Aluno 2"
    DESCRICAO = "Resistente e mais lento. Ataca de perto."
    VIDA = 130
    VELOCIDADE = 180
    IMAGEM = "sprites/aluno2.png"
    PASTA_SPRITE = "aluno2"
    PASTA_TRANSFORMADO = "aluno2_ssj"
    IMAGEM_TRANSFORMADO = "sprites/aluno2_ssj.png"

    def criar_arma_inicial(self):
        return Caramelo()

    def criar_especial(self):
        return SuperSaiyajin()


HEROIS = (AlunoAgil, AlunoResistente)
