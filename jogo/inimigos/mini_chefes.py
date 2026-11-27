"""Mini-chefes do mapa: figuras do campus que o aluno invoca se quiser, em troca de um baú garantido.

Cada um espera no seu local (um círculo de invocação perto de um prédio ou num canto do campus) e, depois
de invocado, guarda aquele pedaço: persegue o aluno só até certa distância do posto e volta para lá se
ele fugir. São fortes de propósito, e cada um traz os próprios lacaios. O tom é de piada interna.
"""
import math
from abc import abstractmethod

import pygame

from jogo.coletaveis.coletaveis import Bigorna, Moeda
from jogo.config import Cor
from jogo.efeitos import TextoFlutuante
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo
from jogo.nucleo.recursos import Recursos
from jogo.nucleo.desenho import desenhar_faixa_de_aviso
from jogo.projeteis.do_campus import (ColunaDeFogo, FeixeDeAbducao, MordidaDaToca, Multa, OndaDeChoque, PapelDoProerd,
                                      ChegadaDoCeia, Silencio, PlacaDigaNao, RugidoDoLeao,
                                      VeiculoDesgovernado)
from jogo.projeteis.tematicos import (Bumerangue, Carimbada, FrascoDeAcido, Marca, PanelaoDeSopa,
                                      ProjetilTematico, arte_existe, imagem_da_arte)


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

    @property
    def progresso_da_mira(self):
        """De 0 a 1, quanto da mira atual já foi."""
        return 1 - self._carga / self.carga_total if self.mirando else 0.0

    @property
    def progresso(self):
        """De 0 a 1, quanto da corrida atual já foi (0 enquanto mira)."""
        return 1 - self._corrida / self.duracao if self.correndo else 0.0

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


class GolpeDeBastao:
    """Golpe corpo a corpo: mira (o chão à frente avisa onde vai bater), avança um passo e bate. A direção é
    escolhida no começo e não muda: dá para fugir para trás ou para o lado. Usado por composição."""

    QUADROS = 6                  # 2 mirando, 1 avançando, 3 batendo e voltando

    def __init__(self, carga, avanco, recuperacao, velocidade, alcance, abertura, dano):
        self.carga, self.avanco, self.recuperacao = carga, avanco, recuperacao
        self.velocidade, self.alcance, self.abertura, self.dano = velocidade, alcance, abertura, dano
        self._tempo = -1.0
        self._bateu = False
        self.rumo = pygame.Vector2(1, 0)

    @property
    def duracao(self):
        return self.carga + self.avanco + self.recuperacao

    @property
    def ativo(self):
        return 0 <= self._tempo < self.duracao

    @property
    def mirando(self):
        return 0 <= self._tempo < self.carga

    @property
    def quadro(self):
        """Qual dos seis quadros da animação mostrar agora."""
        t = self._tempo
        if t < self.carga:
            return 0 if t < self.carga / 2 else 1
        if t < self.carga + self.avanco:
            return 2
        return 3 + min(2, int((t - self.carga - self.avanco) / (self.recuperacao / 3)))

    @property
    def ponto_da_pancada(self):
        return self._origem + self.rumo * self.velocidade * self.avanco

    def comecar(self, chefe, jogo):
        self._tempo = 0.0
        self._bateu = False
        self.rumo = chefe.mirar(jogo)
        self._origem = pygame.Vector2(chefe.posicao)
        chefe.olhando_esquerda = self.rumo.x < 0

    def parar(self):
        self._tempo = -1.0

    def avancar(self, dt, chefe, jogo):
        antes = self._tempo
        self._tempo += dt
        if self.carga <= antes < self.carga + self.avanco:
            chefe.posicao += self.rumo * self.velocidade * dt
        if not self._bateu and self._tempo >= self.carga + self.avanco:
            self._bateu = True
            self.bater(chefe, jogo)
        if self._tempo >= self.duracao:
            self.parar()

    def bater(self, chefe, jogo):
        """A pancada: acerta quem estiver na meia-lua da frente, ao alcance do bastão."""
        ate_o_aluno = jogo.jogador.posicao - chefe.posicao
        chefe.marcar(jogo, "poeira", 36, chefe.posicao + self.rumo * self.alcance * 0.7 + (0, chefe.raio * 0.6),
                     duracao=0.4)
        perto = ate_o_aluno.length() <= self.alcance
        if perto and (ate_o_aluno.length_squared() == 0
                      or abs((self.rumo.angle_to(ate_o_aluno) + 180) % 360 - 180) <= self.abertura / 2):
            if jogo.ferir_jogador(self.dano * chefe.fator_de_dano):
                jogo.adicionar(TextoFlutuante("BASTÃO!", jogo.jogador.posicao - (0, 60), chefe.COR, 22))

    def desenhar_aviso(self, tela, camera, chefe):
        """A meia-lua no chão onde o bastão vai bater, enchendo até a hora da pancada."""
        if not self.mirando:
            return
        centro = camera.para_tela(self.ponto_da_pancada)
        borda = [centro] + [centro + self.rumo.rotate(a) * self.alcance
                            for a in range(-round(self.abertura / 2), round(self.abertura / 2) + 1, 10)]
        cheio = [centro] + [centro + self.rumo.rotate(a) * self.alcance * self._tempo / self.carga
                            for a in range(-round(self.abertura / 2), round(self.abertura / 2) + 1, 10)]
        camada = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(camada, (230, 60, 40, 60), borda)
        pygame.draw.polygon(camada, (230, 60, 40, 110), cheio)
        pygame.draw.polygon(camada, (255, 120, 60, 220), borda, 3)
        tela.blit(camada, (0, 0))


class BatGancho:
    """O gancho do Vigilante, usado por composição: mira onde o aluno está, dispara e, se a ponta chegar com o
    aluno ainda ali (e sem rolar), puxa o aluno até a frente do dono."""

    MIRA = 0.45
    VELOCIDADE = 950
    ALCANCE = 520
    FOLGA = 55                   # quão perto da ponta o aluno tem de estar para ser fisgado
    PUXAO = 0.45
    VELOCIDADE_DO_PUXAO = 1100
    DISTANCIA_FINAL = 70         # onde o aluno para, na frente do dono

    def __init__(self):
        self.etapa = None        # "mirando", "voando", "puxando" ou None
        self._tempo = 0.0
        self.alvo = pygame.Vector2()
        self.ponta = pygame.Vector2()

    @property
    def ativo(self):
        return self.etapa is not None

    @property
    def falta_para_chegar(self):
        return self.ponta.distance_to(self.alvo) / self.VELOCIDADE if self.etapa == "voando" else 0.0

    def comecar(self, dono, jogo):
        rumo = jogo.jogador.posicao - dono.posicao
        if rumo.length() > self.ALCANCE:
            rumo.scale_to_length(self.ALCANCE)
        self.alvo = dono.posicao + rumo
        self.ponta = pygame.Vector2(dono.posicao)
        self.etapa, self._tempo = "mirando", 0.0
        dono.olhando_esquerda = rumo.x < 0

    def avancar(self, dt, dono, jogo):
        """Leva o gancho adiante; devolve "fisgou", "escapou" ou "puxou" quando uma etapa acaba."""
        self._tempo += dt
        if self.etapa == "mirando":
            self.ponta = pygame.Vector2(dono.posicao)
            if self._tempo >= self.MIRA:
                self.etapa, self._tempo = "voando", 0.0
            return None
        if self.etapa == "voando":
            falta = self.alvo - self.ponta
            passo = self.VELOCIDADE * dt
            if falta.length() > passo:
                self.ponta += falta.normalize() * passo
                return None
            self.ponta = pygame.Vector2(self.alvo)
            aluno = jogo.jogador
            if aluno.posicao.distance_to(self.alvo) <= self.FOLGA + aluno.raio and not aluno.rolamento.rolando:
                self.etapa, self._tempo = "puxando", 0.0
                return "fisgou"
            self.etapa = None
            return "escapou"
        destino = dono.posicao + (jogo.jogador.posicao - dono.posicao).normalize() * self.DISTANCIA_FINAL \
            if jogo.jogador.posicao != dono.posicao else pygame.Vector2(dono.posicao)
        falta = destino - jogo.jogador.posicao
        passo = self.VELOCIDADE_DO_PUXAO * dt
        jogo.jogador.posicao += falta if falta.length() <= passo else falta.normalize() * passo
        self.ponta = pygame.Vector2(jogo.jogador.posicao)
        if self._tempo >= self.PUXAO:
            self.etapa = None
            return "puxou"
        return None

    @property
    def quadro(self):
        """Quadro da animação do dono: tirando e apontando a arma, disparando, puxando a corda."""
        if self.etapa == "mirando":
            return 0 if self._tempo < self.MIRA / 2 else 1
        return 2 if self.etapa == "voando" else 3

    def desenhar(self, tela, camera, dono):
        if self.etapa == "mirando":
            desenhar_faixa_de_aviso(tela, camera.para_tela(dono.posicao), camera.para_tela(self.alvo), 30,
                                    dono.COR, self._tempo)
            return
        if self.etapa is None:
            return
        mao = camera.para_tela(dono.posicao + (0, -dono.altura_sprite * 0.1))
        ponta = camera.para_tela(self.ponta)
        pygame.draw.line(tela, Cor.BORDA_ESCURA, mao, ponta, 6)
        pygame.draw.line(tela, (170, 120, 70), mao, ponta, 3)
        rumo = (ponta - mao).normalize() if ponta != mao else pygame.Vector2(1, 0)
        for angulo in (-40, 0, 40):                          # as três garras do gancho
            garra = ponta + rumo.rotate(angulo) * 12
            pygame.draw.line(tela, Cor.BORDA_ESCURA, ponta, garra, 5)
            pygame.draw.line(tela, (200, 200, 210), ponta, garra, 3)


