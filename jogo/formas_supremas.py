"""O que as armas soltam na forma suprema (nível máximo) e nas colabs.

No nível máximo a arma deixa de ser "a mesma, só mais forte": ela passa a soltar outra
coisa, com mecânica própria (a Apostila vira uma bola de neve de conteúdo, o Caramelo vira
matilha caçadora...). As colabs seguem a mesma ideia, mais longe: são armas novas.
A arte fica em assets/sprites/supremas/.
"""
import math

import pygame

from jogo.ajudantes.ajudantes import Ajudante, CachorroCaramelo, FuscaVeiculo, QuadroBrancoNoChao
from jogo.efeitos import Efeito, GolpeClaude
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import (ControleRicochete, EstrelaGemini, MovimentoSerpente, PequiArremessado,
                                      ProjetilDoHeroi)

PASTA = "sprites/supremas/"


def desenhar_imagem(tela, camera, caminho, posicao, altura, angulo=0.0, alfa=255):
    """Desenha a arte de uma forma suprema centrada na posição, no tamanho e no giro pedidos."""
    imagem = Recursos.na_altura(Recursos.imagem(caminho), max(4, int(altura)))
    if angulo:
        imagem = Recursos.rotacionada(imagem, angulo)
    if alfa < 255:
        imagem = imagem.copy()
        imagem.set_alpha(max(0, int(alfa)))
    c = camera.para_tela(posicao)
    tela.blit(imagem, imagem.get_rect(center=(round(c.x), round(c.y))))


class Estouro(Efeito):
    """Explosão que fere uma vez quem está na área e mostra uma arte crescendo e sumindo."""

    def __init__(self, posicao, raio, dano, imagem=PASTA + "supernova.png", excluir=None, duracao=0.4):
        super().__init__(posicao, duracao, raio)
        self.dano = dano
        self.imagem = imagem
        self.excluir = excluir
        self._feriu = False

    def ao_atualizar(self, dt, jogo):
        if self._feriu:
            return
        self._feriu = True
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if inimigo is not self.excluir:
                jogo.causar_dano(inimigo, self.dano, inimigo.posicao - self.posicao)

    def desenhar(self, tela, camera):
        desenhar_imagem(tela, camera, self.imagem, self.posicao, self.raio * 2 * (0.45 + 0.75 * self.fracao),
                        angulo=self.fracao * 60, alfa=255 * (1 - self.fracao ** 2))


class AreaQueFere(Ajudante):
    """Base das coisas que ficam um tempo no jogo ferindo quem encosta, cada inimigo a cada `ESPERA` segundos."""

    ESPERA = 0.35

    def __init__(self, posicao, raio, dano, duracao):
        super().__init__(posicao, raio)
        self.dano = dano
        self.duracao = duracao
        self.tempo = 0.0
        self._feridos = {}

    def esta_visivel(self, camera):
        return True

    def ao_ferir(self, inimigo, jogo):
        """Gancho: efeito extra em quem foi ferido."""

    def ferir(self, dt, jogo, direcao=None):
        for inimigo in list(self._feridos):
            self._feridos[inimigo] -= dt
            if self._feridos[inimigo] <= 0:
                del self._feridos[inimigo]
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if inimigo not in self._feridos:
                self._feridos[inimigo] = self.ESPERA
                jogo.causar_dano(inimigo, self.dano, direcao if direcao is not None else inimigo.posicao - self.posicao)
                self.ao_ferir(inimigo, jogo)

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if self.tempo >= self.duracao:
            self.remover()
            return
        self.mover(dt, jogo)
        self.ferir(dt, jogo)

    def mover(self, dt, jogo):
        """Gancho: áreas que andam."""

    @property
    def alfa_do_fim(self):
        resto = self.duracao - self.tempo
        return 255 if resto > 0.4 else max(0, int(255 * resto / 0.4))


# ------------------------------------------------------------------ formas supremas das armas

class CobraRei(MovimentoSerpente, ProjetilDoHeroi):
    """Cobra Python no máximo: cobra coroada, maior e bem mais rápida, que segue reto na direção da mira."""

    IMAGEM = PASTA + "cobra_rei.png"
    ALTURA = 48
    DURACAO = 2.4
    RAIO = 18
    AMPLITUDE = 20

    def __init__(self, posicao, velocidade, dano, perfuracao=1):
        super().__init__(posicao, velocidade, dano, perfuracao=perfuracao, raio=self.RAIO)


