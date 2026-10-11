"""Peças de interface reaproveitadas pelas cenas."""
import pygame

from jogo.config import Cor
from jogo.nucleo.recursos import Recursos

TECLAS_CONFIRMAR = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


def desenhar_texto(tela, texto, tamanho, cor, *, centro=None, topo_esquerda=None, topo_direita=None, sombra=True):
    fonte = Recursos.fonte(tamanho)
    imagem = fonte.render(texto, True, cor)
    if centro is not None:
        retangulo = imagem.get_rect(center=centro)
    elif topo_direita is not None:
        retangulo = imagem.get_rect(topright=topo_direita)
    else:
        retangulo = imagem.get_rect(topleft=topo_esquerda or (0, 0))
    if sombra:
        tela.blit(fonte.render(texto, True, Cor.BORDA_ESCURA), retangulo.move(2, 2))
    tela.blit(imagem, retangulo)
    return retangulo


def quebrar_linhas(texto, fonte, largura):
    linhas, atual = [], ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if fonte.size(tentativa)[0] <= largura or not atual:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def desenhar_painel(tela, retangulo, cor_fundo=Cor.PAINEL, cor_borda=Cor.BORDA, alfa=235):
    painel = pygame.Surface(retangulo.size, pygame.SRCALPHA)
    pygame.draw.rect(painel, (*cor_fundo, alfa), painel.get_rect(), border_radius=6)
    pygame.draw.rect(painel, Cor.BORDA_ESCURA, painel.get_rect(), 4, border_radius=6)
    pygame.draw.rect(painel, cor_borda, painel.get_rect().inflate(-6, -6), 2, border_radius=4)
    tela.blit(painel, retangulo)


def desenhar_barra(tela, retangulo, fracao, cor, cor_fundo=(40, 30, 50)):
    pygame.draw.rect(tela, Cor.BORDA_ESCURA, retangulo.inflate(4, 4), border_radius=4)
    pygame.draw.rect(tela, cor_fundo, retangulo, border_radius=3)
    cheio = retangulo.copy()
    cheio.width = round(retangulo.width * max(0.0, min(1.0, fracao)))
    if cheio.width > 0:
        pygame.draw.rect(tela, cor, cheio, border_radius=3)


def escurecer(tela, alfa=160):
    veu = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
    veu.fill((10, 8, 18, alfa))
    tela.blit(veu, (0, 0))


class Botao:
    IMAGEM = "legado/ui/btn_wood.png"
    IMAGEM_FOCO = "legado/ui/btn_gold.png"

    def __init__(self, texto, centro, acao, largura=320, altura=64):
        self.texto = texto
        self.acao = acao
        self.retangulo = pygame.Rect(0, 0, largura, altura)
        self.retangulo.center = centro

    def desenhar(self, tela, focado):
        imagem = Recursos.imagem(self.IMAGEM_FOCO if focado else self.IMAGEM)
        tela.blit(pygame.transform.scale(imagem, self.retangulo.size), self.retangulo)
        desenhar_texto(tela, self.texto, 28, Cor.BORDA_ESCURA if focado else Cor.TEXTO,
                       centro=self.retangulo.center, sombra=not focado)


class MenuDeBotoes:
    """Lista de botões navegável por teclado (setas/WS + Enter) e mouse."""

    def __init__(self, botoes):
        self.botoes = botoes
        self.indice = 0

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP, pygame.K_w):
                self.indice = (self.indice - 1) % len(self.botoes)
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self.indice = (self.indice + 1) % len(self.botoes)
            elif evento.key in TECLAS_CONFIRMAR:
                self.botoes[self.indice].acao()
        elif evento.type == pygame.MOUSEMOTION:
            for i, botao in enumerate(self.botoes):
                if botao.retangulo.collidepoint(evento.pos):
                    self.indice = i
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for botao in self.botoes:
                if botao.retangulo.collidepoint(evento.pos):
                    botao.acao()
                    return

    def desenhar(self, tela):
        for i, botao in enumerate(self.botoes):
            botao.desenhar(tela, i == self.indice)
