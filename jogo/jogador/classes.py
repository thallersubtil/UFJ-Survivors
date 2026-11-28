"""Classes de personagem. Cada classe tem uma arma inicial exclusiva (só ela tem), três habilidades (nas cartas) e um especial.

Cada classe tem a sua aparência fixa: um chibi próprio em assets/sprites/<pasta>/ (parado e
andar), que é quem anda na partida, e o retrato grande em assets/retratos/ (a arte principal,
mostrada na matrícula). O rosto em assets/rostos/ é o retrato pequeno do HUD e da carteirinha. A personalização de gênero e cores
continua existindo em Jogador para quem herdar sem aparência fixa.
"""
from jogo.armas.caneta_correcao import CanetaDeCorrecao
from jogo.armas.controle import Controle
from jogo.armas.dado import DadoDeVinteLados
from jogo.armas.fusca import FuscaAzul
from jogo.armas.lightstick import Lightstick
from jogo.armas.mapa_do_campus import MapaDoCampus
from jogo.armas.teclado import TecladoMecanico
from jogo.jogador.especiais import (Calourada, Lotacao, RevisaoParaProva, SuperSaiyajin, TelaAzul, ViradaDeNoite,
                                    Zoltraak)
from jogo.jogador.habilidades import (Bis, Buzina, Cafeinado, CaronaSolidaria, CarroLotado, Combo, Compilar,
                                      FichaDePersonagem, FramePerfect, Gabarito, HorarioDeAtendimento, HypeDoShow,
                                      LacoDeRepeticao, PerdidoNoCampus, PlantaoDeDuvidas, Reflexo, RolagemDeIniciativa,
                                      SedeDeAprender, TesteDeResistencia, VeteranoCamarada, Wotagei)
from jogo.jogador.jogador import Jogador


class Otaku(Jogador):
    NOME = "Otaku"
    DESCRICAO = "Resistente e lento. Fã de carteirinha: agita o lightstick e o show esquenta."
    VIDA = 80
    VELOCIDADE = 180
    IMAGEM = "sprites/otaku.png"
    PASTA_SPRITE = "otaku"
    RETRATO = "retratos/otaku.png"
    ROSTO = "rostos/otaku.png"
    PASTA_TRANSFORMADO = "otaku_ssj"
    IMAGEM_TRANSFORMADO = "sprites/otaku_ssj.png"

    def criar_arma_inicial(self):
        return Lightstick()

    def criar_habilidades(self):
        return [Wotagei(), Bis(), HypeDoShow()]

    def criar_especial(self):
        return SuperSaiyajin()


class Programador(Jogador):
    NOME = "Programador"
    DESCRICAO = "Ágil e frágil. Vira a noite atirando código à base de café."
    VIDA = 50
    VELOCIDADE = 230
    IMAGEM = "sprites/programador.png"
    PASTA_SPRITE = "programador"
    RETRATO = "retratos/programador.png"
    ROSTO = "rostos/programador.png"

    def criar_arma_inicial(self):
        return TecladoMecanico()

    def criar_habilidades(self):
        return [LacoDeRepeticao(), Cafeinado(), Compilar()]

    def criar_especial(self):
        return ViradaDeNoite()


class MestreDeRPG(Jogador):
    NOME = "Mestre de RPG"
    DESCRICAO = "Equilibrado. O especial volta logo."
    VIDA = 60
    VELOCIDADE = 205
    IMAGEM = "sprites/mestre_de_rpg.png"
    PASTA_SPRITE = "mestre_de_rpg"
    RETRATO = "retratos/mestre_de_rpg.png"
    ROSTO = "rostos/mestre_de_rpg.png"

    def criar_arma_inicial(self):
        return DadoDeVinteLados()

    def criar_habilidades(self):
        return [RolagemDeIniciativa(), FichaDePersonagem(), TesteDeResistencia()]

    def criar_especial(self):
        return Zoltraak()


class Monitor(Jogador):
    NOME = "Monitor"
    DESCRICAO = "Paciente. Marca os erros com um X e se cuida sozinho."
    VIDA = 60
    VELOCIDADE = 200
    IMAGEM = "sprites/monitor.png"
    PASTA_SPRITE = "monitor"
    RETRATO = "retratos/monitor.png"
    ROSTO = "rostos/monitor.png"

    def criar_arma_inicial(self):
        return CanetaDeCorrecao()

    def criar_habilidades(self):
        return [PlantaoDeDuvidas(), Gabarito(), HorarioDeAtendimento()]

    def criar_especial(self):
        return RevisaoParaProva()


class Gamer(Jogador):
    NOME = "Gamer"
    DESCRICAO = "Rápido e frágil. Vive rolando e trava o jogo dos inimigos."
    VIDA = 55
    VELOCIDADE = 235
    IMAGEM = "sprites/gamer.png"
    PASTA_SPRITE = "gamer"
    RETRATO = "retratos/gamer.png"
    ROSTO = "rostos/gamer.png"

    def criar_arma_inicial(self):
        return Controle()

    def criar_habilidades(self):
        return [Reflexo(), FramePerfect(), Combo()]

    def criar_especial(self):
        return TelaAzul()


class Calouro(Jogador):
    NOME = "Calouro"
    DESCRICAO = "Começa fraco, mas aprende rápido."
    VIDA = 60
    VELOCIDADE = 215
    IMAGEM = "sprites/calouro.png"
    PASTA_SPRITE = "calouro"
    RETRATO = "retratos/calouro.png"
    ROSTO = "rostos/calouro.png"

    def criar_arma_inicial(self):
        return MapaDoCampus()

    def criar_habilidades(self):
        return [SedeDeAprender(), VeteranoCamarada(), PerdidoNoCampus()]

    def criar_especial(self):
        return Calourada()

    # Gimmick: os períodos. A cada 10 níveis o calouro avança um período e fica um pouco mais forte.
    NIVEIS_POR_PERIODO = 10
    DANO_POR_PERIODO = 0.05
    VELOCIDADE_POR_PERIODO = 0.03

    @property
    def periodo(self):
        return 1 + (self.nivel - 1) // self.NIVEIS_POR_PERIODO

    def _redefinir_atributos(self):
        super()._redefinir_atributos()
        self.mult_dano *= 1 + self.DANO_POR_PERIODO * (self.periodo - 1)
        self.mult_velocidade *= 1 + self.VELOCIDADE_POR_PERIODO * (self.periodo - 1)

    def ao_subir_de_nivel(self, jogo):
        super().ao_subir_de_nivel(jogo)
        if (self.nivel - 1) % self.NIVEIS_POR_PERIODO == 0:
            jogo.anunciar(f"{self.periodo}º período!", 3)


class CaraDaCarona(Jogador):
    NOME = "Cara da Carona"
    DESCRICAO = "Todo mundo quer carona. O Fusca vem junto."
    VIDA = 65
    VELOCIDADE = 195
    IMAGEM = "sprites/cara_da_carona.png"
    PASTA_SPRITE = "cara_da_carona"
    RETRATO = "retratos/cara_da_carona.png"
    ROSTO = "rostos/cara_da_carona.png"

    def criar_arma_inicial(self):
        return FuscaAzul()

    def criar_habilidades(self):
        return [CaronaSolidaria(), Buzina(), CarroLotado()]

    def criar_especial(self):
        return Lotacao()


CLASSES = (Otaku, Programador, MestreDeRPG, Monitor, Gamer, Calouro, CaraDaCarona)
