"""Ataques com a cara de quem lança: a bandeja da Tia da Cantina, a seringa do Técnico, o "dx" do Cálculo.

A arte fica em assets/ataques/<nome>.png (montada por ferramentas/montar_ataques.py). Quem não tem arte
continua saindo como a bolinha com o símbolo de `ProjetilDaMateria`, então nada quebra se faltar um arquivo.
"""
import math

import pygame

from jogo.efeitos import Efeito, TextoFlutuante
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import ProjetilDaMateria

PASTA = "ataques"
_existe = {}


def arte_existe(arte):
    """Se assets/ataques/<arte>.png existe (a resposta fica guardada)."""
    if arte not in _existe:
        _existe[arte] = bool(arte) and (Recursos.pasta / PASTA / f"{arte}.png").is_file()
    return _existe[arte]


def imagem_da_arte(arte, altura):
    return Recursos.imagem(f"{PASTA}/{arte}.png", max(4, round(altura)))


def imagem_na_largura(arte, largura):
    """A arte com a largura pedida (poças e marcas no chão são medidas pelo raio)."""
    original = Recursos.imagem(f"{PASTA}/{arte}.png")
    return imagem_da_arte(arte, largura * original.get_height() / original.get_width())


class ProjetilTematico(ProjetilDaMateria):
    """Projétil inimigo desenhado como um objeto. Cada arte voa de um jeito: umas apontam para onde vão
    (seringa, adaga), outras giram (bandeja, maço de dinheiro) e o resto vai em pé, balançando."""

    APONTAM = {"escova", "pasta_de_dente", "espelhinho", "broca", "rosa_negra", "milho", "laser", "seringa",
               "adaga", "chama_dourada", "caneta", "ponteiro", "giz", "concha", "colher_de_pau"}
    GIRAM = {"bandeja": 420, "prato_feito": 300, "frigideira": 380, "dente": 300, "salto": 360, "dinheiro": 260,
             "chapeu": 500, "bota": 420, "livro": 320, "multa": 200, "osso": 520, "lobeira": 300,
             "tubo_de_ensaio": 460, "batarangue": 760, "cassetete": 560, "cone": 300, "oficio": 220,
             "portaria": 360, "esquadro": 240, "ventoinha": 600, "engrenagem": 300, "selo": 240}
    ALTURAS = {"bandeja": 40, "prato_feito": 40, "frigideira": 34, "laser": 16, "seringa": 20, "adaga": 22,
               "caneta": 16, "escova": 18, "giz": 14, "espelhinho": 18, "broca": 22, "lim": 34, "dx": 34,
               "integral": 42, "null": 40, "new": 40, "self": 40, "cassetete": 14, "osso": 20, "concha": 22,
               "colher_de_pau": 20, "pasta_de_dente": 24, "rosa_negra": 28, "milho": 26, "chama_dourada": 30,
               "ponteiro": 28}
    BALANCO = 10                 # graus para cada lado, para quem vai em pé

    def __init__(self, posicao, velocidade, dano, simbolo, cor, raio=12, arte=None):
        super().__init__(posicao, velocidade, dano, simbolo, cor, raio)
        self.arte = arte if arte_existe(arte) else None

    @property
    def altura(self):
        return self.ALTURAS.get(self.arte, 36) * self.raio / 12

    def angulo_desenho(self):
        if self.arte in self.GIRAM:
            return -self.tempo * self.GIRAM[self.arte]
        if self.arte in self.APONTAM:
            return super().angulo_desenho()
        return math.sin(self.tempo * 9) * self.BALANCO

    def desenhar(self, tela, camera):
        if self.arte is None:                              # sem arte: a bolinha com o símbolo
            super().desenhar(tela, camera)
            return
        centro = camera.para_tela(self.posicao)
        brilho = self.brilho(self.cor, round(self.raio) + 9)
        tela.blit(brilho, brilho.get_rect(center=centro))
        imagem = imagem_da_arte(self.arte, self.altura)
        if self.arte in self.APONTAM and self.velocidade.x < 0:           # não voa de cabeça para baixo
            imagem = Recursos.rotacionada(Recursos.espelhada(imagem), self.angulo_desenho() + 180)
        else:
            imagem = Recursos.rotacionada(imagem, self.angulo_desenho())
        tela.blit(imagem, imagem.get_rect(center=centro))

    _brilhos = {}

    @classmethod
    def brilho(cls, cor, raio):
        """Mancha de luz na cor de quem atirou: destaca o objeto do chão e avisa que aquilo machuca."""
        chave = (tuple(cor), raio)
        if chave not in cls._brilhos:
            mancha = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
            pygame.draw.circle(mancha, (*cor[:3], 55), (raio, raio), raio)
            pygame.draw.circle(mancha, (*cor[:3], 90), (raio, raio), round(raio * 0.7))
            cls._brilhos[chave] = mancha
        return cls._brilhos[chave]