class CachorroDaMatilha(CachorroCaramelo):
    """Caramelo no máximo: uma matilha de muitos cachorros pequenos, em duas rodas, bem mais rápidos."""

    ALTURA_DO_DESENHO = 30                 # com o contorno dourado fica do tamanho do cachorro comum
    FATOR_DA_RODA_DE_DENTRO = 0.6

    def __init__(self, dono, angulo, arma, por_dentro=False):
        super().__init__(dono, angulo, arma)
        self.por_dentro = por_dentro

    def atualizar(self, dt, jogo):
        super().atualizar(dt, jogo)
        if self.por_dentro:                # a roda de dentro gira no outro sentido, mais perto do herói
            self.angulo -= 2 * self.arma.valor("velocidade") * dt
            raio = self.arma.valor("raio") * self.FATOR_DA_RODA_DE_DENTRO
            nova = self.dono.posicao + pygame.Vector2(math.cos(self.angulo), math.sin(self.angulo)) * raio
            self.olhando_esquerda = nova.x < self.posicao.x
            self.posicao = nova

    def desenhar(self, tela, camera):
        imagem = Recursos.na_altura(self.animador.quadro_atual, self.ALTURA_DO_DESENHO)
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.olhando_esquerda, aura=self.aura,
                        deslocamento_y=abs(math.sin(self.tempo * 14)) * 4)


class EstrelaSupernova(EstrelaGemini):
    """Gemini no máximo: a última divisão de cada estrela explode em supernova."""

    ALTURA = 30
    RAIO_DA_EXPLOSAO = 120

    def ao_acertar(self, inimigo, jogo):
        super().ao_acertar(inimigo, jogo)
        if self.geracoes <= 0:
            jogo.adicionar(Estouro(self.posicao, self.RAIO_DA_EXPLOSAO, self.dano, excluir=inimigo))


class FuscaMonstro(FuscaVeiculo):
    """Fusca Azul no máximo: um fusca de rodas gigantes que esmaga, possui e passa de novo por cima."""

    ALTURA = 110
    VELOCIDADE = 520
    ESPERA = 0.45              # o mesmo inimigo é esmagado de novo enquanto estiver embaixo

    def __init__(self, posicao, sentido, possessao, dano):
        super().__init__(posicao, sentido, possessao, dano)
        self.raio = 78
        self._esmagados = {}

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.posicao.x += self.sentido * self.VELOCIDADE * dt
        for inimigo in list(self._esmagados):
            self._esmagados[inimigo] -= dt
            if self._esmagados[inimigo] <= 0:
                del self._esmagados[inimigo]
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if inimigo not in self._esmagados:
                self._esmagados[inimigo] = self.ESPERA
                inimigo.possuir(self.possessao)
                jogo.causar_dano(inimigo, self.dano, pygame.Vector2(self.sentido, -0.3), forte=True)
        if self.tempo > 0.5 and not jogo.camera.visivel(self.posicao, 320):
            self.remover()

    def desenhar(self, tela, camera):
        imagem = Recursos.na_altura(Recursos.imagem(PASTA + "fusca_monstro.png"), self.ALTURA)
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.sentido < 0,
                        deslocamento_y=abs(math.sin(self.tempo * 22)) * 6)


class CampoDeEspinhos(AreaQueFere):
    """O que sobra do Pequi no máximo: um tapete de espinhos que fere e segura quem pisa."""

    camada = 0

    def ao_ferir(self, inimigo, jogo):
        inimigo.atrasar(0.5)

    def desenhar(self, tela, camera):
        cresce = min(1.0, self.tempo / 0.2)
        desenhar_imagem(tela, camera, PASTA + "espinhos.png", self.posicao, self.raio * 2 * cresce, alfa=self.alfa_do_fim * 0.8)


class PequiDeOuro(PequiArremessado):
    """Pequi no máximo: além de estourar, deixa um campo de espinhos onde caiu."""

    DURACAO_DO_CAMPO = 3.5

    def ao_acertar(self, inimigo, jogo):
        super().ao_acertar(inimigo, jogo)
        jogo.adicionar(CampoDeEspinhos(self.posicao, self.raio_explosao * 0.75, self.dano * 0.3, self.DURACAO_DO_CAMPO))


