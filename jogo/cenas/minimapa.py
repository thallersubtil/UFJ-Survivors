"""Mini-mapa do campus (tecla M): onde o aluno está e onde ficam os mini-chefes."""
import math

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import desenhar_painel, desenhar_texto, escurecer
from jogo.config import ALTURA, LARGURA, Cor
from jogo.nucleo.recursos import Recursos


class CenaMiniMapa(Cena):
    """Pausa a partida e mostra o campus inteiro, com o rosto de cada mini-chefe no lugar dele.

    Clicar num rosto marca (ou desmarca) o mini-chefe: só os marcados ganham seta na borda da tela
    durante a partida. Fecha com M, Esc ou Enter.
    """

    ALTURA_DO_MAPA = 640
    TECLAS_FECHAR = (pygame.K_m, pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
    COR_DO_MARCADO = (255, 214, 92)
    COR_ALUNO = (96, 196, 255)
    RAIO = 20

    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.tempo = 0.0

    @property
    def area(self):
        """Retângulo do mapa na tela."""
        mapa = self.jogo.mapa.miniatura(self.ALTURA_DO_MAPA)
        return mapa.get_rect(center=(LARGURA // 2, ALTURA // 2 + 8))

    def ponto_no_mapa(self, posicao, area=None):
        """Converte uma posição do mundo para a tela, dentro do retângulo `area` do mini-mapa."""
        area = area or self.area
        arena = self.jogo.arena
        return (round(area.x + (posicao[0] - arena.left) / arena.width * area.width),
                round(area.y + (posicao[1] - arena.top) / arena.height * area.height))

    def marcador_em(self, ponto):
        """O mini-chefe cujo rosto está debaixo do ponto da tela (o mais próximo), ou None."""
        perto = [(math.dist(ponto, self.ponto_no_mapa(m.posicao)), m) for m in self.jogo.marcadores()]
        perto = [(d, m) for d, m in perto if d <= self.RAIO + 6]
        return min(perto, key=lambda par: par[0])[1] if perto else None

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN and evento.key in self.TECLAS_FECHAR:
            self.app.desempilhar()
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            marcador = self.marcador_em(evento.pos)
            if marcador is not None:
                self.jogo.marcar_no_mapa(marcador.NOME)
                Recursos.tocar("coleta", 0.4)

    def atualizar(self, dt):
        self.tempo += dt

    def desenhar(self, tela):
        escurecer(tela, 200)
        area = self.area
        desenhar_painel(tela, area.inflate(20, 20))
        tela.blit(self.jogo.mapa.miniatura(self.ALTURA_DO_MAPA), area)
        desenhar_texto(tela, "CAMPUS JATOBÁ", 28, Cor.DESTAQUE, centro=(area.centerx, 24))
        pulso = 0.5 + 0.5 * math.sin(self.tempo * 5)
        sobre = self.marcador_em(pygame.mouse.get_pos()) if pygame.mouse.get_focused() else None
        for marcador in self.jogo.marcadores():
            self._marcador(tela, self.ponto_no_mapa(marcador.posicao, area), marcador, pulso, marcador is sobre)
        aluno = self.ponto_no_mapa(self.jogo.jogador.posicao, area)
        pygame.draw.circle(tela, Cor.BORDA_ESCURA, aluno, 9)
        pygame.draw.circle(tela, self.COR_ALUNO, aluno, 7)
        pygame.draw.circle(tela, (255, 255, 255), aluno, round(10 + 5 * pulso), 2)
        x = area.right + 34
        desenhar_texto(tela, "Clique num rosto", 16, Cor.TEXTO, topo_esquerda=(x, area.bottom - 96))
        desenhar_texto(tela, "para marcar: a seta", 16, Cor.TEXTO, topo_esquerda=(x, area.bottom - 74))
        desenhar_texto(tela, "aponta para ele.", 16, Cor.TEXTO, topo_esquerda=(x, area.bottom - 52))
        desenhar_texto(tela, "[M] ou [Esc] fechar", 15, Cor.TEXTO_FRACO, topo_esquerda=(x, area.bottom - 22))

    def _marcador(self, tela, ponto, marcador, pulso, sobre):
        marcado = marcador.NOME in self.jogo.marcados
        raio = self.RAIO + (3 if sobre else 0)
        pygame.draw.circle(tela, Cor.BORDA_ESCURA, ponto, raio)
        rosto = Recursos.imagem(marcador.rosto, raio * 2 - 8)
        tela.blit(rosto, rosto.get_rect(center=ponto))
        pygame.draw.circle(tela, self.COR_DO_MARCADO if marcado else Cor.TEXTO, ponto, raio, 3)
        if marcado:
            pygame.draw.circle(tela, self.COR_DO_MARCADO, ponto, round(raio + 5 + 5 * pulso), 2)
        if sobre:
            desenhar_texto(tela, marcador.NOME, 15, Cor.TEXTO, centro=(ponto[0], ponto[1] - raio - 12))
