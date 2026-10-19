"""Janela do jogo e pilha de cenas."""
import pygame

from jogo.config import ALTURA, ARQUIVO_RANKING, FPS, LARGURA, TITULO
from jogo.ranking import Ranking


class JanelaNitida:
    """Janela que usa todos os pixels da tela (Retina inclusive) e amplia o jogo sem suavizar.

    O jogo desenha sempre em `tela` (1280x720); `mostrar()` copia para a janela,
    ampliando com vizinho mais próximo quando a tela física tem mais pixels.
    """

    def __init__(self, titulo, tamanho):
        self.janela = pygame.Window(titulo, tamanho, allow_high_dpi=True)
        self.tela = pygame.Surface(tamanho)

    def mostrar(self):
        destino = self.janela.get_surface()
        largura, altura = destino.get_size()
        fator = min(largura / self.tela.get_width(), altura / self.tela.get_height())
        if abs(fator - round(fator)) < 0.03:
            fator = round(fator)
        tamanho = (max(1, int(self.tela.get_width() * fator)), max(1, int(self.tela.get_height() * fator)))
        if tamanho == destino.get_size():
            pygame.transform.scale(self.tela, tamanho, destino)
        else:
            destino.fill((0, 0, 0))
            ampliada = pygame.transform.scale(self.tela, tamanho)   # vizinho mais próximo: sem borrar
            destino.blit(ampliada, ampliada.get_rect(center=(largura // 2, altura // 2)))
        self.janela.flip()


class Aplicacao:
    def __init__(self, tela=None):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass
        self.janela = None
        if tela is None:
            try:
                self.janela = JanelaNitida(TITULO, (LARGURA, ALTURA))
                tela = self.janela.tela
            except (pygame.error, AttributeError, TypeError):
                tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.SCALED | pygame.RESIZABLE)
                pygame.display.set_caption(TITULO)
        self.tela = tela
        self.relogio = pygame.time.Clock()
        self.ranking = Ranking(ARQUIVO_RANKING)
        self.aparencia = None        # última aparência escolhida, para a próxima partida
        self.modo_mira = "mouse"     # "mouse": mira no cursor; "automatica": no inimigo mais próximo
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

    def alternar_mira(self):
        self.modo_mira = "automatica" if self.modo_mira == "mouse" else "mouse"
        return self.modo_mira

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
            if self.janela is not None:
                self.janela.mostrar()
            else:
                pygame.display.flip()
        pygame.quit()
