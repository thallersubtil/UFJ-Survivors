"""Mini-chefes do mapa: figuras do campus que o aluno invoca se quiser, em troca de um baú garantido.

Cada um espera no seu local (um círculo de invocação perto de um prédio ou num canto do campus) e, depois
de invocado, guarda aquele pedaço: persegue o aluno só até certa distância do posto e volta para lá se
ele fugir. São fortes de propósito, e cada um traz os próprios lacaios. O tom é de piada interna.
"""
from abc import abstractmethod

import pygame

from jogo.coletaveis.coletaveis import Moeda
from jogo.config import Cor
from jogo.efeitos import TextoFlutuante
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo
from jogo.nucleo.recursos import Recursos
from jogo.nucleo.desenho import desenhar_faixa_de_aviso
from jogo.projeteis.do_campus import FeixeDeAbducao, Multa, VeiculoDesgovernado
from jogo.projeteis.tematicos import (Bumerangue, Carimbada, FrascoDeAcido, Marca, PanelaoDeSopa,
                                      ProjetilTematico)


class Arrancada:
    """Investida em linha reta: o mini-chefe para, mira (com aviso na tela) e dispara. Usada por composição."""

    def __init__(self, carga, duracao, velocidade, vezes=1):
        self.carga_total, self.duracao, self.velocidade, self.vezes_total = carga, duracao, velocidade, vezes
        self._carga = self._corrida = 0.0
        self._restam = 0
        self.rumo = pygame.Vector2(1, 0)

    @property
    def ativa(self):
        return self._carga > 0 or self._corrida > 0

    @property
    def mirando(self):
        return self._carga > 0

    @property
    def correndo(self):
        return self._corrida > 0

    def comecar(self):
        self._carga = self.carga_total
        self._restam = self.vezes_total

    def avancar(self, dt, chefe, jogo):
        if self._carga > 0:
            self._carga -= dt
            self.rumo = chefe.mirar(jogo)
            chefe.olhando_esquerda = self.rumo.x < 0
            if self._carga <= 0:
                self._corrida = self.duracao
        elif self._corrida > 0:
            self._corrida -= dt
            chefe.posicao += self.rumo * self.velocidade * dt
            if self._corrida <= 0:
                self._restam -= 1
                if self._restam > 0:
                    self._carga = self.carga_total * 0.5

    def desenhar_aviso(self, tela, camera, chefe, largura=22):
        if self.mirando:
            inicio = camera.para_tela(chefe.posicao)
            fim = inicio + self.rumo * self.velocidade * self.duracao
            desenhar_faixa_de_aviso(tela, inicio, fim, largura * 2, chefe.COR, self._carga)