class Laco(BatGancho):
    """O laço do Agroboy: mesmo jeito do gancho (mira, lança, fisga e puxa), com corda e argola."""

    VELOCIDADE = 820
    ALCANCE = 460
    FOLGA = 65
    DISTANCIA_FINAL = 110

    @property
    def quadro(self):
        """Quadro da animação do dono: laço enrolado, girando, lançado, puxando."""
        if self.etapa == "mirando":
            return 0 if self._tempo < self.MIRA / 3 else 1
        return 2 if self.etapa == "voando" else 3

    def desenhar(self, tela, camera, dono):
        if self.etapa == "mirando":
            desenhar_faixa_de_aviso(tela, camera.para_tela(dono.posicao), camera.para_tela(self.alvo), 30,
                                    dono.COR, self._tempo)
            return
        if self.etapa is None:
            return
        mao = camera.para_tela(dono.posicao + (0, -dono.altura_sprite * 0.15))
        ponta = camera.para_tela(self.ponta)
        pygame.draw.line(tela, Cor.BORDA_ESCURA, mao, ponta, 6)
        pygame.draw.line(tela, (180, 120, 60), mao, ponta, 3)
        argola = pygame.Rect(0, 0, 44, 26)
        argola.center = (round(ponta.x), round(ponta.y))
        pygame.draw.ellipse(tela, Cor.BORDA_ESCURA, argola, 6)
        pygame.draw.ellipse(tela, (180, 120, 60), argola, 3)


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
    NIVEIS_DE_EXPERIENCIA = 2.5  # derrubado, vale tantos níveis do aluno (a conta é feita na hora, pelo nível dele)
    MOEDAS = 30
    INTERVALO_ATAQUE = 2.4
    GUARDA = 780                 # até onde ele segue o aluno, contado do posto
    CURA_NO_POSTO = 0.04         # fração da vida por segundo que recupera quando o aluno foge
    COR = (255, 170, 60)
    GANHO_VELOCIDADE = 0.04      # o tempo de partida mexe pouco na velocidade dele
    TENACIDADE = 1.0             # nada puxa, atrasa ou prende um mini-chefe no meio do ataque

    SEGUNDA_FASE_ABAIXO_DE = 0.0             # fração da vida em que entra na segunda fase (0: não tem)
    FALA_DA_SEGUNDA_FASE = ""
    ANUNCIO_DA_SEGUNDA_FASE = ""
    ANDAR_DA_SEGUNDA_FASE = "andar"          # a animação de andar depois de mudar de fase
    INTERVALO_SEGUNDA_FASE = 0.0             # 0: INTERVALO_ATAQUE * FATOR_DA_SEGUNDA_FASE
    FATOR_DA_SEGUNDA_FASE = 0.7              # na segunda fase ataca 30% mais rápido

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.posto = pygame.Vector2(posicao)
        self.solta_bau = True
        self.reposiciona = False
        self.ataques = 0
        self._espera_ataque = 1.2
        self.segunda_fase = False
        self.experiencia_ao_morrer = 0           # calculada na hora da morte, pelo nível do aluno
        self._cena = None        # [animação, duração, tempo, parado]: a animação especial que está tocando
        self._agenda = []        # [segundos que faltam, ação]: o que acontece no meio de uma animação

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
        if (not self.segunda_fase and self.SEGUNDA_FASE_ABAIXO_DE
                and self.vida <= self.vida_maxima * self.SEGUNDA_FASE_ABAIXO_DE):
            self.entrar_na_segunda_fase(jogo)
        self.cumprir_agenda(dt, jogo)
        parado = self._avancar_cena(dt)
        if jogo.jogador.posicao.distance_to(self.posto) > self.GUARDA:      # o aluno fugiu: volta e se recupera
            self.ir_em_direcao(self.posto, dt)
            self.curar(self.vida_maxima * self.CURA_NO_POSTO * dt)
            return
        if not parado:
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
        """Na segunda fase ataca mais rápido: o valor próprio da classe, se ela tiver, ou 30% a menos."""
        if self.segunda_fase:
            return self.INTERVALO_SEGUNDA_FASE or self.INTERVALO_ATAQUE * self.FATOR_DA_SEGUNDA_FASE
        return self.INTERVALO_ATAQUE

    @property
    def valor_em_experiencia(self):
        return self.experiencia_ao_morrer

    # ---- segunda fase e animações especiais
    def entrar_na_segunda_fase(self, jogo):
        """Com pouca vida, muda o jeito de lutar (e não volta atrás, mesmo que se cure). Quem tem segunda fase
        diz as falas e o andar dela; o que muda nos ataques fica no `atacar` de cada um."""
        self.segunda_fase = True
        self.marcar(jogo, "poeira", 56, self.posicao + (0, self.raio), duracao=0.5)
        if self.FALA_DA_SEGUNDA_FASE:
            self.falar(jogo, self.FALA_DA_SEGUNDA_FASE, 22)
        if self.ANUNCIO_DA_SEGUNDA_FASE:
            jogo.anunciar(self.ANUNCIO_DA_SEGUNDA_FASE, 3)

    def encenar(self, animacao, duracao, parado=False):
        """Toca uma animação especial (arremesso, uivo) do primeiro ao último quadro em `duracao` segundos.
        Com `parado`, ele fica no lugar enquanto ela toca."""
        self._cena = [animacao, duracao, 0.0, parado]

    @property
    def encenando(self):
        return self._cena is not None

    def agendar(self, atraso, acao):
        """Faz `acao(jogo)` daqui a `atraso` segundos: a bandeja sai da mão no quadro do arremesso."""
        self._agenda.append([atraso, acao])

    def cumprir_agenda(self, dt, jogo):
        for item in list(self._agenda):
            item[0] -= dt
            if item[0] <= 0:
                self._agenda.remove(item)
                item[1](jogo)

    def _avancar_cena(self, dt):
        """Leva a animação especial adiante; diz se ele deve ficar parado neste passo."""
        if self._cena is None:
            return False
        animacao, duracao, tempo, parado = self._cena
        if tempo >= duracao:
            self._cena = None
            return False
        quadros = len(self.animador.animacoes[animacao].quadros) if animacao in self.animador.animacoes else 1
        self.mostrar(animacao, min(quadros - 1, int(tempo / duracao * quadros)))
        self._cena[2] += dt
        return parado

    def mostrar(self, animacao, indice):
        """Segura a animação no quadro pedido: golpes e arremessos seguem o tempo do ataque, não um relógio."""
        self.animador.tocar(animacao)
        if self.animador.atual == animacao:
            self.animador.tempo = (indice + 0.5) / self.animador.animacao.fps

    def escolher_animacao(self):
        if self._cena is not None:
            return self._cena[0]
        return self.ANDAR_DA_SEGUNDA_FASE if self.segunda_fase else "andar"

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

    def _desenhar_aura(self, tela, camera):
        """Segunda fase: uma aura pulsando na cor dele por trás do corpo, como a da matéria nos professores."""
        centro = camera.para_tela(self.posicao)
        pulso = 0.5 + 0.5 * math.sin(self.tempo * 6)
        raio = round(self.raio * (1.35 + 0.15 * pulso))
        aura = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura, (*self.COR, round(70 + 50 * pulso)), (raio, raio), raio)
        pygame.draw.circle(aura, (*self.COR, 200), (raio, raio), raio, 3)
        tela.blit(aura, aura.get_rect(center=(round(centro.x), round(centro.y))))

    def ao_chegar_o_chefe(self, jogo):
        """Um chefe principal chegou: o mini-chefe continua onde está."""

    def assustar(self, duracao):
        """Mini-chefe não cai em trote."""

    def possuir(self, duracao):
        """Nem é possuído pelo Fusca."""

    def empurrar(self, direcao, forca=180):
        """Nem é empurrado."""

    def ao_morrer(self, jogo):
        """Solta a experiência de 2 a 3 níveis do aluno (acompanha qualquer curva de experiência), o baú, as
        moedas e a bigorna."""
        self.experiencia_ao_morrer = jogo.jogador.experiencia_para_subir(self.NIVEIS_DE_EXPERIENCIA)
        super().ao_morrer(jogo)
        jogo.adicionar(Moeda(self.posicao - (18, 0), self.MOEDAS))
        jogo.adicionar(Bigorna(self.posicao + (30, 10)))
        jogo.marcos.add("mini_chefe")
        jogo.contar_mini_chefe()
        jogo.marcados.discard(self.CHAVE)
        jogo.anunciar(f"{self.NOME}: fora de combate! Pegue o baú e a bigorna", 3)

    def desenhar_corpo(self, tela, camera):
        if self.segunda_fase:
            self._desenhar_aura(tela, camera)
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
    """Enorme. Arremessa bandejas, pratos feitos e frigideiras em leque e, de três em três ataques, ergue o
    panelão e joga para o alto: ele cai onde o aluno estava e deixa uma poça de sopa quente, com talheres para
    todo lado. Com metade da vida acaba a merenda: pega a concha gigante e sai girando atrás do aluno."""

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
    TEMPO_DO_ARREMESSO = 0.5
    SAIDA_DA_BANDEJA = 0.25      # segundos do começo do arremesso até a bandeja sair da mão
    TEMPO_DO_PANELAO = 0.9
    SAIDA_DO_PANELAO = 0.6       # quando o panelão sai das mãos (5º dos 6 quadros)

    SEGUNDA_FASE_ABAIXO_DE = 0.5
    FALA_DA_SEGUNDA_FASE = "Acabou a merenda!"
    ANUNCIO_DA_SEGUNDA_FASE = "A Tia da Cantina pegou a concha gigante!"
    ANDAR_DA_SEGUNDA_FASE = "andar_concha"
    DURACAO_DO_GIRO = 2.4
    VELOCIDADE_DO_GIRO = 1.9     # fator da velocidade enquanto gira
    DANO_DO_GIRO = 20
    ALCANCE_DO_GIRO = 95         # do centro dela até onde a concha alcança
    INTERVALO_DO_GIRO = 0.5      # segundos entre uma conchada e a próxima
    INTERVALO_DOS_RESPINGOS = 0.45

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self._giro = 0.0
        self._espera_conchada = 0.0
        self._espera_respingo = 0.0

    @property
    def girando(self):
        return self._giro > 0

    def atacar(self, jogo):
        vez = self.ataques % 3
        if vez == 0:
            if self.segunda_fase:
                self.girar(jogo)
            else:
                self.erguer_o_panelao(jogo)
        elif vez == 1:
            self.arremessar(jogo, "bandeja")
        elif self.segunda_fase:
            self.erguer_o_panelao(jogo)
        else:
            self.arremessar(jogo, "prato_feito", "frigideira")
            self.falar(jogo, "Repete o prato!")

    def arremessar(self, jogo, *artes):
        """Puxa o braço para trás e solta o leque no quadro do arremesso."""
        self.encenar("arremessar", self.TEMPO_DO_ARREMESSO)
        self.agendar(self.SAIDA_DA_BANDEJA, lambda j: self.leque(j, 5, 14, 290, 9, *artes))

    def erguer_o_panelao(self, jogo):
        """Agacha, ergue o panelão acima da cabeça, parada, e joga onde o aluno estiver na hora."""
        self.encenar("panelao", self.TEMPO_DO_PANELAO, parado=True)
        self.falar(jogo, "SOPA QUENTE!")
        self.agendar(self.SAIDA_DO_PANELAO, self._jogar_o_panelao)

    def _jogar_o_panelao(self, jogo):
        jogo.adicionar(PanelaoDeSopa(jogo.jogador.posicao, self.RAIO_DA_SOPA, self.DANO_DA_SOPA * self.fator_de_dano))
        self.anel(jogo, 12, 190, 9, "concha", "colher_de_pau")

    def girar(self, jogo):
        self._giro = self.DURACAO_DO_GIRO
        self._espera_conchada = self._espera_respingo = 0.0
        self.falar(jogo, "Fila andando!", 22)

    def perseguir(self, dt, jogo):
        if not self.girando:
            super().perseguir(dt, jogo)
            return
        self._giro -= dt
        self._espera_conchada -= dt
        self._espera_respingo -= dt
        self.mostrar("girar", int(self._giro * 14) % 4)
        self.ir_em_direcao(jogo.jogador.posicao, dt, self.velocidade * self.VELOCIDADE_DO_GIRO)
        perto = self.posicao.distance_to(jogo.jogador.posicao) <= self.ALCANCE_DO_GIRO + jogo.jogador.raio
        if perto and self._espera_conchada <= 0:
            self._espera_conchada = self.INTERVALO_DO_GIRO
            if jogo.ferir_jogador(self.DANO_DO_GIRO * self.fator_de_dano):
                jogo.adicionar(TextoFlutuante("CONCHADA!", jogo.jogador.posicao - (0, 50), self.COR, 20))
        if self._espera_respingo <= 0:                       # a concha espirra sopa (e conchas) para os lados
            self._espera_respingo = self.INTERVALO_DOS_RESPINGOS
            self.anel(jogo, 4, 220, 8, "concha", giro=self._giro * 200)

    def escolher_animacao(self):
        return "girar" if self.girando else super().escolher_animacao()


