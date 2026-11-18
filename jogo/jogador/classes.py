"""Classes de personagem. Cada classe tem uma arma inicial (ativa), uma passiva e um especial.

A aparência (gênero e cores) é escolhida na personalização, ANTES da classe, e vale para
todas: cada classe tem a sua arte (pastas masculina e feminina), recolorida com as
cores escolhidas.
"""
from jogo.armas.apostila import Apostila
from jogo.armas.caramelo import Caramelo
from jogo.armas.cobra_python import CobraPython
from jogo.armas.controle import Controle
from jogo.armas.fusca import FuscaAzul
from jogo.armas.gemini import Gemini
from jogo.armas.quadro_branco import QuadroBranco
from jogo.jogador.especiais import (Lotacao, RevisaoParaProva, Speedrun, SuperSaiyajin, TroteReverso, ViradaDeNoite,
                                    Zoltraak)
from jogo.jogador.jogador import Jogador
from jogo.jogador.passivas import (Cafeinado, CaronaSolidaria, InstintoOtaku, PlantaoDeDuvidas, Reflexo,
                                   RolagemDeIniciativa, SedeDeAprender)


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


class Monitor(Jogador):
    NOME = "Monitor"
    DESCRICAO = "Paciente. Atrasa os inimigos e se cuida sozinho."
    VIDA = 100
    VELOCIDADE = 200
    IMAGEM = "sprites/aluno1.png"          # arte provisória (usa a do Programador)
    PASTA_SPRITE = "aluno1"
    PASTA_SPRITE_FEMININA = "aluna1"

    def criar_arma_inicial(self):
        return QuadroBranco()

    def criar_passiva(self):
        return PlantaoDeDuvidas()

    def criar_especial(self):
        return RevisaoParaProva()


class Gamer(Jogador):
    NOME = "Gamer"
    DESCRICAO = "Rápido e frágil. Vive rolando."
    VIDA = 95
    VELOCIDADE = 235
    IMAGEM = "sprites/aluno2.png"          # arte provisória (usa a do Otaku)
    PASTA_SPRITE = "aluno2"
    PASTA_SPRITE_FEMININA = "aluna2"
    MOLETOM_ORIGINAL = "laranja"

    def criar_arma_inicial(self):
        return Controle()

    def criar_passiva(self):
        return Reflexo()

    def criar_especial(self):
        return Speedrun()


class Calouro(Jogador):
    NOME = "Calouro"
    DESCRICAO = "Começa fraco, mas aprende rápido."
    VIDA = 85
    VELOCIDADE = 215
    IMAGEM = "sprites/aluno1.png"          # arte provisória
    PASTA_SPRITE = "aluno1"
    PASTA_SPRITE_FEMININA = "aluna1"

    def criar_arma_inicial(self):
        return Apostila()

    def criar_passiva(self):
        return SedeDeAprender()

    def criar_especial(self):
        return TroteReverso()


class CaraDaCarona(Jogador):
    NOME = "Cara da Carona"
    DESCRICAO = "Todo mundo quer carona. O Fusca vem junto."
    VIDA = 110
    VELOCIDADE = 195
    IMAGEM = "sprites/aluno2.png"          # arte provisória
    PASTA_SPRITE = "aluno2"
    PASTA_SPRITE_FEMININA = "aluna2"
    MOLETOM_ORIGINAL = "laranja"

    def criar_arma_inicial(self):
        return FuscaAzul()

    def criar_passiva(self):
        return CaronaSolidaria()

    def criar_especial(self):
        return Lotacao()


CLASSES = (Otaku, Programador, MestreDeRPG, Monitor, Gamer, Calouro, CaraDaCarona)
