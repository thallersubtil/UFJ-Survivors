"""Colabs: junções secretas de duas armas no nível máximo.

Uma colab não é a soma das duas armas: é uma arma nova, com aparência e poder próprios,
mais dano e mais alcance que qualquer forma suprema. O jogo não conta as receitas: quem
tiver a sorte de levar as duas armas certas ao máximo descobre a carta. Nem toda arma tem colab, e só as
armas comuns entram nelas: a arma exclusiva de uma classe (EXCLUSIVA) nunca é ingrediente.
"""
from abc import ABC

from jogo.ajudantes.ajudantes import CachorroCaramelo, MascoteFlutuante
from jogo.ajudantes.colabs_novas import Latido, PequiEmArco, QuadroGigante, RastroDeSinal
from jogo.ajudantes.golpes import ElosDaCorrente, corrente, mais_cheio, mostrar
from jogo.armas.apostila import Apostila
from jogo.armas.arma import Arma, ArmaContinua
from jogo.armas.caramelo import Caramelo
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.claude import MascoteClaude
from jogo.armas.cobra_python import CobraPython
from jogo.armas.corrente_whatsapp import CorrenteDeWhatsApp
from jogo.armas.gemini import Gemini
from jogo.armas.pequi import PequiExplosivo
from jogo.armas.quadro_branco import QuadroBranco
from jogo.armas.regua import ReguaDeUmMetro
from jogo.armas.wifi import WifiEduroam
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


class FakeNews(ArmaContinua, Colab):
    """O ChatGPT inventa a notícia e a Corrente de WhatsApp espalha: quem acredita passa a lutar do seu lado."""

    NOME = "Fake News"
    ICONE = "icones/fake_news.png"
    DESCRICAO = ("O ChatGPT inventa e a corrente espalha: a cada 0,8 s uma notícia falsa pula por 12 inimigos, "
                 "e 30% de quem ela acerta acredita e luta do seu lado por 4 s.")
    INGREDIENTES = (CorrenteDeWhatsApp, MascoteChatGPT)
    ATRIBUTOS = {"dano": (48,), "saltos": (12,), "intervalo": (0.8,), "chance": (0.30,), "possessao": (4.0,)}
    ALCANCE = 460
    ALCANCE_DO_SALTO = 240
    DESLOCAMENTO = (-38, -46)

    def __init__(self):
        super().__init__()
        self.mascote = None
        self._espera = 0.0

    def atualizar(self, dt, jogo, dono):
        if self.mascote is None:
            self.mascote = self.lancar(jogo, MascoteFlutuante(dono, "sprites/chatgpt.png", 34, self.DESLOCAMENTO,
                                                              pasta="chatgpt"))
        self._espera -= dt
        if self._espera > 0:
            return
        origem = self.mascote.posicao
        pontos = corrente(jogo, origem, self.ALCANCE, self.valor("saltos"), self.ALCANCE_DO_SALTO,
                          lambda inimigo: self._espalhar(inimigo, jogo, dono))
        if pontos:
            self.lancar(jogo, ElosDaCorrente(pontos, duracao=0.4))
            self._espera = self.valor("intervalo") * dono.multiplicador_recarga
            Recursos.tocar("disparo", 0.12)
        else:
            self._espera = 0.1

    def _espalhar(self, inimigo, jogo, dono):
        morreu = jogo.causar_dano(inimigo, self.valor("dano") * dono.multiplicador_dano,
                                  inimigo.posicao - self.mascote.posicao)
        if not morreu and not inimigo.CHEFE and jogo.rng.random() < self.valor("chance"):
            inimigo.possuir(self.valor("possessao"))

    def ao_remover(self, jogo):
        if self.mascote is not None:
            self.mascote.remover()
            self.mascote = None


class AulaExpositiva(ArmaContinua, Colab):
    """Apostila e Quadro Branco: um quadro branco gigante gira em volta do aluno soltando folhas em espiral."""

    NOME = "Aula Expositiva"
    ICONE = "legado/itens/chest_f0.png"
    DESCRICAO = ("Um quadro branco gigante gira em volta de você e fere quem encosta, soltando folhas em espiral: "
                 "quem leva uma folha fica lento.")
    INGREDIENTES = (Apostila, QuadroBranco)
    ATRIBUTOS = {"dano": (40,), "raio": (150,), "velocidade": (2.2,), "folhas_por_segundo": (6,), "lentidao": (2.0,)}

    def __init__(self):
        super().__init__()
        self.quadro = None

    def atualizar(self, dt, jogo, dono):
        if self.quadro is None or not self.quadro.ativo:
            self.quadro = self.lancar(jogo, QuadroGigante(dono, self))

    def ao_remover(self, jogo):
        if self.quadro is not None:
            self.quadro.remover()
            self.quadro = None


