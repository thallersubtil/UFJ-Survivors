import math

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import (TECLAS_CONFIRMAR, desenhar_barra, desenhar_fundo, desenhar_painel, desenhar_texto,
                                quebrar_linhas)
from jogo.config import ALTURA, LARGURA, Cor
from jogo.jogador.alunos import HEROIS
from jogo.nucleo.recursos import Recursos
from jogo.opcoes import OpcoesDePartida


class CenaSelecao(Cena):
    def __init__(self, app, opcoes=None):
        super().__init__(app)
        self.opcoes = opcoes or OpcoesDePartida()
        self.indice = 0
        self.tempo = 0.0
        self.exemplos = [classe((0, 0)) for classe in HEROIS]
        self.cartoes = []
        for i in range(len(HEROIS)):
            r = pygame.Rect(0, 0, 420, 500)
            r.center = (LARGURA // 2 + (i - (len(HEROIS) - 1) / 2) * 460, 390)
            self.cartoes.append(r)

    def _comecar(self):
        from jogo.cenas.personalizacao import CenaPersonalizacao
        self.app.trocar(CenaPersonalizacao(self.app, HEROIS[self.indice], self.opcoes))

    def _voltar(self):
        from jogo.cenas.titulo import CenaTitulo
        self.app.trocar(CenaTitulo(self.app))

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_LEFT, pygame.K_a):
                self.indice = (self.indice - 1) % len(HEROIS)
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                self.indice = (self.indice + 1) % len(HEROIS)
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
        desenhar_texto(tela, "ESCOLHA SEU ALUNO", 44, Cor.DESTAQUE, centro=(LARGURA // 2, 70))
        if self.opcoes.treino:
            desenhar_texto(tela, "MODO TREINO", 18, Cor.TEXTO_FRACO, centro=(LARGURA // 2, 112))
        for i, (heroi, r) in enumerate(zip(self.exemplos, self.cartoes)):
            self._cartao(tela, heroi, r, i == self.indice)
        desenhar_texto(tela, "[<- ->] escolher    [Enter] começar    [Esc] voltar", 16, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, ALTURA - 24))

    def _cartao(self, tela, heroi, r, focado):
        desenhar_painel(tela, r, cor_borda=Cor.DESTAQUE if focado else Cor.BORDA_ESCURA)
        animacoes = Recursos.animacoes_ou_imagem(heroi.PASTA_SPRITE, heroi.IMAGEM, 150)
        animacao = animacoes.get("andar" if focado else "parado") or next(iter(animacoes.values()))
        sprite = Recursos.na_altura(animacao.quadro(self.tempo), 150)
        pulo = 0 if len(animacao.quadros) > 1 else (abs(math.sin(self.tempo * 6)) * 8 if focado else 0)
        tela.blit(sprite, sprite.get_rect(midbottom=(r.centerx, r.top + 190 - pulo)))
        desenhar_texto(tela, heroi.NOME, 30, Cor.TEXTO, centro=(r.centerx, r.top + 215))
        desenhar_texto(tela, heroi.DESCRICAO, 16, Cor.TEXTO_FRACO, centro=(r.centerx, r.top + 245))
        x = r.left + 30
        desenhar_texto(tela, "Vida", 16, Cor.TEXTO, topo_esquerda=(x, r.top + 270))
        desenhar_barra(tela, pygame.Rect(x + 120, r.top + 274, 230, 12), heroi.VIDA / 130, Cor.VIDA)
        desenhar_texto(tela, "Velocidade", 16, Cor.TEXTO, topo_esquerda=(x, r.top + 296))
        desenhar_barra(tela, pygame.Rect(x + 120, r.top + 300, 230, 12), heroi.VELOCIDADE / 230, Cor.EXPERIENCIA)
        arma = heroi.armas[0]
        icone = Recursos.icone(arma.ICONE, 40)
        tela.blit(icone, icone.get_rect(center=(x + 20, r.top + 350)))
        desenhar_texto(tela, f"Arma: {arma.NOME}", 18, Cor.TEXTO, topo_esquerda=(x + 50, r.top + 340))
        especial = heroi.especial
        icone = Recursos.icone(especial.ICONE, 40)
        tela.blit(icone, icone.get_rect(center=(x + 20, r.top + 405)))
        desenhar_texto(tela, f"Especial: {especial.NOME}", 18, Cor.DESTAQUE, topo_esquerda=(x + 50, r.top + 395))
        fonte = Recursos.fonte(15)
        for n, linha in enumerate(quebrar_linhas(especial.DESCRICAO, fonte, r.width - 110)):
            desenhar_texto(tela, linha, 15, Cor.TEXTO_FRACO, topo_esquerda=(x + 50, r.top + 420 + n * 18))
