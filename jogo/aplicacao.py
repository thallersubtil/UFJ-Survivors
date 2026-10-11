"""Janela do jogo e pilha de cenas."""
import pygame

from jogo.config import ALTURA, ARQUIVO_RANKING, FPS, LARGURA, TITULO
from jogo.ranking import Ranking


class Aplicacao:
    def __init__(self, tela=None):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass
        if tela is None:
            tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.SCALED | pygame.RESIZABLE)
            pygame.display.set_caption(TITULO)
        self.tela = tela
        self.relogio = pygame.time.Clock()
        self.ranking = Ranking(ARQUIVO_RANKING)
        self.mira_mouse = False
        self.cenas = []
        self.rodando = True

    @property
    def cena_atual(self):
        return self.cenas[-1]

    def empilhar(self, cena):
        self.cenas.append(cena)

    def desempilhar(self):
        self.cenas.pop()

    def trocar(self, cena):
        self.cenas = [cena]

    def sair(self):
        self.rodando = False

    def passo(self, dt, eventos):
        """Um quadro: entrega eventos, atualiza a cena do topo e desenha a pilha."""
        for evento in eventos:
            if evento.type == pygame.QUIT:
                self.sair()
                return
            self.cena_atual.tratar_evento(evento)
        self.cena_atual.atualizar(dt)
        for cena in list(self.cenas):
            cena.desenhar(self.tela)

    def executar(self, cena_inicial):
        self.trocar(cena_inicial)
        while self.rodando and self.cenas:
            dt = min(self.relogio.tick(FPS) / 1000, 1 / 20)
            self.passo(dt, pygame.event.get())
            pygame.display.flip()
        pygame.quit()
