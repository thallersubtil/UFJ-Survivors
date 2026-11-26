"""Efeitos visuais de curta duração: números de dano, explosões, raios."""
import math
from abc import ABC

import pygame

from jogo.config import Cor
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Efeito(Entidade, ABC):
    grupo = "efeito"
    camada = 3

    def __init__(self, posicao, duracao, raio=0):
        super().__init__(posicao, raio)
        self.duracao = duracao
        self.tempo = 0.0

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.ao_atualizar(dt, jogo)
        if self.tempo >= self.duracao:
            self.remover()

    def ao_atualizar(self, dt, jogo):
        """Gancho para efeitos que interagem com o jogo enquanto duram."""

    @property
    def fracao(self):
        return min(1.0, self.tempo / self.duracao) if self.duracao > 0 else 1.0


class EfeitoAnimado(Efeito):
    """Efeito que toca uma vez a tira assets/sprites/<PASTA_SPRITE>/explodir-<n>.png, do começo ao fim.

    Sem a arte, a subclasse desenha a versão simples (formas geométricas) em `desenhar_simples`.
    """

    PASTA_SPRITE = None
    ANIMACAO = "explodir"

    def quadro(self, altura):
        """Quadro da vez já na altura pedida, ou None se a arte não existe."""
        animacao = Recursos.animacoes(self.PASTA_SPRITE).get(self.ANIMACAO) if self.PASTA_SPRITE else None
        if animacao is None:
            return None
        quadros = animacao.quadros
        return Recursos.na_altura(quadros[min(len(quadros) - 1, int(self.fracao * len(quadros)))], max(8, int(altura)))

    def desenhar_simples(self, tela, camera):
        """Desenho usado quando a arte não está disponível."""

    def altura_do_quadro(self):
        return self.raio * 2

    def desenhar(self, tela, camera):
        imagem = self.quadro(self.altura_do_quadro())
        if imagem is None:
            self.desenhar_simples(tela, camera)
            return
        if self.aura is not None:
            imagem = Recursos.suprema(imagem, self.aura)
        c = camera.para_tela(self.posicao)
        tela.blit(imagem, imagem.get_rect(center=(round(c.x), round(c.y))))


class TextoFlutuante(Efeito):
    def __init__(self, texto, posicao, cor=Cor.DANO, tamanho=16, duracao=0.7, subida=36):
        super().__init__(posicao, duracao)
        self.subida = subida
        fonte = Recursos.fonte(tamanho)
        frente = fonte.render(texto, True, cor)
        contorno = fonte.render(texto, True, Cor.BORDA_ESCURA)
        self.imagem = pygame.Surface((frente.get_width() + 2, frente.get_height() + 2), pygame.SRCALPHA)
        for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
            self.imagem.blit(contorno, (dx, dy))
        self.imagem.blit(frente, (1, 1))

    def desenhar(self, tela, camera):
        p = camera.para_tela(self.posicao)
        p.y -= self.subida * self.fracao
        alfa = 255 if self.fracao < 0.6 else int(255 * (1 - self.fracao) / 0.4)
        self.imagem.set_alpha(alfa)
        tela.blit(self.imagem, self.imagem.get_rect(center=(round(p.x), round(p.y))))


