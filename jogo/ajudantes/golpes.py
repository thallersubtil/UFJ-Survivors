"""O que as armas novas do semestre põem na arena: o dado jogado, o arco da régua, a estocada da caneta, a poça de
tinta e os elos da corrente do WhatsApp. Desenhados por código até a arte própria ser aprovada."""
import math

import pygame

from jogo.ajudantes.ajudantes import Ajudante
from jogo.efeitos import Efeito, TextoFlutuante
from jogo.formas_supremas import AreaQueFere
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import ProjetilDoHeroi


class DadoArremessado(ProjetilDoHeroi):
    """Um d20 voando, com o número que saiu."""

    DURACAO = 1.2
    LADO = 15

    def __init__(self, posicao, velocidade, dano, numero):
        super().__init__(posicao, velocidade, dano, perfuracao=1, raio=12)
        self.numero = numero

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        giro = self.tempo * 720
        pontos = [centro + pygame.Vector2(self.LADO, 0).rotate(giro + 60 * i) for i in range(6)]
        cor = (255, 214, 90) if self.numero == 20 else (200, 60, 60)
        pygame.draw.polygon(tela, cor, pontos)
        pygame.draw.polygon(tela, (30, 20, 30), pontos, 2)
        texto = Recursos.fonte(14).render(str(self.numero), True, (255, 255, 255))
        tela.blit(texto, texto.get_rect(center=(round(centro.x), round(centro.y))))


def no_arco(inimigo, origem, direcao, alcance, abertura):
    """Se o inimigo está no arco de `abertura` graus à frente de `direcao`, até `alcance`."""
    falta = inimigo.posicao - origem
    if falta.length() > alcance + inimigo.raio:
        return False
    if falta.length_squared() < 1:
        return True
    desvio = (direcao.angle_to(falta) + 180) % 360 - 180      # ângulo entre a mira e o inimigo, de -180 a 180
    return abs(desvio) <= abertura / 2


class ArcoDaRegua(Ajudante):
    """A régua varre um arco na frente do aluno: fere quem estiver nele uma vez e some."""

    camada = 3
    DURACAO = 0.18

    def __init__(self, dono, direcao, alcance, abertura, dano):
        super().__init__(dono.posicao, alcance)
        self.dono = dono
        self.direcao = pygame.Vector2(direcao)
        self.alcance = alcance
        self.abertura = abertura
        self.dano = dano
        self.tempo = 0.0
        self._ja_feriu = False

    def esta_visivel(self, camera):
        return True

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.posicao = pygame.Vector2(self.dono.posicao)
        if not self._ja_feriu:
            self._ja_feriu = True
            for inimigo in jogo.inimigos_proximos(self.posicao, self.alcance):
                if no_arco(inimigo, self.posicao, self.direcao, self.alcance, self.abertura):
                    jogo.causar_dano(inimigo, self.dano, inimigo.posicao - self.posicao)
        if self.tempo >= self.DURACAO:
            self.remover()

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        fracao = min(1.0, self.tempo / self.DURACAO)
        inicio = -self.abertura / 2
        varrido = inicio + self.abertura * fracao               # a régua passa de um lado ao outro
        base = self.direcao.as_polar()[1]
        pontos = [centro]
        for passo in range(9):
            angulo = base + inicio + (varrido - inicio) * passo / 8
            pontos.append(centro + pygame.Vector2(self.alcance, 0).rotate(angulo))
        cor = self.aura or (250, 230, 120)
        if len(pontos) > 2:
            sup = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(sup, (*cor, 90), pontos)
            tela.blit(sup, (0, 0))
        ponta = centro + pygame.Vector2(self.alcance, 0).rotate(base + varrido)
        pygame.draw.line(tela, (200, 150, 70), centro, ponta, 8)            # a régua de madeira
        pygame.draw.line(tela, (90, 60, 30), centro, ponta, 2)