@FabricaDeInimigos.registrar("vigilante")
class Vigilante(MiniChefe):
    """O segurança que se veste de morcego: aponta a lanterna e arranca em linha reta. Anda com morcegos. Com
    metade da vida saca o bat-gancho: fisga o aluno, puxa até ele e acerta uma voadora."""

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

    SEGUNDA_FASE_ABAIXO_DE = 0.5
    FALA_DA_SEGUNDA_FASE = "Ninguém foge da vigilância!"
    ANUNCIO_DA_SEGUNDA_FASE = "O Vigilante sacou o bat-gancho!"
    TEMPO_DA_VOADORA = 0.55
    CHUTE_DA_VOADORA = 0.3       # quando o pé chega (3º dos 4 quadros)
    ALCANCE_DA_VOADORA = 115
    DANO_DA_VOADORA = 24

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.arrancada = Arrancada(carga=0.7, duracao=0.55, velocidade=700)
        self.gancho = BatGancho()

    def atacar(self, jogo):
        if self.segunda_fase and self.ataques % 2 == 0:
            self.gancho.comecar(self, jogo)
            self.falar(jogo, "Bat-gancho!")
            return
        if self.ataques % 2 == 0:                            # antes de correr, solta os batarangues
            self.leque(jogo, 3, 22, 430, 8, "batarangue")
            self.falar(jogo, "Parado aí!")
        self.arrancada.comecar()

    def criar_projetil(self, direcao, velocidade, dano, arte, raio):
        """O batarangue vai e volta."""
        return Bumerangue(self.posicao, direcao * velocidade, dano * self.fator_de_dano, self.SIMBOLO, self.COR,
                          raio, arte=arte)

    def perseguir(self, dt, jogo):
        if self.gancho.ativo:
            resultado = self.gancho.avancar(dt, self, jogo)
            self.mostrar("gancho", self.gancho.quadro)
            if resultado == "fisgou":
                self.falar(jogo, "Te peguei!")
            elif resultado == "escapou":
                self.falar(jogo, "Escapou...")
            elif resultado == "puxou":
                self.voadora(jogo)
        elif self.arrancada.ativa:
            self.arrancada.avancar(dt, self, jogo)
            if self.arrancada.mirando:
                self.mostrar("lanterna", min(3, int(self.arrancada.progresso_da_mira * 4)))
            elif self.arrancada.correndo:
                self.mostrar("arrancada", int(self.tempo * 12) % 4)
        else:
            super().perseguir(dt, jogo)

    def voadora(self, jogo):
        self.encenar("voadora", self.TEMPO_DA_VOADORA, parado=True)
        self.agendar(self.CHUTE_DA_VOADORA, self._chutar)

    def _chutar(self, jogo):
        if self.posicao.distance_to(jogo.jogador.posicao) <= self.ALCANCE_DA_VOADORA:
            if jogo.ferir_jogador(self.DANO_DA_VOADORA * self.fator_de_dano):
                jogo.adicionar(TextoFlutuante("VOADORA!", jogo.jogador.posicao - (0, 50), self.COR, 22))

    def escolher_animacao(self):
        if self.gancho.ativo:
            return "gancho"
        if self.arrancada.ativa and not self.encenando:
            return "lanterna" if self.arrancada.mirando else "arrancada"
        return super().escolher_animacao()

    def desenhar_corpo(self, tela, camera):
        self.arrancada.desenhar_aviso(tela, camera, self)
        self.gancho.desenhar(tela, camera, self)
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
    """Anota o nome do aluno no caderno preto e, ao fechar o caderno, solta as multas de atraso: cada uma que
    acerta leva moedas. De três em três ataques arremessa um livro de capa dura. Com metade da vida pede
    silêncio: quem fica perto do "SHHH!" atira mais devagar por um tempo."""

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
    TEMPO_ANOTANDO = 0.7
    SAIDA_DAS_MULTAS = 0.55      # quando ela fecha o caderno (último quadro)
    TEMPO_DO_ARREMESSO = 0.5
    SAIDA_DO_LIVRO = 0.25

    SEGUNDA_FASE_ABAIXO_DE = 0.5
    FALA_DA_SEGUNDA_FASE = "SILÊNCIO NA BIBLIOTECA!"
    ANUNCIO_DA_SEGUNDA_FASE = "A Bibliotecária pediu silêncio: perto dela as armas emperram!"
    TEMPO_DO_SHHH = 0.9
    RAIO_DO_SILENCIO = 230
    DANO_DO_SILENCIO = 6

    def atacar(self, jogo):
        if self.segunda_fase and self.ataques % 2 == 0:
            self.pedir_silencio(jogo)
            return
        if self.ataques % 3 == 0:                            # um livro de capa dura e as multas, no arremesso
            self.encenar("arremessar", self.TEMPO_DO_ARREMESSO)
            self.agendar(self.SAIDA_DO_LIVRO, lambda j: (self.leque(j, 3, 16, 300, 8, "livro"), self.multar(j)))
        else:
            self.encenar("anotar", self.TEMPO_ANOTANDO)
            self.agendar(self.SAIDA_DAS_MULTAS, self.multar)
        self.falar(jogo, "MULTA POR ATRASO!" if self.ataques % 2 else "Vou anotar o seu nome...")

    def multar(self, jogo):
        giro = 360 / self.MULTAS / 2 * (self.ataques % 2)
        for i in range(self.MULTAS):
            direcao = pygame.Vector2(1, 0).rotate(giro + 360 * i / self.MULTAS)
            jogo.adicionar(Multa(self.posicao, direcao * 210, self.DANO_DA_MULTA * self.fator_de_dano,
                                 self.VALOR_DA_MULTA, self.COR))

    def pedir_silencio(self, jogo):
        """O chão em volta dela avisa enquanto ela respira fundo; no "SHHH!", quem estiver perto emperra."""
        self.encenar("shhh", self.TEMPO_DO_SHHH, parado=True)
        jogo.adicionar(Silencio(self.posicao, self.RAIO_DO_SILENCIO, self.DANO_DO_SILENCIO * self.fator_de_dano))


