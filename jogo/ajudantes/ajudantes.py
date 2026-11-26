"""Ajudantes: coisas que as armas colocam na arena (cachorro, fusca, mascotes)."""
import math
from abc import ABC

import pygame

from jogo.nucleo.animacao import Animador
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Ajudante(Entidade, ABC):
    grupo = "ajudante"
    camada = 2
    PASTA_SPRITE = None
    IMAGEM = ""
    ALTURA = 24

    def criar_animador(self, pasta=None, imagem=None, altura=None):
        return Animador(Recursos.animacoes_ou_imagem(pasta or self.PASTA_SPRITE, imagem or self.IMAGEM,
                                                     altura or self.ALTURA))


class CachorroCaramelo(Ajudante):
    """Vira-lata caramelo que corre em volta do herói e morde quem encosta."""

    IMAGEM = "sprites/caramelo.png"
    PASTA_SPRITE = "caramelo"
    ALTURA = 40
    ESPERA_MORDIDA = 0.5

    def __init__(self, dono, angulo, arma):
        super().__init__(dono.posicao, 18)
        self.dono = dono
        self.angulo = angulo
        self.arma = arma
        self.tempo = 0.0
        self.animador = self.criar_animador()
        self.olhando_esquerda = False
        self._mordidos = {}

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.animador.atualizar(dt)
        self.angulo += self.arma.valor("velocidade") * dt
        raio = self.arma.valor("raio")
        nova = self.dono.posicao + pygame.Vector2(math.cos(self.angulo), math.sin(self.angulo)) * raio
        if abs(nova.x - self.posicao.x) > 0.5:
            self.olhando_esquerda = nova.x < self.posicao.x
        self.posicao = nova
        for chave in list(self._mordidos):
            self._mordidos[chave] -= dt
            if self._mordidos[chave] <= 0:
                del self._mordidos[chave]
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if inimigo in self._mordidos:
                continue
            self._mordidos[inimigo] = self.ESPERA_MORDIDA
            jogo.causar_dano(inimigo, self.arma.valor("dano") * self.dono.multiplicador_dano,
                             inimigo.posicao - self.dono.posicao)

    def desenhar(self, tela, camera):
        imagem = self.animador.quadro_atual
        desenhar_sprite(tela, camera, imagem, self.posicao, aura=self.aura, espelhar=self.olhando_esquerda,
                        deslocamento_y=abs(math.sin(self.tempo * 14)) * 4)


class MascoteFlutuante(Ajudante):
    """Mascote que flutua perto do herói (ChatGPT, Claude). Pode mostrar uma barrinha."""

    camada = 2

    def __init__(self, dono, imagem, altura, deslocamento, barra=None, pasta=None):
        super().__init__(dono.posicao + deslocamento, 14)
        self.dono = dono
        self.imagem = imagem
        self.altura = altura
        self.deslocamento = pygame.Vector2(deslocamento)
        self.barra = barra
        self.tempo = 0.0
        self.animador = self.criar_animador(pasta, imagem, altura)

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.animador.atualizar(dt)
        alvo = self.dono.posicao + self.deslocamento + pygame.Vector2(0, math.sin(self.tempo * 3) * 6)
        self.posicao += (alvo - self.posicao) * min(1.0, dt * 8)

    def desenhar(self, tela, camera):
        imagem = self.animador.quadro_atual
        desenhar_sprite(tela, camera, imagem, self.posicao, sombra=False, aura=self.aura)
        if self.barra is not None:
            c = camera.para_tela(self.posicao)
            fundo = pygame.Rect(0, 0, 34, 5)
            fundo.midtop = (round(c.x), round(c.y - self.altura / 2 - 10))
            pygame.draw.rect(tela, (20, 16, 30), fundo.inflate(2, 2))
            cheio = fundo.copy()
            cheio.width = round(fundo.width * self.barra())
            pygame.draw.rect(tela, (240, 140, 70), cheio)


