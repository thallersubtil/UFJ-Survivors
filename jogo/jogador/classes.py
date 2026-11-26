"""Classes de personagem. Cada classe tem uma arma inicial (ativa), uma passiva e um especial.

Cada classe tem a sua aparência fixa: um chibi próprio em assets/sprites/<pasta>/ (parado e
andar), que é quem anda na partida, e o retrato grande em assets/retratos/ (a arte principal,
mostrada na matrícula). O rosto em assets/rostos/ é o retrato pequeno do HUD e da carteirinha. A personalização de gênero e cores
continua existindo em Jogador para quem herdar sem aparência fixa.
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
    IMAGEM = "sprites/otaku.png"
    PASTA_SPRITE = "otaku"
    RETRATO = "retratos/otaku.png"
    ROSTO = "rostos/otaku.png"
    APARENCIA_FIXA = True
    PASTA_TRANSFORMADO = "otaku_ssj"
    IMAGEM_TRANSFORMADO = "sprites/otaku_ssj.png"

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
    IMAGEM = "sprites/programador.png"
    PASTA_SPRITE = "programador"
    RETRATO = "retratos/programador.png"
    ROSTO = "rostos/programador.png"
    APARENCIA_FIXA = True

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
    IMAGEM = "sprites/mestre_de_rpg.png"
    PASTA_SPRITE = "mestre_de_rpg"
    RETRATO = "retratos/mestre_de_rpg.png"
    ROSTO = "rostos/mestre_de_rpg.png"
    APARENCIA_FIXA = True

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
    IMAGEM = "sprites/monitor.png"
    PASTA_SPRITE = "monitor"
    RETRATO = "retratos/monitor.png"
    ROSTO = "rostos/monitor.png"
    APARENCIA_FIXA = True

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
    IMAGEM = "sprites/gamer.png"
    PASTA_SPRITE = "gamer"
    RETRATO = "retratos/gamer.png"
    ROSTO = "rostos/gamer.png"
    APARENCIA_FIXA = True

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
    IMAGEM = "sprites/calouro.png"
    PASTA_SPRITE = "calouro"
    RETRATO = "retratos/calouro.png"
    ROSTO = "rostos/calouro.png"
    APARENCIA_FIXA = True

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
    IMAGEM = "sprites/cara_da_carona.png"
    PASTA_SPRITE = "cara_da_carona"
    RETRATO = "retratos/cara_da_carona.png"
    ROSTO = "rostos/cara_da_carona.png"
    APARENCIA_FIXA = True

    def criar_arma_inicial(self):
        return FuscaAzul()

    def criar_passiva(self):
        return CaronaSolidaria()

    def criar_especial(self):
        return Lotacao()


CLASSES = (Otaku, Programador, MestreDeRPG, Monitor, Gamer, Calouro, CaraDaCarona)
