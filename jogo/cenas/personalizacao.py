"""Personalização do aluno (gênero, pele, cabelo, moletom e calça). Vem antes da escolha de classe."""
import random

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_ENTER, desenhar_fundo, desenhar_painel, desenhar_texto
from jogo.config import ALTURA, LARGURA, Cor
from jogo.jogador.aparencia import CORES, OPCOES, Aparencia
from jogo.jogador.classes import Programador
from jogo.nucleo.recursos import Recursos
from jogo.opcoes import OpcoesDePartida


class CenaPersonalizacao(Cena):
    LINHAS = (("genero", "Gênero"), ("pele", "Tom de pele"), ("cabelo", "Cabelo"), ("moletom", "Moletom"),
              ("calca", "Calça"))
    ALTURA_PREVIA = 230
    CLASSE_DA_PREVIA = Programador     # o aluno "base" mostrado enquanto personaliza

    def __init__(self, app, opcoes=None):
        super().__init__(app)
        self.opcoes = opcoes or OpcoesDePartida()
        anterior = getattr(app, "aparencia", None)
        self.aparencia = Aparencia(*anterior.chave()) if anterior is not None else Aparencia()
        self.linha = 0
        self.tempo = 0.0
        self.previa = self.CLASSE_DA_PREVIA((0, 0))
        self.previa.vestir(self.aparencia)
        self.retangulos = []
        for i in range(len(self.LINHAS)):
            r = pygame.Rect(0, 0, 600, 70)
            r.topleft = (590, 140 + i * 84)
            self.retangulos.append(r)

    def _mudar(self, passo):
        parte = self.LINHAS[self.linha][0]
        self.aparencia.trocar(parte, passo)
        self.previa.vestir(Aparencia(*self.aparencia.chave()))

    def _sortear(self):
        for parte in CORES:          # sorteia as cores; o gênero fica como está
            nome = random.choice([n for n, _ in OPCOES[parte]])
            setattr(self.aparencia, parte, nome)
        self.previa.vestir(Aparencia(*self.aparencia.chave()))

    def _restaurar(self):
        """Volta todas as cores para as originais do desenho (o gênero fica)."""
        self.aparencia.restaurar_cores()
        self.previa.vestir(Aparencia(*self.aparencia.chave()))

    def _comecar(self):
        from jogo.cenas.selecao import CenaSelecao
        escolhida = Aparencia(*self.aparencia.chave())
        self.app.aparencia = escolhida
        self.app.trocar(CenaSelecao(self.app, self.opcoes.com_aparencia(escolhida)))

    def _voltar(self):
        if self.opcoes.treino:
            from jogo.cenas.treino import CenaTreino
            self.app.trocar(CenaTreino(self.app))
        else:
            from jogo.cenas.titulo import CenaTitulo
            self.app.trocar(CenaTitulo(self.app))

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP, pygame.K_w):
                self.linha = (self.linha - 1) % len(self.LINHAS)
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self.linha = (self.linha + 1) % len(self.LINHAS)
            elif evento.key in (pygame.K_LEFT, pygame.K_a):
                self._mudar(-1)
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                self._mudar(1)
            elif evento.key == pygame.K_r:
                self._sortear()
            elif evento.key in (pygame.K_p, pygame.K_BACKSPACE):
                self._restaurar()
            elif evento.key in TECLAS_ENTER:
                self._comecar()
            elif evento.key == pygame.K_ESCAPE:
                self._voltar()
        elif evento.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.retangulos):
                if r.collidepoint(evento.pos):
                    self.linha = i
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, r in enumerate(self.retangulos):
                if r.collidepoint(evento.pos):
                    self.linha = i
                    self._mudar(-1 if evento.pos[0] < r.centerx else 1)

    def atualizar(self, dt):
        self.tempo += dt
        self.previa.animador.tocar("andar")
        self.previa.animador.atualizar(dt)

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/titulo_fundo.png", escuro=170)
        desenhar_texto(tela, "MONTE SEU ALUNO", 44, Cor.DESTAQUE, centro=(LARGURA // 2, 70))
        if self.opcoes.treino:
            desenhar_texto(tela, "MODO TREINO", 18, Cor.TEXTO_FRACO, centro=(LARGURA // 2, 112))
        palco = pygame.Rect(90, 150, 420, 420)
        desenhar_painel(tela, palco)
        sprite = Recursos.na_altura(self.previa.animador.quadro_atual, self.ALTURA_PREVIA)
        tela.blit(sprite, sprite.get_rect(midbottom=(palco.centerx, palco.bottom - 70)))
        desenhar_texto(tela, "Aluna" if self.aparencia.feminino else "Aluno", 26, Cor.TEXTO,
                       centro=(palco.centerx, palco.bottom - 40))
        for i, ((parte, rotulo), r) in enumerate(zip(self.LINHAS, self.retangulos)):
            focado = i == self.linha
            desenhar_painel(tela, r, cor_borda=Cor.DESTAQUE if focado else Cor.BORDA_ESCURA)
            desenhar_texto(tela, rotulo, 20, Cor.TEXTO_FRACO, topo_esquerda=(r.left + 22, r.centery - 10))
            nome = self.aparencia.escolha(parte)
            desenhar_texto(tela, f"<  {nome}  >", 24, Cor.DESTAQUE if focado else Cor.TEXTO,
                           centro=(r.left + 360, r.centery))
            if parte == "genero":
                continue
            cor = self.aparencia.cor(parte)
            amostra = (r.right - 44, r.centery)
            if cor is None:
                pygame.draw.circle(tela, Cor.TEXTO_FRACO, amostra, 16, 3)
            else:
                pygame.draw.circle(tela, Cor.BORDA_ESCURA, amostra, 18)
                pygame.draw.circle(tela, cor, amostra, 15)
        desenhar_texto(tela, "[Cima/Baixo] parte    [<- ->] cor    [R] sortear    [P] padrão    "
                       "[Enter] escolher classe    [Esc] voltar", 16, Cor.TEXTO_FRACO, centro=(LARGURA // 2, ALTURA - 24))