class MiniChefe(Inimigo):
    """Base dos mini-chefes do mapa. Cada subclasse diz onde fica, quem a acompanha e como ataca (`atacar`)."""

    LOCAL = ""                   # nome do prédio do mapa perto de onde ele aparece
    PONTO = None                 # (x, y) fixo no campus, para quem não fica perto de prédio nenhum
    ONDE = ""                    # como o anúncio diz o lugar ("perto do RU")
    SECRETO = False              # True: não é anunciado nem aparece no mapa até o aluno chegar perto
    ARTIGO = "Um"                # "Um Vigilante selvagem apareceu!"
    GRITO = ""                   # o que ele fala ao ser invocado
    LACAIO = ""                  # quem o acompanha (nome na FabricaDeInimigos)
    LACAIOS_NA_CHEGADA = 5
    REFORCO_A_CADA = 4           # de quantos em quantos ataques chegam mais lacaios
    LACAIOS_DE_REFORCO = 3
    SIMBOLO = "!"                # o que aparece no projétil se faltar a arte dele
    RAIO = 30
    PONTOS = 500
    EXPERIENCIA = 45
    MOEDAS = 30
    INTERVALO_ATAQUE = 2.4
    GUARDA = 780                 # até onde ele segue o aluno, contado do posto
    CURA_NO_POSTO = 0.04         # fração da vida por segundo que recupera quando o aluno foge
    COR = (255, 170, 60)
    GANHO_VELOCIDADE = 0.04      # o tempo de partida mexe pouco na velocidade dele
    TENACIDADE = 1.0             # nada puxa, atrasa ou prende um mini-chefe no meio do ataque

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.posto = pygame.Vector2(posicao)
        self.solta_bau = True
        self.reposiciona = False
        self.ataques = 0
        self._espera_ataque = 1.2

    # ---- o que o mini-mapa e a apresentação leem
    @property
    def ROSTO(self):
        return f"rostos/{self.PASTA_SPRITE}.png"

    @property
    def rosto(self):
        return self.ROSTO

    @property
    def ILUSTRACAO(self):
        return f"chefes/{self.PASTA_SPRITE}.png"

    @property
    def COR_DA_APRESENTACAO(self):
        return self.COR

    @property
    def invocado(self):
        return True

    # ---- luta
    @abstractmethod
    def atacar(self, jogo):
        """O golpe deste mini-chefe (chamado a cada INTERVALO_ATAQUE enquanto o aluno está por perto)."""

    def ao_chegar(self, jogo):
        """Acabou de ser invocado: já chega acompanhado."""
        self.chamar_lacaios(jogo, self.LACAIOS_NA_CHEGADA)

    def chamar_lacaios(self, jogo, quantos, nome=None, raio=90):
        nome = nome or self.LACAIO
        if not nome:
            return
        for i in range(quantos):
            lado = pygame.Vector2(raio, 0).rotate(360 * i / quantos + 20 * self.ataques)
            self.receber_lacaio(jogo, FabricaDeInimigos.criar(nome, self.posicao + lado, self.escala))

    def receber_lacaio(self, jogo, lacaio):
        """Põe o lacaio na arena. Quem conta ou enfeita os próprios lacaios sobrescreve."""
        jogo.adicionar(lacaio)

    def mover(self, dt, jogo):
        if jogo.jogador.posicao.distance_to(self.posto) > self.GUARDA:      # o aluno fugiu: volta e se recupera
            self.ir_em_direcao(self.posto, dt)
            self.curar(self.vida_maxima * self.CURA_NO_POSTO * dt)
            return
        self.perseguir(dt, jogo)
        self._espera_ataque -= dt
        if self._espera_ataque <= 0:
            self._espera_ataque = self.intervalo_de_ataque
            self.ataques += 1
            self.atacar(jogo)
            if self.ataques % self.REFORCO_A_CADA == 0:
                self.chamar_lacaios(jogo, self.LACAIOS_DE_REFORCO)

    @property
    def intervalo_de_ataque(self):
        return self.INTERVALO_ATAQUE

    def perseguir(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)

    def mirar(self, jogo):
        rumo = jogo.jogador.posicao - self.posicao
        return rumo.normalize() if rumo.length_squared() > 0 else pygame.Vector2(1, 0)

    def criar_projetil(self, direcao, velocidade, dano, arte, raio):
        """O objeto que este mini-chefe arremessa. Quem joga algo que se comporta diferente sobrescreve."""
        return ProjetilTematico(self.posicao, direcao * velocidade, dano * self.fator_de_dano, self.SIMBOLO,
                                self.COR, raio, arte=arte)

    def disparar(self, jogo, direcao, velocidade, dano, arte, raio=12):
        jogo.adicionar(self.criar_projetil(direcao, velocidade, dano, arte, raio))

    def leque(self, jogo, quantos, abertura, velocidade, dano, *artes):
        """Objetos em leque na direção do aluno; com mais de uma arte, elas se revezam."""
        rumo = self.mirar(jogo)
        for i in range(quantos):
            self.disparar(jogo, rumo.rotate((i - (quantos - 1) / 2) * abertura), velocidade, dano,
                          artes[i % len(artes)])

    def anel(self, jogo, quantos, velocidade, dano, *artes, giro=0.0):
        for i in range(quantos):
            self.disparar(jogo, pygame.Vector2(1, 0).rotate(giro + 360 * i / quantos), velocidade, dano,
                          artes[i % len(artes)])

    def marcar(self, jogo, arte, altura, posicao=None, **opcoes):
        """Um efeito desenhado (nuvem, garra, uivo) no lugar do mini-chefe ou onde for pedido."""
        jogo.adicionar(Marca(self.posicao if posicao is None else posicao, arte, altura, **opcoes))

    def falar(self, jogo, texto, tamanho=18):
        jogo.adicionar(TextoFlutuante(texto, self.posicao - (0, self.altura_sprite / 2 + 26), self.COR, tamanho,
                                      duracao=0.9))

    @property
    def fator_de_dano(self):
        return 1 + max(0.0, self.escala - 1) * self.GANHO_DANO

    def assustar(self, duracao):
        """Mini-chefe não cai em trote."""

    def possuir(self, duracao):
        """Nem é possuído pelo Fusca."""

    def empurrar(self, direcao, forca=180):
        """Nem é empurrado."""

    def ao_morrer(self, jogo):
        super().ao_morrer(jogo)
        jogo.adicionar(Moeda(self.posicao - (18, 0), self.MOEDAS))
        jogo.marcos.add("mini_chefe")
        jogo.marcados.discard(self.NOME)
        jogo.anunciar(f"{self.NOME}: fora de combate! Pegue o baú", 3)

    def desenhar_corpo(self, tela, camera):
        super().desenhar_corpo(tela, camera)
        centro = camera.para_tela(self.posicao)
        barra = pygame.Rect(0, 0, 84, 9)
        barra.midbottom = (round(centro.x), round(centro.y - self.altura_sprite / 2 - 8))
        pygame.draw.rect(tela, Cor.BORDA_ESCURA, barra.inflate(4, 4), border_radius=3)
        cheia = barra.copy()
        cheia.width = round(barra.width * self.vida / self.vida_maxima)
        pygame.draw.rect(tela, self.COR, cheia, border_radius=2)
        nome = Recursos.fonte(13).render(self.NOME, True, Cor.TEXTO)
        tela.blit(nome, nome.get_rect(midbottom=(barra.centerx, barra.top - 3)))


