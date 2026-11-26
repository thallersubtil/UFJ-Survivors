"""O que os mini-chefes do mapa jogam no aluno: multas, carros desgovernados e o feixe de abdução."""
import math

import pygame

from jogo.config import Cor
from jogo.efeitos import TextoFlutuante
from jogo.nucleo.animacao import Animador
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import ProjetilDaMateria


class Multa(ProjetilDaMateria):
    """Multa de atraso da Bibliotecária: quase não fere, mas tira moedas do aluno."""

    def __init__(self, posicao, velocidade, dano, valor, cor):
        super().__init__(posicao, velocidade, dano, "R$", cor, raio=13)
        self.valor = valor

    def verificar_colisao(self, jogo):
        if Colisao.circulos_colidem(self, jogo.jogador):
            if jogo.ferir_jogador(self.dano):
                jogo.multar(self.valor)
            self.remover()


class VeiculoDesgovernado(Entidade):
    """Carro que buzina parado por um instante (a faixa no chão avisa por onde vai passar) e atravessa a tela."""

    grupo = "projetil_inimigo"
    camada = 1

    def __init__(self, posicao, direcao, pasta, velocidade, dano, raio, aviso=0.8, duracao=2.6):
        super().__init__(posicao, raio)
        self.direcao = pygame.Vector2(direcao).normalize()
        self.velocidade = velocidade
        self.dano = dano
        self.aviso = aviso
        self.duracao = duracao
        self.tempo = 0.0
        self.animador = Animador(Recursos.animacoes(pasta))

    @property
    def parado(self):
        return self.tempo < self.aviso

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if self.parado:
            return
        self.animador.atualizar(dt)
        self.posicao += self.direcao * self.velocidade * dt
        if Colisao.circulos_colidem(self, jogo.jogador):
            jogo.ferir_jogador(self.dano)
        if self.tempo >= self.aviso + self.duracao:
            self.remover()

    def esta_visivel(self, camera):
        return True                       # a faixa de aviso atravessa a tela mesmo com o carro fora dela

    def desenhar(self, tela, camera):
        if self.parado:
            inicio = camera.para_tela(self.posicao)
            fim = inicio + self.direcao * self.velocidade * self.duracao
            faixa = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            pulso = int(70 + 60 * abs(math.sin(self.tempo * 14)))
            pygame.draw.line(faixa, (240, 60, 60, pulso), inicio, fim, round(self.raio * 2))
            tela.blit(faixa, (0, 0))
        desenhar_sprite(tela, camera, self.animador.quadro_atual, self.posicao, espelhar=self.direcao.x < 0)


class FeixeDeAbducao(Entidade):
    """Círculo verde que cresce no chão (aviso) e, quando fecha, puxa para cima quem estiver dentro."""

    grupo = "projetil_inimigo"
    camada = 0
    AVISO = 0.9
    BRILHO = 0.3

    def __init__(self, posicao, raio, dano):
        super().__init__(posicao, raio)
        self.dano = dano
        self.tempo = 0.0
        self.disparou = False

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if not self.disparou and self.tempo >= self.AVISO:
            self.disparou = True
            if jogo.jogador.posicao.distance_to(self.posicao) <= self.raio:
                if jogo.ferir_jogador(self.dano):
                    jogo.adicionar(TextoFlutuante("ABDUZIDO!", jogo.jogador.posicao - (0, 50), (130, 255, 110), 18))
        if self.tempo >= self.AVISO + self.BRILHO:
            self.remover()

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        lado = self.raio * 2 + 8
        chao = pygame.Surface((lado, lado), pygame.SRCALPHA)
        meio = (lado // 2, lado // 2)
        if self.disparou:
            pygame.draw.circle(chao, (190, 255, 160, 210), meio, self.raio)
        else:
            fracao = self.tempo / self.AVISO
            pygame.draw.circle(chao, (90, 230, 90, 60), meio, self.raio)
            pygame.draw.circle(chao, (150, 255, 120, 150), meio, round(self.raio * fracao))
            pygame.draw.circle(chao, (200, 255, 170, 230), meio, self.raio, 3)
        chao = pygame.transform.scale(chao, (lado, round(lado * 0.6)))
        tela.blit(chao, chao.get_rect(center=(round(centro.x), round(centro.y))))
        if self.disparou:                                  # a coluna de luz subindo
            coluna = pygame.Surface((self.raio * 2, 420), pygame.SRCALPHA)
            coluna.fill((170, 255, 140, 90))
            tela.blit(coluna, coluna.get_rect(midbottom=(round(centro.x), round(centro.y))))
