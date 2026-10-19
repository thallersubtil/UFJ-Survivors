"""Professor possuído por matérias: cada matéria é uma fase da luta contra o chefe."""
import math
from abc import ABC
from functools import partial

import pygame

from jogo.config import Cor
from jogo.efeitos import TextoFlutuante
from jogo.inimigos.chefe import Chefe


class ChefePossuido(Chefe, ABC):
    """Contém uma lista de matérias (composição). O nome, a vida e os ataques vêm da matéria atual.

    Quando a vida zera e ainda há matéria na lista, a próxima possui o professor: a vida
    volta cheia e a luta continua na fase seguinte. Só a última matéria derrota o chefe.
    """

    MATERIAS = ()                  # classes de Materia, na ordem das fases
    NOME_PROFESSOR = "o Professor"
    IMAGEM = "sprites/professor.png"
    PASTA_SPRITE = "professor"
    ALTURA = 112
    RAIO = 46
    VELOCIDADE = 75
    DANO = 18
    PONTOS = 5000
    EXPERIENCIA = 0
    DURACAO_TROCA = 1.6            # segundos parado e invulnerável enquanto troca de matéria

    def __init__(self, posicao, escala=1.0):
        if not self.MATERIAS:
            raise ValueError(f"{type(self).__name__} precisa de pelo menos uma matéria")
        self.materias = [classe() for classe in self.MATERIAS]
        self._indice_materia = 0
        self.troca = 0.0
        self.escudo = 0.0
        self._anunciar_troca = False
        super().__init__(posicao, escala)
        self._assumir(self.materias[0])

    @property
    def materia(self):
        return self.materias[self._indice_materia]

    @property
    def nome(self):
        return self.materia.NOME

    @property
    def fase_da_luta(self):
        return self._indice_materia + 1

    @property
    def total_de_fases(self):
        return len(self.materias)

    @property
    def tem_proxima_materia(self):
        return self._indice_materia + 1 < len(self.materias)

    @property
    def intervalo_ataque(self):
        return self.materia.INTERVALO_FURIOSO if self.furioso else self.materia.INTERVALO_ATAQUE

    @property
    def invulneravel(self):
        return self.troca > 0 or self.escudo > 0

    def _assumir(self, materia):
        self.vida_maxima = materia.VIDA
        self.vida = materia.VIDA
        self._indice = 0
        self._espera_ataque = 2.0
        self.acao_atual = None

    def ataques(self):
        return [partial(ataque, self) for ataque in self.materia.ataques()]

    def proteger(self, duracao):
        """Fica invulnerável por um tempo (usado por ataques de defesa)."""
        self.escudo = max(self.escudo, duracao)

    def receber_dano(self, quantidade):
        if self.invulneravel:
            return False
        morreu = super().receber_dano(quantidade)
        if morreu and self.tem_proxima_materia:
            self._indice_materia += 1
            self._assumir(self.materia)
            self.troca = self.DURACAO_TROCA
            self._anunciar_troca = True
            return False
        return morreu

    def mover(self, dt, jogo):
        if self._anunciar_troca:
            self._anunciar_troca = False
            jogo.anunciar(f"{self.materia.NOME} possuiu {self.NOME_PROFESSOR}!", 3)
            jogo.adicionar(TextoFlutuante(f"FASE {self.fase_da_luta}", self.posicao - (0, 90), Cor.DESTAQUE, 28,
                                          duracao=1.5))
        if self.troca > 0:
            self.troca -= dt
            return
        self.escudo = max(0.0, self.escudo - dt)
        super().mover(dt, jogo)

    def ao_morrer(self, jogo):
        """Última matéria derrotada: a prova acabou."""
        jogo.concluir_fase()

    def desenhar_corpo(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        pulso = 0.5 + 0.5 * math.sin(self.tempo * (14 if self.troca > 0 else 4))
        raio = round(self.raio * (1.3 + 0.15 * pulso))
        aura = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura, (*self.materia.COR, 60 + round(60 * pulso)), (raio, raio), raio)
        tela.blit(aura, aura.get_rect(center=(round(centro.x), round(centro.y))))
        super().desenhar_corpo(tela, camera)
        if self.escudo > 0:
            pygame.draw.circle(tela, self.materia.COR, centro, self.raio * 1.6, 4)
