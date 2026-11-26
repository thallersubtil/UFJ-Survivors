"""Apresentação do chefe: a partida para por um instante e o professor aparece em pose de chefão."""
import math

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR, escurecer
from jogo.nucleo.recursos import Recursos
from jogo.ui.pixel import Paleta as P, ease_back, ease_out, janela, texto


class CenaChefe(Cena):
    """Fica por cima da partida (que não anda enquanto isso) e sai sozinha; Enter, Espaço ou clique pulam."""

    DURACAO = 3.0
    TEMPO_MINIMO = 0.5           # antes disso não dá para pular (evita pular sem ver, no calor da luta)

    def __init__(self, app, chefe):
        super().__init__(app)
        self.chefe = chefe
        self.tempo = 0.0
        Recursos.tocar("especial", 0.7)

    @property
    def frase(self):
        proprio = getattr(self.chefe, "NOME_PROPRIO", "")
        if proprio:                                  # chefe com nome: "O Professor de Cálculo Flávio apareceu!"
            return f"{self.chefe.ARTIGO_DEFINIDO} {self.chefe.NOME} {proprio} apareceu!"
        return f"{self.chefe.ARTIGO} {self.chefe.NOME} selvagem apareceu!"

    def _sair(self):
        self.app.desempilhar()

    def tratar_evento(self, evento):
        pular = (evento.type == pygame.KEYDOWN and evento.key in TECLAS_CONFIRMAR) or \
                (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1)
        if pular and self.tempo >= self.TEMPO_MINIMO:
            self._sair()

    def atualizar(self, dt):
        self.tempo += dt
        if self.tempo >= self.DURACAO:
            self._sair()

    def _raios(self, tela, centro, cor):
        """Raios de velocidade girando atrás do chefe, como em abertura de luta."""
        largura, altura = tela.get_size()
        alcance = math.hypot(largura, altura)
        camada = pygame.Surface((largura, altura), pygame.SRCALPHA)
        for i in range(18):
            angulo = math.radians(i * 20 + self.tempo * 25)
            abertura = math.radians(5)
            pontas = [centro,
                      (centro[0] + math.cos(angulo - abertura) * alcance, centro[1] + math.sin(angulo - abertura) * alcance),
                      (centro[0] + math.cos(angulo + abertura) * alcance, centro[1] + math.sin(angulo + abertura) * alcance)]
            pygame.draw.polygon(camada, (*cor, 46), pontas)
        tela.blit(camada, (0, 0))

    def desenhar(self, tela):
        largura, altura = tela.get_size()
        entrada = ease_out(janela(self.tempo, 0, 0.25))
        saida = 1 - janela(self.tempo, self.DURACAO - 0.3, 0.3)
        escurecer(tela, int(215 * entrada * saida))
        cor = self.chefe.COR_DA_APRESENTACAO
        self._raios(tela, (largura * 0.3, altura * 0.5), cor)

        # o chefe entra pela esquerda, com um tranco
        caminho = self.chefe.ILUSTRACAO
        if caminho and (Recursos.pasta / caminho).is_file():
            arte = Recursos.na_altura(Recursos.imagem(caminho), int(altura * 0.9))
        else:                                   # sem a ilustração: o próprio sprite do chefe, bem grande
            arte = Recursos.na_altura(self.chefe.animador.quadro_atual, int(altura * 0.6))
        chegada = ease_back(janela(self.tempo, 0.05, 0.45), 1.3)
        x = -arte.get_width() / 2 + (largura * 0.3 + arte.get_width() / 2) * chegada
        y = altura / 2 + math.sin(self.tempo * 3) * 6
        arte = arte.copy()
        arte.set_alpha(int(255 * saida))
        tela.blit(arte, arte.get_rect(center=(round(x), round(y))))

        # a faixa com a frase entra pela direita
        faixa = pygame.Rect(0, 0, int(largura * 0.56), 150)
        desliza = ease_out(janela(self.tempo, 0.3, 0.4))
        faixa.midleft = (int(largura - faixa.w * desliza) + 20, int(altura * 0.62))
        fundo = pygame.Surface(faixa.size, pygame.SRCALPHA)
        fundo.fill((14, 10, 26, int(235 * saida)))
        tela.blit(fundo, faixa)
        pygame.draw.rect(tela, cor, (faixa.x, faixa.y, faixa.w, 6))
        pygame.draw.rect(tela, cor, (faixa.x, faixa.bottom - 6, faixa.w, 6))
        if desliza > 0.6:
            visiveis = max(1, int(len(self.frase) * janela(self.tempo, 0.6, 0.7)))
            linhas = self._quebrar(self.frase[:visiveis], 26)
            for i, linha in enumerate(linhas):
                texto(tela, linha, (faixa.x + 34, faixa.y + 26 + i * 50), P.BRANCO if i else P.OURO, 46)
        grito = getattr(self.chefe, "GRITO", "")
        if grito and self.tempo >= 1.2:                         # a fala dele, em itálico de mentira: entre aspas
            texto(tela, f"“{grito}”", (faixa.x + 34, faixa.bottom + 18), cor, 23)
        if self.tempo >= self.TEMPO_MINIMO and int(self.tempo * 3) % 2:
            texto(tela, "Enter: lutar", (largura - 30, altura - 44), P.CINZA, 23, ancora="topright")

    @staticmethod
    def _quebrar(frase, limite):
        """Parte a frase em duas linhas, sem cortar palavra."""
        if len(frase) <= limite:
            return [frase]
        corte = frase.rfind(" ", 0, limite + 1)
        return [frase[:corte], frase[corte + 1:]] if corte > 0 else [frase]