@FabricaDeInimigos.registrar("tia_da_cantina")
class TiaDaCantina(MiniChefe):
    """Enorme. Arremessa bandejas, pratos feitos e frigideiras em leque e, de três em três ataques, joga o
    panelão para o alto: ele cai onde o aluno estava e deixa uma poça de sopa quente, com talheres para todo lado."""

    NOME = "Tia da Cantina"
    ARTIGO = "Uma"
    LOCAL = "RU"
    ONDE = "perto do RU"
    GRITO = "Sem ficha não almoça, meu filho!"
    PASTA_SPRITE = "tia_da_cantina"
    LACAIO = "coxinha"
    RAIO = 72                    # três vezes a altura do aluno e mais larga que alta
    VIDA = 1700
    VELOCIDADE = 82
    DANO = 16
    COR = (255, 150, 70)

    RAIO_DA_SOPA = 105
    DANO_DA_SOPA = 14

    def atacar(self, jogo):
        if self.ataques % 3 == 0:
            jogo.adicionar(PanelaoDeSopa(jogo.jogador.posicao, self.RAIO_DA_SOPA,
                                         self.DANO_DA_SOPA * self.fator_de_dano))
            self.anel(jogo, 12, 190, 9, "concha", "colher_de_pau")
            self.falar(jogo, "SOPA QUENTE!")
        elif self.ataques % 3 == 1:
            self.leque(jogo, 5, 14, 290, 9, "bandeja")
        else:
            self.leque(jogo, 5, 14, 290, 9, "prato_feito", "frigideira")
            self.falar(jogo, "Repete o prato!")