@FabricaDeInimigos.registrar("tecnico_do_laboratorio")
class TecnicoDoLaboratorio(MiniChefe):
    """Resultado dos próprios experimentos: enorme, verde, vai aonde quer. Arremessa seringas e regenera o tempo
    todo. Com pouca vida entra em fúria (a segunda fase dele, que não passa nem quando ele se recupera): fica
    mais rápido, arremessa três seringas de cada vez e soca o chão em volta dele."""

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
    TEMPO_DO_ARREMESSO = 0.45
    SAIDA_DA_SERINGA = 0.22

    SEGUNDA_FASE_ABAIXO_DE = FURIA_ABAIXO_DE
    FALA_DA_SEGUNDA_FASE = "FÚRIA!"
    ANUNCIO_DA_SEGUNDA_FASE = "O Técnico do Laboratório entrou em fúria!"
    ANDAR_DA_SEGUNDA_FASE = "andar_furia"
    TEMPO_DA_PANCADA = 0.8
    RAIO_DA_PANCADA = 170
    DANO_DA_PANCADA = 24

    @property
    def em_furia(self):
        return self.segunda_fase

    @property
    def intervalo_de_ataque(self):
        return self.INTERVALO_ATAQUE * (0.6 if self.em_furia else 1)

    def perseguir(self, dt, jogo):
        self.curar(self.vida_maxima * self.REGENERACAO * dt)
        self.ir_em_direcao(jogo.jogador.posicao, dt,
                           self.velocidade * (self.VELOCIDADE_EM_FURIA if self.em_furia else 1))

    def atacar(self, jogo):
        if self.em_furia and self.ataques % 3 == 0:
            self.socar_o_chao(jogo)
            return
        self.encenar("arremessar", self.TEMPO_DO_ARREMESSO)
        self.agendar(self.SAIDA_DA_SERINGA, self.arremessar_seringas)
        if self.ataques % 3 == 0:                            # um frasco para o alto: cai e vira poça de ácido
            jogo.adicionar(FrascoDeAcido(jogo.jogador.posicao, self.RAIO_DO_ACIDO,
                                         self.DANO_DO_ACIDO * self.fator_de_dano))
            self.falar(jogo, "Experimento!")

    def arremessar_seringas(self, jogo):
        rumo = self.mirar(jogo)
        for desvio in ((-12, 0, 12) if self.em_furia else (0,)):
            self.disparar(jogo, rumo.rotate(desvio), 380, 14, "seringa", raio=16)

    def socar_o_chao(self, jogo):
        """Ergue os punhos e soca: o chão em volta dele avisa e explode no quadro da pancada."""
        self.encenar("socar_chao", self.TEMPO_DA_PANCADA, parado=True)
        jogo.adicionar(OndaDeChoque(self.posicao, self.RAIO_DA_PANCADA, self.DANO_DA_PANCADA * self.fator_de_dano))
        self.falar(jogo, "FÚRIA!", 22)


