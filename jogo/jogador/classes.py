"""Classes de personagem. Cada classe tem uma arma inicial (ativa), três habilidades (nas cartas) e um especial.

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
from jogo.jogador.especiais import (Calourada, Lotacao, RevisaoParaProva, SuperSaiyajin, TelaAzul, ViradaDeNoite,
                                    Zoltraak)
from jogo.jogador.habilidades import (ArmaduraDeRoteiro, Buzina, Cafeinado, CanetaVermelha, CaronaSolidaria,
                                      CarroLotado, Combo, Compilar, FichaDePersonagem, FramePerfect,
                                      HorarioDeAtendimento, InstintoOtaku, LacoDeRepeticao, PerdidoNoCampus,
                                      PlantaoDeDuvidas, PoderDaAmizade, Reflexo, RolagemDeIniciativa, SedeDeAprender,
                                      TesteDeResistencia, VeteranoCamarada)
from jogo.jogador.jogador import Jogador


class Otaku(Jogador):
    NOME = "Otaku"
    DESCRICAO = "Resistente e lento. O Caramelo luta junto."
    VIDA = 80
    VELOCIDADE = 180
    IMAGEM = "sprites/otaku.png"
    PASTA_SPRITE = "otaku"
    RETRATO = "retratos/otaku.png"
    ROSTO = "rostos/otaku.png"
    PASTA_TRANSFORMADO = "otaku_ssj"
    IMAGEM_TRANSFORMADO = "sprites/otaku_ssj.png"

    def criar_arma_inicial(self):
        return Caramelo()

    def criar_habilidades(self):
        return [InstintoOtaku(), ArmaduraDeRoteiro(), PoderDaAmizade()]

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
        return CobraPython()

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
        return Gemini()

    def criar_habilidades(self):
        return [RolagemDeIniciativa(), FichaDePersonagem(), TesteDeResistencia()]

    def criar_especial(self):
        return Zoltraak()


class Monitor(Jogador):
    NOME = "Monitor"
    DESCRICAO = "Paciente. Atrasa os inimigos e se cuida sozinho."
    VIDA = 60
    VELOCIDADE = 200
    IMAGEM = "sprites/monitor.png"
    PASTA_SPRITE = "monitor"
    RETRATO = "retratos/monitor.png"
    ROSTO = "rostos/monitor.png"

    def criar_arma_inicial(self):
        return QuadroBranco()

    def criar_habilidades(self):
        return [PlantaoDeDuvidas(), CanetaVermelha(), HorarioDeAtendimento()]

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
    VIDA = 50
    VELOCIDADE = 215
    IMAGEM = "sprites/calouro.png"
    PASTA_SPRITE = "calouro"
    RETRATO = "retratos/calouro.png"
    ROSTO = "rostos/calouro.png"

    def criar_arma_inicial(self):
        return Apostila()

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
