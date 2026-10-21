import math

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import (TECLAS_CONFIRMAR, desenhar_barra, desenhar_fundo, desenhar_painel, desenhar_texto,
                                quebrar_linhas)
from jogo.config import ALTURA, LARGURA, Cor
from jogo.jogador.classes import CLASSES
from jogo.nucleo.recursos import Recursos
from jogo.opcoes import OpcoesDePartida


class CenaSelecao(Cena):
    def __init__(self, app, opcoes=None):
        super().__init__(app)
        self.opcoes = opcoes or OpcoesDePartida()
        self.indice = 0
        self.tempo = 0.0
        self.exemplos = [classe((0, 0)) for classe in CLASSES]
        for exemplo in self.exemplos:            # o aluno personalizado, caracterizado para cada classe
            if self.opcoes.aparencia is not None:
                exemplo.vestir(self.opcoes.aparencia)
        self.cartoes = []
        for i in range(len(CLASSES)):
            r = pygame.Rect(0, 0, 390, 540)
            r.center = (LARGURA // 2 + (i - (len(CLASSES) - 1) / 2) * 410, 400)
            self.cartoes.append(r)

    def _comecar(self):
        from jogo.cenas.partida import CenaPartida
        self.app.trocar(CenaPartida(self.app, CLASSES[self.indice], self.opcoes))

    def _voltar(self):
        from jogo.cenas.personalizacao import CenaPersonalizacao
        self.app.trocar(CenaPersonalizacao(self.app, self.opcoes))

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_LEFT, pygame.K_a):
                self.indice = (self.indice - 1) % len(CLASSES)
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                self.indice = (self.indice + 1) % len(CLASSES)
            elif evento.key in TECLAS_CONFIRMAR:
                self._comecar()
            elif evento.key == pygame.K_ESCAPE:
                self._voltar()
        elif evento.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.cartoes):
                if r.collidepoint(evento.pos):
                    self.indice = i
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, r in enumerate(self.cartoes):
                if r.collidepoint(evento.pos):
                    self.indice = i
                    self._comecar()

    def atualizar(self, dt):
        self.tempo += dt

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/titulo_fundo.png", escuro=170)
        desenhar_texto(tela, "ESCOLHA SUA CLASSE", 44, Cor.DESTAQUE, centro=(LARGURA // 2, 70))
        if self.opcoes.treino:
            desenhar_texto(tela, "MODO TREINO", 18, Cor.TEXTO_FRACO, centro=(LARGURA // 2, 112))
        for i, (heroi, r) in enumerate(zip(self.exemplos, self.cartoes)):
            self._cartao(tela, heroi, r, i == self.indice)
        desenhar_texto(tela, "[<- ->] escolher    [Enter] começar    [Esc] voltar", 16, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, ALTURA - 24))

    def _cartao(self, tela, heroi, r, focado):
        desenhar_painel(tela, r, cor_borda=Cor.DESTAQUE if focado else Cor.BORDA_ESCURA)
        animacoes = heroi.animador.animacoes
        animacao = animacoes.get("andar" if focado else "parado") or next(iter(animacoes.values()))
        sprite = Recursos.na_altura(animacao.quadro(self.tempo), 130)
        pulo = 0 if len(animacao.quadros) > 1 else (abs(math.sin(self.tempo * 6)) * 8 if focado else 0)
        tela.blit(sprite, sprite.get_rect(midbottom=(r.centerx, r.top + 160 - pulo)))
        desenhar_texto(tela, heroi.NOME, 30, Cor.TEXTO, centro=(r.centerx, r.top + 185))
        desenhar_texto(tela, heroi.DESCRICAO, 15, Cor.TEXTO_FRACO, centro=(r.centerx, r.top + 212))
        x = r.left + 24
        largura_barra = r.width - 150
        desenhar_texto(tela, "Vida", 16, Cor.TEXTO, topo_esquerda=(x, r.top + 232))
        desenhar_barra(tela, pygame.Rect(x + 110, r.top + 236, largura_barra, 12), heroi.VIDA / 130, Cor.VIDA)
        desenhar_texto(tela, "Velocidade", 16, Cor.TEXTO, topo_esquerda=(x, r.top + 256))
        desenhar_barra(tela, pygame.Rect(x + 110, r.top + 260, largura_barra, 12), heroi.VELOCIDADE / 230,
                       Cor.EXPERIENCIA)
        arma, passiva, especial = heroi.armas[0], heroi.passiva, heroi.especial
        topo = r.top + 290
        topo = self._habilidade(tela, r, topo, "Ativa", arma.NOME, arma.DESCRICAO, Cor.TEXTO, arma.ICONE)
        topo = self._habilidade(tela, r, topo, "Passiva", passiva.NOME, passiva.DESCRICAO, Cor.EXPERIENCIA)
        self._habilidade(tela, r, topo, "Especial", especial.NOME, especial.DESCRICAO, Cor.DESTAQUE, especial.ICONE)

    def _habilidade(self, tela, r, topo, tipo, nome, descricao, cor, icone=None):
        """Uma linha do cartão (ícone, tipo e nome, descrição). Retorna onde a próxima começa."""
        x = r.left + 24
        if icone:
            imagem = Recursos.icone(icone, 34)
            tela.blit(imagem, imagem.get_rect(center=(x + 17, topo + 18)))
        else:
            pygame.draw.circle(tela, cor, (x + 17, topo + 18), 13, 3)
        desenhar_texto(tela, f"{tipo}: {nome}", 17, cor, topo_esquerda=(x + 44, topo))
        fonte = Recursos.fonte(14)
        linhas = quebrar_linhas(descricao, fonte, r.width - 80)[:3]
        for n, linha in enumerate(linhas):
            desenhar_texto(tela, linha, 14, Cor.TEXTO_FRACO, topo_esquerda=(x + 44, topo + 22 + n * 16))
        return topo + 30 + max(1, len(linhas)) * 16