class FuscaVeiculo(Ajudante):
    """Fusca azul que atravessa a tela buzinando e possui quem atropela."""

    IMAGEM = "sprites/fusca.png"
    PASTA_SPRITE = "fusca"
    ALTURA = 56
    VELOCIDADE = 650

    def __init__(self, posicao, sentido, possessao, dano):
        super().__init__(posicao, 34)
        self.sentido = sentido
        self.possessao = possessao
        self.dano = dano
        self.tempo = 0.0
        self.animador = self.criar_animador()
        self._atingidos = set()

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.animador.atualizar(dt)
        self.posicao.x += self.sentido * self.VELOCIDADE * dt
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if inimigo in self._atingidos:
                continue
            self._atingidos.add(inimigo)
            inimigo.possuir(self.possessao)
            jogo.causar_dano(inimigo, self.dano, pygame.Vector2(self.sentido, -0.3))
        if self.tempo > 0.5 and not jogo.camera.visivel(self.posicao, 300):
            self.remover()

    def desenhar(self, tela, camera):
        imagem = self.animador.quadro_atual
        desenhar_sprite(tela, camera, imagem, self.posicao, aura=self.aura, espelhar=self.sentido < 0,
                        deslocamento_y=abs(math.sin(self.tempo * 30)) * 2)


class FuscaCircular(Ajudante):
    """Um Caramelo dirigindo um fusca em círculo em volta do herói, atropelando e possuindo inimigos."""

    IMAGEM = "sprites/caramelo_no_fusca.png"
    PASTA_SPRITE = "caramelo_no_fusca"
    ALTURA = 64
    ESPERA_ATROPELO = 0.4

    def __init__(self, dono, arma, angulo=0.0):
        super().__init__(dono.posicao, 36)
        self.dono = dono
        self.arma = arma
        self.angulo = angulo
        self.tempo = 0.0
        self.animador = self.criar_animador()
        self.olhando_esquerda = False
        self._atropelados = {}

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.animador.atualizar(dt)
        self.angulo += self.arma.valor("velocidade") * dt
        nova = self.dono.posicao + pygame.Vector2(math.cos(self.angulo), math.sin(self.angulo)) * self.arma.valor("raio")
        self.olhando_esquerda = math.sin(self.angulo) > 0          # anda no sentido da volta
        self.posicao = nova
        for chave in list(self._atropelados):
            self._atropelados[chave] -= dt
            if self._atropelados[chave] <= 0:
                del self._atropelados[chave]
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if inimigo in self._atropelados:
                continue
            self._atropelados[inimigo] = self.ESPERA_ATROPELO
            inimigo.possuir(self.arma.valor("possessao"))
            jogo.causar_dano(inimigo, self.arma.valor("dano") * self.dono.multiplicador_dano,
                             inimigo.posicao - self.dono.posicao)

    def desenhar(self, tela, camera):
        imagem = self.animador.quadro_atual
        desenhar_sprite(tela, camera, imagem, self.posicao, aura=self.aura, espelhar=self.olhando_esquerda,
                        deslocamento_y=abs(math.sin(self.tempo * 30)) * 2)


