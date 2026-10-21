"""O herói controlado pelo jogador."""
import math
from abc import ABC, abstractmethod

import pygame

from jogo.config import ESCALA_PIXEL, INVENCIBILIDADE_APOS_DANO
from jogo.nucleo.animacao import Animador
from jogo.nucleo.desenho import desenhar_sprite
from jogo.jogador.aparencia import vestir_animacoes
from jogo.nucleo.recursos import Recursos
from jogo.nucleo.ser_vivo import SerVivo


class Jogador(SerVivo, ABC):
    grupo = "jogador"
    camada = 1

    NOME = "Jogador"
    DESCRICAO = ""
    VIDA = 100
    VELOCIDADE = 200
    IMAGEM = ""
    IMAGEM_TRANSFORMADO = None
    PASTA_SPRITE = None          # pasta em assets/sprites/ com as animações (parado, andar)
    PASTA_TRANSFORMADO = None    # animações da forma transformada (Super Saiyajin)
    ALTURA = 64
    RAIO = 22
    MAX_ARMAS = 4                # habilidades ativas; no limite, só melhorias (uma colab libera vaga)
    MOLETOM_ORIGINAL = "verde"    # como achar o moletom na arte, para trocar a cor
    PASTA_SPRITE_FEMININA = None        # arte da versão feminina; sem ela, usa a masculina
    PASTA_TRANSFORMADO_FEMININA = None
    MAX_ITENS = 4                # habilidades passivas
    ALCANCE_COLETA_BASE = 90
    MULT_CRITICO = 2.0           # quanto o acerto crítico multiplica o dano

    def __init__(self, posicao):
        super().__init__(posicao, self.RAIO, self.VIDA)
        self.armas = []
        self.itens = []
        self.bonus = []
        self.armas_em_colab = set()
        self.direcao_mira = pygame.Vector2(1, 0)
        self.movendo = False
        self.olhando_esquerda = False
        self.invencivel = 0.0
        self.aparencia = None         # Aparencia escolhida na personalização
        self.imortal = False          # modo treino
        self.tempo = 0.0
        self.transformado = False
        self.animador = Animador(self._animacoes(), inicial="parado")
        self.nivel = 1
        self.experiencia = 0
        self.passiva = self.criar_passiva()
        self.recalcular_atributos()
        self.especial = self.criar_especial()
        self.adicionar_arma(self.criar_arma_inicial())

    @abstractmethod
    def criar_arma_inicial(self):
        """Arma com que este herói começa."""

    @abstractmethod
    def criar_passiva(self):
        """Passiva desta classe (cresce com o nível)."""

    @abstractmethod
    def criar_especial(self):
        """Especial (tecla Espaço) deste herói."""

    def _redefinir_atributos(self):
        self.mult_dano = 1.0
        self.mult_velocidade = 1.0
        self.mult_recarga = 1.0
        self.mult_especial = 1.0
        self.chance_critico = 0.0
        self.mult_cafe = 1.0
        self.regeneracao = 0.0
        self.alcance_coleta = self.ALCANCE_COLETA_BASE
        self.vida_maxima_extra = 0

    def recalcular_atributos(self):
        """Zera os modificadores e deixa a passiva e cada item aplicarem o seu (polimorfismo)."""
        maxima_antes = self.vida_maxima
        self._redefinir_atributos()
        self.passiva.aplicar(self)
        for item in self.itens:
            item.aplicar(self)
        self.vida_maxima = self.VIDA + self.vida_maxima_extra
        if self.vida_maxima > maxima_antes:
            self.curar(self.vida_maxima - maxima_antes)

    def multiplicador(self, atributo):
        resultado = 1.0
        for b in self.bonus:
            if b.atributo == atributo:
                resultado *= b.multiplicador
        return resultado

    @property
    def velocidade(self):
        return self.VELOCIDADE * self.mult_velocidade * self.multiplicador("velocidade")

    @property
    def multiplicador_dano(self):
        return self.mult_dano * self.multiplicador("dano")

    @property
    def multiplicador_recarga(self):
        """Fator aplicado ao tempo de recarga das armas (menor é mais rápido)."""
        return self.mult_recarga * self.multiplicador("recarga")

    def tem_bonus(self, nome):
        return any(b.nome == nome for b in self.bonus)

    def adicionar_bonus(self, bonus):
        self.bonus = [b for b in self.bonus if b.nome != bonus.nome] + [bonus]

    def adicionar_arma(self, arma):
        if len(self.armas) >= self.MAX_ARMAS:
            raise ValueError("o herói já carrega o máximo de armas")
        self.armas.append(arma)

    def remover_arma(self, arma, jogo):
        arma.ao_remover(jogo)
        self.armas.remove(arma)

    def aplicar_colab(self, receita, jogo):
        """Funde as duas armas da receita na colab: ocupam uma vaga só, e a outra fica livre."""
        from jogo.armas.colabs import Colab
        for arma in Colab.ingredientes_em(receita, self.armas):
            self.armas_em_colab.add(type(arma))
            self.remover_arma(arma, jogo)
        self.armas.append(receita())

    def adicionar_item(self, item):
        if len(self.itens) >= self.MAX_ITENS:
            raise ValueError("o herói já carrega o máximo de itens")
        self.itens.append(item)
        self.recalcular_atributos()

    def subir_nivel_item(self, item):
        item.subir_nivel()
        self.recalcular_atributos()

    def encher_cafe(self):
        for arma in self.armas:
            arma.encher()

    @property
    def experiencia_necessaria(self):
        return 6 + (self.nivel - 1) * 3

    def ganhar_experiencia(self, quantidade):
        """Soma experiência e retorna quantos níveis o herói subiu."""
        if quantidade < 0:
            raise ValueError("experiência não pode ser negativa")
        self.experiencia += quantidade
        ganhos = 0
        while self.experiencia >= self.experiencia_necessaria:
            self.experiencia -= self.experiencia_necessaria
            self.nivel += 1
            ganhos += 1
        if ganhos:
            self.recalcular_atributos()     # passivas crescem com o nível
        return ganhos

    @property
    def pode_levar_dano(self):
        return self.invencivel <= 0 and self.esta_vivo and not self.imortal

    def receber_dano(self, quantidade):
        morreu = super().receber_dano(quantidade)
        self.invencivel = INVENCIBILIDADE_APOS_DANO
        return morreu

    def _arte(self, pasta, pasta_feminina, imagem):
        """Animações do aluno ou, se a aparência é feminina e a arte existe, da aluna."""
        if self.aparencia is not None and self.aparencia.feminino and pasta_feminina:
            feminina = Recursos.animacoes(pasta_feminina)
            if feminina:
                return feminina
        return Recursos.animacoes_ou_imagem(pasta, imagem, self.ALTURA)

    def _animacoes(self):
        if self.transformado:
            base = self._arte(self.PASTA_TRANSFORMADO, self.PASTA_TRANSFORMADO_FEMININA, self.IMAGEM_TRANSFORMADO)
            return vestir_animacoes(base, self.aparencia, self.MOLETOM_ORIGINAL, cabelo_natural=False)
        base = self._arte(self.PASTA_SPRITE, self.PASTA_SPRITE_FEMININA, self.IMAGEM)
        return vestir_animacoes(base, self.aparencia, self.MOLETOM_ORIGINAL)

    def vestir(self, aparencia):
        """Troca o gênero e as cores do aluno (pele, cabelo, moletom, calça)."""
        self.aparencia = aparencia
        self.animador.trocar_conjunto(self._animacoes())

    @property
    def animado(self):
        return len(self.animador.animacoes) > 1

    def _atualizar_animacao(self, dt):
        transformado = bool(self.PASTA_TRANSFORMADO or self.IMAGEM_TRANSFORMADO) and self.tem_bonus("ssj")
        if transformado != self.transformado:
            self.transformado = transformado
            self.animador.trocar_conjunto(self._animacoes())
        self.animador.tocar("andar" if self.movendo else "parado")
        self.animador.atualizar(dt)

    def usar_especial(self, jogo):
        return self.especial.usar(self, jogo)

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.piscar = max(0.0, self.piscar - dt)
        self.invencivel = max(0.0, self.invencivel - dt)
        direcao = pygame.Vector2(jogo.entrada.direcao)
        self.movendo = direcao.length_squared() > 0
        if self.movendo:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * dt
            self.direcao_mira = pygame.Vector2(direcao)
            if abs(direcao.x) > 0.01:
                self.olhando_esquerda = direcao.x < 0
        self.posicao = jogo.resolver_obstaculos(self.posicao, self.raio)
        arena = jogo.arena
        self.posicao.x = max(arena.left + self.raio, min(self.posicao.x, arena.right - self.raio))
        self.posicao.y = max(arena.top + self.raio, min(self.posicao.y, arena.bottom - self.raio))
        if jogo.entrada.mira is not None:
            mira = pygame.Vector2(jogo.entrada.mira) - self.posicao
            if mira.length_squared() > 1:
                self.direcao_mira = mira.normalize()
                self.olhando_esquerda = mira.x < 0
        if self.regeneracao:
            self.curar(self.regeneracao * dt)
        for b in self.bonus:
            b.atualizar(dt)
        self.bonus = [b for b in self.bonus if b.ativo]
        self._atualizar_animacao(dt)
        self.especial.atualizar(dt, self.mult_recarga * self.mult_especial)
        for arma in list(self.armas):
            arma.atualizar(dt, jogo, self)

    def desenhar(self, tela, camera):
        imagem = self.animador.quadro_atual
        if self.animado:
            pulo = 0
        else:
            pulo = abs(math.sin(self.tempo * 10)) * 4 if self.movendo else (1 + math.sin(self.tempo * 2)) * 0.8
        alfa = 130 if self.invencivel > 0 and int(self.invencivel * 20) % 2 else 255
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.olhando_esquerda,
                        piscar=self.piscar > 0, deslocamento_y=pulo, alfa=alfa)