class FeixeDeFibra(Ajudante):
    """Wi-Fi no máximo: um feixe de fibra óptica gira em volta do herói queimando bem além do campo."""

    camada = 2
    COMPRIMENTO = 430
    VELOCIDADE_ANGULAR = 2.6
    INTERVALO = 0.12
    LARGURA = 22

    def __init__(self, dono, arma):
        super().__init__(dono.posicao, self.COMPRIMENTO)
        self.dono, self.arma = dono, arma
        self.angulo = 0.0
        self._espera = 0.0

    def esta_visivel(self, camera):
        return True

    @property
    def ponta(self):
        return self.posicao + pygame.Vector2(self.COMPRIMENTO, 0).rotate_rad(self.angulo)

    def atualizar(self, dt, jogo):
        self.posicao = pygame.Vector2(self.dono.posicao)
        self.angulo += self.VELOCIDADE_ANGULAR * dt
        self._espera -= dt
        if self._espera > 0:
            return
        self._espera = self.INTERVALO
        dano = self.arma.valor("dano") * self.dono.multiplicador_dano
        for inimigo in jogo.inimigos_proximos(self.posicao, self.COMPRIMENTO + 30):
            if Colisao.segmento_acerta_circulo(self.posicao, self.ponta, self.LARGURA, inimigo.posicao, inimigo.raio):
                jogo.causar_dano(inimigo, dano)

    def desenhar(self, tela, camera):
        inicio, fim = camera.para_tela(self.posicao), camera.para_tela(self.ponta)
        cor = self.arma.aura or (255, 214, 90)
        pygame.draw.line(tela, (70, 180, 255), inicio, fim, 12)
        pygame.draw.line(tela, cor, inicio, fim, 7)
        pygame.draw.line(tela, (255, 255, 255), inicio, fim, 3)
        pygame.draw.circle(tela, (255, 255, 255), (round(fim.x), round(fim.y)), 9)
        pygame.draw.circle(tela, cor, (round(fim.x), round(fim.y)), 6)


class BolaDeConteudo(AreaQueFere):
    """Apostila no máximo: uma bola de neve de matéria acumulada, que rola pela tela e cresce no caminho."""

    camada = 2
    VELOCIDADE = 340
    RAIO_INICIAL, RAIO_FINAL = 34, 105
    ESPERA = 0.28

    def __init__(self, posicao, direcao, dano, duracao):
        super().__init__(posicao, self.RAIO_INICIAL, dano, duracao)
        self.direcao = pygame.Vector2(direcao).normalize() if pygame.Vector2(direcao).length_squared() else pygame.Vector2(1, 0)
        self.giro = 0.0

    def mover(self, dt, jogo):
        self.posicao += self.direcao * self.VELOCIDADE * dt
        self.raio = self.RAIO_INICIAL + (self.RAIO_FINAL - self.RAIO_INICIAL) * min(1.0, self.tempo / (self.duracao * 0.7))
        self.giro -= math.degrees(self.VELOCIDADE * dt / self.raio) * (1 if self.direcao.x >= 0 else -1)

    def desenhar(self, tela, camera):
        desenhar_imagem(tela, camera, PASTA + "bola_de_conteudo.png", self.posicao, self.raio * 2.1, angulo=self.giro,
                        alfa=self.alfa_do_fim)


class AulaMagna(QuadroBrancoNoChao):
    """Quadro Branco no máximo: a área vira um redemoinho de matéria que puxa os inimigos para o centro."""

    PUXAO = 150                # pixels por segundo em direção ao centro

    def atualizar(self, dt, jogo):
        super().atualizar(dt, jogo)
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio * 1.25):
            rumo = self.posicao - inimigo.posicao
            if rumo.length_squared() > 100:
                inimigo.posicao += rumo.normalize() * self.PUXAO * dt

    def desenhar(self, tela, camera):
        resto = self.duracao - self.tempo
        desenhar_imagem(tela, camera, PASTA + "redemoinho.png", self.posicao, self.raio * 2.3, angulo=-self.tempo * 200,
                        alfa=150 if resto > 0.5 else 150 * resto / 0.5)