class SinalWifi(Ajudante):
    """Campo do Wi-Fi Eduroam: a cada pulso fere todos dentro do raio, se o sinal não cair."""

    camada = 0

    def __init__(self, dono, arma):
        super().__init__(dono.posicao, arma.valor("raio"))
        self.dono = dono
        self.arma = arma
        self.tempo = 0.0
        self._espera = 0.0
        self.sem_sinal = 0.0

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.posicao = pygame.Vector2(self.dono.posicao)
        self.raio = self.arma.valor("raio")
        self.sem_sinal = max(0.0, self.sem_sinal - dt)
        self._espera -= dt * (1 / self.dono.multiplicador_recarga)
        if self._espera > 0:
            return
        self._espera = self.arma.valor("intervalo")
        if self.sem_sinal > 0:
            return
        if jogo.rng.random() < self.arma.valor("queda") * 0.2:
            self.sem_sinal = 1.0          # o sinal caiu por um segundo
            return
        dano = self.arma.valor("dano") * self.dono.multiplicador_dano
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            jogo.causar_dano(inimigo, dano)

    def esta_visivel(self, camera):
        return True

    def desenhar(self, tela, camera):
        c = camera.para_tela(self.posicao)
        lado = int(self.raio * 2 + 8)
        sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
        meio = (lado // 2, lado // 2)
        if self.sem_sinal > 0:
            pygame.draw.circle(sup, (160, 160, 170, 40), meio, int(self.raio), 2)
        else:
            pulso = (self.tempo * 1.5) % 1.0
            if self.arma.aura is None:
                pygame.draw.circle(sup, (90, 200, 255, 28), meio, int(self.raio))
                pygame.draw.circle(sup, (140, 220, 255, 110), meio, int(self.raio), 2)
                pygame.draw.circle(sup, (180, 240, 255, int(140 * (1 - pulso))), meio, max(2, int(self.raio * pulso)), 2)
            else:                                   # fibra óptica: campo dourado com três ondas seguidas
                cor = self.arma.aura
                pygame.draw.circle(sup, (*cor, 38), meio, int(self.raio))
                pygame.draw.circle(sup, (*cor, 200), meio, int(self.raio), 4)
                pygame.draw.circle(sup, (255, 255, 255, 150), meio, int(self.raio) - 3, 1)
                for atraso in (0.0, 0.33, 0.66):
                    onda = (self.tempo * 2.2 + atraso) % 1.0
                    pygame.draw.circle(sup, (*cor, int(190 * (1 - onda))), meio, max(2, int(self.raio * onda)), 3)
        tela.blit(sup, sup.get_rect(center=(round(c.x), round(c.y))))


class FolhaDaApostila(Ajudante):
    """Folha da Apostila: gira em volta do herói por um tempo e fere quem encosta."""

    VELOCIDADE_ANGULAR = 3.4       # radianos por segundo
    RAIO_ACERTO = 16
    ESPERA_ACERTO = 0.6            # o mesmo inimigo só leva de novo depois disso (uma vez por volta)
    PASTA_SPRITE = "folha_apostila"
    QUADROS_POR_SEGUNDO = 9
    _imagem = None

    def __init__(self, dono, arma, indice, total, duracao):
        super().__init__(dono.posicao, self.RAIO_ACERTO)
        self.dono = dono
        self.arma = arma
        self.fase = 2 * math.pi * indice / total
        self.duracao = duracao
        self.tempo = 0.0
        self._acertados = {}
        self._posicionar()

    def _posicionar(self):
        angulo = self.fase + self.tempo * self.VELOCIDADE_ANGULAR
        raio = self.arma.valor("raio")
        self.posicao = self.dono.posicao + pygame.Vector2(math.cos(angulo), math.sin(angulo)) * raio

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if self.tempo >= self.duracao:
            self.remover()
            return
        self._posicionar()
        for inimigo in list(self._acertados):
            self._acertados[inimigo] -= dt
            if self._acertados[inimigo] <= 0:
                del self._acertados[inimigo]
        dano = self.arma.valor("dano") * self.dono.multiplicador_dano
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if inimigo in self._acertados:
                continue
            self._acertados[inimigo] = self.ESPERA_ACERTO
            jogo.causar_dano(inimigo, dano, inimigo.posicao - self.dono.posicao)

    @classmethod
    def imagem(cls):
        """Folha de papel em pixel art (desenhada uma vez): contorno escuro, linhas azuis."""
        if cls._imagem is None:
            sup = pygame.Surface((14, 18), pygame.SRCALPHA)
            sup.fill((30, 26, 40))
            sup.fill((250, 248, 236), pygame.Rect(1, 1, 12, 16))
            sup.fill((214, 210, 196), pygame.Rect(1, 15, 12, 2))
            for y in (5, 8, 11):
                sup.fill((110, 150, 220), pygame.Rect(3, y, 8, 1))
            sup.fill((220, 80, 80), pygame.Rect(3, 2, 1, 14))
            cls._imagem = pygame.transform.scale(sup, (28, 36))
        return cls._imagem

    def _quadro(self):
        """Folha esvoaçando (arte em assets/sprites/folha_apostila/); sem a arte, a folha desenhada aqui."""
        animacao = Recursos.animacoes(self.PASTA_SPRITE).get("mover")
        if animacao is None:
            return self.imagem()
        return animacao.quadros[int(self.tempo * self.QUADROS_POR_SEGUNDO + self.fase) % len(animacao.quadros)]

    def desenhar(self, tela, camera):
        c = camera.para_tela(self.posicao)
        angulo = round(math.degrees(self.fase + self.tempo * self.VELOCIDADE_ANGULAR) / 30) * 30
        quadro = self._quadro() if self.aura is None else Recursos.suprema(self._quadro(), self.aura)
        imagem = pygame.transform.rotate(quadro, -angulo)
        if self.duracao - self.tempo < 0.4:          # pisca antes de sumir
            imagem.set_alpha(120 if int(self.tempo * 20) % 2 else 255)
        tela.blit(imagem, imagem.get_rect(center=(round(c.x), round(c.y))))


class QuadroBrancoNoChao(Ajudante):
    """Área do Quadro Branco: quem está dentro anda devagar e leva dano a cada pulso."""

    camada = 0
    INTERVALO = 0.5

    def __init__(self, dono, arma, posicao):
        super().__init__(posicao, arma.valor("raio"))
        self.dono = dono
        self.arma = arma
        self.duracao = arma.valor("duracao")
        self.tempo = 0.0
        self._espera = 0.0

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if self.tempo >= self.duracao:
            self.remover()
            return
        self._espera -= dt
        pulso = self._espera <= 0
        if pulso:
            self._espera = self.INTERVALO
        dano = self.arma.valor("dano") * self.dono.multiplicador_dano
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            inimigo.atrasar(0.3)
            if pulso:
                jogo.causar_dano(inimigo, dano)

    def esta_visivel(self, camera):
        return True

    def desenhar(self, tela, camera):
        c = camera.para_tela(self.posicao)
        lado = int(self.raio * 2 + 8)
        sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
        meio = (lado // 2, lado // 2)
        alfa = 1.0 if self.duracao - self.tempo > 0.5 else (self.duracao - self.tempo) / 0.5
        if self.aura is not None:         # lousa digital: tela acesa com grade e borda brilhante
            pygame.draw.circle(sup, (40, 70, 120, int(110 * alfa)), meio, int(self.raio))
            passo = 22
            for d in range(-int(self.raio), int(self.raio) + 1, passo):
                meia = int(math.sqrt(max(0, self.raio ** 2 - d ** 2)))
                pygame.draw.line(sup, (120, 220, 255, int(70 * alfa)), (meio[0] - meia, meio[1] + d), (meio[0] + meia, meio[1] + d))
                pygame.draw.line(sup, (120, 220, 255, int(70 * alfa)), (meio[0] + d, meio[1] - meia), (meio[0] + d, meio[1] + meia))
            pulso = 0.5 + 0.5 * math.sin(self.tempo * 6)
            pygame.draw.circle(sup, (*self.aura, int((150 + 90 * pulso) * alfa)), meio, int(self.raio), 5)
            pygame.draw.circle(sup, (255, 255, 255, int(160 * alfa)), meio, int(self.raio) - 4, 1)
            tela.blit(sup, sup.get_rect(center=(round(c.x), round(c.y))))
            return
        pygame.draw.circle(sup, (235, 240, 250, int(70 * alfa)), meio, int(self.raio))
        pygame.draw.circle(sup, (60, 110, 200, int(170 * alfa)), meio, int(self.raio), 3)
        for i in range(3):                # rabiscos de pincel atômico
            y = meio[1] - 18 + i * 18
            pygame.draw.line(sup, (60, 110, 200, int(120 * alfa)), (meio[0] - 30 + i * 6, y), (meio[0] + 26 - i * 4, y), 3)
        tela.blit(sup, sup.get_rect(center=(round(c.x), round(c.y))))