@FabricaDeInimigos.registrar("vigilante")
class Vigilante(MiniChefe):
    """O segurança que se veste de morcego: aponta a lanterna e arranca em linha reta. Anda com morcegos."""

    NOME = "Vigilante"
    LOCAL = "CENTRO DE AULAS II"
    ONDE = "no Centro de Aulas II"
    GRITO = "Eu sou a vigilância. Cadê a carteirinha?"
    PASTA_SPRITE = "vigilante"
    LACAIO = "morcego"
    VIDA = 1300
    VELOCIDADE = 125
    DANO = 16
    COR = (250, 220, 80)
    INTERVALO_ATAQUE = 3.0

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.arrancada = Arrancada(carga=0.7, duracao=0.55, velocidade=700)

    def atacar(self, jogo):
        if self.ataques % 2 == 0:                            # antes de correr, solta os batarangues
            self.leque(jogo, 3, 22, 430, 8, "batarangue")
            self.falar(jogo, "Parado aí!")
        self.arrancada.comecar()

    def criar_projetil(self, direcao, velocidade, dano, arte, raio):
        """O batarangue vai e volta."""
        return Bumerangue(self.posicao, direcao * velocidade, dano * self.fator_de_dano, self.SIMBOLO, self.COR,
                          raio, arte=arte)

    def perseguir(self, dt, jogo):
        if self.arrancada.ativa:
            self.arrancada.avancar(dt, self, jogo)
        else:
            super().perseguir(dt, jogo)

    def desenhar_corpo(self, tela, camera):
        self.arrancada.desenhar_aviso(tela, camera, self)
        if self.arrancada.mirando:                           # o facho da lanterna em cima do aluno
            origem = camera.para_tela(self.posicao)
            rumo = self.arrancada.rumo
            facho = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(facho, (255, 240, 150, 70),
                                [origem, origem + rumo.rotate(-13) * 420, origem + rumo.rotate(13) * 420])
            tela.blit(facho, (0, 0))
        super().desenhar_corpo(tela, camera)


@FabricaDeInimigos.registrar("bibliotecaria")
class Bibliotecaria(MiniChefe):
    """Anota o nome do aluno no caderno preto e distribui multas de atraso: cada uma que acerta leva moedas."""

    NOME = "Bibliotecária"
    ARTIGO = "Uma"
    LOCAL = "BIBLIOTECA"
    ONDE = "na Biblioteca"
    GRITO = "Nome completo para o cadastro, por favor."
    PASTA_SPRITE = "bibliotecaria"
    LACAIO = "livro_atrasado"
    VIDA = 1500
    VELOCIDADE = 84
    DANO = 12
    COR = (200, 130, 230)
    INTERVALO_ATAQUE = 2.0
    MULTAS = 12
    VALOR_DA_MULTA = 8           # moedas que cada multa tira
    DANO_DA_MULTA = 4

    def atacar(self, jogo):
        giro = 360 / self.MULTAS / 2 * (self.ataques % 2)
        for i in range(self.MULTAS):
            direcao = pygame.Vector2(1, 0).rotate(giro + 360 * i / self.MULTAS)
            jogo.adicionar(Multa(self.posicao, direcao * 210, self.DANO_DA_MULTA * self.fator_de_dano,
                                 self.VALOR_DA_MULTA, self.COR))
        if self.ataques % 3 == 0:                            # e um livro de capa dura na direção do aluno
            self.leque(jogo, 3, 16, 300, 8, "livro")
        self.falar(jogo, "MULTA POR ATRASO!" if self.ataques % 2 else "Vou anotar o seu nome...")