class Caramelo5G(ArmaContinua, Colab):
    """Caramelo e Wi-Fi: o Caramelo corre com o roteador na boca, deixando um rastro de sinal que fere."""

    NOME = "Caramelo 5G"
    ICONE = "legado/itens/chest_f1.png"
    DESCRICAO = ("O Caramelo corre em volta de você com o roteador na boca e deixa um rastro de sinal que fere. "
                 "Quando o sinal cai, ele late e atordoa quem está perto.")
    INGREDIENTES = (Caramelo, WifiEduroam)
    ATRIBUTOS = {"dano": (30,), "raio": (130,), "velocidade": (4.5,), "rastro": (12,), "queda": (5.0,),
                 "latido": (170,), "atordoa": (1.0,)}
    RAIO_DO_RASTRO = 34
    DURACAO_DO_RASTRO = 1.2

    def __init__(self):
        super().__init__()
        self.cachorro = None
        self._espera_rastro = 0.0
        self._ate_cair = self.ATRIBUTOS["queda"][0]

    def atualizar(self, dt, jogo, dono):
        if self.cachorro is None or not self.cachorro.ativo:
            self.cachorro = self.lancar(jogo, CachorroCaramelo(dono, 0.0, self))
        dano = self.valor("dano") * dono.multiplicador_dano
        self._espera_rastro -= dt
        while self._espera_rastro <= 0:
            self._espera_rastro += 1 / self.valor("rastro")
            self.lancar(jogo, RastroDeSinal(self.cachorro.posicao, self.RAIO_DO_RASTRO, dano * 0.4,
                                            self.DURACAO_DO_RASTRO))
        self._ate_cair -= dt
        if self._ate_cair <= 0:
            self._ate_cair = self.valor("queda")
            self.lancar(jogo, Latido(self.cachorro.posicao, self.valor("latido"), dano, self.valor("atordoa")))
            mostrar(jogo, "AU AU!", self.cachorro.posicao, (255, 200, 90), 18)

    def ao_remover(self, jogo):
        if self.cachorro is not None:
            self.cachorro.remover()
            self.cachorro = None


class CatapultaDoCerrado(ArmaContinua, Colab):
    """Régua e Pequi: a régua vira catapulta e lança pequis em arco por cima do bolo de inimigos."""

    NOME = "Catapulta do Cerrado"
    ICONE = "legado/itens/chest_f2.png"
    DESCRICAO = ("A régua vira catapulta: três pequis voam em arco por cima de todo mundo e caem no maior bolo de "
                 "inimigos, estourando em espinhos.")
    INGREDIENTES = (ReguaDeUmMetro, PequiExplosivo)
    ATRIBUTOS = {"dano": (60,), "raio": (120,), "quantidade": (3,), "intervalo": (0.9,)}
    ALCANCE = 650
    ESPALHAMENTO = 60

    def __init__(self):
        super().__init__()
        self._espera = 0.0

    def atualizar(self, dt, jogo, dono):
        self._espera -= dt
        if self._espera > 0:
            return
        destino = mais_cheio(jogo, dono.posicao, self.ALCANCE)
        if destino is None:
            self._espera = 0.1
            return
        self._espera = self.valor("intervalo") * dono.multiplicador_recarga
        dano = self.valor("dano") * dono.multiplicador_dano
        for _ in range(self.valor("quantidade")):
            espalhado = destino + (jogo.rng.uniform(-1, 1) * self.ESPALHAMENTO, jogo.rng.uniform(-1, 1) * self.ESPALHAMENTO)
            self.lancar(jogo, PequiEmArco(dono.posicao, espalhado, self.valor("raio"), dano))


Colab.RECEITAS = [SerpenteEstelar, MetralhadoraDePrompts, FakeNews, AulaExpositiva, Caramelo5G, CatapultaDoCerrado]
