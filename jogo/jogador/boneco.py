"""Boneco articulado do aluno, no estilo Scribblenauts: cabeça, tronco, braços e pernas separados.

O Boneco contém as partes escolhidas na Aparencia (composição) e monta cada quadro
girando braços e pernas em volta dos ombros e do quadril. As animações são geradas
por código (muitos quadros, por isso o andar fica fluido) e guardadas em cache.
"""
import math
from dataclasses import dataclass

import pygame

from jogo.jogador import partes
from jogo.nucleo.animacao import Animacao


@dataclass(frozen=True)
class Pose:
    """Ângulos em graus a partir da vertical (positivo = para a frente)."""

    perna: float = 0.0           # perna da frente; a de trás faz o oposto
    braco: float = 0.0           # braço da frente; o de trás faz o oposto
    respiracao: float = 0.0      # sobe o tronco e a cabeça (pixels)
    cabeca: float = 0.0          # balanço extra da cabeça (pixels)
    balanco: float = 0.0         # cabelo e saia atrasados em relação ao corpo
    piscando: bool = False


class Boneco:
    LARGURA, ALTURA = 72, 92     # tamanho do quadro na tela; o chão fica embaixo, no meio
    AMPLIACAO = 3                # desenha 3x maior e reduz suavizando
    ESPESSURA = 1.3              # contorno, em pixels de tela
    PERNA = 21                   # do quadril ao tornozelo
    BRACO = 15
    TRONCO = 17                  # do quadril ao ombro
    PE = 2.6                     # altura do centro do sapato acima do chão
    QUADROS_ANDAR, FPS_ANDAR = 12, 18
    QUADROS_PARADO, FPS_PARADO = 16, 8
    PISCAR = (12,)               # quadros do "parado" em que ele pisca
    _cache = {}

    def __init__(self, aparencia, transformado=False, escala=1):
        self.aparencia = aparencia
        self.escala = escala         # maior que 1 para as prévias dos menus
        self.corpo = partes.CORPOS[aparencia.genero]()
        classe_penteado = partes.PenteadoSuperSaiyajin if transformado else partes.PENTEADOS[aparencia.penteado]
        self.penteado = classe_penteado()
        self.olhos = partes.OLHOS[aparencia.olhos]()
        self.cima = partes.ROUPAS_DE_CIMA[aparencia.cima]()
        self.baixo = partes.ROUPAS_DE_BAIXO[aparencia.baixo]()
        self.acessorio = partes.ACESSORIOS[aparencia.acessorio]()

    @classmethod
    def animacoes_de(cls, aparencia, transformado=False, escala=1):
        """Animações "parado" e "andar" desta aparência (geradas uma vez e guardadas)."""
        chave = (aparencia.chave(), transformado, escala)
        if chave not in cls._cache:
            cls._cache[chave] = cls(aparencia, transformado, escala).animacoes()
        return cls._cache[chave]

    # Poses

    @staticmethod
    def pose_andando(fase):
        """`fase` de 0 a 1 percorre um passo completo (as duas pernas)."""
        onda = math.sin(2 * math.pi * fase)
        return Pose(perna=30 * onda, braco=-28 * onda, cabeca=0.6 * math.sin(4 * math.pi * fase),
                    balanco=-3.5 * math.sin(2 * math.pi * fase - 0.8))

    @classmethod
    def pose_parada(cls, fase, piscando=False):
        onda = math.sin(2 * math.pi * fase)
        return Pose(perna=6, braco=4 + 3 * onda, respiracao=0.7 * (onda + 1) / 2, cabeca=0.3 * onda,
                    balanco=1.2 * math.sin(2 * math.pi * fase - 0.6), piscando=piscando)

    def animacoes(self):
        andar = [self.quadro(self.pose_andando(i / self.QUADROS_ANDAR)) for i in range(self.QUADROS_ANDAR)]
        parado = [self.quadro(self.pose_parada(i / self.QUADROS_PARADO, i in self.PISCAR))
                  for i in range(self.QUADROS_PARADO)]
        return {"parado": Animacao(parado, self.FPS_PARADO), "andar": Animacao(andar, self.FPS_ANDAR)}

    # Esqueleto e desenho

    def esqueleto(self, pose):
        """Posição das juntas para a pose (chão em y = 0)."""
        def ponta(origem, angulo, comprimento):
            a = math.radians(angulo)
            return (origem[0] + comprimento * math.sin(a), origem[1] + comprimento * math.cos(a))

        quadril_y = -self.PE - self.PERNA * math.cos(math.radians(pose.perna))
        ombro_y = quadril_y - self.TRONCO - pose.respiracao
        e = {"quadril_y": quadril_y, "ombro_y": ombro_y,
             "cabeca": (1.5, ombro_y - 13.5 + pose.cabeca)}
        e["quadril_tras"], e["quadril_frente"] = (-1.5, quadril_y), (1.5, quadril_y)
        e["pe_tras"] = ponta(e["quadril_tras"], -pose.perna, self.PERNA)
        e["pe_frente"] = ponta(e["quadril_frente"], pose.perna, self.PERNA)
        e["ombro_tras"], e["ombro_frente"] = (-3.5, ombro_y + 2.5), (3.5, ombro_y + 2.5)
        e["mao_tras"] = ponta(e["ombro_tras"], -pose.braco, self.BRACO)
        e["mao_frente"] = ponta(e["ombro_frente"], pose.braco, self.BRACO)
        return e

    def quadro(self, pose):
        k = self.AMPLIACAO * self.escala
        grande = pygame.Surface((round(self.LARGURA * k), round(self.ALTURA * k)), pygame.SRCALPHA)
        pincel = partes.Pincel(grande, (self.LARGURA * k / 2, (self.ALTURA - 2) * k), k, self.ESPESSURA)
        self.desenhar(pincel, self.esqueleto(pose), pose)
        tamanho = (round(self.LARGURA * self.escala), round(self.ALTURA * self.escala))
        return pygame.transform.smoothscale(grande, tamanho)

    def desenhar(self, p, e, pose):
        """Pinta as partes de trás para a frente."""
        a = self.aparencia
        cabelo = a.cor("cabelo")
        self.penteado.desenhar_tras(p, e, cabelo, pose.balanco)
        self.cima.desenhar_braco(p, e["ombro_tras"], e["mao_tras"], a, sombra=True)
        self.baixo.desenhar_perna(p, e["quadril_tras"], e["pe_tras"], a, sombra=True)
        self.baixo.desenhar_perna(p, e["quadril_frente"], e["pe_frente"], a, sombra=False)
        self.baixo.desenhar_quadril(p, e, self.corpo, a)
        self.cima.desenhar_tronco(p, e, self.corpo, a)
        self.baixo.desenhar_sobre_tronco(p, e, self.corpo, a, pose.balanco)
        self.corpo.desenhar_cabeca(p, e, a)
        self.olhos.desenhar(p, e, self.corpo, a, pose.piscando)
        self.penteado.desenhar_frente(p, e, cabelo, pose.balanco)
        self.acessorio.desenhar(p, e, a)
        self.cima.desenhar_braco(p, e["ombro_frente"], e["mao_frente"], a, sombra=False)