@FabricaDeInimigos.registrar("reitor")
class Reitor(MiniChefe):
    """Muito, muito alto (o Reitor de verdade é). Carimba parado: o carimbo desce em cima do aluno e os ofícios
    saem em anel quando ele bate; no meio, despacha portarias. O meme dele são as promessas para o ano que vem: a
    cada carimbo, solta uma delas. À distância joga emblemas da UFJ. Com metade da vida apresenta o projeto e o
    CEIA prometido finalmente chega: as placas do CEIA caem do céu em volta do aluno e cabeças do CEIA voam."""

    NOME = "Reitor"
    LOCAL = "REITORIA"
    ONDE = "na Reitoria"
    GRITO = "Ano que vem chega o CEIA ein... Estamos conversando... Vai sair ein..."
    PROMESSAS = ("Ano que vem vamos ter datacenter ein...", "Estamos conversando...", "Vai sair ein...",
                 "O CEIA tá quase...")
    PASTA_SPRITE = "reitor"
    RAIO_DO_CARIMBO = 90
    DANO_DO_CARIMBO = 16
    LACAIO = "carimbo"
    RAIO = 42                    # o boneco tem 375 px de altura: 1,5x o tamanho de antes
    VIDA = 2000
    VELOCIDADE = 96
    DANO = 15
    COR = (120, 220, 150)
    INTERVALO_ATAQUE = 2.1
    TEMPO_DO_CARIMBO = 0.8
    SAIDA_DOS_OFICIOS = 0.45     # quando o carimbo bate no chão (3º dos 4 quadros)
    PARA_PARA_CARIMBAR = 450     # mais longe do aluno que isso, ele carimba andando (para chegar logo)

    SEGUNDA_FASE_ABAIXO_DE = 0.5
    FALA_DA_SEGUNDA_FASE = "Agora vai! O CEIA tá chegando!"
    ANUNCIO_DA_SEGUNDA_FASE = "O Reitor apresentou o projeto: o CEIA está chegando!"
    TEMPO_DA_APRESENTACAO = 1.0
    SAIDA_DAS_PLACAS = 0.5       # quando ele ergue a planta (3º dos 4 quadros)
    PLACAS = 5
    RAIO_DA_PLACA = 70
    DANO_DA_PLACA = 14

    def atacar(self, jogo):
        if self.ataques % 2:
            perto = self.posicao.distance_to(jogo.jogador.posicao) < self.PARA_PARA_CARIMBAR
            self.encenar("carimbar", self.TEMPO_DO_CARIMBO, parado=perto)
            jogo.adicionar(Carimbada(jogo.jogador.posicao, self.RAIO_DO_CARIMBO,
                                     self.DANO_DO_CARIMBO * self.fator_de_dano))
            self.agendar(self.SAIDA_DOS_OFICIOS, lambda j: self.anel(j, 16, 200, 10, "oficio", giro=11 * self.ataques))
            self.falar(jogo, self.PROMESSAS[(self.ataques // 2) % len(self.PROMESSAS)], 16)
        elif self.segunda_fase:
            self.encenar("apresentar", self.TEMPO_DA_APRESENTACAO, parado=True)
            self.agendar(self.SAIDA_DAS_PLACAS, self.chover_placas)
        else:
            self.leque(jogo, 7, 9, 330, 10, "logo_ufj", "portaria")

    def chover_placas(self, jogo):
        """Uma placa do CEIA em cima do aluno e as outras em volta; cabeças do CEIA voam na direção dele."""
        alvo = pygame.Vector2(jogo.jogador.posicao)
        pontos = [alvo] + [alvo + pygame.Vector2(jogo.rng.uniform(130, 230), 0).rotate(jogo.rng.uniform(0, 360))
                           for _ in range(self.PLACAS - 1)]
        for ponto in pontos:
            jogo.adicionar(ChegadaDoCeia(ponto, self.RAIO_DA_PLACA, self.DANO_DA_PLACA * self.fator_de_dano))
        self.leque(jogo, 5, 12, 300, 10, "ceia_icone", "logo_ufj")
        self.falar(jogo, "Chegou! Quer dizer... quase.", 16)


@FabricaDeInimigos.registrar("lobo_guara")
class LoboGuara(MiniChefe):
    """O mascote da UFJ. Rápido: agacha, dá dois botes seguidos e, de tempos em tempos, uiva parado para chamar
    a ninhada antes do bote. Com metade da vida vem a lua cheia: cava, some debaixo da terra, vai atrás do aluno
    por baixo do chão e sai bem embaixo dele mordendo."""

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
    TEMPO_DO_UIVO = 0.8

    SEGUNDA_FASE_ABAIXO_DE = 0.5
    FALA_DA_SEGUNDA_FASE = "AUUUUU! Lua cheia!"
    ANUNCIO_DA_SEGUNDA_FASE = "Lua cheia: o Lobo-Guará vai para debaixo da terra!"
    TEMPO_CAVANDO = 0.6
    TEMPO_ESCONDIDO = 1.3
    VELOCIDADE_ESCONDIDO = 2.2   # fator da velocidade por baixo da terra
    TEMPO_EMERGINDO = 0.9
    RAIO_DA_MORDIDA = 90
    DANO_DA_MORDIDA = 22
    INTERVALO_DO_RASTRO = 0.12

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.arrancada = Arrancada(carga=0.45, duracao=0.4, velocidade=780, vezes=2)
        self._espera_garra = 0.0
        self._toca = None        # [etapa ("cavando", "escondido" ou "emergindo"), segundos que faltam]
        self._espera_rastro = 0.0

    @property
    def escondido(self):
        return self._toca is not None and self._toca[0] == "escondido"

    @property
    def invulneravel(self):
        """Debaixo da terra (e entrando ou saindo dela) não leva golpe."""
        if self._toca is None:
            return False
        etapa, falta = self._toca
        return (etapa == "escondido" or (etapa == "cavando" and falta < self.TEMPO_CAVANDO / 2)
                or (etapa == "emergindo" and falta > self.TEMPO_EMERGINDO * 0.75))

    def atacar(self, jogo):
        if self.segunda_fase and self.ataques % 2 == 0:
            self.entocar(jogo)
            return
        if self.ataques % self.REFORCO_A_CADA == 0:          # uiva parado (o uivo sai para os dois lados)
            self.encenar("uivar", self.TEMPO_DO_UIVO, parado=True)
            self.falar(jogo, "AUUUUU!")
            for lado, angulo in ((60, 0), (-60, 180)):
                self.marcar(jogo, "uivo", 70, self.posicao + (lado, -30), duracao=0.8, angulo=angulo,
                            crescimento=1.2)
            self.agendar(self.TEMPO_DO_UIVO, lambda j: self.dar_o_bote(j))
        else:
            self.dar_o_bote(jogo)

    def dar_o_bote(self, jogo):
        self.arrancada.comecar()
        self.marcar(jogo, "poeira", 40, self.posicao + (0, self.raio), duracao=0.5)

    def entocar(self, jogo):
        self._toca = ["cavando", self.TEMPO_CAVANDO]
        self.marcar(jogo, "poeira", 60, self.posicao + (0, self.raio), duracao=0.7)

    def perseguir(self, dt, jogo):
        if self._toca is not None:
            self._avancar_toca(dt, jogo)
        elif self.arrancada.ativa:
            self.arrancada.avancar(dt, self, jogo)
            if self.arrancada.mirando:
                self.mostrar("bote", 0)
            elif self.arrancada.correndo:
                self.mostrar("bote", 1 + min(2, int(self.arrancada.progresso * 3)))
            self._espera_garra -= dt
            if self.arrancada.correndo and self._espera_garra <= 0:      # o bote deixa um rastro de garras
                self._espera_garra = self.INTERVALO_DA_GARRA
                rumo = self.arrancada.rumo
                self.marcar(jogo, "garra", 64, duracao=0.35, angulo=-rumo.as_polar()[1])
        else:
            super().perseguir(dt, jogo)

    def _avancar_toca(self, dt, jogo):
        etapa, falta = self._toca
        falta -= dt
        if etapa == "cavando":
            self.mostrar("cavar", min(3, int((1 - falta / self.TEMPO_CAVANDO) * 4)))
            self._toca = ["escondido", self.TEMPO_ESCONDIDO] if falta <= 0 else [etapa, falta]
        elif etapa == "escondido":                           # um montinho de terra corre atrás do aluno
            self.ir_em_direcao(jogo.jogador.posicao, dt, self.velocidade * self.VELOCIDADE_ESCONDIDO)
            self._espera_rastro -= dt
            if self._espera_rastro <= 0:
                self._espera_rastro = self.INTERVALO_DO_RASTRO
                self.marcar(jogo, "poeira", 34, self.posicao + (0, 10), duracao=0.6)
            if falta <= 0:
                self.emergir(jogo)
            else:
                self._toca = [etapa, falta]
        else:
            self.mostrar("emergir", min(3, int((1 - falta / self.TEMPO_EMERGINDO) * 4)))
            self._toca = None if falta <= 0 else [etapa, falta]

    def emergir(self, jogo):
        """Sai do chão bem debaixo do aluno: o chão racha primeiro, então dá para pular fora."""
        self.posicao = pygame.Vector2(jogo.jogador.posicao)
        self._toca = ["emergindo", self.TEMPO_EMERGINDO]
        jogo.adicionar(MordidaDaToca(self.posicao, self.RAIO_DA_MORDIDA, self.DANO_DA_MORDIDA * self.fator_de_dano))
        self.agendar(MordidaDaToca.AVISO, lambda j: self.anel(j, 8, 230, 9, "osso", giro=22.5))

    def tocar_jogador(self, jogo):
        """Cavando, debaixo da terra ou saindo dela, quem morde é a MordidaDaToca, não o encostão."""
        if self._toca is None:
            super().tocar_jogador(jogo)

    def escolher_animacao(self):
        if self._toca is not None:
            return "emergir" if self._toca[0] == "emergindo" else "cavar"
        if self.arrancada.ativa:
            return "bote"
        return super().escolher_animacao()

    def desenhar_corpo(self, tela, camera):
        if self.escondido:                                   # só o montinho de terra andando
            if arte_existe("poeira"):
                monte = imagem_da_arte("poeira", 44)
                tela.blit(monte, monte.get_rect(midbottom=camera.para_tela(self.posicao) + (0, 24)))
            return
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
    """Não desce do salto e nunca anda sozinha: joga o cabelo e chama a turma (várias loirinhas iguais a ela, em
    miniatura), arremessa escova, pasta e espelhinho e, entre uma coisa e outra, aperta a chave e manda os HB20
    brancos passarem por cima do aluno. Com metade da vida pega a broca e sai atravessando o aluno."""

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
    TEMPO_DA_CHAMADA = 0.7
    SAIDA_DA_TURMA = 0.35        # quando ela acena com a escova (3º dos 4 quadros)
    TEMPO_DA_CHAVE = 0.7

    SEGUNDA_FASE_ABAIXO_DE = 0.5
    FALA_DA_SEGUNDA_FASE = "Agora é com a broca!"
    ANUNCIO_DA_SEGUNDA_FASE = "A Loira da Odontologia pegou a broca!"
    DANO_DA_BROCA = 22
    ALCANCE_DA_BROCA = 30        # além dos raios dos dois

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.turma = []
        self.arrancada = Arrancada(carga=0.5, duracao=0.6, velocidade=650)
        self._brocou = False

    def atacar(self, jogo):
        if self.segunda_fase and self.ataques % 2 == 0:
            self.arrancada.comecar()
            self._brocou = False
            self.falar(jogo, "Abre a boca!")
        elif self.ataques % 2:
            self.encenar("chamar", self.TEMPO_DA_CHAMADA)
            self.agendar(self.SAIDA_DA_TURMA, self._chamar_a_turma)
            self.falar(jogo, "Meninas, vem cá!")
        else:
            self.encenar("chave", self.TEMPO_DA_CHAVE)
            for i in range(2 + self.ataques // 2 % 2):
                self.chamar_veiculo(jogo, desvio=(i - 1) * 90)
            self.falar(jogo, "BI BI!")

    def _chamar_a_turma(self, jogo):
        self.chamar_lacaios(jogo, self.LACAIOS_POR_CHAMADA, raio=70)
        self.leque(jogo, 3, 18, 320, 8, "escova", "pasta_de_dente", "espelhinho")

    def chamar_lacaios(self, jogo, quantos, nome=None, raio=90):
        """A turma tem limite: só chama quantas ainda cabem."""
        self.turma = [loirinha for loirinha in self.turma if loirinha.ativo]
        super().chamar_lacaios(jogo, min(quantos, self.TURMA_MAXIMA - len(self.turma)), nome, raio)

    def receber_lacaio(self, jogo, lacaio):
        self.turma.append(lacaio)
        self.marcar(jogo, "dente", 30, lacaio.posicao - (0, 30), duracao=0.6, subida=50)      # chegam brilhando
        super().receber_lacaio(jogo, lacaio)

    def perseguir(self, dt, jogo):
        if not self.arrancada.ativa:
            super().perseguir(dt, jogo)
            return
        self.arrancada.avancar(dt, self, jogo)
        self.mostrar("broca", 0 if self.arrancada.mirando else 1 + int(self.tempo * 12) % 3)
        perto = self.posicao.distance_to(jogo.jogador.posicao) <= self.raio + jogo.jogador.raio + self.ALCANCE_DA_BROCA
        if self.arrancada.correndo and perto and not self._brocou:
            self._brocou = True
            if jogo.ferir_jogador(self.DANO_DA_BROCA * self.fator_de_dano):
                jogo.adicionar(TextoFlutuante("BROCADA!", jogo.jogador.posicao - (0, 50), self.COR, 20))

    def escolher_animacao(self):
        return "broca" if self.arrancada.ativa else super().escolher_animacao()

    def desenhar_corpo(self, tela, camera):
        self.arrancada.desenhar_aviso(tela, camera, self)
        super().desenhar_corpo(tela, camera)


@FabricaDeInimigos.registrar("agroboy")
class Agroboy(Motorizado):
    """O super-herói da Agronomia: faz chover maços de dinheiro e chama a caminhonete. Com metade da vida monta no
    touro (rodeio): anda mais rápido, o encostão dói mais, e ele laça o aluno e o touro arranca em cima dele.
    Derrotado, chove moeda."""

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
    TEMPO_DO_DINHEIRO = 0.6
    SAIDA_DO_DINHEIRO = 0.35     # quando as notas saem da mão (3º dos 4 quadros)

    SEGUNDA_FASE_ABAIXO_DE = 0.5
    FALA_DA_SEGUNDA_FASE = "Segura peão!"
    ANUNCIO_DA_SEGUNDA_FASE = "O Agroboy montou no touro: é rodeio!"
    ANDAR_DA_SEGUNDA_FASE = "andar_touro"
    VELOCIDADE_NO_TOURO = 1.6
    ENCOSTAO_NO_TOURO = 1.6

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.laco = Laco()
        self.arrancada = Arrancada(carga=0.3, duracao=0.6, velocidade=760)

    @property
    def velocidade_atual(self):
        return self.velocidade * (self.VELOCIDADE_NO_TOURO if self.segunda_fase else 1)

    @property
    def dano_de_contato(self):
        return super().dano_de_contato * (self.ENCOSTAO_NO_TOURO if self.segunda_fase else 1)

    def atacar(self, jogo):
        if self.ataques % 2:
            self.encenar("dinheiro", self.TEMPO_DO_DINHEIRO)
            self.agendar(self.SAIDA_DO_DINHEIRO,
                         lambda j: self.leque(j, 6, 11, 310, 10, "dinheiro", "milho", "dinheiro", "bota"))
        elif self.segunda_fase:
            self.laco.comecar(self, jogo)
            self.falar(jogo, "Laçou!")
        else:
            self.chamar_veiculo(jogo)
            self.disparar(jogo, self.mirar(jogo), 420, 10, "chapeu", raio=14)
            self.falar(jogo, "OLHA A RAM!")

    def criar_projetil(self, direcao, velocidade, dano, arte, raio):
        """O chapéu volta para a mão dele; o resto ele joga fora mesmo."""
        classe = Bumerangue if arte == self.ARTE_QUE_VOLTA else ProjetilTematico
        return classe(self.posicao, direcao * velocidade, dano * self.fator_de_dano, self.SIMBOLO, self.COR, raio,
                      arte=arte)

    def perseguir(self, dt, jogo):
        if self.laco.ativo:
            if self.laco.avancar(dt, self, jogo) == "puxou":
                self.arrancada.comecar()                     # puxou: o touro arranca em cima do aluno
                self.falar(jogo, "IIIIRRA!", 22)
            self.mostrar("laco", self.laco.quadro)
        elif self.arrancada.ativa:
            self.arrancada.avancar(dt, self, jogo)
        else:
            self.ir_em_direcao(jogo.jogador.posicao, dt, self.velocidade_atual)

    def escolher_animacao(self):
        return "laco" if self.laco.ativo else super().escolher_animacao()

    def desenhar_corpo(self, tela, camera):
        self.laco.desenhar(tela, camera, self)
        self.arrancada.desenhar_aviso(tela, camera, self, largura=30)
        super().desenhar_corpo(tela, camera)


@FabricaDeInimigos.registrar("grao_mestre_do_culto")
class GraoMestreDoCulto(MiniChefe):
    """Secreto: escondido na mata do canto do campus. Solta uma espiral de três braços que não para, e de tempos
    em tempos faz o ritual, parado, e os cultistas fecham um círculo em volta do aluno. Com metade da vida
    ascende: flutua, a espiral ganha cinco braços e o olho que tudo vê marca o aluno para uma coluna de fogo."""

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
    TEMPO_DO_RITUAL = 1.2

    SEGUNDA_FASE_ABAIXO_DE = 0.5
    FALA_DA_SEGUNDA_FASE = "Eu vejo TUDO."
    ANUNCIO_DA_SEGUNDA_FASE = "O Grão-Mestre ascendeu!"
    ANDAR_DA_SEGUNDA_FASE = "andar_ascensao"
    BRACOS_ASCENDIDO = 5
    COLUNA_A_CADA = 9            # de quantos em quantos disparos o olho marca o aluno
    RAIO_DA_COLUNA = 85
    DANO_DA_COLUNA = 20

    def atacar(self, jogo):
        arte = "adaga" if self.ataques % 4 == 0 else "chama_dourada"
        bracos = self.BRACOS_ASCENDIDO if self.segunda_fase else self.BRACOS
        self.anel(jogo, bracos, 230, 9, arte, giro=self.GIRO_POR_DISPARO * self.ataques)
        if self.segunda_fase and self.ataques % self.COLUNA_A_CADA == 0:
            jogo.adicionar(ColunaDeFogo(jogo.jogador.posicao, self.RAIO_DA_COLUNA,
                                        self.DANO_DA_COLUNA * self.fator_de_dano))

    def chamar_lacaios(self, jogo, quantos, nome=None, raio=90):
        """O ritual: ele para, e os cultistas não nascem do lado dele, já aparecem em círculo em volta do aluno."""
        self.encenar("ritual", self.TEMPO_DO_RITUAL, parado=True)
        for i in range(quantos):
            lado = pygame.Vector2(260, 0).rotate(360 * i / quantos)
            self.marcar(jogo, "olho", 46, jogo.jogador.posicao + lado - (0, 50), duracao=0.9, subida=30)
            self.receber_lacaio(jogo, FabricaDeInimigos.criar(nome or self.LACAIO, jogo.jogador.posicao + lado,
                                                              self.escala))

    def balanco(self):
        """Ascendido, flutua."""
        return 10 + 5 * math.sin(self.tempo * 3) if self.segunda_fase else super().balanco()


@FabricaDeInimigos.registrar("gotica_trevosa")
class GoticaTrevosa(MiniChefe):
    """Vira uma nuvem de morcegos, reaparece colada no aluno e solta um anel de corações pretos. Com metade da vida
    pega a boneca de vodu: uma caveira aparece em cima do aluno e, quando ela enfia a agulha, ele leva o golpe
    onde estiver (só rolando na hora escapa)."""

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
    TEMPO_SUMINDO = 0.5

    SEGUNDA_FASE_ABAIXO_DE = 0.5
    FALA_DA_SEGUNDA_FASE = "Olha o que eu costurei pra você <3"
    ANUNCIO_DA_SEGUNDA_FASE = "A Gótica Trevosa pegou a boneca de vodu: role na hora da agulhada!"
    TEMPO_DO_VODU = 0.9
    AGULHADA = 0.55              # quando a agulha entra na boneca (3º dos 4 quadros)
    DANO_DO_VODU = 18

    def atacar(self, jogo):
        if self.segunda_fase and self.ataques % 2:
            self.vodu(jogo)
            return
        if self.ataques % 2 == 0:                            # some numa nuvem e aparece do nada perto do aluno
            self.encenar("sumir", self.TEMPO_SUMINDO, parado=True)
            self.agendar(self.TEMPO_SUMINDO, self._reaparecer)
        else:
            self.anel(jogo, 10, 220, 10, "coracao_preto", "rosa_negra", giro=18 * self.ataques)

    def _reaparecer(self, jogo):
        lado = pygame.Vector2(self.DISTANCIA_DO_SUSTO, 0).rotate(jogo.rng.uniform(0, 360))
        self.marcar(jogo, "nuvem_de_morcegos", 110, duracao=0.7)                 # some numa nuvem...
        self.posicao = jogo.mapa.empurrar(jogo.jogador.posicao + lado, self.raio)
        self.marcar(jogo, "nuvem_de_morcegos", 110, duracao=0.7)                 # ...e sai de outra
        self.falar(jogo, "Achei você <3")
        self.anel(jogo, 10, 220, 10, "coracao_preto", "rosa_negra", giro=18 * self.ataques)

    def vodu(self, jogo):
        self.encenar("vodu", self.TEMPO_DO_VODU, parado=True)
        aluno = jogo.jogador
        self.marcar(jogo, "caveira", 40, aluno.posicao - (0, 70), duracao=self.AGULHADA, crescimento=0.6, dono=aluno)
        self.agendar(self.AGULHADA, self._agulhada)

    def _agulhada(self, jogo):
        if jogo.ferir_jogador(self.DANO_DO_VODU * self.fator_de_dano):
            jogo.adicionar(TextoFlutuante("AGULHADA!", jogo.jogador.posicao - (0, 50), self.COR, 20))


@FabricaDeInimigos.registrar("et_de_varginha")
class ETDeVarginha(MiniChefe):
    """Mora no Centro de Aulas Secreto 51. Faz telepatia e abre feixes de abdução debaixo do aluno; anda com gatos
    verdes. Com metade da vida entra no disco voador: anda mais rápido, abre três feixes de cada vez e o raio
    debaixo do disco puxa e machuca quem fica perto."""

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
    TEMPO_DA_TELEPATIA = 0.6

    SEGUNDA_FASE_ABAIXO_DE = 0.5
    FALA_DA_SEGUNDA_FASE = "Bip bip! Chamei a carona."
    ANUNCIO_DA_SEGUNDA_FASE = "O ET de Varginha entrou no disco voador!"
    ANDAR_DA_SEGUNDA_FASE = "andar_disco"
    INTERVALO_SEGUNDA_FASE = 1.4             # o disco dispara o raio que puxa: golpe mais pesado, um pouco menos que 30%
    VELOCIDADE_NO_DISCO = 1.5
    FEIXES_NO_DISCO = 3
    ALCANCE_DO_RAIO = 150        # o raio debaixo do disco
    PUXAO_DO_RAIO = 90           # pixels por segundo que ele puxa o aluno
    DANO_DO_RAIO = 6
    INTERVALO_DO_RAIO = 0.5

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self._espera_raio = 0.0

    def atacar(self, jogo):
        if not self.segunda_fase:                            # no disco ele não desce para a telepatia
            self.encenar("telepatia", self.TEMPO_DA_TELEPATIA)
        if self.segunda_fase:
            for i in range(self.FEIXES_NO_DISCO):            # um no aluno e dois dos lados, em triângulo
                lado = pygame.Vector2(0, 0) if i == 0 else pygame.Vector2(150, 0).rotate(jogo.rng.uniform(0, 360))
                jogo.adicionar(FeixeDeAbducao(jogo.jogador.posicao + lado, self.RAIO_DO_FEIXE,
                                              self.DANO_DO_FEIXE * self.fator_de_dano))
        else:
            adiantado = jogo.jogador.direcao_movimento * (60 if jogo.jogador.movendo else 0)
            jogo.adicionar(FeixeDeAbducao(jogo.jogador.posicao + adiantado, self.RAIO_DO_FEIXE,
                                          self.DANO_DO_FEIXE * self.fator_de_dano))
        if self.ataques % 5 == 0:
            self.chamar_lacaios(jogo, 2, "mini_ovni", raio=140)
            self.falar(jogo, "Bip bip!")

    def perseguir(self, dt, jogo):
        if not self.segunda_fase:
            super().perseguir(dt, jogo)
            return
        self.ir_em_direcao(jogo.jogador.posicao, dt, self.velocidade * self.VELOCIDADE_NO_DISCO)
        self.puxar_com_o_raio(dt, jogo)

    def puxar_com_o_raio(self, dt, jogo):
        """O raio debaixo do disco puxa o aluno para perto e machuca de tempos em tempos."""
        self._espera_raio -= dt
        falta = self.posicao - jogo.jogador.posicao
        if falta.length() > self.ALCANCE_DO_RAIO or falta.length_squared() < 1:
            return
        jogo.jogador.posicao += falta.normalize() * min(falta.length(), self.PUXAO_DO_RAIO * dt)
        if self._espera_raio <= 0:
            self._espera_raio = self.INTERVALO_DO_RAIO
            jogo.ferir_jogador(self.DANO_DO_RAIO * self.fator_de_dano)

    def desenhar_corpo(self, tela, camera):
        if self.segunda_fase:                                # o círculo do raio no chão, debaixo do disco
            centro = camera.para_tela(self.posicao)
            lado = self.ALCANCE_DO_RAIO * 2
            chao = pygame.Surface((lado, lado), pygame.SRCALPHA)
            pulso = 0.5 + 0.5 * math.sin(self.tempo * 6)
            pygame.draw.circle(chao, (*self.COR, int(35 + 30 * pulso)), (lado // 2, lado // 2), self.ALCANCE_DO_RAIO)
            pygame.draw.circle(chao, (*self.COR, 200), (lado // 2, lado // 2), self.ALCANCE_DO_RAIO, 3)
            chao = pygame.transform.scale(chao, (lado, round(lado * 0.6)))
            tela.blit(chao, chao.get_rect(center=(round(centro.x), round(centro.y + self.altura_sprite * 0.4))))
        super().desenhar_corpo(tela, camera)

    def balanco(self):
        return 8 + 4 * math.sin(self.tempo * 4) if self.segunda_fase else super().balanco()


@FabricaDeInimigos.registrar("leao_do_proerd")
class LeaoDoProerd(MiniChefe):
    """O mascote da palestra, só que enorme, musculoso e sem nenhum senso de humor. Arremessa cartilhas e
    certificados, desce a placa de DIGA NÃO em cima do aluno e, de três em três ataques, para e ruge: quem
    está perto fica paralisado de medo e ele chama mais cães farejadores. Os malandros do fundão que ele traz
    morrem de medo dele; os cães seguem o rastro do aluno.

    Com metade da vida acaba a palestra (segunda fase): tira o bastão de beisebol, que mira, avança e bate
    forte, e come os malandros para recuperar vida."""

    NOME = "Leão do PROERD"
    LOCAL = "AUDITORIO"
    ONDE = "no Auditório"
    GRITO = "Quem aqui ainda não fez a redação do PROERD?"
    PASTA_SPRITE = "leao_do_proerd"
    LACAIO = "malandro"
    LACAIOS_NA_CHEGADA = 6
    RAIO = 48
    VIDA = 1900
    VELOCIDADE = 100
    DANO = 16
    COR = (255, 170, 40)
    INTERVALO_ATAQUE = 2.4

    PAPEIS = 6                   # cartilhas e certificados por arremesso
    MEDALHAS = 8
    RAIO_DA_PLACA = 100
    DANO_DA_PLACA = 16
    RAIO_DO_RUGIDO = 200
    DANO_DO_RUGIDO = 12
    TEMPO_DO_RUGIDO = 1.4        # segundos parado, rugindo
    CAES_NA_CHEGADA = 2          # dos LACAIOS_NA_CHEGADA, quantos são cães (o resto é malandro)
    CAES_POR_RUGIDO = 2
    MATILHA_MAXIMA = 6           # cães vivos ao mesmo tempo

    SEGUNDA_FASE_ABAIXO_DE = 0.5             # com metade da vida ele tira o bastão
    FALA_DA_SEGUNDA_FASE = "Acabou a palestra."
    ANUNCIO_DA_SEGUNDA_FASE = "O Leão do PROERD tirou o bastão!"
    ANDAR_DA_SEGUNDA_FASE = "andar_bastao"
    INTERVALO_SEGUNDA_FASE = 1.9             # a meia-lua do bastão pesa mais que a cartilha: só 20% mais rápido
    DANO_DO_BASTAO = 28
    ALCANCE_DO_BASTAO = 150
    ABERTURA_DO_BASTAO = 150                 # graus da meia-lua que o bastão varre
    TEMPO_COMENDO = 1.6
    CURA_POR_MALANDRO = 0.08                 # fração da vida máxima
    ALCANCE_DA_FOME = 420                    # até onde ele alcança um malandro para comer

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self._rugido = 0.0
        self._comendo = 0.0
        self._curou = False
        self.matilha = []
        self.malandros = []
        self.golpe = GolpeDeBastao(carga=0.7, avanco=0.25, recuperacao=0.5, velocidade=520,
                                   alcance=self.ALCANCE_DO_BASTAO, abertura=self.ABERTURA_DO_BASTAO,
                                   dano=self.DANO_DO_BASTAO)

    @property
    def rugindo(self):
        return self._rugido > 0

    @property
    def comendo(self):
        return self._comendo > 0

    @property
    def indice_do_quadro_comendo(self):
        return min(3, int((1 - self._comendo / self.TEMPO_COMENDO) * 4))

    # ---- chegada e lacaios
    def ao_chegar(self, jogo):
        """Chega com os malandros e com os cães."""
        self.chamar_lacaios(jogo, self.LACAIOS_NA_CHEGADA - self.CAES_NA_CHEGADA)
        self.chamar_caes(jogo, self.CAES_NA_CHEGADA)

    def chamar_caes(self, jogo, quantos):
        """Solta cães farejadores dos lados dele, sem passar do tamanho da matilha."""
        self.matilha = [cao for cao in self.matilha if cao.ativo]
        for i in range(min(quantos, self.MATILHA_MAXIMA - len(self.matilha))):
            lado = pygame.Vector2(110, 0).rotate(180 * i + 90 * (self.ataques % 2))
            cao = FabricaDeInimigos.criar("cao_farejador", self.posicao + lado, self.escala)
            self.matilha.append(cao)
            self.marcar(jogo, "pegada", 34, cao.posicao + (0, 20), duracao=0.8)
            jogo.adicionar(cao)

    def receber_lacaio(self, jogo, lacaio):
        """Os malandros que ele chama sabem muito bem de quem fugir (e ele sabe onde estão quando bate a fome)."""
        lacaio.temido = self
        self.malandros.append(lacaio)
        super().receber_lacaio(jogo, lacaio)

    # ---- ataques
    def atacar(self, jogo):
        if self.segunda_fase:
            vez = self.ataques % 4
            if vez in (1, 3):
                self.golpe.comecar(self, jogo)
                self.falar(jogo, "Aqui é na base do bastão!" if vez == 1 else "DIGA NÃO!", 20)
            elif vez == 2:
                self.comer(jogo)
            else:
                self.rugir(jogo)
            return
        vez = self.ataques % 3
        if vez == 1:
            self.leque(jogo, self.PAPEIS, 12, 320, 9, "cartilha", "certificado")
            self.falar(jogo, "Leia a cartilha.")
        elif vez == 2:
            jogo.adicionar(PlacaDigaNao(jogo.jogador.posicao, self.RAIO_DA_PLACA,
                                        self.DANO_DA_PLACA * self.fator_de_dano))
            self.anel(jogo, self.MEDALHAS, 210, 8, "medalha", giro=17 * self.ataques)
            self.falar(jogo, "DIGA NÃO!", 22)
        else:
            self.rugir(jogo)

    def rugir(self, jogo):
        self._rugido = self.TEMPO_DO_RUGIDO
        jogo.adicionar(RugidoDoLeao(self.posicao, self.RAIO_DO_RUGIDO, self.DANO_DO_RUGIDO * self.fator_de_dano))
        for lado, angulo in ((70, 0), (-70, 180)):         # o rugido sai para os dois lados
            self.marcar(jogo, "rugido", 80, self.posicao + (lado, -self.altura_sprite / 4), duracao=1.0,
                        angulo=angulo, crescimento=0.8)
        self.chamar_caes(jogo, self.CAES_POR_RUGIDO)
        self.falar(jogo, "ROOOAAAR!", 24)

    def comer(self, jogo):
        """Agarra o malandro mais perto (se não há nenhum ao alcance, chama um) e come, parado."""
        self.malandros = [m for m in self.malandros if m.ativo]
        ao_alcance = [m for m in self.malandros if m.posicao.distance_to(self.posicao) <= self.ALCANCE_DA_FOME]
        if not ao_alcance:
            self.chamar_lacaios(jogo, 1, raio=60)
            ao_alcance = self.malandros[-1:]
        if not ao_alcance:
            return
        presa = min(ao_alcance, key=lambda m: m.posicao.distance_to(self.posicao))
        jogo.adicionar(TextoFlutuante("SOCORRO!", presa.posicao - (0, 34), Cor.TEXTO, 14))
        presa.remover()                                      # vai para a boca: não solta nota nem moeda
        self.olhando_esquerda = presa.posicao.x < self.posicao.x
        self._comendo = self.TEMPO_COMENDO
        self._curou = False
        self.falar(jogo, "NHAC!", 22)

    # ---- movimento
    def criar_projetil(self, direcao, velocidade, dano, arte, raio):
        """O material da palestra voa girando."""
        return PapelDoProerd(self.posicao, direcao * velocidade, dano * self.fator_de_dano, self.SIMBOLO, self.COR,
                             raio, arte=arte)

    def perseguir(self, dt, jogo):
        if self.golpe.ativo:
            self.golpe.avancar(dt, self, jogo)
            if self.golpe.ativo:
                self.mostrar("golpe", self.golpe.quadro)
            return
        if self.comendo:                                     # come parado; a vida volta quando ele engole
            self.mostrar("comer", self.indice_do_quadro_comendo)
            self._comendo -= dt
            if not self._curou and self.indice_do_quadro_comendo >= 3:
                self._curou = True
                cura = self.vida_maxima * self.CURA_POR_MALANDRO
                self.curar(cura)
                jogo.adicionar(TextoFlutuante(f"+{round(cura)}", self.posicao - (0, self.altura_sprite / 2),
                                              Cor.CURA, 20))
            return
        if self.rugindo:                                     # rugindo ele não sai do lugar e treme
            self._rugido -= dt
            return
        super().perseguir(dt, jogo)

    # ---- desenho
    def escolher_animacao(self):
        if self.comendo:
            return "comer"
        if self.golpe.ativo:
            return "golpe"
        return super().escolher_animacao()

    def balanco(self):
        """O tremor do rugido."""
        return 3 * math.sin(self._rugido * 60) if self.rugindo else super().balanco()

    def desenhar_corpo(self, tela, camera):
        self.golpe.desenhar_aviso(tela, camera, self)
        super().desenhar_corpo(tela, camera)


MINI_CHEFES = ("tia_da_cantina", "vigilante", "bibliotecaria", "tecnico_do_laboratorio", "reitor", "lobo_guara",
               "loira_da_odontologia", "agroboy", "grao_mestre_do_culto", "gotica_trevosa", "et_de_varginha",
               "leao_do_proerd")