@FabricaDeInimigos.registrar("tecnico_do_laboratorio")
class TecnicoDoLaboratorio(MiniChefe):
    """Resultado dos próprios experimentos: enorme, verde, vai aonde quer. Arremessa seringas, regenera
    o tempo todo e entra em fúria com pouca vida."""

    NOME = "Técnico do Laboratório"
    LOCAL = "LABORATORIOS MULTI"
    ONDE = "nos Laboratórios"
    GRITO = "TÉCNICO VAI AONDE QUER!"
    PASTA_SPRITE = "tecnico"
    LACAIO = "cobaia"
    RAIO = 46
    VIDA = 2100
    VELOCIDADE = 92
    DANO = 18
    COR = (130, 240, 90)
    INTERVALO_ATAQUE = 2.2
    REGENERACAO = 0.006          # fração da vida por segundo, sempre
    FURIA_ABAIXO_DE = 0.4        # fração da vida em que ele se enfurece
    RAIO_DO_ACIDO = 85
    DANO_DO_ACIDO = 12
    VELOCIDADE_EM_FURIA = 1.5

    @property
    def em_furia(self):
        return self.vida <= self.vida_maxima * self.FURIA_ABAIXO_DE

    @property
    def intervalo_de_ataque(self):
        return self.INTERVALO_ATAQUE * (0.6 if self.em_furia else 1)

    def perseguir(self, dt, jogo):
        self.curar(self.vida_maxima * self.REGENERACAO * dt)
        self.ir_em_direcao(jogo.jogador.posicao, dt,
                           self.velocidade * (self.VELOCIDADE_EM_FURIA if self.em_furia else 1))

    def atacar(self, jogo):
        rumo = self.mirar(jogo)
        for desvio in ((-12, 0, 12) if self.em_furia else (0,)):
            self.disparar(jogo, rumo.rotate(desvio), 380, 14, "seringa", raio=16)
        if self.ataques % 3 == 0:                            # um frasco para o alto: cai e vira poça de ácido
            jogo.adicionar(FrascoDeAcido(jogo.jogador.posicao, self.RAIO_DO_ACIDO,
                                         self.DANO_DO_ACIDO * self.fator_de_dano))
            self.falar(jogo, "FÚRIA!" if self.em_furia else "Experimento!", 22 if self.em_furia else 18)


@FabricaDeInimigos.registrar("reitor")
class Reitor(MiniChefe):
    """Muito, muito alto. Cada pisada espalha ofícios em anel; no meio, despacha uma portaria no aluno."""

    NOME = "Reitor"
    LOCAL = "REITORIA"
    ONDE = "na Reitoria"
    GRITO = "Isso não consta no regimento!"
    PASTA_SPRITE = "reitor"
    RAIO_DO_CARIMBO = 90
    DANO_DO_CARIMBO = 16
    LACAIO = "carimbo"
    RAIO = 28
    VIDA = 2000
    VELOCIDADE = 96
    DANO = 15
    COR = (120, 220, 150)
    INTERVALO_ATAQUE = 2.1

    def atacar(self, jogo):
        if self.ataques % 2:
            self.anel(jogo, 16, 200, 10, "oficio", giro=11 * self.ataques)
            jogo.adicionar(Carimbada(jogo.jogador.posicao, self.RAIO_DO_CARIMBO,
                                     self.DANO_DO_CARIMBO * self.fator_de_dano))
            self.falar(jogo, "INDEFERIDO!")
        else:
            self.leque(jogo, 7, 9, 330, 10, "portaria", "caneta")


