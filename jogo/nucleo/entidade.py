"""Classe abstrata base de tudo que existe na arena."""
from abc import ABC, abstractmethod

import pygame


class Entidade(ABC):
    """Algo com posição na arena que se atualiza e se desenha a cada quadro.

    `grupo` diz em qual lista do Jogo a entidade também entra (por exemplo
    "inimigo"), para buscas rápidas. `camada` define a ordem de desenho:
    camadas menores são desenhadas primeiro.
    """

    grupo = "geral"
    camada = 1

    def __init__(self, posicao, raio):
        self.posicao = pygame.Vector2(posicao)
        self.raio = raio
        self.ativo = True

    @abstractmethod
    def atualizar(self, dt, jogo):
        """Avança a entidade `dt` segundos dentro do `jogo`."""

    @abstractmethod
    def desenhar(self, tela, camera):
        """Desenha a entidade na tela, convertendo a posição pela câmera."""

    def esta_visivel(self, camera):
        """Se vale a pena desenhar. Entidades grandes (prédios) sobrescrevem."""
        return camera.visivel(self.posicao, 160)

    def remover(self):
        """Marca a entidade para sair do jogo no fim do quadro."""
        self.ativo = False

    def distancia_ate(self, outra):
        return self.posicao.distance_to(outra.posicao)