class Bumerangue(ProjetilTematico):
    """Vai, perde o fôlego e volta pelo mesmo caminho (o batarangue do Vigilante, o chapéu do Agroboy)."""

    DURACAO = 2.4
    IDA = 0.9                    # segundos até parar e começar a voltar

    def mover(self, dt):
        self.posicao += self.velocidade * (1 - self.tempo / self.IDA) * dt


class Marca(Efeito):
    """Um desenho que aparece, cresce um pouco e some: garra do bote, nuvem de morcegos, uivo, cadeado."""

    camada = 3

    def __init__(self, posicao, arte, altura, duracao=0.5, angulo=0.0, crescimento=0.3, dono=None, subida=0.0):
        super().__init__(posicao, duracao)
        self.arte = arte if arte_existe(arte) else None
        self.altura = altura
        self.angulo = angulo
        self.crescimento = crescimento
        self.dono = dono                                   # se tiver dono, acompanha quem a criou
        self.desvio = pygame.Vector2(posicao) - dono.posicao if dono is not None else None
        self.subida = subida

    def ao_atualizar(self, dt, jogo):
        if self.dono is not None:
            self.posicao = self.dono.posicao + self.desvio
        self.posicao.y -= self.subida * dt

    def desenhar(self, tela, camera):
        if self.arte is None:
            return
        altura = round(self.altura * (1 + self.crescimento * self.fracao) / 4) * 4
        imagem = imagem_da_arte(self.arte, altura)
        if self.angulo:
            imagem = Recursos.rotacionada(imagem, self.angulo)
        some = max(0.0, (self.fracao - 0.6) / 0.4)          # só apaga no fim
        if some > 0:
            imagem = imagem.copy()
            imagem.set_alpha(round(255 * (1 - some)))
        tela.blit(imagem, imagem.get_rect(center=camera.para_tela(self.posicao)))