@FabricaDeInimigos.registrar("lobo_guara")
class LoboGuara(MiniChefe):
    """O mascote da UFJ. Rápido: dá dois botes seguidos e uiva para chamar a ninhada."""

    NOME = "Lobo-Guará"
    LOCAL = "ENG. FLORESTAL"
    ONDE = "na Engenharia Florestal"
    GRITO = "Auuuuuuu! Aqui é UFJ!"
    PASTA_SPRITE = "lobo_guara"
    LACAIO = "lobinho"
    LACAIOS_DE_REFORCO = 4
    REFORCO_A_CADA = 3
    VIDA = 1400
    VELOCIDADE = 165
    DANO = 14
    COR = (255, 140, 60)
    INTERVALO_ATAQUE = 2.8
    INTERVALO_DA_GARRA = 0.07

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.arrancada = Arrancada(carga=0.45, duracao=0.4, velocidade=780, vezes=2)
        self._espera_garra = 0.0

    def atacar(self, jogo):
        self.arrancada.comecar()
        self.marcar(jogo, "poeira", 40, self.posicao + (0, self.raio), duracao=0.5)
        if self.ataques % self.REFORCO_A_CADA == 0:
            self.falar(jogo, "AUUUUU!")
            for lado, angulo in ((60, 0), (-60, 180)):       # o uivo sai para os dois lados
                self.marcar(jogo, "uivo", 70, self.posicao + (lado, -30), duracao=0.8, angulo=angulo,
                            crescimento=1.2)

    def perseguir(self, dt, jogo):
        if self.arrancada.ativa:
            self.arrancada.avancar(dt, self, jogo)
            self._espera_garra -= dt
            if self.arrancada.correndo and self._espera_garra <= 0:      # o bote deixa um rastro de garras
                self._espera_garra = self.INTERVALO_DA_GARRA
                rumo = self.arrancada.rumo
                self.marcar(jogo, "garra", 64, duracao=0.35, angulo=-rumo.as_polar()[1])
        else:
            super().perseguir(dt, jogo)

    def desenhar_corpo(self, tela, camera):
        self.arrancada.desenhar_aviso(tela, camera, self, largura=16)
        super().desenhar_corpo(tela, camera)


class Motorizado(MiniChefe):
    """Mini-chefe que chama carros: eles buzinam parados fora da tela e atravessam por cima do aluno."""

    VEICULO = ""                 # pasta do sprite do carro
    VELOCIDADE_DO_VEICULO = 620
    DANO_DO_VEICULO = 14
    RAIO_DO_VEICULO = 30
    DISTANCIA_DO_VEICULO = 620

    def chamar_veiculo(self, jogo, desvio=0.0):
        lado = jogo.rng.choice((-1, 1))
        rumo = pygame.Vector2(lado, 0).rotate(jogo.rng.uniform(-18, 18))
        alvo = jogo.jogador.posicao + pygame.Vector2(0, desvio)
        partida = alvo - rumo * self.DISTANCIA_DO_VEICULO
        jogo.adicionar(VeiculoDesgovernado(partida, rumo, self.VEICULO, self.VELOCIDADE_DO_VEICULO,
                                           self.DANO_DO_VEICULO * self.fator_de_dano, self.RAIO_DO_VEICULO))


