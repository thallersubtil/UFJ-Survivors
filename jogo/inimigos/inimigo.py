"""Classe base abstrata dos inimigos."""
import math
from abc import ABC, abstractmethod

import pygame

from jogo.coletaveis.coletaveis import Bau, CopoDeCafe, PocaoDeVida
from jogo.config import DISTANCIA_REPOSICIONAR, Cor
from jogo.nucleo.animacao import Animador
from jogo.efeitos import TextoFlutuante
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.recursos import Recursos
from jogo.nucleo.ser_vivo import SerVivo


class Inimigo(SerVivo, ABC):
    grupo = "inimigo"
    camada = 1

    NOME = "Inimigo"
    IMAGEM = ""
    ALTURA = 40
    PASTA_SPRITE = None   # pasta em assets/sprites/ com as animações; <pasta>_gigante para o mini-chefe
    RAIO = 16
    VIDA = 10
    VELOCIDADE = 80
    DANO = 5
    PONTOS = 10
    EXPERIENCIA = 1
    TAMANHO_GRUPO = 1
    CHANCE_CAFE = 0.03
    CHANCE_POCAO = 0.006

    ESCALA_GIGANTE = 3
    VIDA_GIGANTE = 30
    PONTOS_GIGANTE = 20
    EXPERIENCIA_GIGANTE = 15

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, self.RAIO, self.VIDA * escala)
        self.escala = escala
        self.velocidade = self.VELOCIDADE * (1 + (escala - 1) * 0.08)
        self.tempo = 0.0
        self.possuido = 0.0
        self._espera_soco = 0.0
        self.empurrao = pygame.Vector2()
        self.olhando_esquerda = False
        self.gigante = False
        self.solta_bau = False
        self.reposiciona = True
        self.animador = Animador(Recursos.animacoes_ou_imagem(self.PASTA_SPRITE, self.IMAGEM, self.ALTURA))

    def tornar_gigante(self):
        self.gigante = True
        self.solta_bau = True
        self.reposiciona = False
        self.raio = self.RAIO * self.ESCALA_GIGANTE
        proprias = Recursos.animacoes(f"{self.PASTA_SPRITE}_gigante") if self.PASTA_SPRITE else {}
        self.animador = Animador(proprias or Recursos.animacoes_ou_imagem(
            self.PASTA_SPRITE, self.IMAGEM, self.ALTURA * self.ESCALA_GIGANTE, self.ESCALA_GIGANTE))
        self.vida_maxima = self.vida_maxima * self.VIDA_GIGANTE
        self.vida = self.vida_maxima

    @property
    def altura_sprite(self):
        return self.animador.quadro_atual.get_height()

    def escolher_animacao(self):
        """Nome da animação que o inimigo quer agora. Sobrescreva para variar."""
        return "andar"

    @property
    def valor_em_pontos(self):
        return self.PONTOS * (self.PONTOS_GIGANTE if self.gigante else 1)

    @property
    def valor_em_experiencia(self):
        return self.EXPERIENCIA * (self.EXPERIENCIA_GIGANTE if self.gigante else 1)

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.piscar = max(0.0, self.piscar - dt)
        self.animador.tocar(self.escolher_animacao())
        self.animador.atualizar(dt)
        if self.reposiciona and \
                self.posicao.distance_squared_to(jogo.jogador.posicao) > DISTANCIA_REPOSICIONAR ** 2:
            self.posicao = jogo.fase.posicao_de_nascimento(jogo)
        if self.possuido > 0:
            self.possuido -= dt
            self._agir_possuido(dt, jogo)
        else:
            self.mover(dt, jogo)
            self.tocar_jogador(jogo)
        if self.empurrao.length_squared() > 1:
            self.posicao += self.empurrao * dt
            self.empurrao *= max(0.0, 1 - 8 * dt)
        self._separar(jogo)
        self.posicao = jogo.resolver_obstaculos(self.posicao, self.raio)
        self.posicao.x = max(jogo.arena.left + self.raio, min(self.posicao.x, jogo.arena.right - self.raio))
        self.posicao.y = max(jogo.arena.top + self.raio, min(self.posicao.y, jogo.arena.bottom - self.raio))

    @abstractmethod
    def mover(self, dt, jogo):
        """Como este inimigo se desloca. Cada tipo tem o seu jeito."""

    def ir_em_direcao(self, alvo, dt, velocidade=None):
        falta = pygame.Vector2(alvo) - self.posicao
        if falta.length_squared() > 1:
            falta.normalize_ip()
            self.posicao += falta * (velocidade or self.velocidade) * dt
            if abs(falta.x) > 0.1:
                self.olhando_esquerda = falta.x < 0

    def tocar_jogador(self, jogo):
        if Colisao.circulos_colidem(self, jogo.jogador):
            jogo.ferir_jogador(self.DANO)

    def possuir(self, duracao):
        """Efeito do Fusca Azul: por um tempo, ataca outros inimigos."""
        self.possuido = max(self.possuido, duracao)

    def _agir_possuido(self, dt, jogo):
        self._espera_soco -= dt
        alvo = jogo.inimigo_mais_proximo(self.posicao, 400, excluir=self)
        if alvo is None:
            return
        self.ir_em_direcao(alvo.posicao, dt, self.velocidade * 1.4)
        if self._espera_soco <= 0 and Colisao.circulos_colidem(self, alvo):
            self._espera_soco = 0.5
            jogo.causar_dano(alvo, max(5, self.DANO * 2), alvo.posicao - self.posicao)
            jogo.adicionar(TextoFlutuante("POW!", alvo.posicao, Cor.DESTAQUE, 16))

    def empurrar(self, direcao, forca=180):
        direcao = pygame.Vector2(direcao)
        if direcao.length_squared() > 0:
            self.empurrao += direcao.normalize() * forca * (0.25 if self.gigante else 1)

    def _separar(self, jogo):
        for outro in jogo.grade.proximos(self.posicao, self.raio * 2)[:8]:
            if outro is self:
                continue
            afastar = self.posicao - outro.posicao
            soma = self.raio + outro.raio
            distancia2 = afastar.length_squared()
            if 0 < distancia2 < soma * soma:
                distancia = math.sqrt(distancia2)
                self.posicao += afastar / distancia * (soma - distancia) * 0.25

    def ao_morrer(self, jogo):
        """O que acontece quando morre. Por padrão solta nota e, às vezes, café ou poção."""
        jogo.soltar_nota(self.posicao, self.valor_em_experiencia)
        sorte = jogo.rng.random()
        if sorte < self.CHANCE_POCAO:
            jogo.adicionar(PocaoDeVida(self.posicao + (10, 0)))
        elif sorte < self.CHANCE_POCAO + self.CHANCE_CAFE:
            jogo.adicionar(CopoDeCafe(self.posicao + (10, 0)))
        if self.solta_bau:
            jogo.adicionar(Bau(self.posicao))

    @property
    def animado(self):
        return len(self.animador.animacao.quadros) > 1

    def balanco(self):
        """Balanço de quem não tem animação de verdade (arte estática)."""
        return 0 if self.animado else abs(math.sin(self.tempo * 9)) * 3

    def desenhar(self, tela, camera):
        self.desenhar_corpo(tela, camera)
        if self.possuido > 0:
            self._desenhar_possessao(tela, camera)

    def desenhar_corpo(self, tela, camera):
        """Desenha o sprite. Inimigos com visual especial sobrescrevem só isto."""
        imagem = self.animador.quadro_atual
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.olhando_esquerda,
                        piscar=self.piscar > 0, deslocamento_y=self.balanco())

    def _desenhar_possessao(self, tela, camera):
        p = camera.para_tela(self.posicao)
        topo = (round(p.x), round(p.y - self.altura_sprite / 2 - 14))
        pygame.draw.circle(tela, (40, 110, 230), topo, 9)
        marca = Recursos.fonte(14).render("!", True, Cor.TEXTO)
        tela.blit(marca, marca.get_rect(center=topo))