class GolpeNoChao(Entidade):
    """Marca no chão que avisa (vai enchendo) e, quando fecha, acerta quem ainda estiver dentro.

    As subclasses dizem a cor, o que cai do céu (`ARTE_DO_GOLPE`), o que fica no chão depois (`ARTE_DA_MARCA`)
    e o que mais acontece na hora da pancada (`ao_cair`, `ao_acertar`).
    """

    grupo = "projetil_inimigo"
    camada = 0
    AVISO = 0.9
    BRILHO = 0.3
    COR = (240, 80, 80)
    TEXTO = ""                   # o que aparece em cima do aluno quando acerta
    ARTE_DO_GOLPE = None
    ARTE_DA_MARCA = None
    ALTURA_DA_QUEDA = 460

    def __init__(self, posicao, raio, dano):
        super().__init__(posicao, raio)
        self.dano = dano
        self.tempo = 0.0
        self.disparou = False

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if not self.disparou and self.tempo >= self.AVISO:
            self.disparou = True
            self.ao_cair(jogo)
            if jogo.jogador.posicao.distance_to(self.posicao) <= self.raio and jogo.ferir_jogador(self.dano):
                self.ao_acertar(jogo)
        if self.tempo >= self.AVISO + self.BRILHO:
            self.remover()

    def ao_cair(self, jogo):
        """Gancho: a pancada aconteceu, tenha acertado ou não."""

    def ao_acertar(self, jogo):
        if self.TEXTO:
            jogo.adicionar(TextoFlutuante(self.TEXTO, jogo.jogador.posicao - (0, 50), self.COR, 18))

    def esta_visivel(self, camera):
        return camera.visivel(self.posicao, self.raio + self.ALTURA_DA_QUEDA)

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        self.desenhar_chao(tela, centro)
        self.desenhar_golpe(tela, centro)

    def desenhar_chao(self, tela, centro):
        """O círculo de aviso visto de cima em 3/4, enchendo até a hora da pancada."""
        raio = round(self.raio)
        lado = raio * 2 + 8
        chao = pygame.Surface((lado, lado), pygame.SRCALPHA)
        meio = (lado // 2, lado // 2)
        if self.disparou:
            pygame.draw.circle(chao, (*self.COR, 150), meio, raio)
        else:
            pygame.draw.circle(chao, (*self.COR, 50), meio, raio)
            pygame.draw.circle(chao, (*self.COR, 120), meio, round(raio * self.tempo / self.AVISO))
        pygame.draw.circle(chao, (30, 20, 30, 230), meio, raio, 5)
        pygame.draw.circle(chao, (*self.COR, 255), meio, raio - 1, 3)
        chao = pygame.transform.smoothscale(chao, (lado, round(lado * 0.6)))
        tela.blit(chao, chao.get_rect(center=(round(centro.x), round(centro.y))))
        if self.disparou and arte_existe(self.ARTE_DA_MARCA):
            marca = imagem_na_largura(self.ARTE_DA_MARCA, self.raio * 1.5)
            tela.blit(marca, marca.get_rect(center=(round(centro.x), round(centro.y))))

    def desenhar_golpe(self, tela, centro):
        """O objeto caindo: lá do alto no começo do aviso, no chão na hora da pancada."""
        if not arte_existe(self.ARTE_DO_GOLPE):
            return
        falta = max(0.0, 1 - self.tempo / self.AVISO)
        imagem = imagem_da_arte(self.ARTE_DO_GOLPE, round(self.raio * 1.1 / 4) * 4)
        base = (round(centro.x), round(centro.y + 10 - self.ALTURA_DA_QUEDA * falta * falta))
        tela.blit(imagem, imagem.get_rect(midbottom=base))


class Poca(Entidade):
    """Poça que fica no chão por um tempo e queima quem pisa nela (sopa quente, ácido)."""

    grupo = "projetil_inimigo"
    camada = 0
    INTERVALO = 0.5              # segundos entre uma queimadura e a próxima

    def __init__(self, posicao, raio, dano, arte, cor, duracao=4.0):
        super().__init__(posicao, raio)
        self.dano = dano
        self.arte = arte
        self.cor = tuple(cor)
        self.duracao = duracao
        self.tempo = 0.0
        self._espera = 0.0

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self._espera -= dt
        if self._espera <= 0 and jogo.jogador.posicao.distance_to(self.posicao) <= self.raio:
            jogo.ferir_jogador(self.dano)
            self._espera = self.INTERVALO
        if self.tempo >= self.duracao:
            self.remover()

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        nasce = min(1.0, self.tempo / 0.25)                # espalha rápido e seca no último segundo
        some = min(1.0, max(0.0, self.duracao - self.tempo))
        largura = round(self.raio * 2.3 * nasce / 8) * 8
        if arte_existe(self.arte) and largura >= 8:
            imagem = imagem_na_largura(self.arte, largura)
        else:
            imagem = pygame.Surface((max(8, largura), max(4, round(largura * 0.6))), pygame.SRCALPHA)
            pygame.draw.ellipse(imagem, (*self.cor, 200), imagem.get_rect())
        if some < 1:
            imagem = imagem.copy()
            imagem.set_alpha(round(255 * some))
        tela.blit(imagem, imagem.get_rect(center=(round(centro.x), round(centro.y))))


class ArremessoQueDerrama(GolpeNoChao):
    """Algo cheio de líquido arremessado para o alto: cai onde o aluno estava e deixa uma poça."""

    ARTE_DA_POCA = ""
    DURACAO_DA_POCA = 4.0
    DANO_DA_POCA = 0.4           # fração do dano da pancada a cada queimadura

    def ao_cair(self, jogo):
        jogo.adicionar(Poca(self.posicao, self.raio, self.dano * self.DANO_DA_POCA, self.ARTE_DA_POCA, self.COR,
                            self.DURACAO_DA_POCA))


class PanelaoDeSopa(ArremessoQueDerrama):
    """O panelão da Tia da Cantina."""
    COR = (255, 140, 40)
    TEXTO = "QUEIMOU!"
    ARTE_DO_GOLPE = "panelao"
    ARTE_DA_POCA = "poca_de_sopa"


class FrascoDeAcido(ArremessoQueDerrama):
    """O erlenmeyer do Técnico do Laboratório."""
    COR = (120, 235, 70)
    TEXTO = "CORROEU!"
    ARTE_DO_GOLPE = "erlenmeyer"
    ARTE_DA_POCA = "poca_de_acido"
    DURACAO_DA_POCA = 3.5


class Carimbada(GolpeNoChao):
    """O carimbo do Reitor desce do céu e deixa o INDEFERIDO no chão."""
    COR = (225, 50, 50)
    TEXTO = "INDEFERIDO!"
    AVISO = 0.8
    BRILHO = 0.45
    ARTE_DO_GOLPE = "carimbo"
    ARTE_DA_MARCA = "indeferido"