class ControleLendario(ControleRicochete):
    """Controle no máximo: cada ricochete aumenta o combo (mais dano) e o último acerto explode."""

    IMAGEM = PASTA + "controle_lendario.png"
    ALTURA = 36
    GANHO_POR_COMBO = 0.2
    RAIO_DO_FINAL = 120

    def ao_acertar(self, inimigo, jogo):
        tinha = self.ricochetes
        super().ao_acertar(inimigo, jogo)
        if self.ricochetes < tinha:
            self.dano *= 1 + self.GANHO_POR_COMBO
        else:                                   # não achou para onde ir ou acabou o combo: explode
            jogo.adicionar(Estouro(self.posicao, self.RAIO_DO_FINAL, self.dano, excluir=inimigo))


def golpe_em_cadeia(jogo, arma, dono, primeiro, dano, origem, saltos=4, alcance=280, perda=0.75):
    """Claude no máximo: o golpe salta do alvo para os inimigos vizinhos, um depois do outro."""
    atingidos, atual = [primeiro], primeiro
    for _ in range(saltos):
        vizinhos = [e for e in jogo.inimigos_proximos(atual.posicao, alcance) if e not in atingidos]
        if not vizinhos:
            break
        proximo = min(vizinhos, key=lambda e: e.posicao.distance_squared_to(atual.posicao))
        dano *= perda
        jogo.causar_dano(proximo, dano, proximo.posicao - atual.posicao, forte=True)
        arma.lancar(jogo, GolpeClaude(proximo.posicao.copy(), 40, origem=atual.posicao.copy()))
        atingidos.append(proximo)
        atual = proximo


# ------------------------------------------------------------------ colabs

class SerpenteEstelarProjetil(MovimentoSerpente, ProjetilDoHeroi):
    """Serpente Estelar: cobra cósmica que cruza a tela atravessando tudo; cada mordida estoura em estrelas."""

    IMAGEM = "sprites/serpente_estelar.png"
    PASTA_SPRITE = "serpente_estelar"
    ALTURA = 50
    DURACAO = 2.6
    AMPLITUDE = 26
    FREQUENCIA = 7

    def __init__(self, posicao, velocidade, dano, raio_estouro, dano_estouro):
        super().__init__(posicao, velocidade, dano, perfuracao=10 ** 6, raio=34)
        self.raio_estouro, self.dano_estouro = raio_estouro, dano_estouro

    def ao_acertar(self, inimigo, jogo):
        jogo.adicionar(Estouro(inimigo.posicao, self.raio_estouro, self.dano_estouro, excluir=inimigo, duracao=0.35))


class PromptDisparado(ProjetilDoHeroi):
    """Bala da Metralhadora de Prompts: um balão de conversa, verde ou laranja."""

    ALTURA = 20
    DURACAO = 1.1

    def __init__(self, posicao, velocidade, dano, laranja=False, perfuracao=2):
        self.IMAGEM = PASTA + ("prompt_laranja.png" if laranja else "prompt_verde.png")
        super().__init__(posicao, velocidade, dano, perfuracao=perfuracao, raio=11)


class MetralhadoraFlutuante(Ajudante):
    """As duas IAs fundidas numa metralhadora que flutua ao lado do herói e aponta para a mira."""

    camada = 2
    DESLOCAMENTO = 46

    def __init__(self, dono):
        super().__init__(dono.posicao, 20)
        self.dono = dono
        self.tempo = 0.0
        self.atirando = False
        self.animador = self.criar_animador("metralhadora", "sprites/metralhadora.png", 56)

    @property
    def boca(self):
        """Ponto de onde saem os prompts."""
        return self.posicao + self.dono.direcao_mira * 34

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if self.atirando:
            self.animador.atualizar(dt * 2.5)
        lado = pygame.Vector2(-self.dono.direcao_mira.y, self.dono.direcao_mira.x)
        alvo = self.dono.posicao + lado * -self.DESLOCAMENTO * (1 if self.dono.direcao_mira.x >= 0 else -1) \
            + pygame.Vector2(0, math.sin(self.tempo * 4) * 4)
        self.posicao += (alvo - self.posicao) * min(1.0, dt * 12)

    def desenhar(self, tela, camera):
        imagem = self.animador.quadro_atual
        mira = self.dono.direcao_mira
        if mira.x < 0:                            # apontando para a esquerda: vira para não ficar de cabeça para baixo
            imagem = Recursos.espelhada(imagem)
            angulo = -math.degrees(math.atan2(-mira.y, -mira.x))
        else:
            angulo = -math.degrees(math.atan2(mira.y, mira.x))
        desenhar_sprite(tela, camera, imagem, self.posicao, angulo=angulo or 0.001, sombra=False, aura=self.aura)