class FaiscaExplosao(Efeito):
    """Explosão da Pilha AA: fere o herói uma vez se ele estiver perto."""

    def __init__(self, posicao, raio=70, dano=10):
        super().__init__(posicao, 0.35, raio)
        self.dano = dano
        self._feriu = False

    def ao_atualizar(self, dt, jogo):
        if not self._feriu:
            self._feriu = True
            if Colisao.circulos_colidem(self, jogo.jogador):
                jogo.ferir_jogador(self.dano)

    def desenhar(self, tela, camera):
        lado = int(self.raio * 2.4)
        sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
        centro = pygame.Vector2(lado / 2, lado / 2)
        r = self.raio * (0.4 + 0.6 * self.fracao)
        alfa = int(255 * (1 - self.fracao))
        pygame.draw.circle(sup, (255, 220, 80, alfa // 2), centro, int(r))
        pygame.draw.circle(sup, (255, 255, 200, alfa), centro, int(r), 3)
        for i in range(8):
            direcao = pygame.Vector2(1, 0).rotate(i * 45 + self.fracao * 60)
            pygame.draw.line(sup, (255, 240, 120, alfa), centro + direcao * r * 0.5, centro + direcao * r * 1.15, 3)
        c = camera.para_tela(self.posicao)
        tela.blit(sup, sup.get_rect(center=(round(c.x), round(c.y))))


class AuraSSJ(Efeito):
    """Aura dourada do Super Saiyajin, desenhada logo atrás do herói."""

    camada = 1

    def __init__(self, dono, duracao):
        super().__init__(dono.posicao, duracao)
        self.dono = dono

    def ao_atualizar(self, dt, jogo):
        self.posicao = self.dono.posicao - pygame.Vector2(0, 0.5)

    def desenhar(self, tela, camera):
        c = camera.para_tela(self.dono.posicao)
        largura, altura = 70, 96
        sup = pygame.Surface((largura + 20, altura + 30), pygame.SRCALPHA)
        base = pygame.Vector2(sup.get_width() / 2, sup.get_height() - 6)
        brilho = 0.85 + 0.15 * math.sin(self.tempo * 25)
        pygame.draw.ellipse(sup, (255, 210, 60, int(70 * brilho)), (10, 20, largura, altura))
        for i in range(7):
            x = 14 + i * (largura - 8) / 6
            topo = 8 + 10 * (1 + math.sin(self.tempo * 18 + i * 1.7))
            pygame.draw.polygon(sup, (255, 236, 120, int(110 * brilho)),
                                [(x - 7, base.y - 20), (x, topo), (x + 7, base.y - 20)])
        tela.blit(sup, sup.get_rect(midbottom=(round(c.x), round(c.y + 34))))


class RaioZoltraak(Efeito):
    """Raio mágico que sai do herói na direção da mira e atravessa tudo."""

    COMPRIMENTO = 950
    LARGURA = 70
    INTERVALO = 0.1

    def __init__(self, dono, dano, duracao=1.5):
        super().__init__(dono.posicao, duracao)
        self.dono = dono
        self.dano = dano
        self.direcao = pygame.Vector2(dono.direcao_mira)
        self._espera = 0.0

    def ao_atualizar(self, dt, jogo):
        self.posicao = pygame.Vector2(self.dono.posicao)
        self.direcao = pygame.Vector2(self.dono.direcao_mira)
        self._espera -= dt
        if self._espera > 0:
            return
        self._espera = self.INTERVALO
        fim = self.posicao + self.direcao * self.COMPRIMENTO
        meio = (self.posicao + fim) / 2
        for inimigo in jogo.inimigos_proximos(meio, self.COMPRIMENTO / 2 + self.LARGURA):
            if Colisao.segmento_acerta_circulo(self.posicao, fim, self.LARGURA, inimigo.posicao, inimigo.raio):
                jogo.causar_dano(inimigo, self.dano, self.direcao)

    def desenhar(self, tela, camera):
        inicio = camera.para_tela(self.posicao) + self.direcao * 28   # começa fora do herói
        fim = inicio + self.direcao * self.COMPRIMENTO
        sumindo = 1.0 if self.fracao < 0.85 else (1 - self.fracao) / 0.15
        largura = self.LARGURA * (1 + 0.12 * math.sin(self.tempo * 40)) * sumindo
        for cor, fator in (((140, 80, 255), 1.0), ((210, 190, 255), 0.55), ((255, 255, 255), 0.25)):
            espessura = max(1, int(largura * fator))
            pygame.draw.line(tela, cor, inicio, fim, espessura)
            pygame.draw.circle(tela, cor, inicio, espessura // 2 + 4)


class GolpeClaude(EfeitoAnimado):
    """Golpe do Claude: um risco laranja sai do mascote e estoura em estrela onde bateu."""

    PASTA_SPRITE = "golpe_claude"
    DURACAO = 0.5
    TEMPO_DO_RISCO = 0.35          # fração da duração em que o risco do mascote ao alvo aparece
    ALTURA_MINIMA = 130

    def __init__(self, posicao, raio, origem=None):
        super().__init__(posicao, self.DURACAO, raio)
        self.origem = pygame.Vector2(origem) if origem is not None else None

    def altura_do_quadro(self):
        return max(self.ALTURA_MINIMA, self.raio * 2.6)

    def _desenhar_risco(self, tela, camera):
        if self.origem is None or self.fracao >= self.TEMPO_DO_RISCO:
            return
        avanco = self.fracao / self.TEMPO_DO_RISCO
        inicio, fim = camera.para_tela(self.origem), camera.para_tela(self.posicao)
        cauda = inicio + (fim - inicio) * max(0.0, avanco * 1.6 - 0.6)
        ponta = inicio + (fim - inicio) * min(1.0, avanco * 1.6)
        if self.aura is not None:              # raciocínio profundo: risco mais grosso, com brilho
            pygame.draw.line(tela, self.aura, cauda, ponta, 15)
        pygame.draw.line(tela, (150, 60, 30), cauda, ponta, 9)
        pygame.draw.line(tela, (240, 130, 60), cauda, ponta, 6)
        pygame.draw.line(tela, (255, 236, 210), cauda, ponta, 2)

    def desenhar(self, tela, camera):
        self._desenhar_risco(tela, camera)
        super().desenhar(tela, camera)

    def desenhar_simples(self, tela, camera):
        c = camera.para_tela(self.posicao)
        r = self.raio * (0.5 + 0.7 * self.fracao)
        alfa = int(255 * (1 - self.fracao))
        lado = int(self.raio * 3)
        sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
        meio = pygame.Vector2(lado / 2, lado / 2)
        pontas = []
        for i in range(8):
            distancia = r if i % 2 == 0 else r * 0.35
            pontas.append(meio + pygame.Vector2(distancia, 0).rotate(i * 45 + 22.5))
        pygame.draw.polygon(sup, (240, 130, 60, alfa), pontas)
        pygame.draw.circle(sup, (255, 230, 200, alfa), meio, int(r * 0.25))
        tela.blit(sup, sup.get_rect(center=(round(c.x), round(c.y))))


class EstouroDePequi(EfeitoAnimado):
    """Explosão de espinhos do Pequi: fere uma vez cada inimigo na área (menos o que já levou o pequi)."""

    PASTA_SPRITE = "estouro_pequi"

    def __init__(self, posicao, raio, dano, excluir=None):
        super().__init__(posicao, 0.4, raio)
        self.dano = dano
        self.excluir = excluir
        self._feriu = False

    def ao_atualizar(self, dt, jogo):
        if self._feriu:
            return
        self._feriu = True
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if inimigo is not self.excluir:
                jogo.causar_dano(inimigo, self.dano, inimigo.posicao - self.posicao)

    def altura_do_quadro(self):
        return self.raio * 2.4

    def desenhar_simples(self, tela, camera):
        c = camera.para_tela(self.posicao)
        r = self.raio * (0.5 + 0.5 * self.fracao)
        alfa = int(230 * (1 - self.fracao))
        lado = int(self.raio * 2.4)
        sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
        meio = pygame.Vector2(lado / 2, lado / 2)
        pygame.draw.circle(sup, (250, 200, 40, alfa // 3), meio, int(r))
        for i in range(12):
            direcao = pygame.Vector2(1, 0).rotate(i * 30 + 15 * self.fracao)
            pygame.draw.line(sup, (120, 170, 40, alfa), meio + direcao * r * 0.3, meio + direcao * r, 3)
        tela.blit(sup, sup.get_rect(center=(round(c.x), round(c.y))))


class OndaDoGrito(Efeito):
    """Anel que se abre em volta do herói no grito de guerra da Atlética."""

    camada = 1

    def __init__(self, dono, raio, duracao=0.45):
        super().__init__(dono.posicao, duracao)
        self.dono = dono
        self.raio_final = raio

    def ao_atualizar(self, dt, jogo):
        self.posicao = pygame.Vector2(self.dono.posicao)

    def desenhar(self, tela, camera):
        c = camera.para_tela(self.posicao)
        raio = max(4, int(self.raio_final * (0.25 + 0.75 * self.fracao)))
        alfa = int(200 * (1 - self.fracao))
        sup = pygame.Surface((raio * 2 + 8, raio * 2 + 8), pygame.SRCALPHA)
        meio = (raio + 4, raio + 4)
        pygame.draw.circle(sup, (255, 200, 60, alfa // 4), meio, raio)
        pygame.draw.circle(sup, (255, 230, 120, alfa), meio, raio, 4)
        tela.blit(sup, sup.get_rect(center=(round(c.x), round(c.y))))


class AvisoDeFormacao(Efeito):
    """Setas piscando na borda da tela antes de um cerco ou de uma parede; no fim, chama a formação.

    `lados`: -1 esquerda, 1 direita, -2 em cima, 2 embaixo.
    """

    camada = 4

    def __init__(self, lados, duracao, ao_terminar):
        super().__init__(pygame.Vector2(), duracao)
        self.lados = tuple(lados)
        self.ao_terminar = ao_terminar

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if self.tempo >= self.duracao:
            self.remover()
            self.ao_terminar()

    def esta_visivel(self, camera):
        return True

    def desenhar(self, tela, camera):
        if int(self.tempo * 8) % 2:
            return
        largura, altura = tela.get_size()
        for lado in self.lados:
            for i in (-1, 0, 1):
                if abs(lado) == 1:
                    x = 26 if lado < 0 else largura - 26
                    y = altura // 2 + i * 120
                    base = x - 16 * lado
                    pontos = [(x, y), (base, y - 18), (base, y + 18)]
                else:
                    y = 26 if lado < 0 else altura - 26
                    x = largura // 2 + i * 200
                    base = y - 16 * (1 if lado > 0 else -1)
                    pontos = [(x, y), (x - 18, base), (x + 18, base)]
                pygame.draw.polygon(tela, (235, 70, 60), pontos)
                pygame.draw.polygon(tela, Cor.BORDA_ESCURA, pontos, 3)