class EstocadaDaCaneta(Ajudante):
    """Estocadas rápidas da caneta na direção da mira; no nível máximo, a última deixa uma poça de tinta."""

    camada = 3
    INTERVALO = 0.07
    LARGURA = 18

    def __init__(self, dono, direcao, alcance, dano, estocadas, poca=None):
        super().__init__(dono.posicao, alcance)
        self.dono = dono
        self.direcao = pygame.Vector2(direcao)
        self.alcance = alcance
        self.dano = dano
        self.restantes = estocadas
        self.poca = poca                  # (raio, dano, duração) da poça, ou None
        self.tempo = 0.0
        self._espera = 0.0

    def esta_visivel(self, camera):
        return True

    @property
    def ponta(self):
        return self.dono.posicao + self.direcao * self.alcance

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self._espera -= dt
        if self._espera > 0:
            return
        if self.restantes <= 0:
            self.remover()
            return
        self.restantes -= 1
        self._espera = self.INTERVALO
        for inimigo in jogo.inimigos_proximos(self.dono.posicao, self.alcance):
            if Colisao.segmento_acerta_circulo(self.dono.posicao, self.ponta, self.LARGURA, inimigo.posicao,
                                               inimigo.raio):
                jogo.causar_dano(inimigo, self.dano, self.direcao)
        if self.poca is not None and self.restantes == 0:      # a poça sai só da última estocada da série
            raio, dano, duracao = self.poca
            jogo.adicionar(PocaDeTinta(self.ponta, raio, dano, duracao))

    def desenhar(self, tela, camera):
        inicio = camera.para_tela(self.dono.posicao)
        avanco = 0.6 + 0.4 * abs(math.sin(self.tempo * 40))   # a caneta vai e volta
        fim = camera.para_tela(self.dono.posicao + self.direcao * self.alcance * avanco)
        pygame.draw.line(tela, (40, 60, 200), inicio, fim, 6)
        pygame.draw.line(tela, self.aura or (230, 230, 240), inicio, fim, 2)


class PocaDeTinta(AreaQueFere):
    """Tinta de caneta derramada no chão: fere quem pisa."""

    camada = 0

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        sup = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(sup, (30, 50, 170, round(150 * self.alfa_do_fim / 255)), sup.get_rect())
        tela.blit(sup, sup.get_rect(center=(round(centro.x), round(centro.y))))


class ElosDaCorrente(Efeito):
    """As linhas entre quem a corrente do WhatsApp acertou, piscando por um instante."""

    camada = 3

    def __init__(self, pontos, cor=(70, 210, 100), duracao=0.3):
        super().__init__(pontos[0], duracao)
        self.pontos = [pygame.Vector2(p) for p in pontos]
        self.cor = cor

    def esta_visivel(self, camera):
        return True

    def desenhar(self, tela, camera):
        if len(self.pontos) < 2:
            return
        na_tela = [camera.para_tela(p) for p in self.pontos]
        cor = self.aura or self.cor
        pygame.draw.lines(tela, (20, 40, 20), False, na_tela, 6)
        pygame.draw.lines(tela, cor, False, na_tela, 3)
        for ponto in na_tela[1:]:
            pygame.draw.circle(tela, cor, (round(ponto.x), round(ponto.y)), 6)


def corrente(jogo, origem, alcance_inicial, saltos, alcance_do_salto, ao_acertar):
    """Acerta o inimigo mais perto de `origem` e pula de inimigo em inimigo, sem repetir. Chama `ao_acertar` em
    cada um e devolve os pontos do caminho (para desenhar os elos), ou [] se não havia ninguém."""
    alvo = jogo.inimigo_mais_proximo(origem, alcance_inicial)
    if alvo is None:
        return []
    pontos, atingidos = [pygame.Vector2(origem)], set()
    while alvo is not None and len(atingidos) <= saltos:
        atingidos.add(alvo)
        pontos.append(pygame.Vector2(alvo.posicao))
        ao_acertar(alvo)
        perto = [i for i in jogo.inimigos_proximos(alvo.posicao, alcance_do_salto)
                 if i not in atingidos and i.ativo and i.ALVO_DA_MIRA]
        alvo = min(perto, key=lambda i: i.posicao.distance_squared_to(pontos[-1]), default=None)
    return pontos


def mostrar(jogo, texto, posicao, cor, tamanho=18):
    jogo.adicionar(TextoFlutuante(texto, pygame.Vector2(posicao) - (0, 40), cor, tamanho, duracao=0.9))