@FabricaDeInimigos.registrar("loira_da_odontologia")
class LoiraDaOdontologia(Motorizado):
    """Não desce do salto e nunca anda sozinha: chama a turma (várias loirinhas iguais a ela, em miniatura),
    arremessa escova, pasta e espelhinho e, entre uma coisa e outra, manda os HB20 brancos passarem por cima
    do aluno."""

    NOME = "Loira da Odontologia"
    ARTIGO = "Uma"
    LOCAL = "LAB. SAUDE"
    ONDE = "nos Laboratórios da Saúde"
    GRITO = "Cuidado com o meu HB20, tá?"
    PASTA_SPRITE = "loira"
    LACAIO = "loirinha"
    LACAIOS_NA_CHEGADA = 6
    LACAIOS_POR_CHAMADA = 4
    TURMA_MAXIMA = 14            # loirinhas vivas ao mesmo tempo
    VEICULO = "hb20"
    VIDA = 1300
    VELOCIDADE = 104
    DANO = 12
    COR = (255, 130, 190)
    INTERVALO_ATAQUE = 2.6

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.turma = []

    def atacar(self, jogo):
        if self.ataques % 2:
            self.chamar_lacaios(jogo, self.LACAIOS_POR_CHAMADA, raio=70)
            self.leque(jogo, 3, 18, 320, 8, "escova", "pasta_de_dente", "espelhinho")
            self.falar(jogo, "Meninas, vem cá!")
        else:
            for i in range(2 + self.ataques // 2 % 2):
                self.chamar_veiculo(jogo, desvio=(i - 1) * 90)
            self.falar(jogo, "BI BI!")

    def chamar_lacaios(self, jogo, quantos, nome=None, raio=90):
        """A turma tem limite: só chama quantas ainda cabem."""
        self.turma = [loirinha for loirinha in self.turma if loirinha.ativo]
        super().chamar_lacaios(jogo, min(quantos, self.TURMA_MAXIMA - len(self.turma)), nome, raio)

    def receber_lacaio(self, jogo, lacaio):
        self.turma.append(lacaio)
        self.marcar(jogo, "dente", 30, lacaio.posicao - (0, 30), duracao=0.6, subida=50)      # chegam brilhando
        super().receber_lacaio(jogo, lacaio)


@FabricaDeInimigos.registrar("agroboy")
class Agroboy(Motorizado):
    """O super-herói da Agronomia: joga maços de dinheiro e chama a caminhonete. Derrotado, chove moeda."""

    NOME = "Agroboy"
    PONTO = (770, 7380)          # no cruzamento dos corredores da lavoura, a oeste
    ONDE = "na lavoura das Agrárias"
    GRITO = "O agro não para! Sabe com quem tá falando?"
    PASTA_SPRITE = "agroboy"
    LACAIO = "boi"
    LACAIOS_NA_CHEGADA = 3
    LACAIOS_DE_REFORCO = 2
    VEICULO = "caminhonete"
    SIMBOLO = "$"
    ARTE_QUE_VOLTA = "chapeu"
    VELOCIDADE_DO_VEICULO = 560
    DANO_DO_VEICULO = 20
    RAIO_DO_VEICULO = 46
    VIDA = 1800
    VELOCIDADE = 110
    DANO = 14
    MOEDAS = 150                 # é cheio de dinheiro
    COR = (120, 220, 100)
    INTERVALO_ATAQUE = 2.3

    def atacar(self, jogo):
        if self.ataques % 2:
            self.leque(jogo, 6, 11, 310, 10, "dinheiro", "milho", "dinheiro", "bota")
        else:
            self.chamar_veiculo(jogo)
            self.disparar(jogo, self.mirar(jogo), 420, 10, "chapeu", raio=14)
            self.falar(jogo, "OLHA A RAM!")

    def criar_projetil(self, direcao, velocidade, dano, arte, raio):
        """O chapéu volta para a mão dele; o resto ele joga fora mesmo."""
        classe = Bumerangue if arte == self.ARTE_QUE_VOLTA else ProjetilTematico
        return classe(self.posicao, direcao * velocidade, dano * self.fator_de_dano, self.SIMBOLO, self.COR, raio,
                      arte=arte)


@FabricaDeInimigos.registrar("grao_mestre_do_culto")
class GraoMestreDoCulto(MiniChefe):
    """Secreto: escondido na mata do canto do campus. Solta uma espiral de três braços que não para, e
    de tempos em tempos os cultistas fecham um círculo em volta do aluno."""

    NOME = "Grão-Mestre do Culto"
    PONTO = (5640, 9640)         # mata fechada no canto sudeste
    ONDE = "em algum canto do campus"
    SECRETO = True
    GRITO = "Você viu demais."
    PASTA_SPRITE = "culto"
    LACAIO = "cultista"
    LACAIOS_NA_CHEGADA = 8
    REFORCO_A_CADA = 14
    VIDA = 2600
    VELOCIDADE = 70
    DANO = 15
    MOEDAS = 90
    COR = (255, 205, 70)
    INTERVALO_ATAQUE = 0.32
    BRACOS = 3
    GIRO_POR_DISPARO = 13

    def atacar(self, jogo):
        arte = "adaga" if self.ataques % 4 == 0 else "chama_dourada"
        self.anel(jogo, self.BRACOS, 230, 9, arte, giro=self.GIRO_POR_DISPARO * self.ataques)

    def chamar_lacaios(self, jogo, quantos, nome=None, raio=90):
        """Os cultistas não nascem do lado do mestre: já aparecem em círculo em volta do aluno."""
        for i in range(quantos):
            lado = pygame.Vector2(260, 0).rotate(360 * i / quantos)
            self.marcar(jogo, "olho", 46, jogo.jogador.posicao + lado - (0, 50), duracao=0.9, subida=30)
            self.receber_lacaio(jogo, FabricaDeInimigos.criar(nome or self.LACAIO, jogo.jogador.posicao + lado,
                                                              self.escala))


@FabricaDeInimigos.registrar("gotica_trevosa")
class GoticaTrevosa(MiniChefe):
    """Some numa nuvem de morcegos, reaparece colada no aluno e solta um anel de corações pretos."""

    NOME = "Gótica Trevosa"
    ARTIGO = "Uma"
    LOCAL = "CONVIVENCIA"
    ONDE = "no Centro de Convivência"
    GRITO = "Você não é como os outros... fica comigo PRA SEMPRE."
    PASTA_SPRITE = "gotica"
    LACAIO = "morcego"
    VIDA = 1250
    VELOCIDADE = 118
    DANO = 13
    COR = (190, 110, 255)
    SIMBOLO = "<3"
    INTERVALO_ATAQUE = 2.5
    DISTANCIA_DO_SUSTO = 190

    def atacar(self, jogo):
        if self.ataques % 2 == 0:                            # aparece do nada perto do aluno
            lado = pygame.Vector2(self.DISTANCIA_DO_SUSTO, 0).rotate(jogo.rng.uniform(0, 360))
            self.marcar(jogo, "nuvem_de_morcegos", 110, duracao=0.7)             # some numa nuvem...
            self.posicao = jogo.mapa.empurrar(jogo.jogador.posicao + lado, self.raio)
            self.marcar(jogo, "nuvem_de_morcegos", 110, duracao=0.7)             # ...e sai de outra
            self.falar(jogo, "Achei você <3")
        self.anel(jogo, 10, 220, 10, "coracao_preto", "rosa_negra", giro=18 * self.ataques)


@FabricaDeInimigos.registrar("et_de_varginha")
class ETDeVarginha(MiniChefe):
    """Mora no Centro de Aulas Secreto 51. Abre feixes de abdução debaixo do aluno e anda com gatos verdes."""

    NOME = "ET de Varginha"
    LOCAL = "CENTRO DE AULAS SECRETO 51"
    ONDE = "no Centro de Aulas Secreto 51"
    GRITO = "Bip. Vim buscar o seu histórico escolar."
    PASTA_SPRITE = "et"
    LACAIO = "gato_alienigena"
    LACAIOS_NA_CHEGADA = 6
    VIDA = 1600
    VELOCIDADE = 112
    DANO = 13
    COR = (130, 255, 110)
    INTERVALO_ATAQUE = 1.5
    RAIO_DO_FEIXE = 95
    DANO_DO_FEIXE = 16

    def atacar(self, jogo):
        adiantado = jogo.jogador.direcao_movimento * (60 if jogo.jogador.movendo else 0)
        jogo.adicionar(FeixeDeAbducao(jogo.jogador.posicao + adiantado, self.RAIO_DO_FEIXE,
                                      self.DANO_DO_FEIXE * self.fator_de_dano))
        if self.ataques % 5 == 0:
            self.chamar_lacaios(jogo, 2, "mini_ovni", raio=140)
            self.falar(jogo, "Bip bip!")


MINI_CHEFES = ("tia_da_cantina", "vigilante", "bibliotecaria", "tecnico_do_laboratorio", "reitor", "lobo_guara",
               "loira_da_odontologia", "agroboy", "grao_mestre_do_culto", "gotica_trevosa", "et_de_varginha")
