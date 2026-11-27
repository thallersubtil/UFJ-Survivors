"""Colabs: junções secretas de duas armas no nível máximo.

Uma colab não é a soma das duas armas: é uma arma nova, com aparência e poder próprios,
mais dano e mais alcance que qualquer forma suprema. O jogo não conta as receitas: quem
tiver a sorte de levar as duas armas certas ao máximo descobre a carta. Nem toda arma tem colab.
"""
import math
from abc import ABC

from jogo.ajudantes.ajudantes import FuscaCircular
from jogo.armas.arma import Arma, ArmaContinua
from jogo.armas.caramelo import Caramelo
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.claude import MascoteClaude
from jogo.armas.cobra_python import CobraPython
from jogo.armas.fusca import FuscaAzul
from jogo.armas.gemini import Gemini
from jogo.formas_supremas import MetralhadoraFlutuante, PromptDisparado, SerpenteEstelarProjetil
from jogo.nucleo.recursos import Recursos


class Colab(Arma, ABC):
    """Arma nova que nasce da junção de duas armas no nível máximo.

    Já vem pronta: tem um nível só, não volta às cartas de melhoria e a Bigorna não afia.
    """

    NIVEL_MAXIMO = 1
    MAX_CARIMBOS = 0
    COR_SUPREMA = (255, 120, 230)      # contorno rosa: diferente do dourado do nível máximo
    MELHORIAS = ()
    INGREDIENTES = ()
    RECEITAS = []

    @staticmethod
    def colabs_disponiveis(armas):
        """Receitas cujas duas armas estão no nível máximo."""
        disponiveis = []
        for receita in Colab.RECEITAS:
            if all(any(type(a) is ingrediente and a.no_maximo for a in armas) for ingrediente in receita.INGREDIENTES):
                disponiveis.append(receita)
        return disponiveis

    @staticmethod
    def ingredientes_em(receita, armas):
        return [a for a in armas if type(a) in receita.INGREDIENTES]


class CarameloNoFusca(ArmaContinua, Colab):
    """Carrossel de fuscas: vários Caramelos ao volante girando num círculo perfeito, longe do herói."""

    NOME = "Carrossel de Fuscas"
    ICONE = "sprites/caramelo_no_fusca.png"
    DESCRICAO = ("Seis Caramelos ao volante giram em volta de você num círculo perfeito, bem longe: nada chega "
                 "perto sem ser atropelado e possuído.")
    INGREDIENTES = (Caramelo, FuscaAzul)
    ATRIBUTOS = {"quantidade": (6,), "dano": (85,), "raio": (285,), "velocidade": (2.3,), "possessao": (8.0,)}

    def __init__(self):
        super().__init__()
        self.fuscas = []

    def atualizar(self, dt, jogo, dono):
        if not self.fuscas:
            total = self.valor("quantidade")
            self.fuscas = [self.lancar(jogo, FuscaCircular(dono, self, 2 * math.pi * i / total)) for i in range(total)]

    def ao_remover(self, jogo):
        for fusca in self.fuscas:
            fusca.remover()
        self.fuscas = []


class SerpenteEstelar(ArmaContinua, Colab):
    """A cobra e a estrela viram uma serpente cósmica que cruza a tela inteira atravessando tudo."""

    NOME = "Serpente Estelar"
    ICONE = "sprites/serpente_estelar.png"
    DESCRICAO = ("Uma serpente feita de céu estrelado cruza a tela inteira na direção da mira, atravessa tudo e "
                 "cada mordida estoura em estrelas.")
    INGREDIENTES = (CobraPython, Gemini)
    ATRIBUTOS = {"dano": (110,), "serpentes": (3,), "recarga": (0.9,), "raio_estouro": (95,), "dano_estouro": (55,)}
    VELOCIDADE = 560
    ABERTURA = 16

    def __init__(self):
        super().__init__()
        self._espera = 0.3

    def atualizar(self, dt, jogo, dono):
        self._espera -= dt
        if self._espera > 0:
            return
        self._espera = self.valor("recarga") * dono.multiplicador_recarga
        total = self.valor("serpentes")
        for i in range(total):
            direcao = dono.direcao_mira.rotate((i - (total - 1) / 2) * self.ABERTURA)
            self.lancar(jogo, SerpenteEstelarProjetil(dono.posicao, direcao * self.VELOCIDADE,
                                                      self.valor("dano") * dono.multiplicador_dano,
                                                      self.valor("raio_estouro"),
                                                      self.valor("dano_estouro") * dono.multiplicador_dano))
        Recursos.tocar("disparo", 0.2)


class MetralhadoraDePrompts(ArmaContinua, Colab):
    """ChatGPT e Claude fundidos numa metralhadora que despeja prompts sem parar na direção da mira."""

    NOME = "Metralhadora de Prompts"
    ICONE = "sprites/metralhadora.png"
    DESCRICAO = ("As duas IAs se fundem numa metralhadora que despeja prompts sem parar na direção da mira: "
                 "20 por segundo, sem pausa para recarregar.")
    INGREDIENTES = (MascoteChatGPT, MascoteClaude)
    ATRIBUTOS = {"dano": (34,), "cadencia": (20,), "perfuracao": (2,), "espalhamento": (5.0,)}
    VELOCIDADE = 950                   # com 1,1 s de vida, cada prompt alcança mais de 1000 pixels
    CONVERGENCIA = 420                 # distância em que os tiros cruzam a linha da mira

    def __init__(self):
        super().__init__()
        self.metralhadora = None
        self._espera = 0.0
        self._disparos = 0

    def atualizar(self, dt, jogo, dono):
        if self.metralhadora is None:
            self.metralhadora = self.lancar(jogo, MetralhadoraFlutuante(dono))
        self.metralhadora.atirando = True
        self._espera -= dt
        while self._espera <= 0:
            self._espera += 1 / self.valor("cadencia") * dono.multiplicador_recarga
            self._disparos += 1
            desvio = jogo.rng.uniform(-1, 1) * self.valor("espalhamento")
            boca = self.metralhadora.boca
            rumo = dono.posicao + dono.direcao_mira * self.CONVERGENCIA - boca      # os tiros fecham na linha da mira
            self.lancar(jogo, PromptDisparado(boca, rumo.normalize().rotate(desvio) * self.VELOCIDADE,
                                              self.valor("dano") * dono.multiplicador_dano,
                                              laranja=self._disparos % 2 == 0, perfuracao=self.valor("perfuracao")))
            if self._disparos % 4 == 0:
                Recursos.tocar("disparo", 0.06)

    def ao_remover(self, jogo):
        if self.metralhadora is not None:
            self.metralhadora.remover()
            self.metralhadora = None


Colab.RECEITAS = [CarameloNoFusca, SerpenteEstelar, MetralhadoraDePrompts]
